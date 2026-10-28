"""아침 경제 브리핑 한 번 만들기: 시세·뉴스 수집 → GPT 요약 → MongoDB 저장 → 알림(·Notion).

워커가 매일 아침 이 run_once 를 부른다. 손으로 한 번 돌릴 때는 `pnpm brief:run`.
"""

from __future__ import annotations

from datetime import datetime

from openai import OpenAI
from pymongo.database import Database

from . import notion, push, store, summarize
from .collect.market import fetch_quotes
from .collect.news import fetch_news
from .config import KST, Settings
from .markdown import briefing_markdown

WEEKDAYS = "월화수목금토일"
# AI 요약이 실패했을 때 앱에 대신 보여 줄 헤드라인 수
FALLBACK_HEADLINES = 20


def run_once(
    settings: Settings,
    db: Database,
    *,
    send_push: bool = True,
    publish_notion: bool = True,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(KST)
    date_iso = now.strftime("%Y-%m-%d")
    date_label = f"{now:%Y년 %m월 %d일} ({WEEKDAYS[now.weekday()]})"

    quotes = fetch_quotes()
    articles = fetch_news()
    print(f"[pipeline] 시세 {len(quotes)}개, 뉴스 {len(articles)}건 수집")
    store.save_quotes(db, quotes, now)
    store.save_articles(db, date_iso, articles, now)

    content, error = None, None
    if settings.openai_api_key:
        try:
            client = OpenAI(api_key=settings.openai_api_key, timeout=300, max_retries=2)
            content = summarize.write_briefing(
                client, settings.openai_model, settings.openai_reasoning_effort, date_label, quotes, articles
            )
        except Exception as e:
            error = f"GPT 요약 실패: {e}"[:1000]
            print(f"[pipeline] {error} → 원자료로 대체")
    else:
        error = "OPENAI_API_KEY 없음"
        print("[pipeline] OPENAI_API_KEY 없음 → 원자료만 정리")

    briefing = {
        "date": date_iso,
        "date_label": date_label,
        "title": f"{date_label} 아침 경제 브리핑",
        "status": "ok" if content else "fallback",
        "content": content,
        "quotes": [q.to_doc() for q in quotes],
        "headlines": [
            {"source": a.source, "title": a.title, "link": a.link} for a in articles[:FALLBACK_HEADLINES]
        ],
        "model": settings.openai_model if content else None,
        "error": error,
        "created_at": now,
    }
    store.save_briefing(db, briefing)
    print(f"[pipeline] 저장: briefings/{date_iso} ({briefing['status']})")

    if publish_notion and settings.notion_enabled:
        try:
            url = notion.publish(briefing["title"], date_iso, briefing_markdown(briefing))
            print(f"[pipeline] Notion 게시 완료: {url}")
        except Exception as e:
            print(f"[pipeline] Notion 게시 실패: {e}")

    if send_push and settings.push_enabled:
        result = push.broadcast(db, settings, push.briefing_payload(briefing))
        print(f"[pipeline] 알림 발송: {result}")

    return briefing
