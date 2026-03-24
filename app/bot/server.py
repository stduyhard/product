from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.bot.service import ProductConsultingBot
from app.settings import settings


class EventMessage(BaseModel):
    text: str


class FeishuEvent(BaseModel):
    token: str
    challenge: str | None = None
    event: EventMessage | None = None


app = FastAPI(title="FootBath Local Bot")
bot = ProductConsultingBot("data/knowledge_base.json")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/feishu/webhook")
def feishu_webhook(payload: FeishuEvent) -> dict[str, str]:
    if payload.token != settings.bot_verify_token:
        raise HTTPException(status_code=401, detail="invalid token")
    if payload.challenge:
        return {"challenge": payload.challenge}
    if not payload.event:
        return {"text": "empty event"}
    answer = bot.answer(payload.event.text)
    return {"text": answer}

