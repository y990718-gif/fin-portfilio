"""저장된 브리핑을 마크다운으로 바꾼다. Notion 게시와 터미널 미리보기에 쓴다."""

from __future__ import annotations

GROUPS = ("증시", "환율", "금리·원자재")


def quote_line(q: dict) -> str:
    digits = q["digits"]
    arrow = "▲" if q["change"] > 0 else "▼" if q["change"] < 0 else "–"
    return (
        f"{q['name']}: {q['price']:,.{digits}f} "
        f"({arrow}{abs(q['change']):,.{digits}f}, {q['change_pct']:+.2f}%) [{q['trade_date']}]"
    )


def _bullets(lines: list[str]) -> list[str]:
    return [f"- {line}" for line in lines]


def briefing_markdown(briefing: dict) -> str:
    content = briefing.get("content")
    lines: list[str] = []
    if content:
        lines += ["## 🧭 오늘의 3줄 요약", *_bullets(content["summary"]), ""]
        lines += ["## 📈 증시", *_bullets(content["stocks"]), ""]
        lines += ["## 💱 환율", *_bullets(content["fx"]), ""]
        lines += ["## 🏦 금리·원자재", *_bullets(content["rates_commodities"]), ""]
        lines.append("## 📰 주요 뉴스")
        for i, news in enumerate(content["top_news"], start=1):
            lines += [
                f"### {i}. {news['title']}",
                f"- 요약: {news['summary']}",
                f"- 은행원 관점: {news['bank_view']}",
                f"- [원문 · {news['source']}]({news['link']})",
            ]
        lines += ["", "## 🏛️ 은행·금융권 이슈", *_bullets(content["bank_issues"]), ""]
        term = content["term"]
        lines += ["## 📚 오늘의 경제 용어", f"- **{term['term']}**: {term['explanation']}", ""]
        interview = content["interview"]
        lines += [
            "## 🎤 면접 대비 한 문장",
            f"- 질문: {interview['question']}",
            *[f"- 답변 포인트: {point}" for point in interview["answer_points"]],
            "",
        ]
    else:
        lines += ["## ⚠️ AI 요약 없이 원자료만 정리했습니다", "", "## 📰 헤드라인"]
        lines += [f"- ({h['source']}) [{h['title']}]({h['link']})" for h in briefing.get("headlines", [])]
        lines.append("")

    lines.append("## 📊 오늘의 시세")
    for group in GROUPS:
        rows = [q for q in briefing.get("quotes", []) if q["group"] == group]
        if rows:
            lines.append(f"### {group}")
            lines += [f"- {quote_line(q)}" for q in rows]
    lines += ["", "## ✍️ 오늘 내 생각 한 줄", "- "]
    return "\n".join(lines)
