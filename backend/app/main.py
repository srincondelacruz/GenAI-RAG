"""
main.py — Punto de entrada de la API FastAPI.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import engine, Base
from app.routers import assistants, documents, chat

load_dotenv()

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear directorios necesarios
os.makedirs(os.getenv("UPLOAD_DIR", "./uploads"), exist_ok=True)
os.makedirs(os.getenv("CHROMA_PERSIST_DIR", "./chroma_data"), exist_ok=True)

app = FastAPI(
    title="GenAI-RAG API",
    description="API para asistentes RAG con documentos propios",
    version="1.0.0",
)

# CORS para permitir peticiones del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(assistants.router, prefix="/api/assistants", tags=["Asistentes"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documentos"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "GenAI-RAG API is running 🚀"}
