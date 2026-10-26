"""MongoDB 읽기·쓰기. 컬렉션 구조는 db.py 상단 설명을 따른다."""

from __future__ import annotations

from datetime import datetime

from pymongo import DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from .collect.market import Quote
from .collect.news import Article

# 기기 등록 상한. 혼자 쓰는 앱이라 넉넉하다. 누가 주소를 알아내 등록을 쏟아 넣는 것을 막는다.
MAX_PUSH_SUBSCRIPTIONS = 20

# API 로 내보낼 때 숨기는 필드. error 는 서버 로그 확인용이다.
_BRIEFING_PUBLIC = {"_id": 0, "error": 0}


def save_quotes(db: Database, quotes: list[Quote], now: datetime) -> None:
    for q in quotes:
        doc = q.to_doc()
        db.quotes.update_one(
            {"ticker": doc["ticker"], "trade_date": doc["trade_date"]},
            {"$set": {**doc, "collected_at": now}},
            upsert=True,
        )


def save_articles(db: Database, date_iso: str, articles: list[Article], now: datetime) -> None:
    for a in articles:
        if not a.link:
            continue
        db.articles.update_one(
            {"link": a.link},
            {"$setOnInsert": {**a.to_doc(), "briefing_date": date_iso, "collected_at": now}},
            upsert=True,
        )


def save_briefing(db: Database, briefing: dict) -> None:
    """같은 날짜로 다시 만들면 덮어쓴다."""
    db.briefings.replace_one({"date": briefing["date"]}, briefing, upsert=True)


def latest_briefing(db: Database) -> dict | None:
    return db.briefings.find_one({}, _BRIEFING_PUBLIC, sort=[("date", DESCENDING)])


def get_briefing(db: Database, date_iso: str) -> dict | None:
    return db.briefings.find_one({"date": date_iso}, _BRIEFING_PUBLIC)


def list_briefings(db: Database, limit: int) -> list[dict]:
    cursor = (
        db.briefings.find({}, {"_id": 0, "date": 1, "title": 1, "status": 1, "content.summary": 1})
        .sort("date", DESCENDING)
        .limit(limit)
    )
    return [
        {
            "date": doc["date"],
            "title": doc["title"],
            "status": doc["status"],
            "headline": ((doc.get("content") or {}).get("summary") or [None])[0],
        }
        for doc in cursor
    ]


def quote_history(db: Database, ticker: str, days: int) -> list[dict]:
    cursor = (
        db.quotes.find({"ticker": ticker}, {"_id": 0, "collected_at": 0})
        .sort("trade_date", DESCENDING)
        .limit(days)
    )
    return list(reversed(list(cursor)))


def add_push_subscription(db: Database, subscription: dict, user_agent: str | None, now: datetime) -> bool:
    """새로 등록했으면 True, 이미 있던 기기면 키만 갱신하고 False. 상한을 넘으면 ValueError."""
    endpoint = subscription["endpoint"]
    if db.push_subscriptions.count_documents({"endpoint": endpoint}, limit=1):
        db.push_subscriptions.update_one(
            {"endpoint": endpoint}, {"$set": {"keys": subscription["keys"], "updated_at": now}}
        )
        return False
    if db.push_subscriptions.count_documents({}) >= MAX_PUSH_SUBSCRIPTIONS:
        raise ValueError("등록된 기기가 너무 많습니다.")
    try:
        db.push_subscriptions.insert_one(
            {
                "endpoint": endpoint,
                "keys": subscription["keys"],
                "user_agent": (user_agent or "")[:300],
                "created_at": now,
                "updated_at": now,
            }
        )
    except DuplicateKeyError:
        return False
    return True


def remove_push_subscription(db: Database, endpoint: str) -> bool:
    return db.push_subscriptions.delete_one({"endpoint": endpoint}).deleted_count > 0


def get_push_subscription(db: Database, endpoint: str) -> dict | None:
    return db.push_subscriptions.find_one({"endpoint": endpoint}, {"_id": 0})


def all_push_subscriptions(db: Database) -> list[dict]:
    return list(db.push_subscriptions.find({}, {"_id": 0}))
