from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from fastapi.testclient import TestClient

from morning_brief import push
from morning_brief.api import create_app
from morning_brief.config import KST

APPLE_ENDPOINT = "https://web.push.apple.com/QGkG4c8Fv2abcdef"
KEYS = {
    "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
    "auth": "tBHItJI5svbpez7KI4CCXg",
}


def _briefing(date: str) -> dict:
    return {
        "date": date,
        "title": f"{date} 아침 경제 브리핑",
        "status": "ok",
        "content": {"summary": [f"{date} 첫 줄"]},
        "quotes": [],
        "headlines": [],
        "error": "내부 오류 내용",
        "created_at": datetime.now(KST),
    }


def test_브리핑이_없으면_404(client):
    response = client.get("/api/briefings/latest")
    assert response.status_code == 404


def test_최신_목록_날짜별_조회(client, db):
    db.briefings.insert_many([_briefing("2026-10-26"), _briefing("2026-10-27")])

    latest = client.get("/api/briefings/latest").json()
    assert latest["date"] == "2026-10-27"
    assert "error" not in latest and "_id" not in latest

    listing = client.get("/api/briefings?limit=5").json()
    assert [b["date"] for b in listing] == ["2026-10-27", "2026-10-26"]
    assert listing[0]["headline"] == "2026-10-27 첫 줄"

    assert client.get("/api/briefings/2026-10-26").json()["date"] == "2026-10-26"
    assert client.get("/api/briefings/2026-01-01").status_code == 404
    assert client.get("/api/briefings/not-a-date").status_code == 422


def test_시세_추이는_오래된_순으로(client, db):
    for day in ("2026-10-22", "2026-10-23", "2026-10-26"):
        db.quotes.insert_one(
            {"ticker": "KRW=X", "trade_date": day, "price": 1380.0, "collected_at": datetime.now(KST)}
        )

    history = client.get("/api/quotes/KRW=X/history?days=2").json()
    assert [q["trade_date"] for q in history] == ["2026-10-23", "2026-10-26"]
    assert "collected_at" not in history[0]


def test_알림_등록_해제(client, db):
    assert client.get("/api/push/public-key").json() == {"public_key": "BPublicKeyForTests"}

    first = client.post("/api/push/subscriptions", json={"endpoint": APPLE_ENDPOINT, "keys": KEYS})
    again = client.post("/api/push/subscriptions", json={"endpoint": APPLE_ENDPOINT, "keys": KEYS})
    assert first.status_code == 201 and first.json() == {"created": True}
    assert again.json() == {"created": False}
    assert db.push_subscriptions.count_documents({}) == 1

    assert client.post("/api/push/unsubscribe", json={"endpoint": APPLE_ENDPOINT}).json() == {"removed": True}
    assert db.push_subscriptions.count_documents({}) == 0


def test_푸시서비스가_아닌_주소는_등록하지_않는다(client, db):
    response = client.post(
        "/api/push/subscriptions", json={"endpoint": "https://192.168.0.1/x", "keys": KEYS}
    )
    assert response.status_code == 400
    assert db.push_subscriptions.count_documents({}) == 0


def test_기기_수_상한을_넘으면_거부한다(client, db, monkeypatch):
    monkeypatch.setattr("morning_brief.store.MAX_PUSH_SUBSCRIPTIONS", 1)
    client.post("/api/push/subscriptions", json={"endpoint": APPLE_ENDPOINT, "keys": KEYS})
    response = client.post("/api/push/subscriptions", json={"endpoint": APPLE_ENDPOINT + "2", "keys": KEYS})
    assert response.status_code == 409


def test_시험알림은_등록된_기기에만(client, monkeypatch):
    monkeypatch.setattr(push, "send", lambda *args: "sent")
    assert client.post("/api/push/test", json={"endpoint": APPLE_ENDPOINT}).status_code == 404

    client.post("/api/push/subscriptions", json={"endpoint": APPLE_ENDPOINT, "keys": KEYS})
    assert client.post("/api/push/test", json={"endpoint": APPLE_ENDPOINT}).json() == {"result": "sent"}


def test_VAPID설정이_없으면_알림API는_503(client, settings):
    client.app.dependency_overrides.clear()
    from morning_brief.api.routes import settings_dep

    client.app.dependency_overrides[settings_dep] = lambda: replace(settings, vapid_private_key=None)
    assert client.get("/api/push/public-key").status_code == 503


def test_빌드된_웹을_함께_서빙한다(tmp_path, settings):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (dist / "assets" / "app-abc.js").write_text("js")
    (dist / "sw.js").write_text("sw")
    (tmp_path / "secret.env").write_text("OPENAI_API_KEY=sk-secret")
    client = TestClient(create_app(replace(settings, web_dist=str(dist))))

    page = client.get("/briefings/2026-10-27")
    assert page.text == "<html>app</html>" and page.headers["cache-control"] == "no-cache"
    assert "immutable" in client.get("/assets/app-abc.js").headers["cache-control"]
    assert client.get("/sw.js").headers["cache-control"] == "no-cache"
    assert client.get("/api/unknown").status_code == 404
    # dist 바깥 파일은 인코딩된 ../ 로도 읽을 수 없다
    assert client.get("/%2e%2e/secret.env").text == "<html>app</html>"
    assert client.get("/assets/%2e%2e/%2e%2e/secret.env").text == "<html>app</html>"
