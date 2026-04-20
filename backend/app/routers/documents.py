"""
documents.py — Endpoints para subir, listar y borrar documentos.
"""

import os
import shutil
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assistant, Document
from app.services.ingestion import ingest_document

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


# ── Schemas ───────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: str
    filename: str
    file_size: int
    chunk_count: int
    assistant_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/{assistant_id}", response_model=list[DocumentOut])
def list_documents(assistant_id: str, db: Session = Depends(get_db)):
    """Listar documentos de un asistente."""
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")

    docs = (
        db.query(Document)
        .filter(Document.assistant_id == assistant_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return docs


@router.post("/{assistant_id}", response_model=DocumentOut, status_code=201)
async def upload_document(
    assistant_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Subir un documento (PDF o TXT) y procesarlo (chunking + embeddings)."""
    # Validar que el asistente existe
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")

    # Validar tipo de archivo
    allowed_extensions = {".pdf", ".txt"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado. Usa: {', '.join(allowed_extensions)}",
        )

    # Guardar archivo en disco
    assistant_dir = os.path.join(UPLOAD_DIR, assistant_id)
    os.makedirs(assistant_dir, exist_ok=True)
    file_path = os.path.join(assistant_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    # Procesar documento: extraer texto, crear chunks, generar embeddings
    try:
        chunk_count = ingest_document(
            file_path=file_path,
            assistant_id=assistant_id,
            document_filename=file.filename,
        )
    except Exception as e:
        # Si falla la ingesta, limpiar el archivo
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {e}")

    # Guardar metadatos en DB
    doc = Document(
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        chunk_count=chunk_count,
        assistant_id=assistant_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc


@router.delete("/{assistant_id}/{document_id}", status_code=204)
def delete_document(
    assistant_id: str, document_id: str, db: Session = Depends(get_db)
):
    """Eliminar un documento y sus chunks del vector store."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.assistant_id == assistant_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Eliminar archivo físico
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # Eliminar chunks de ChromaDB
    from app.services.ingestion import delete_document_chunks

    delete_document_chunks(assistant_id=assistant_id, document_filename=doc.filename)

    # Eliminar de DB
    db.delete(doc)
    db.commit()
