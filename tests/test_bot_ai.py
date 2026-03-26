import json
from pathlib import Path

from app.bot.service import MISS_MESSAGE, ProductConsultingBot


class _FakeResponder:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.queries: list[str] = []

    def answer(self, query: str) -> str:
        self.queries.append(query)
        return self.reply


def test_bot_uses_ai_fallback_when_kb_misses():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_ai.json"
    kb_path.write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")

    responder = _FakeResponder("???????????????????")
    bot = ProductConsultingBot(str(kb_path), ai_responder=responder)

    answer = bot.answer("????????")

    assert "??" in answer
    assert responder.queries == ["????????"]


def test_bot_keeps_miss_message_without_ai_fallback():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_empty.json"
    kb_path.write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")

    bot = ProductConsultingBot(str(kb_path))

    assert bot.answer("????????") == MISS_MESSAGE
