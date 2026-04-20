"""
models.py — Modelos SQLAlchemy para asistentes y documentos.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class Assistant(Base):
    """Representa un asistente RAG con su system prompt."""

    __tablename__ = "assistants"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    system_prompt = Column(
        Text,
        nullable=False,
        default="Eres un asistente útil. Responde basándote en el contexto proporcionado.",
    )
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relación con documentos
    documents = relationship(
        "Document", back_populates="assistant", cascade="all, delete-orphan"
    )


class Document(Base):
    """Representa un documento subido asociado a un asistente."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación inversa
    assistant = relationship("Assistant", back_populates="documents")
