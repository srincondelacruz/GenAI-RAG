"""
ingestion.py — Servicio de ingesta de documentos.

Flujo: Extraer texto → Chunking → Generar embeddings → Almacenar en ChromaDB.
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import chromadb

load_dotenv()

# ── Clientes ──────────────────────────────────────────────────────

_openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

_chroma_client = chromadb.PersistentClient(
    path=os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
)

EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"
)

# ── Configuración de chunking ────────────────────────────────────

CHUNK_SIZE = 1000  # caracteres por chunk
CHUNK_OVERLAP = 200  # solapamiento entre chunks


# ── Funciones de extracción ──────────────────────────────────────

def _extract_text_from_pdf(file_path: str) -> str:
    """Extrae texto de un archivo PDF usando pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_text_from_txt(file_path: str) -> str:
    """Lee texto plano de un archivo .txt."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text(file_path: str) -> str:
    """Extrae texto de un archivo según su extensión."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".pdf":
        return _extract_text_from_pdf(file_path)
    elif ext == ".txt":
        return _extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Tipo de archivo no soportado: {ext}")


# ── Chunking ─────────────────────────────────────────────────────

def split_into_chunks(text: str) -> list[str]:
    """
    Divide el texto en chunks con solapamiento.
    Intenta cortar en límites de párrafo/frase cuando es posible.
    """
    if not text.strip():
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE

        # Si no estamos al final, buscar un buen punto de corte
        if end < len(text):
            # Buscar el último salto de párrafo dentro del rango
            last_paragraph = text.rfind("\n\n", start, end)
            if last_paragraph > start + CHUNK_SIZE // 2:
                end = last_paragraph + 2
            else:
                # Buscar el último punto seguido de espacio
                last_period = text.rfind(". ", start, end)
                if last_period > start + CHUNK_SIZE // 2:
                    end = last_period + 2

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - CHUNK_OVERLAP

    return chunks


# ── Embeddings ───────────────────────────────────────────────────

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Genera embeddings para una lista de textos usando Azure OpenAI."""
    response = _openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=texts,
    )
    return [item.embedding for item in response.data]


# ── ChromaDB ─────────────────────────────────────────────────────

def _get_collection(assistant_id: str):
    """Obtiene o crea una colección de ChromaDB para un asistente."""
    collection_name = f"assistant_{assistant_id.replace('-', '_')[:50]}"
    return _chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_document(
    file_path: str, assistant_id: str, document_filename: str
) -> int:
    """
    Pipeline completo de ingesta:
    1. Extraer texto del archivo
    2. Dividir en chunks
    3. Generar embeddings
    4. Almacenar en ChromaDB

    Returns:
        Número de chunks generados.
    """
    # 1. Extraer texto
    text = extract_text(file_path)
    if not text.strip():
        raise ValueError("El documento no contiene texto extraíble.")

    # 2. Chunking
    chunks = split_into_chunks(text)
    if not chunks:
        raise ValueError("No se pudieron generar chunks del documento.")

    # 3. Generar embeddings
    embeddings = generate_embeddings(chunks)

    # 4. Almacenar en ChromaDB
    collection = _get_collection(assistant_id)

    ids = [f"{document_filename}__chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"document": document_filename, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    print(f"✅ Ingestados {len(chunks)} chunks de '{document_filename}' para asistente {assistant_id}")
    return len(chunks)


def delete_document_chunks(assistant_id: str, document_filename: str):
    """Elimina todos los chunks de un documento de ChromaDB."""
    collection = _get_collection(assistant_id)

    # Buscar todos los IDs que pertenecen a este documento
    results = collection.get(
        where={"document": document_filename},
    )

    if results["ids"]:
        collection.delete(ids=results["ids"])
        print(f"🗑️ Eliminados {len(results['ids'])} chunks de '{document_filename}'")
