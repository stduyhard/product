from __future__ import annotations

from typing import Protocol

from app.bot.kb import load_knowledge_base

MISS_MESSAGE = "当前知识库没有直接命中这条问题。建议补充品牌、预算、容量等关键词后再问。"


class AIResponder(Protocol):
    def answer(self, query: str) -> str: ...


class ProductConsultingBot:
    def __init__(self, kb_path: str, ai_responder: AIResponder | None = None) -> None:
        self.knowledge = load_knowledge_base(kb_path)
        self.ai_responder = ai_responder

    def answer(self, query: str, session_id: str | None = None) -> str:
        del session_id
        query_lower = query.lower()
        scored: list[tuple[int, dict[str, object]]] = []
        for row in self.knowledge:
            raw_keywords = row.get("keywords", [])
            if not isinstance(raw_keywords, list):
                continue
            keywords = [str(k).lower() for k in raw_keywords]
            score = sum(1 for kw in keywords if kw and kw in query_lower)
            if score > 0:
                scored.append((score, row))

        if not scored:
            if self.ai_responder is not None:
                return self.ai_responder.answer(query)
            return MISS_MESSAGE

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]
        return str(best.get("answer", "暂时没有合适的答案，请补充更多商品信息后再试。"))
