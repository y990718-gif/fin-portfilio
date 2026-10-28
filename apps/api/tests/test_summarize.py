from __future__ import annotations

from types import SimpleNamespace

import pytest

from morning_brief.summarize import (
    BriefingDraft,
    Interview,
    NewsPick,
    Term,
    build_user_message,
    write_briefing,
)


def _draft(*article_ids: int) -> BriefingDraft:
    return BriefingDraft(
        summary=["요약 1", "요약 2", "요약 3"],
        stocks=["증시"],
        fx=["환율"],
        rates_commodities=["금리"],
        top_news=[NewsPick(article_id=i, title=f"뉴스 {i}", summary="s", bank_view="b") for i in article_ids],
        bank_issues=["특별한 이슈 없음"],
        term=Term(term="기준금리", explanation="설명"),
        interview=Interview(question="질문", answer_points=["포인트"]),
    )


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed, status="completed", incomplete_details=None)


def test_기사번호를_실제_링크로_바꾸고_없는_번호는_버린다(quotes, articles):
    fake = FakeResponses(_draft(2, 99, 1))
    client = SimpleNamespace(responses=fake)

    content = write_briefing(client, "gpt-test", "medium", "2026년 10월 27일 (화)", quotes, articles)

    assert [n["link"] for n in content["top_news"]] == ["https://example.com/a2", "https://example.com/a1"]
    assert content["top_news"][0]["source"] == "CNBC Markets"
    assert "article_id" not in content["top_news"][0]
    call = fake.calls[0]
    assert call["model"] == "gpt-test"
    assert call["reasoning"] == {"effort": "medium"}
    assert call["text_format"] is BriefingDraft


def test_추론강도가_비어있으면_reasoning_을_보내지_않는다(quotes, articles):
    fake = FakeResponses(_draft(1))
    write_briefing(SimpleNamespace(responses=fake), "gpt-test", None, "오늘", quotes, articles)
    assert "reasoning" not in fake.calls[0]


def test_해석된_응답이_없으면_실패한다(quotes, articles):
    client = SimpleNamespace(responses=FakeResponses(None))
    with pytest.raises(RuntimeError, match="해석하지 못했습니다"):
        write_briefing(client, "gpt-test", "medium", "오늘", quotes, articles)


def test_뉴스에는_번호만_붙고_링크는_넘기지_않는다(quotes, articles):
    message = build_user_message("오늘", quotes, articles)
    assert "1. (연합뉴스 경제) 한은 기준금리 동결" in message
    assert "https://example.com" not in message
    assert "원/달러: 1,385.50" in message
