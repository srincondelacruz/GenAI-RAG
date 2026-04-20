# 📋 GenAI-RAG — Walkthrough del proyecto

## Resumen

Se ha construido una **aplicación full-stack** de asistentes RAG (Retrieval-Augmented Generation) que permite crear asistentes de chat alimentados con documentos propios (PDF/TXT), usando **Azure OpenAI** como proveedor de LLM y embeddings, y **ChromaDB** como base de datos vectorial local.

---

## Arquitectura

```mermaid
graph LR
    subgraph Frontend["Frontend (React + Vite)"]
        A[Assistants.jsx] --> API[api/client.js]
        B[Documents.jsx] --> API
        C[Chat.jsx] --> API
    end

    subgraph Backend["Backend (FastAPI)"]
        R1[/assistants] --> DB[(SQLite)]
        R2[/documents] --> ING[ingestion.py]
        R3[/chat] --> RAG[rag.py]
        ING --> EMB[Azure OpenAI Embeddings]
        ING --> VDB[(ChromaDB)]
        RAG --> VDB
        RAG --> LLM[Azure OpenAI GPT-4o-mini]
    end

    API -->|HTTP| R1
    API -->|HTTP| R2
    API -->|HTTP| R3
```

---

## Estructura de archivos creados

```
GenAI-RAG/
├── .gitignore                    # Protege .env, DB, uploads, node_modules
├── README.md                     # Documentación principal del proyecto
│
├── backend/
│   ├── .env.example              # Plantilla de variables de entorno (sin credenciales)
│   ├── .env                      # Credenciales reales (protegido por .gitignore)
│   ├── requirements.txt          # Dependencias Python (compatibles con 3.14)
│   └── app/
│       ├── __init__.py
│       ├── main.py               # Entry point FastAPI + CORS + routers
│       ├── database.py           # Conexión SQLAlchemy + SQLite
│       ├── models.py             # Modelos: Assistant y Document
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── assistants.py     # CRUD completo de asistentes
│       │   ├── documents.py      # Subida, listado y borrado de documentos
│       │   └── chat.py           # Endpoint de chat RAG
│       └── services/
│           ├── __init__.py
│           ├── ingestion.py      # Pipeline de ingesta de documentos
│           └── rag.py            # Pipeline RAG completo
│
└── frontend/
    ├── .env.example              # URL del backend
    ├── package.json              # React 18 + Vite + React Router + Lucide
    ├── vite.config.js            # Proxy /api → backend
    ├── index.html                # HTML entry con Google Fonts (Inter)
    └── src/
        ├── main.jsx              # Punto de entrada React
        ├── App.jsx               # Layout + navegación + rutas
        ├── index.css             # Design system dark theme completo
        ├── api/
        │   └── client.js         # Funciones fetch para todos los endpoints
        └── pages/
            ├── Assistants.jsx    # Lista cards + modal crear/editar + borrar
            ├── Documents.jsx     # Drag & drop upload + lista con metadata
            └── Chat.jsx          # Chat con burbujas + selector + fuentes
```

---

## Detalle de cada componente

### Backend

#### 1. `database.py` — Conexión a BD
- Motor SQLAlchemy con **SQLite** local
- Función `get_db()` como dependency de FastAPI (una sesión por request)

#### 2. `models.py` — Modelos de datos

| Modelo | Campos principales |
|---|---|
| **Assistant** | `id` (UUID), `name`, `system_prompt`, `created_at`, `updated_at` |
| **Document** | `id` (UUID), `filename`, `file_path`, `file_size`, `chunk_count`, `assistant_id` (FK) |

- Relación 1:N → Un asistente tiene muchos documentos
- Cascade delete → al borrar un asistente se borran sus documentos

#### 3. `main.py` — Entry point
- Registra los 3 routers bajo `/api/`
- Configura CORS para `localhost:5173`
- Crea tablas automáticamente al arrancar
- Crea directorios `uploads/` y `chroma_data/`

#### 4. `routers/assistants.py` — CRUD Asistentes

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/assistants/` | Listar todos |
| `GET` | `/api/assistants/{id}` | Obtener uno |
| `POST` | `/api/assistants/` | Crear nuevo |
| `PUT` | `/api/assistants/{id}` | Actualizar |
| `DELETE` | `/api/assistants/{id}` | Eliminar (cascade) |

#### 5. `routers/documents.py` — Gestión de documentos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/documents/{assistant_id}` | Listar documentos |
| `POST` | `/api/documents/{assistant_id}` | Subir PDF/TXT |
| `DELETE` | `/api/documents/{assistant_id}/{doc_id}` | Borrar doc + chunks |

