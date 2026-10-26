"""수집한 시세·뉴스를 Claude로 '출근 전 5분 브리핑'으로 정리."""

from __future__ import annotations

import anthropic

from .market import Quote
from .news import Article

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """\
당신은 은행 취업을 준비하는 사회초년생을 위해 매일 아침 경제 브리핑을 쓰는 애널리스트입니다.
독자는 출근길 5분 안에 읽고, 면접이나 업무 대화에서 오늘 시장 이야기를 할 수 있어야 합니다.

규칙:
- 숫자(지수, 환율, 금리, 등락률)는 제공된 [시세 데이터]에 있는 값만 쓰세요. 없는 숫자는 만들지 마세요.
- 뉴스 내용은 제공된 [뉴스 목록]에 근거해서만 쓰고, 추측은 '전망'이라고 분명히 표시하세요.
- 쉬운 한국어로, 문장은 짧게. 전문 용어는 처음 나올 때 괄호로 짧게 풀어 주세요.
- 형식은 아래 마크다운 구조를 정확히 따르세요. 사용할 수 있는 문법: '## ', '### ', '- ', '**굵게**', '[제목](링크)', '> '. 표와 코드블록은 쓰지 마세요.

## 🧭 오늘의 3줄 요약
- (오늘 시장을 이해하는 데 가장 중요한 세 가지, 각 한 줄)

## 📈 증시
- (국내·미국·아시아 증시 흐름과 이유, 3~4줄)

## 💱 환율
- (원/달러 중심. 움직임의 원인과 은행·수출입 기업·개인에게 주는 영향, 2~3줄)

## 🏦 금리·원자재
- (미 국채 금리, 유가, 금 흐름과 의미, 2~3줄)

## 📰 주요 뉴스 5선
### 1. (뉴스 제목을 짧게)
- 요약: (2줄 이내)
- 은행원 관점: (예대마진, 대출 수요, 건전성, 외환, 규제 등 은행 업무와의 연결 1줄)
- [원문](링크)
(같은 형식으로 5개)

## 🏛️ 은행·금융권 이슈
- (금융당국, 한국은행, 시중은행 관련 소식 2~3개. 없으면 '특별한 이슈 없음')

## 📚 오늘의 경제 용어
- **용어**: 뜻을 2줄로, 오늘 뉴스와 연결해서

## 🎤 면접 대비 한 문장
- 질문: (오늘 이슈로 은행 면접에서 나올 법한 질문 1개)
- 답변 포인트: (핵심 논리 2~3개)
"""


def _build_user_message(date_label: str, quotes: list[Quote], articles: list[Article]) -> str:
    quote_lines = "\n".join(f"- [{q.group}] {q.line()}" for q in quotes) or "- (시세 수집 실패)"
    news_lines = "\n".join(
        f"- ({a.source}) {a.title} | {a.summary} | {a.link}" for a in articles
    ) or "- (뉴스 수집 실패)"
    return (
        f"오늘은 {date_label}입니다. 아래 데이터로 오늘 아침 브리핑을 작성하세요.\n\n"
        f"[시세 데이터] (괄호 안 날짜는 마지막 거래일)\n{quote_lines}\n\n"
        f"[뉴스 목록] (최근 24시간)\n{news_lines}"
    )


def write_briefing(date_label: str, quotes: list[Quote], articles: list[Article]) -> str:
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_message(date_label, quotes, articles)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude가 요청을 거절했습니다 (stop_reason=refusal).")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise RuntimeError(f"Claude 응답에 본문이 없습니다 (stop_reason={response.stop_reason}).")
    return text


def fallback_briefing(quotes: list[Quote], articles: list[Article]) -> str:
    """API 키가 없거나 Claude 호출이 실패했을 때: 요약 없이 원자료만 정리."""
    lines = ["## ⚠️ AI 요약 없이 원자료만 정리했습니다", ""]
    lines.append("## 📰 헤드라인")
    lines += [f"- ({a.source}) [{a.title}]({a.link})" for a in articles[:20]]
    return "\n".join(lines)


def market_markdown(quotes: list[Quote]) -> str:
    """시세 숫자는 AI를 거치지 않고 코드에서 직접 만든다."""
    lines = ["## 📊 오늘의 시세"]
    for group in ("증시", "환율", "금리·원자재"):
        rows = [q for q in quotes if q.group == group]
        if rows:
            lines.append(f"### {group}")
            lines += [f"- {q.line()}" for q in rows]
    return "\n".join(lines)
