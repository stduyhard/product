import json
from pathlib import Path

from app.bot.service import ProductConsultingBot

MISS_MESSAGE = (
    "\u5f53\u524d\u77e5\u8bc6\u5e93\u6ca1\u6709\u76f4\u63a5\u547d\u4e2d\u8fd9\u6761\u95ee\u9898\u3002"
    "\u5efa\u8bae\u8865\u5145\u54c1\u724c\u3001\u9884\u7b97\u3001\u5bb9\u91cf\u7b49"
    "\u5173\u952e\u8bcd\u540e\u518d\u95ee\u3002"
)


def test_bot_answer_hit_and_miss():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb.json"

    kb = [
        {
            "question": "What are midea foot bath highlights?",
            "answer": "Price around 299 CNY, constant-temp plus drain support.",
            "keywords": ["midea", "constant-temp", "drain", "foot-bath"],
        }
    ]
    kb_path.write_text(json.dumps(kb, ensure_ascii=True), encoding="utf-8")

    bot = ProductConsultingBot(str(kb_path))
    assert "299" in bot.answer("Need midea constant-temp foot-bath")
    assert MISS_MESSAGE in bot.answer("Will it sing songs?")