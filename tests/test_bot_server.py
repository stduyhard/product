from fastapi.testclient import TestClient

import app.bot.server as server_module
from app.bot.server import app


class _FakeBot:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def answer(self, text: str, session_id: str | None = None) -> str:
        self.calls.append((text, session_id))
        return "????"


def test_feishu_webhook_returns_utf8_json_content_type():
    fake_bot = _FakeBot()
    original = server_module.bot
    server_module.bot = fake_bot
    try:
        client = TestClient(app)
        response = client.post(
            "/feishu/webhook",
            json={"token": "dev-token", "event": {"text": "???????"}},
        )
    finally:
        server_module.bot = original

    assert response.status_code == 200
    assert "charset=utf-8" in response.headers["content-type"].lower()
    assert fake_bot.calls == [("???????", None)]


def test_chat_endpoint_returns_utf8_json_answer():
    fake_bot = _FakeBot()
    original = server_module.bot
    server_module.bot = fake_bot
    try:
        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"text": "?????????"},
        )
    finally:
        server_module.bot = original

    assert response.status_code == 200
    assert response.json()["text"] == "????"
    assert "charset=utf-8" in response.headers["content-type"].lower()
    assert fake_bot.calls == [("?????????", None)]


def test_chat_endpoint_rejects_empty_text():
    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"text": ""},
    )

    assert response.status_code == 422


def test_chat_endpoint_accepts_session_id():
    fake_bot = _FakeBot()
    original = server_module.bot
    server_module.bot = fake_bot
    try:
        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"text": "?????????", "session_id": "demo-session"},
        )
    finally:
        server_module.bot = original

    assert response.status_code == 200
    assert response.json()["text"] == "????"
    assert fake_bot.calls == [("?????????", "demo-session")]



def test_chat_endpoint_returns_cors_headers_for_vue_dev_server():
    client = TestClient(app)
    response = client.options(
        "/chat",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"



def test_dashboard_summary_endpoint_returns_snapshot(tmp_path, monkeypatch):
    dashboard_file = tmp_path / "dashboard_summary.json"
    dashboard_file.write_text(
        '{"summary":{"total":12,"avg_price":288.5},"charts":{"brand_top":[{"brand":"midea","count":5}],"price_band":[{"band":"200-399","count":7}],"feature_coverage":[{"feature":"??","count":6}],"shop_type_share":[{"shop_type":"flagship","count":12}]}}',
        encoding="utf-8",
    )

    import app.bot.server as server_module
    monkeypatch.setattr(server_module, "DASHBOARD_PATH", dashboard_file)

    client = TestClient(app)
    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["summary"]["total"] == 12
    assert response.json()["charts"]["brand_top"][0]["brand"] == "midea"
