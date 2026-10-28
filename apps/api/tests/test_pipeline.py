from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import pytest

from morning_brief import pipeline
from morning_brief.config import KST
from morning_brief.markdown import briefing_markdown

NOW = datetime(2026, 10, 27, 7, 30, tzinfo=KST)
CONTENT = {
    "summary": ["원/달러 하락"],
    "stocks": [],
    "fx": [],
    "rates_commodities": [],
    "top_news": [
        {"title": "t", "summary": "s", "bank_view": "b", "source": "연합", "link": "https://example.com/a1"}
    ],
    "bank_issues": [],
    "term": {"term": "용어", "explanation": "설명"},
    "interview": {"question": "질문", "answer_points": ["p1"]},
}


@pytest.fixture(autouse=True)
def fake_collectors(monkeypatch, quotes, articles):
    monkeypatch.setattr(pipeline, "fetch_quotes", lambda: quotes)
    monkeypatch.setattr(pipeline, "fetch_news", lambda: articles)


def test_API키가_없으면_원자료만으로_저장한다(db, settings):
    briefing = pipeline.run_once(settings, db, send_push=False, now=NOW)

    saved = db.briefings.find_one({"date": "2026-10-27"})
    assert saved["status"] == "fallback"
    assert saved["content"] is None
    assert saved["error"] == "OPENAI_API_KEY 없음"
    assert briefing["title"] == "2026년 10월 27일 (화) 아침 경제 브리핑"
    assert db.quotes.count_documents({}) == 2
    assert db.articles.count_documents({}) == 2  # 링크 없는 기사는 저장하지 않는다
    assert "AI 요약 없이" in briefing_markdown(briefing)


def test_GPT요약을_저장하고_같은날_다시_돌리면_덮어쓴다(db, settings, monkeypatch):
    monkeypatch.setattr(pipeline.summarize, "write_briefing", lambda *args: CONTENT)
    keyed = replace(settings, openai_api_key="sk-test")

    pipeline.run_once(keyed, db, send_push=False, now=NOW)
    pipeline.run_once(keyed, db, send_push=False, now=NOW)

    assert db.briefings.count_documents({}) == 1
    saved = db.briefings.find_one({"date": "2026-10-27"})
    assert saved["status"] == "ok"
    assert saved["model"] == settings.openai_model
    assert saved["content"]["summary"] == ["원/달러 하락"]
    markdown = briefing_markdown(saved)
    assert "[원문 · 연합](https://example.com/a1)" in markdown
    assert "원/달러: 1,385.50 (▼4.50, -0.32%) [2026-10-26]" in markdown


def test_GPT가_실패하면_원자료로_대체하고_오류를_남긴다(db, settings, monkeypatch):
    def boom(*args):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(pipeline.summarize, "write_briefing", boom)
    briefing = pipeline.run_once(replace(settings, openai_api_key="sk-test"), db, send_push=False, now=NOW)

    assert briefing["status"] == "fallback"
    assert "rate limited" in db.briefings.find_one()["error"]


def test_완성되면_등록된_기기에_알림을_보낸다(db, settings, monkeypatch):
    sent = []
    monkeypatch.setattr(pipeline.push, "broadcast", lambda _db, _s, payload: sent.append(payload) or {})

    pipeline.run_once(settings, db, now=NOW)

    assert sent == [
        {
            "title": "☀️ 오늘의 아침 경제 브리핑",
            "body": "2026년 10월 27일 (화) 아침 경제 브리핑",
            "url": "/briefings/2026-10-27",
        }
    ]
