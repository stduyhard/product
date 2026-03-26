from __future__ import annotations

from app.analysis.ai_summary import DeepSeekAnalyzer


class DeepSeekConsultingResponder:
    def __init__(self, analyzer: DeepSeekAnalyzer) -> None:
        self.analyzer = analyzer

    def answer(self, query: str) -> str:
        return self.analyzer.answer_product_question(query)
