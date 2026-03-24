from __future__ import annotations

from app.bot.kb import load_knowledge_base


class ProductConsultingBot:
    def __init__(self, kb_path: str) -> None:
        self.knowledge = load_knowledge_base(kb_path)

    def answer(self, query: str) -> str:
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
            return "当前知识库没有直接命中这条问题。建议补充品牌、预算、容量等关键词后再问。"

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]
        return str(best.get("answer", "暂无答案"))