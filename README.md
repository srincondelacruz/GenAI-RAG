# GenAI-RAG — Asistentes RAG con documentos propios

Aplicación full-stack que permite crear **asistentes de chat** alimentados con tus propios documentos, usando Retrieval-Augmented Generation (RAG).

## Arquitectura

```
┌─────────────┐        ┌─────────────────────────────────────┐
│  Frontend   │  HTTP   │            Backend (FastAPI)         │
│  (React +   │◄──────►│                                     │
│   Vite)     │        │  /assistants  /documents  /chat     │
└─────────────┘        │       │            │          │      │
                       │       ▼            ▼          ▼      │
                       │   SQLite DB    ingestion    rag.py   │
                       │                service      service  │
                       │                   │          │       │
                       │                   ▼          ▼       │
                       │              ChromaDB    Azure OpenAI│
                       └─────────────────────────────────────┘
```

## Stack tecnológico

| Capa       | Tecnología                              |
|------------|-----------------------------------------|
| Frontend   | React 18 + Vite + React Router          |
| Backend    | FastAPI + SQLAlchemy + Uvicorn           |
| VectorDB   | ChromaDB (persistente, local)            |
| Embeddings | Azure OpenAI `text-embedding-ada-002`   |
| LLM        | Azure OpenAI `gpt-4o-mini`              |
| Base datos | SQLite (metadatos de asistentes/docs)   |

## Requisitos previos

- Python 3.10+
- Node.js 18+
- Cuenta de Azure con acceso a Azure OpenAI

## Inicio rápido

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # ← Rellena con tus credenciales
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env    # ← Ajusta la URL del backend si es necesario
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173) en tu navegador.

## Flujo de uso

1. **Crear un asistente** — Dale un nombre y un system prompt personalizado.
2. **Subir documentos** — PDFs o TXTs que serán procesados (chunking + embeddings).
3. **Chatear** — Haz preguntas y el asistente responderá basándose en tus documentos.

## Estructura del proyecto

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── routers/
│   │   │   ├── assistants.py    # CRUD asistentes
│   │   │   ├── documents.py     # Subida + listado + borrado
│   │   │   └── chat.py          # Endpoint de chat RAG
│   │   ├── services/
│   │   │   ├── ingestion.py     # Extracción, chunking, embeddings
│   │   │   └── rag.py           # Retrieve + build prompt + llamar LLM
│   │   ├── models.py            # SQLAlchemy models
│   │   └── database.py          # Conexión DB
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Assistants.jsx   # Lista + crear + editar
│   │   │   ├── Documents.jsx    # Docs de un asistente
│   │   │   └── Chat.jsx         # Interfaz de chat
│   │   ├── api/
│   │   │   └── client.js        # Llamadas al backend
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
└── README.md
```
