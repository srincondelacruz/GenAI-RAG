"""
chat.py — Endpoint de chat RAG.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assistant
from app.services.rag import rag_query

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    assistant_id: str
    message: str = Field(..., min_length=1)


class SourceChunk(BaseModel):
    text: str
    document: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = []


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Enviar un mensaje al asistente.
    Realiza búsqueda semántica en los documentos del asistente,
    construye el prompt con contexto y llama al LLM.
    """
    # Validar que el asistente existe
    assistant = (
        db.query(Assistant).filter(Assistant.id == request.assistant_id).first()
    )
    if not assistant:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")

    # Ejecutar pipeline RAG
    try:
        result = rag_query(
            question=request.message,
            assistant_id=assistant.id,
            system_prompt=assistant.system_prompt,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el chat: {e}")

    return ChatResponse(
        answer=result["answer"],
        sources=[
            SourceChunk(text=s["text"], document=s["document"], score=s["score"])
            for s in result.get("sources", [])
        ],
    )
