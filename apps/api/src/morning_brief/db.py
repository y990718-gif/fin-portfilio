"""MongoDB 연결과 인덱스.

컬렉션 구조(스키마)를 바꾸면 이미 쌓인 데이터와 어긋난다. 바꿀 때는 AGENTS.md 의 "데이터 구조" 절을 먼저 본다.

- briefings          하루 한 건. date(YYYY-MM-DD) 로 구분한다.
- quotes             지표별 일별 시세. (ticker, trade_date) 로 구분한다. 추이 그래프용.
- articles           수집한 기사 원문 정보. link 로 중복을 막는다.
- push_subscriptions 알림을 받을 기기. endpoint 로 구분한다.
"""

from __future__ import annotations

from functools import lru_cache

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

from .config import Settings, get_settings


def connect(settings: Settings) -> Database:
    client = MongoClient(settings.mongodb_uri, tz_aware=True, serverSelectionTimeoutMS=10_000)
    return client[settings.mongodb_db]


def ensure_indexes(db: Database) -> None:
    db.briefings.create_index([("date", ASCENDING)], unique=True)
    db.quotes.create_index([("ticker", ASCENDING), ("trade_date", ASCENDING)], unique=True)
    db.articles.create_index([("link", ASCENDING)], unique=True)
    db.articles.create_index([("collected_at", DESCENDING)])
    db.push_subscriptions.create_index([("endpoint", ASCENDING)], unique=True)


@lru_cache
def get_db() -> Database:
    db = connect(get_settings())
    ensure_indexes(db)
    return db
