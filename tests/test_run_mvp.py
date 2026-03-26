import json
from pathlib import Path

from app.settings import settings
from run_mvp import _load_keywords


def test_load_keywords_from_config_file():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cfg = tmp_dir / "keywords.json"
    payload = {"keywords": ["泡脚桶", "足浴盆"]}
    cfg.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    old_override = settings.keywords_override
    settings.keywords_override = ""
    try:
        keywords = _load_keywords(str(cfg))
    finally:
        settings.keywords_override = old_override

    assert keywords == ["泡脚桶", "足浴盆"]


def test_load_keywords_prefers_settings_override():
    old_override = settings.keywords_override
    settings.keywords_override = "泡脚桶"
    try:
        keywords = _load_keywords("config/keywords.json")
    finally:
        settings.keywords_override = old_override

    assert keywords == ["泡脚桶"]


def test_load_keywords_repairs_mojibake_override():
    old_override = settings.keywords_override
    settings.keywords_override = "æ³¡èæ¡¶"
    try:
        keywords = _load_keywords("config/keywords.json")
    finally:
        settings.keywords_override = old_override

    assert keywords == ["泡脚桶"]
