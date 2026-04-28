from fastapi import APIRouter, HTTPException
import httpx
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class ChatRequest(BaseModel):
    query: str


@router.post("/chat")
async def chat(req: ChatRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://ai-agent:8001/chat", json={"query": req.query})
        return resp.json()
