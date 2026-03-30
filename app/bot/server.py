from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.analysis.ai_summary import DeepSeekAnalyzer
from app.bot.rag import LangChainRAGResponder
from app.bot.service import ProductConsultingBot
from app.settings import settings


class EventMessage(BaseModel):
    text: str


class ChatMessage(BaseModel):
    text: str = Field(min_length=1)
    session_id: str | None = None


class FeishuEvent(BaseModel):
    token: str
    challenge: str | None = None
    event: EventMessage | None = None


app = FastAPI(title="FootBath Local Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ai_responder = None
if settings.ai_enabled:
    analyzer = DeepSeekAnalyzer(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
    )
    ai_responder = LangChainRAGResponder(
        "data/knowledge_base.json",
        llm=analyzer.llm,
        cache_path=settings.bot_vector_cache_path,
    )
bot = ai_responder or ProductConsultingBot("data/knowledge_base.json")
DASHBOARD_PATH = Path("output/dashboard_summary.json")


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        content={"status": "ok"},
        media_type="application/json; charset=utf-8",
    )


@app.post("/feishu/webhook")
def feishu_webhook(payload: FeishuEvent) -> JSONResponse:
    if payload.token != settings.bot_verify_token:
        raise HTTPException(status_code=401, detail="invalid token")
    if payload.challenge:
        return JSONResponse(
            content={"challenge": payload.challenge},
            media_type="application/json; charset=utf-8",
        )
    if not payload.event:
        return JSONResponse(
            content={"text": "empty event"},
            media_type="application/json; charset=utf-8",
        )
    answer = bot.answer(payload.event.text)
    return JSONResponse(
        content={"text": answer},
        media_type="application/json; charset=utf-8",
    )


@app.post("/chat")
def chat(payload: ChatMessage) -> JSONResponse:
    answer = bot.answer(payload.text, session_id=payload.session_id)
    return JSONResponse(
        content={"text": answer},
        media_type="application/json; charset=utf-8",
    )

@app.get("/dashboard/summary")
def dashboard_summary() -> JSONResponse:
    if not DASHBOARD_PATH.exists():
        return JSONResponse(
            content={
                "summary": {"total": 0, "avg_price": 0},
                "charts": {
                    "brand_top": [],
                    "price_band": [],
                    "feature_coverage": [],
                    "shop_type_share": [],
                },
            },
            media_type="application/json; charset=utf-8",
        )

    payload = json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
    return JSONResponse(
        content=payload,
        media_type="application/json; charset=utf-8",
    )

