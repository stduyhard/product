import json
from pathlib import Path

from app.bot.service import MISS_MESSAGE, ProductConsultingBot


def test_bot_answer_hit_and_miss():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb.json"

    kb = [
        {
            "question": "美的泡脚桶有什么特点？",
            "answer": "价格约299元，支持恒温和排水，适合作为主力款参考。",
            "keywords": ["美的", "恒温", "排水", "泡脚桶"],
        }
    ]
    kb_path.write_text(json.dumps(kb, ensure_ascii=False), encoding="utf-8")

    bot = ProductConsultingBot(str(kb_path))
    assert "299" in bot.answer("想看美的恒温泡脚桶")
    assert MISS_MESSAGE in bot.answer("它会唱歌吗？")
