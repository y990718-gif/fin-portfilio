"""웹 푸시(아이폰 홈 화면 앱 알림) 발송.

브라우저가 알려준 endpoint 주소로 서버가 직접 요청을 보내므로, 아무 주소나 받으면 서버가
내부망 등 엉뚱한 곳으로 요청을 보내게 된다. 그래서 알려진 푸시 서비스 주소만 받는다.
"""

from __future__ import annotations

import base64
import json
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pymongo.database import Database
from pywebpush import WebPushException, webpush

from . import store
from .config import Settings

# 아이폰(Safari)·크롬·파이어폭스·엣지의 푸시 서비스
_PUSH_HOSTS = {"web.push.apple.com", "fcm.googleapis.com", "updates.push.services.mozilla.com"}
_PUSH_HOST_SUFFIXES = (".push.apple.com", ".notify.windows.com")

# 폰이 꺼져 있어도 반나절 안에 켜지면 받도록
_TTL_SECONDS = 12 * 3600


def is_allowed_endpoint(endpoint: str) -> bool:
    try:
        url = urlsplit(endpoint)
        port = url.port
    except ValueError:
        return False
    host = (url.hostname or "").lower()
    return (
        url.scheme == "https"
        and port in (None, 443)
        and not url.username
        and (host in _PUSH_HOSTS or host.endswith(_PUSH_HOST_SUFFIXES))
    )


def generate_vapid_keys() -> tuple[str, str]:
    """(공개키, 비밀키)를 base64url 로 만든다. .env 의 VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY 에 넣는다."""
    key = ec.generate_private_key(ec.SECP256R1())
    private = key.private_numbers().private_value.to_bytes(32, "big")
    public = key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    return _b64url(public), _b64url(private)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def send(settings: Settings, subscription: dict, payload: dict) -> str:
    """한 기기에 보낸다. 결과: "sent" | "gone"(기기가 구독을 끊음) | "failed"."""
    try:
        webpush(
            subscription_info={"endpoint": subscription["endpoint"], "keys": subscription["keys"]},
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.vapid_private_key,
            # webpush 가 이 dict 에 aud·exp 를 써 넣으므로 기기마다 새로 만든다
            vapid_claims={"sub": settings.vapid_subject},
            ttl=_TTL_SECONDS,
            timeout=10,
        )
        return "sent"
    except WebPushException as e:
        status = e.response.status_code if e.response is not None else None
        if status in (404, 410):
            return "gone"
        print(f"[push] 발송 실패 ({status}): {e}")
        return "failed"
    except Exception as e:  # 네트워크 오류 등. 한 기기 실패가 나머지를 막지 않도록
        print(f"[push] 발송 실패: {e}")
        return "failed"


def broadcast(db: Database, settings: Settings, payload: dict) -> dict:
    """등록된 모든 기기에 보내고, 구독이 끊긴 기기는 지운다."""
    result = {"sent": 0, "gone": 0, "failed": 0}
    for subscription in store.all_push_subscriptions(db):
        outcome = send(settings, subscription, payload)
        result[outcome] += 1
        if outcome == "gone":
            store.remove_push_subscription(db, subscription["endpoint"])
    return result


def briefing_payload(briefing: dict) -> dict:
    summary = (briefing.get("content") or {}).get("summary") or []
    return {
        "title": "☀️ 오늘의 아침 경제 브리핑",
        "body": summary[0] if summary else briefing["title"],
        "url": f"/briefings/{briefing['date']}",
    }