- Valida extensiones (solo `.pdf` y `.txt`)
- Guarda archivos en `uploads/{assistant_id}/`
- Ejecuta pipeline de ingesta al subir

#### 6. `routers/chat.py` — Endpoint de chat

| Método | Ruta | Body | Respuesta |
|---|---|---|---|
| `POST` | `/api/chat/` | `{assistant_id, message}` | `{answer, sources[]}` |

#### 7. `services/ingestion.py` — Pipeline de ingesta

```
Archivo → Extraer texto → Chunking → Embeddings → ChromaDB
```

- **Extracción:** `pypdf` para PDFs, lectura directa para TXTs
- **Chunking:** 1000 caracteres por chunk, 200 de solapamiento, corte inteligente en párrafos/frases
- **Embeddings:** Azure OpenAI `text-embedding-ada-002`
- **Storage:** ChromaDB persistente, una colección por asistente, distancia coseno

#### 8. `services/rag.py` — Pipeline RAG

```
Pregunta → Embedding → Búsqueda vectorial → Construir prompt → LLM → Respuesta
```

- **Retrieve:** Top 5 chunks más relevantes de ChromaDB
- **Augment:** Construye prompt con contexto de los documentos + system prompt del asistente
- **Generate:** Azure OpenAI `gpt-4o-mini` con temperatura 0.3

---

### Frontend

#### 1. `index.css` — Design System
- **Dark theme** con paleta indigo/cyan
- Glassmorphism en header (backdrop-filter blur)
- Gradientes en accent colors
- Animaciones: fadeIn, slideUp, bounce (loading dots)
- Cards con hover glow effect
- Responsive (breakpoint 768px)

#### 2. `App.jsx` — Layout principal
- Header con logo gradiente + navegación (Asistentes, Chat)
- React Router con 4 rutas:
  - `/` → Assistants
  - `/assistants/:id/documents` → Documents
  - `/chat` → Chat (selector)
  - `/chat/:assistantId` → Chat (directo)

#### 3. `pages/Assistants.jsx`
- Grid de cards con nombre, system prompt (truncado), nº docs, fecha
- Botón "Nuevo asistente" → modal con formulario
- Editar → mismo modal prellenado
- Eliminar → confirmación
- Navegar a Documentos o Chat desde cada card

#### 4. `pages/Documents.jsx`
- Drag & drop upload zone
- Lista de documentos con: nombre, tamaño, nº chunks, fecha, badge "Indexado"
- Eliminar con limpieza de archivo + chunks vectoriales
- Botón volver a asistentes

#### 5. `pages/Chat.jsx`
- Selector de asistente (dropdown)
- Burbujas de mensajes (usuario → gradiente, asistente → card)
- **Fuentes citadas** expandibles con % de relevancia y preview del texto
- Loading animation con dots
- Auto-scroll al nuevo mensaje

#### 6. `api/client.js` — Cliente HTTP
- Funciones para todos los endpoints
- Manejo de errores con mensajes del backend
- Upload con FormData (multipart)

---

## Stack tecnológico

| Componente | Tecnología | Versión |
|---|---|---|
| Runtime Python | Python | 3.14.4 |
| Backend framework | FastAPI | ≥0.115.0 |
| Server ASGI | Uvicorn | ≥0.34.0 |
| ORM | SQLAlchemy | ≥2.0.36 |
| Base de datos | SQLite | (incluida en Python) |
| Vector DB | ChromaDB | ≥0.6.0 |
| Extracción PDF | pypdf | ≥5.1.0 |
| LLM & Embeddings | Azure OpenAI (openai SDK) | ≥1.58.0 |
| Frontend framework | React | 18.x |
| Bundler | Vite | 6.x |
| Routing | React Router DOM | 6.x |
| Iconos | Lucide React | — |
| Fuente | Inter (Google Fonts) | — |

---

## Configuración Azure OpenAI

```
Endpoint:   https://ai-sergiorincon0872ai045504941434.openai.azure.com/
Chat model: gpt-4o-mini
Embeddings: text-embedding-ada-002
API version: 2025-01-01-preview
```

---

## Comandos para arrancar

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### URLs
- **App:** http://localhost:5173
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs

---

## Flujo de uso

1. **Crear asistente** → Nombre + system prompt personalizado
2. **Subir documentos** → PDFs o TXTs → se procesan automáticamente (chunking + embeddings)
3. **Chatear** → Hacer preguntas → el asistente responde basándose en los documentos con citas de las fuentes
