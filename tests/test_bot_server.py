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
