from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import mongomock
import pytest
from fastapi.testclient import TestClient

from morning_brief.collect.market import Quote
from morning_brief.collect.news import Article
from morning_brief.config import load_settings
from morning_brief.db import ensure_indexes


@pytest.fixture
def db():
    database = mongomock.MongoClient(tz_aware=True)["test"]
    ensure_indexes(database)
    return database


@pytest.fixture
def settings(monkeypatch):
    for name in ("OPENAI_API_KEY", "NOTION_TOKEN", "NOTION_DATABASE_ID", "WEB_DIST"):
        monkeypatch.delenv(name, raising=False)
    return replace(
        load_settings(),
        vapid_public_key="BPublicKeyForTests",
        vapid_private_key="private-key-for-tests",
        vapid_subject="mailto:test@example.com",
    )


@pytest.fixture
def client(db, settings):
    from morning_brief.api import create_app
    from morning_brief.api.routes import db_dep, settings_dep

    app = create_app(settings)
    app.dependency_overrides[db_dep] = lambda: db
    app.dependency_overrides[settings_dep] = lambda: settings
    return TestClient(app)


@pytest.fixture
def quotes():
    return [
        Quote("증시", "코스피", "^KS11", 2650.12, 2630.0, "2026-10-26", 2),
        Quote("환율", "원/달러", "KRW=X", 1385.5, 1390.0, "2026-10-26", 2),
    ]


@pytest.fixture
def articles():
    published = datetime(2026, 10, 26, 22, 0, tzinfo=UTC)
    return [
        Article("연합뉴스 경제", "한은 기준금리 동결", "https://example.com/a1", "요약1", published),
        Article("CNBC Markets", "Fed signals pause", "https://example.com/a2", "summary2", published),
        Article("매일경제 경제", "링크 없는 기사", "", "요약3", None),
    ]
