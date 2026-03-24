import json
from pathlib import Path

from run_mvp import _load_keywords


def test_load_keywords_from_config_file():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cfg = tmp_dir / "keywords.json"
    payload = {"keywords": ["泡脚桶", "足浴盆"]}
    cfg.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    keywords = _load_keywords(str(cfg))
    assert keywords == ["泡脚桶", "足浴盆"]