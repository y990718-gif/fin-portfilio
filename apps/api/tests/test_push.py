from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest
from py_vapid import Vapid02
from pywebpush import WebPushException

from morning_brief import push, store
from morning_brief.config import KST

APPLE_ENDPOINT = "https://web.push.apple.com/QGkG4c8Fv2abcdef"


@pytest.mark.parametrize(
    "endpoint",
    [
        APPLE_ENDPOINT,
        "https://fcm.googleapis.com/fcm/send/abc",
        "https://updates.push.services.mozilla.com/wpush/v2/abc",
        "https://wns2-par02p.notify.windows.com/w/?token=abc",
    ],
)
def test_알려진_푸시서비스는_허용한다(endpoint):
    assert push.is_allowed_endpoint(endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://web.push.apple.com/abc",  # https 아님
        "https://web.push.apple.com:8443/abc",  # 다른 포트
        "https://web.push.apple.com.evil.com/abc",
        "https://user@web.push.apple.com/abc",
        "https://192.168.0.10/abc",  # 내부망
        "https://localhost/abc",
        "not a url",
    ],
)
def test_그밖의_주소는_막는다(endpoint):
    assert not push.is_allowed_endpoint(endpoint)


def test_생성한_VAPID키는_발송라이브러리가_읽을_수_있다():
    public, private = push.generate_vapid_keys()
    vapid = Vapid02.from_string(private)
    assert vapid.public_key is not None
    assert len(public) == 87  # 65바이트 공개키의 base64url


def test_구독이_끊긴_기기는_발송하면서_지운다(db, settings, monkeypatch):
    now = datetime.now(KST)
    store.add_push_subscription(
        db, {"endpoint": APPLE_ENDPOINT, "keys": {"p256dh": "k", "auth": "a"}}, None, now
    )
    alive = "https://fcm.googleapis.com/fcm/send/alive"
    store.add_push_subscription(db, {"endpoint": alive, "keys": {"p256dh": "k", "auth": "a"}}, None, now)
    claims_seen = []

    def fake_webpush(subscription_info, vapid_claims, **kwargs):
        claims_seen.append(vapid_claims)
        if subscription_info["endpoint"] == APPLE_ENDPOINT:
            raise WebPushException("gone", response=SimpleNamespace(status_code=410))

    monkeypatch.setattr(push, "webpush", fake_webpush)
    result = push.broadcast(db, settings, {"title": "t", "body": "b", "url": "/"})

    assert result == {"sent": 1, "gone": 1, "failed": 0}
    assert [s["endpoint"] for s in store.all_push_subscriptions(db)] == [alive]
    assert claims_seen[0] is not claims_seen[1]  # 기기마다 새 claims (aud 가 섞이지 않게)
