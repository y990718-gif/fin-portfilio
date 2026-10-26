"""아침 경제 브리핑: 시세·뉴스 수집 → Claude 요약 → 파일 저장 → Notion 게시.

사용법:
    python main.py              # 전체 실행 (Notion 게시 포함)
    python main.py --no-notion  # Notion 없이 reports/ 폴더에만 저장
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from brief import notion
from brief.market import fetch_quotes
from brief.news import fetch_news
from brief.report import fallback_briefing, market_markdown, write_briefing

KST = ZoneInfo("Asia/Seoul")
WEEKDAYS = "월화수목금토일"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-notion", action="store_true", help="Notion에 올리지 않음")
    args = parser.parse_args()

    now = datetime.now(KST)
    date_iso = now.strftime("%Y-%m-%d")
    date_label = f"{now:%Y년 %m월 %d일} ({WEEKDAYS[now.weekday()]})"
    title = f"{date_label} 아침 경제 브리핑"

    quotes = fetch_quotes()
    articles = fetch_news()
    print(f"[main] 시세 {len(quotes)}개, 뉴스 {len(articles)}건 수집")

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            body = write_briefing(date_label, quotes, articles)
        except Exception as e:
            print(f"[main] Claude 요약 실패, 원자료로 대체: {e}")
            body = fallback_briefing(quotes, articles)
    else:
        print("[main] ANTHROPIC_API_KEY 없음 → 원자료만 정리")
        body = fallback_briefing(quotes, articles)

    markdown = "\n\n".join([
        body,
        market_markdown(quotes),
        "## ✍️ 오늘 내 생각 한 줄\n- ",
    ])

    out = Path("reports") / f"{date_iso}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(f"# {title}\n\n{markdown}\n", encoding="utf-8")
    print(f"[main] 저장: {out}")

    if args.no_notion:
        return 0
    if not (os.environ.get("NOTION_TOKEN") and os.environ.get("NOTION_DATABASE_ID")):
        print("[main] NOTION_TOKEN / NOTION_DATABASE_ID 없음 → Notion 게시 건너뜀")
        return 0
    url = notion.publish(title, date_iso, markdown)
    print(f"[main] Notion 게시 완료: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
