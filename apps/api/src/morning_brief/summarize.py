"""수집한 시세·뉴스를 GPT(OpenAI)로 '출근 전 5분 브리핑'으로 정리.

GPT 에게는 정해진 구조(BriefingDraft)로만 답하게 한다. 숫자는 [시세 데이터]에 있는 값만 쓰게 하고,
뉴스 링크는 GPT 가 쓰지 않고 기사 번호(article_id)만 고르게 한 뒤 코드가 진짜 링크를 붙인다.
"""

from __future__ import annotations

from openai import OpenAI
from pydantic import BaseModel, Field

from .collect.market import Quote
from .collect.news import Article

SYSTEM_PROMPT = """\
당신은 은행 취업을 준비하는 사회초년생을 위해 매일 아침 경제 브리핑을 쓰는 애널리스트입니다.
독자는 출근길 5분 안에 읽고, 면접이나 업무 대화에서 오늘 시장 이야기를 할 수 있어야 합니다.

규칙:
- 숫자(지수, 환율, 금리, 등락률)는 제공된 [시세 데이터]에 있는 값만 쓰세요. 없는 숫자는 만들지 마세요.
- 뉴스 내용은 제공된 [뉴스 목록]에 근거해서만 쓰고, 추측은 '전망'이라고 분명히 표시하세요.
- 뉴스를 고를 때는 [뉴스 목록]의 번호를 article_id 로 적으세요. 링크 주소는 적지 마세요.
- 쉬운 한국어로, 문장은 짧게. 전문 용어는 처음 나올 때 괄호로 짧게 풀어 주세요.
- 각 항목은 한 문장씩, 마크다운 기호 없이 평문으로 쓰세요.
"""


class NewsPick(BaseModel):
    article_id: int = Field(description="[뉴스 목록]에서 고른 기사 번호")
    title: str = Field(description="뉴스 제목을 짧게 다듬은 것")
    summary: str = Field(description="2줄 이내 요약")
    bank_view: str = Field(
        description="은행원 관점: 예대마진, 대출 수요, 건전성, 외환, 규제 등 은행 업무와의 연결 1줄"
    )


class Term(BaseModel):
    term: str = Field(description="오늘 뉴스와 관련된 경제 용어 하나")
    explanation: str = Field(description="뜻을 2줄로, 오늘 뉴스와 연결해서")


class Interview(BaseModel):
    question: str = Field(description="오늘 이슈로 은행 면접에서 나올 법한 질문 1개")
    answer_points: list[str] = Field(description="답변의 핵심 논리 2~3개")


class BriefingDraft(BaseModel):
    """GPT 가 채우는 브리핑 구조. 앱 화면의 카드 순서와 같다."""

    summary: list[str] = Field(description="오늘 시장을 이해하는 데 가장 중요한 세 가지, 각 한 줄")
    stocks: list[str] = Field(description="국내·미국·아시아 증시 흐름과 이유, 3~4줄")
    fx: list[str] = Field(
        description="원/달러 중심 환율 움직임의 원인과 은행·수출입 기업·개인에게 주는 영향, 2~3줄"
    )
    rates_commodities: list[str] = Field(description="미 국채 금리, 유가, 금 흐름과 의미, 2~3줄")
    top_news: list[NewsPick] = Field(description="오늘의 주요 뉴스 5개")
    bank_issues: list[str] = Field(
        description="금융당국, 한국은행, 시중은행 관련 소식 2~3개. 없으면 '특별한 이슈 없음' 한 줄"
    )
    term: Term
    interview: Interview


def build_user_message(date_label: str, quotes: list[Quote], articles: list[Article]) -> str:
    quote_lines = "\n".join(f"- [{q.group}] {q.line()}" for q in quotes) or "- (시세 수집 실패)"
    news_lines = (
        "\n".join(f"{i}. ({a.source}) {a.title} | {a.summary}" for i, a in enumerate(articles, start=1))
        or "- (뉴스 수집 실패)"
    )
    return (
        f"오늘은 {date_label}입니다. 아래 데이터로 오늘 아침 브리핑을 작성하세요.\n\n"
        f"[시세 데이터] (괄호 안 날짜는 마지막 거래일)\n{quote_lines}\n\n"
        f"[뉴스 목록] (최근 24시간, 앞의 숫자가 기사 번호)\n{news_lines}"
    )


def attach_links(draft: BriefingDraft, articles: list[Article]) -> dict:
    """GPT 가 고른 기사 번호를 실제 출처·링크로 바꾼다. 없는 번호를 고른 뉴스는 버린다."""
    content = draft.model_dump()
    news = []
    for pick in draft.top_news:
        if not 1 <= pick.article_id <= len(articles):
            print(f"[summarize] 없는 기사 번호 {pick.article_id} 무시")
            continue
        article = articles[pick.article_id - 1]
        news.append(
            {
                "title": pick.title,
                "summary": pick.summary,
                "bank_view": pick.bank_view,
                "source": article.source,
                "link": article.link,
            }
        )
    content["top_news"] = news
    return content


def write_briefing(
    client: OpenAI,
    model: str,
    reasoning_effort: str | None,
    date_label: str,
    quotes: list[Quote],
    articles: list[Article],
) -> dict:
    options = {"reasoning": {"effort": reasoning_effort}} if reasoning_effort else {}
    response = client.responses.parse(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=build_user_message(date_label, quotes, articles),
        text_format=BriefingDraft,
        max_output_tokens=16_000,
        **options,
    )
    draft = response.output_parsed
    if draft is None:
        # 거절(refusal)이거나 토큰이 모자라 중간에 끊긴 경우
        raise RuntimeError(
            f"GPT 응답을 해석하지 못했습니다 (status={response.status}, "
            f"incomplete={response.incomplete_details})"
        )
    return attach_links(draft, articles)
