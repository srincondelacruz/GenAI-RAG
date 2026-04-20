"""
rag.py — Servicio RAG (Retrieval-Augmented Generation).

Flujo: Pregunta → Embedding → Búsqueda en ChromaDB → Construir prompt → Llamar LLM.
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
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

# Número de chunks relevantes a recuperar
TOP_K = 5


# ── Funciones auxiliares ─────────────────────────────────────────

def _get_collection(assistant_id: str):
    """Obtiene la colección de ChromaDB de un asistente."""
    collection_name = f"assistant_{assistant_id.replace('-', '_')[:50]}"
    return _chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def _retrieve_context(question: str, assistant_id: str) -> list[dict]:
    """
    Busca los chunks más relevantes para la pregunta.

    Returns:
        Lista de dicts con 'text', 'document' y 'score'.
    """
    # Generar embedding de la pregunta
    response = _openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=[question],
    )
    query_embedding = response.data[0].embedding

    # Buscar en ChromaDB
    collection = _get_collection(assistant_id)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # Si la colección está vacía
        return []

    # Formatear resultados
    sources = []
    if results["documents"] and results["documents"][0]:
        for i, doc_text in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            # ChromaDB con cosine devuelve distancia; convertir a similaridad
            similarity = 1 - distance

            sources.append(
                {
                    "text": doc_text,
                    "document": metadata.get("document", "desconocido"),
                    "score": round(similarity, 4),
                }
            )

    return sources


def _build_prompt(question: str, context_chunks: list[dict], system_prompt: str) -> list[dict]:
    """
    Construye los mensajes para el LLM incluyendo el contexto recuperado.
    """
    # Construir el bloque de contexto
    if context_chunks:
        context_text = "\n\n---\n\n".join(
            [
                f"[Fuente: {chunk['document']}]\n{chunk['text']}"
                for chunk in context_chunks
            ]
        )
        user_content = (
            f"Contexto de los documentos:\n\n{context_text}\n\n"
            f"---\n\n"
            f"Pregunta del usuario: {question}\n\n"
            f"Instrucciones: Responde la pregunta basándote en el contexto proporcionado. "
            f"Si el contexto no contiene información relevante, indícalo claramente. "
            f"Cita las fuentes cuando sea posible."
        )
    else:
        user_content = (
            f"Pregunta del usuario: {question}\n\n"
            f"Nota: No se encontraron documentos relevantes para esta pregunta. "
            f"Responde con tu conocimiento general, pero aclara que no encontraste "
            f"información en los documentos del asistente."
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


# ── Pipeline RAG principal ───────────────────────────────────────

def rag_query(question: str, assistant_id: str, system_prompt: str) -> dict:
    """
    Pipeline RAG completo:
    1. Recuperar chunks relevantes (Retrieve)
    2. Construir prompt con contexto (Augment)
    3. Llamar al LLM (Generate)

    Returns:
        Dict con 'answer' y 'sources'.
    """
    # 1. Retrieve
    sources = _retrieve_context(question, assistant_id)
    print(f"🔍 Recuperados {len(sources)} chunks relevantes")

    # 2. Augment — construir prompt
    messages = _build_prompt(question, sources, system_prompt)

    # 3. Generate — llamar al LLM
    completion = _openai_client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=messages,
        temperature=0.3,
        max_tokens=1500,
    )

    answer = completion.choices[0].message.content

    return {
        "answer": answer,
        "sources": sources,
    }
