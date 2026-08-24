from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag import answer_question

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    answer = answer_question(request.conversation_id, request.message)
    return ChatResponse(conversation_id=request.conversation_id, answer=answer)
