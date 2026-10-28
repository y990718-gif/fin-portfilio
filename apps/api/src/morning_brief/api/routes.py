"""앱(apps/web)이 부르는 API. 모든 경로는 /api 로 시작한다."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field
from pymongo.database import Database

from .. import push, store
from ..config import KST, Settings, get_settings
from ..db import get_db

router = APIRouter(prefix="/api")

_B64URL = r"^[A-Za-z0-9_\-=]+$"


def db_dep() -> Database:
    return get_db()


def settings_dep() -> Settings:
    return get_settings()


class PushKeys(BaseModel):
    p256dh: str = Field(max_length=200, pattern=_B64URL)
    auth: str = Field(max_length=100, pattern=_B64URL)


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(max_length=1000)
    keys: PushKeys


class EndpointIn(BaseModel):
    endpoint: str = Field(max_length=1000)


@router.get("/health")
def health(db: Database = Depends(db_dep)) -> dict:
    db.command("ping")
    return {"ok": True}


@router.get("/briefings/latest")
def latest_briefing(db: Database = Depends(db_dep)) -> dict:
    briefing = store.latest_briefing(db)
    if briefing is None:
        raise HTTPException(404, "아직 만들어진 브리핑이 없습니다.")
    return briefing


@router.get("/briefings")
def list_briefings(limit: int = Query(30, ge=1, le=100), db: Database = Depends(db_dep)) -> list[dict]:
    return store.list_briefings(db, limit)


@router.get("/briefings/{date}")
def get_briefing(date: str = Path(pattern=r"^\d{4}-\d{2}-\d{2}$"), db: Database = Depends(db_dep)) -> dict:
    briefing = store.get_briefing(db, date)
    if briefing is None:
        raise HTTPException(404, f"{date} 브리핑이 없습니다.")
    return briefing


@router.get("/quotes/{ticker}/history")
def quote_history(
    ticker: str = Path(max_length=20, pattern=r"^[\w^=.\-]+$"),
    days: int = Query(30, ge=1, le=365),
    db: Database = Depends(db_dep),
) -> list[dict]:
    return store.quote_history(db, ticker, days)


def _require_push(settings: Settings) -> None:
    if not settings.push_enabled:
        raise HTTPException(503, "서버에 알림 설정(VAPID)이 없습니다.")


@router.get("/push/public-key")
def push_public_key(settings: Settings = Depends(settings_dep)) -> dict:
    _require_push(settings)
    return {"public_key": settings.vapid_public_key}


@router.post("/push/subscriptions", status_code=201)
def subscribe(
    body: PushSubscriptionIn,
    request: Request,
    db: Database = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
) -> dict:
    _require_push(settings)
    if not push.is_allowed_endpoint(body.endpoint):
        raise HTTPException(400, "지원하지 않는 알림 주소입니다.")
    try:
        created = store.add_push_subscription(
            db, body.model_dump(), request.headers.get("user-agent"), datetime.now(KST)
        )
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    return {"created": created}


@router.post("/push/unsubscribe")
def unsubscribe(body: EndpointIn, db: Database = Depends(db_dep)) -> dict:
    return {"removed": store.remove_push_subscription(db, body.endpoint)}


@router.post("/push/test")
def send_test_push(
    body: EndpointIn, db: Database = Depends(db_dep), settings: Settings = Depends(settings_dep)
) -> dict:
    """이미 등록된 이 기기에만 시험 알림을 보낸다."""
    _require_push(settings)
    subscription = store.get_push_subscription(db, body.endpoint)
    if subscription is None:
        raise HTTPException(404, "등록되지 않은 기기입니다. 알림을 먼저 켜 주세요.")
    outcome = push.send(
        settings,
        subscription,
        {"title": "🔔 알림 테스트", "body": "내일 아침 브리핑도 이렇게 도착해요.", "url": "/"},
    )
    if outcome == "gone":
        store.remove_push_subscription(db, body.endpoint)
    return {"result": outcome}
