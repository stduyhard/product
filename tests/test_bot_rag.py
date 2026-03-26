import json
from pathlib import Path

from app.bot.rag import LangChainRAGResponder


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[object] = []

    def invoke(self, prompt_value, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(prompt_value)

        class _Message:
            def __init__(self, content: str) -> None:
                self.content = content

        return _Message(self.content)


def test_rag_responder_uses_kb_context_in_langchain_chain():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag.json"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "恒温泡脚桶有什么特点？",
                    "answer": "支持恒温、排水方便，适合冬季家用。",
                    "keywords": ["恒温", "排水", "泡脚桶"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    llm = _FakeLLM("建议优先选择恒温和排水设计。")
    responder = LangChainRAGResponder(str(kb_path), llm=llm)

    answer = responder.answer("恒温泡脚桶怎么选？")

    assert answer == "建议优先选择恒温和排水设计。"
    assert len(llm.calls) == 1
    prompt_text = llm.calls[0].to_string()
    assert "支持恒温、排水方便，适合冬季家用。" in prompt_text
    assert "恒温泡脚桶怎么选？" in prompt_text


def test_rag_responder_returns_default_message_when_no_context():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag_empty.json"
    kb_path.write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")

    responder = LangChainRAGResponder(str(kb_path), llm=_FakeLLM("不会被调用"))

    answer = responder.answer("这个会唱歌吗？")

    assert "知识库" in answer


def test_rag_responder_can_retrieve_without_explicit_keywords():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag_vector.json"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "深桶恒温足浴盆适合什么人？",
                    "answer": "深桶设计更适合冬季家用，配合恒温功能体验更稳定。",
                    "keywords": [],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    llm = _FakeLLM("更推荐冬季家用场景，优先考虑深桶和恒温。")
    responder = LangChainRAGResponder(str(kb_path), llm=llm)

    answer = responder.answer("冬天家里用的恒温泡脚桶怎么选？")

    assert answer == "更推荐冬季家用场景，优先考虑深桶和恒温。"


def test_rag_responder_persists_vector_cache_files():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag_cache.json"
    cache_path = tmp_dir / "kb_rag_cache"
    manifest_path = tmp_dir / "kb_rag_cache.meta.json"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "足浴盆容量怎么选？",
                    "answer": "两人家庭可优先看中大容量款。",
                    "keywords": ["容量"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    LangChainRAGResponder(str(kb_path), llm=_FakeLLM("ok"), cache_path=str(cache_path))

    assert cache_path.exists()
    assert manifest_path.exists()
    assert (cache_path / "chroma.sqlite3").exists()


def test_rag_responder_rebuilds_cache_when_kb_changes():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag_cache_refresh.json"
    cache_path = tmp_dir / "kb_rag_cache_refresh"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "泡脚桶排水重要吗？",
                    "answer": "排水方便能提升清洁体验。",
                    "keywords": ["排水"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    responder = LangChainRAGResponder(
        str(kb_path),
        llm=_FakeLLM("初始回答"),
        cache_path=str(cache_path),
    )
    assert responder.answer("排水重要吗？") == "初始回答"

    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "泡脚桶折叠功能有必要吗？",
                    "answer": "小户型更适合折叠款，收纳更方便。",
                    "keywords": [],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    refreshed = LangChainRAGResponder(
        str(kb_path),
        llm=_FakeLLM("更新后的回答"),
        cache_path=str(cache_path),
    )

    assert refreshed.answer("小户型泡脚桶怎么选？") == "更新后的回答"


def test_rag_responder_uses_chroma_for_persistent_store():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag_chroma.json"
    cache_path = tmp_dir / "kb_rag_chroma"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "泡脚桶深桶设计有必要吗？",
                    "answer": "冬季家用更适合深桶设计。",
                    "keywords": [],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    responder = LangChainRAGResponder(
        str(kb_path),
        llm=_FakeLLM("可以优先考虑深桶。"),
        cache_path=str(cache_path),
    )

    assert responder.vector_store.__class__.__name__ == "Chroma"


def test_rag_responder_includes_session_history_in_follow_up_turn():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag_memory.json"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "恒温泡脚桶有什么特点？",
                    "answer": "恒温功能适合冬季持续泡脚。",
                    "keywords": ["恒温", "泡脚桶"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    llm = _FakeLLM("第二轮回答")
    responder = LangChainRAGResponder(str(kb_path), llm=llm)

    responder.answer("恒温泡脚桶怎么选？", session_id="demo-session")
    responder.answer("那预算300左右呢？", session_id="demo-session")

    prompt_text = llm.calls[-1].to_string()
    assert "恒温泡脚桶怎么选？" in prompt_text
    assert "那预算300左右呢？" in prompt_text
    assert "第二轮回答" in prompt_text


def test_rag_responder_isolates_different_sessions():
    tmp_dir = Path("data/test-tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    kb_path = tmp_dir / "kb_rag_sessions.json"
    kb_path.write_text(
        json.dumps(
            [
                {
                    "question": "按摩泡脚桶有什么特点？",
                    "answer": "按摩功能更适合放松场景。",
                    "keywords": ["按摩", "泡脚桶"],
                },
                {
                    "question": "泡脚桶预算多少合适？",
                    "answer": "300元左右适合作为主力价格带。",
                    "keywords": ["预算", "300元"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    llm = _FakeLLM("会话回答")
    responder = LangChainRAGResponder(str(kb_path), llm=llm)

    responder.answer("按摩泡脚桶怎么选？", session_id="session-a")
    responder.answer("预算多少合适？", session_id="session-b")

    prompt_text = llm.calls[-1].to_string()
    assert "用户：按摩泡脚桶怎么选？\n助手：会话回答" not in prompt_text
    assert "预算多少合适？" in prompt_text
