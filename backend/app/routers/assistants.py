"""
assistants.py — CRUD endpoints para asistentes.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assistant

router = APIRouter()


# ── Schemas Pydantic ──────────────────────────────────────────────

class AssistantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    system_prompt: str = Field(
        default="Eres un asistente útil. Responde basándote en el contexto proporcionado."
    )


class AssistantUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    system_prompt: str | None = None


class AssistantOut(BaseModel):
    id: str
    name: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/", response_model=list[AssistantOut])
def list_assistants(db: Session = Depends(get_db)):
    """Listar todos los asistentes."""
    assistants = db.query(Assistant).order_by(Assistant.created_at.desc()).all()
    results = []
    for a in assistants:
        results.append(
            AssistantOut(
                id=a.id,
                name=a.name,
                system_prompt=a.system_prompt,
                created_at=a.created_at,
                updated_at=a.updated_at,
                document_count=len(a.documents),
            )
        )
    return results


@router.get("/{assistant_id}", response_model=AssistantOut)
def get_assistant(assistant_id: str, db: Session = Depends(get_db)):
    """Obtener un asistente por ID."""
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")
    return AssistantOut(
        id=assistant.id,
        name=assistant.name,
        system_prompt=assistant.system_prompt,
        created_at=assistant.created_at,
        updated_at=assistant.updated_at,
        document_count=len(assistant.documents),
    )


@router.post("/", response_model=AssistantOut, status_code=201)
def create_assistant(data: AssistantCreate, db: Session = Depends(get_db)):
    """Crear un nuevo asistente."""
    assistant = Assistant(name=data.name, system_prompt=data.system_prompt)
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return AssistantOut(
        id=assistant.id,
        name=assistant.name,
        system_prompt=assistant.system_prompt,
        created_at=assistant.created_at,
        updated_at=assistant.updated_at,
        document_count=0,
    )


@router.put("/{assistant_id}", response_model=AssistantOut)
def update_assistant(
    assistant_id: str, data: AssistantUpdate, db: Session = Depends(get_db)
):
    """Actualizar un asistente existente."""
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")

    if data.name is not None:
        assistant.name = data.name
    if data.system_prompt is not None:
        assistant.system_prompt = data.system_prompt

    assistant.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant)

    return AssistantOut(
        id=assistant.id,
        name=assistant.name,
        system_prompt=assistant.system_prompt,
        created_at=assistant.created_at,
        updated_at=assistant.updated_at,
        document_count=len(assistant.documents),
    )


@router.delete("/{assistant_id}", status_code=204)
def delete_assistant(assistant_id: str, db: Session = Depends(get_db)):
    """Eliminar un asistente y todos sus documentos."""
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")

    db.delete(assistant)
    db.commit()
