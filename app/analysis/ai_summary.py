from __future__ import annotations

import json
from typing import Any, Protocol

from pydantic import SecretStr

from app.models import ProductRecord


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


class SupportsInvoke(Protocol):
    def invoke(self, *args: Any, **kwargs: Any) -> object: ...


class DeepSeekAnalyzer:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        llm: SupportsInvoke | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = _chat_completions_url(base_url)
        self.model = model
        self.llm = llm or self._build_llm()

    def _build_llm(self) -> SupportsInvoke:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=SecretStr(self.api_key),
            base_url=self.base_url.removesuffix("/chat/completions"),
            model=self.model,
            temperature=0.3,
        )

    def generate_market_summary(
        self,
        records: list[ProductRecord],
        metrics: dict[str, Any],
    ) -> str:
        prompt = self._build_market_prompt(records, metrics)
        return self._invoke(
            system_prompt=(
                "你是一名电商市场分析师，请基于结构化商品数据给出简洁、可执行的中文结论。"
            ),
            user_prompt=prompt,
        )

    def answer_product_question(self, query: str) -> str:
        return self._invoke(
            system_prompt=(
                "你是一名泡脚桶产品顾问，请用简洁中文回答用户咨询。"
                "不要编造医疗功效，遇到不确定信息要明确说明。"
            ),
            user_prompt=query,
        )

    def _invoke(self, system_prompt: str, user_prompt: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = self.llm.invoke(messages)
        content = getattr(response, "content", "")
        if isinstance(content, list):
            return "".join(str(item) for item in content).strip()
        return str(content).strip()

    def _build_market_prompt(
        self,
        records: list[ProductRecord],
        metrics: dict[str, Any],
    ) -> str:
        sample = [
            {
                "title": item.title,
                "brand": item.brand,
                "price_current": item.price_current,
                "shop_name": item.shop_name,
            }
            for item in records[:10]
        ]
        return (
            "请根据以下泡脚桶市场样本，输出 3-5 条简短结论，重点回答价格带、卖点、产品线建议。\n"
            f"统计指标：{json.dumps(metrics, ensure_ascii=False)}\n"
            f"样本商品：{json.dumps(sample, ensure_ascii=False)}"
        )
