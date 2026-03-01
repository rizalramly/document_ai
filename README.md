# DOCS.ai – Engineering Document Intelligence Platform

> A production-ready web application that enables engineers to **browse**, **search**, **chat with**, and **visually inspect** PDF engineering documents, technical drawings, and P&IDs (Piping & Instrumentation Diagrams) using AI-powered retrieval and understanding.

**Built for**: TNB Genco – Technology & Engineering Department (TED)
**Domain**: Power Generation Engineering

---

## Table of Contents

1. [Product Overview](#product-overview)
2. [Architecture Overview](#architecture-overview)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [AI/LLM Pipeline](#aillm-pipeline)
7. [API Reference](#api-reference)
8. [Frontend Pages](#frontend-pages)
9. [Getting Started](#getting-started)
10. [Docker Deployment](#docker-deployment)
11. [Environment Variables](#environment-variables)
12. [Roadmap](#roadmap)

---

## Product Overview

### Problem Statement
Power generation engineers work with thousands of PDF documents — RCA reports, technical manuals, P&ID drawings, specification sheets, and maintenance logbooks. Finding specific information across these documents is time-consuming, error-prone, and critical for safety.

### Solution
DOCS.ai provides three core capabilities:

| Feature | Description |
|---------|-------------|
| **Document Library** | Browse, search, and filter documents with AI-extracted metadata, summaries, and intelligent clustering |
| **RAG Chatbot** | Ask natural language questions grounded in the document repository, with citations linking back to exact pages |
| **Drawing Viewer** | Interactive viewer for P&IDs and technical drawings with layer controls, annotations, and AI-assisted analysis |

### Admin Capabilities
| Action | Description |
|--------|-------------|
| **Refresh DB** | Scans the storage directory for new PDFs and ingests them |
| **Remove Duplicates** | Identifies and removes duplicate documents by file hash |
| **Delete All** | Clears the entire repository (with confirmation) |
| **Upload PDF(s)** | Drag-and-drop upload with progress tracking |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │    React 19 + Vite 6 + Tailwind CSS 3                  │  │
│  │    ├── LibraryPage   (doc tiles, search, filters)      │  │
│  │    ├── ChatbotPage   (RAG chat + Source Context)       │  │
│  │    └── ViewerPage    (canvas, layers, annotations)     │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │ REST API (Axios)                     │
└───────────────────────┼──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                        API LAYER                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │    FastAPI (Python 3.12, async/await)                   │  │
│  │    ├── /api/documents    CRUD + search + admin actions  │  │
│  │    ├── /api/ingest       PDF upload → pipeline          │  │
│  │    ├── /api/chat/query   RAG with vector search         │  │
│  │    ├── /api/graph/query  Entity graph traversal         │  │
│  │    └── /api/annotations  CRUD for viewer annotations    │  │
│  └──────┬─────────────────┬───────────────────────────────┘  │
│         │                 │                                  │
│  ┌──────▼──────┐   ┌─────▼──────────────────────────────┐   │
│  │  Services   │   │         Ingestion Pipeline          │   │
│  │ ├ LLM Prov. │   │  PDF Extract → Chunk → VLM → Embed │   │
│  │ ├ Prompts   │   │  → Entity Extract → Graph Build     │   │
│  │ └ Retrieval │   └─────────────────────────────────────┘   │
│  └──────┬──────┘                                             │
└─────────┼────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────┐
│                     DATA / AI LAYER                          │
│  ┌─────────────────┐    ┌────────────────────────────────┐   │
│  │  PostgreSQL 16   │    │  Ollama (Local LLM)            │   │
│  │  + pgvector ext  │    │  ├ llava-phi3:3.8b (vision)    │   │
│  │  ├ documents     │    │  ├ nomic-embed-text (embed)    │   │
│  │  ├ chunks + emb  │    │  └ llava-phi3:3.8b (chat)      │   │
│  │  ├ entities      │    └────────────────────────────────┘   │
│  │  ├ graph_edges   │                                        │
│  │  └ annotations   │    ┌────────────────────────────────┐   │
│  └─────────────────┘    │  File Storage                   │   │
│                          │  ├ /storage/pdfs/   (originals) │   │
│                          │  └ /storage/renders/ (page PNG) │   │
│                          └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Request Flow

```
User asks question → Frontend sends POST /api/chat/query
  → Embed query with nomic-embed-text (768-dim vector)
  → pgvector cosine similarity search across chunks
  → Retrieve top-K relevant chunks with metadata
  → Build prompt with context + citations
  → LLM generates grounded answer (llava-phi3)
  → Return answer + citations + viewer actions
  → Frontend shows answer + Source Context panel
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19, Vite 6, Tailwind CSS 3 | SPA with dark theme UI |
| **API Server** | Python 3.12, FastAPI | Async REST API |
| **ORM** | SQLAlchemy 2.0 (async) | Database models + queries |
| **Database** | PostgreSQL 16 + pgvector | Relational data + vector embeddings |
| **LLM** | Ollama | Local inference (no cloud dependency) |
| **Vision Model** | llava-phi3:3.8b-mini-q4_0 | Document classification, entity extraction |
| **Embedding Model** | nomic-embed-text | 768-dim embeddings for RAG |
| **PDF Processing** | PyMuPDF (fitz) | Text extraction + page rendering |
| **Containerization** | Docker Compose | Multi-service orchestration |

---

## Project Structure

```
01_docs.ai/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── api/                      # Route handlers
│   │   │   ├── documents.py          # Document CRUD, search, admin actions
│   │   │   ├── chat.py               # RAG chat endpoint
│   │   │   ├── annotations.py        # Annotation CRUD
│   │   │   └── graph.py              # Knowledge graph queries
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── document.py           # Document, Page, Chunk (+ pgvector)
│   │   │   ├── entity.py             # Entity, EntityMention, GraphEdge
│   │   │   ├── annotation.py         # Annotation
│   │   │   ├── chat.py               # ChatSession, ChatMessage
│   │   │   └── user.py               # User, AuditLog
│   │   ├── schemas/
│   │   │   └── schemas.py            # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── extractor.py      # PDF text + metadata extraction
│   │   │   │   ├── chunker.py        # Structure-aware text chunking
│   │   │   │   ├── vlm_extractor.py  # Vision-LLM: classify, summarise, entities
│   │   │   │   └── pipeline.py       # Orchestrates full ingest flow
│   │   │   └── llm/
│   │   │       ├── provider.py       # LLM abstraction + OllamaProvider
│   │   │       └── prompts.py        # Prompt templates
│   │   ├── config.py                 # Pydantic settings (env vars)
│   │   ├── database.py               # Async engine + session factory
│   │   └── main.py                   # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                          # Local environment variables
│
├── frontend/                         # React.js frontend
│   ├── public/
│   │   └── images/
│   │       └── ted-tnb-logo.png      # TED TNB GENCO corporate logo
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx           # Left nav with branding
│   │   │   └── UploadModal.jsx       # Drag-and-drop PDF upload
│   │   ├── pages/
│   │   │   ├── LibraryPage.jsx       # Document library with admin actions
│   │   │   ├── ChatbotPage.jsx       # RAG chatbot + Source Context
│   │   │   └── ViewerPage.jsx        # Drawing viewer + annotations
│   │   ├── api.js                    # Axios API client
│   │   ├── App.jsx                   # Root component + routing
│   │   ├── main.jsx                  # Entry point
│   │   └── index.css                 # Tailwind + custom styles
│   ├── package.json
│   ├── vite.config.js                # Dev server + API proxy
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── nginx.conf                    # Production SPA routing
│
├── docker-compose.yml                # PostgreSQL + Backend + Frontend
├── .gitignore
└── README.md
```

---

## Database Schema

### Entity-Relationship Diagram

```mermaid
erDiagram
    documents ||--o{ pages : has
    documents ||--o{ chunks : contains
    documents ||--o{ annotations : has
    chunks ||--o{ entity_mentions : references
    entities ||--o{ entity_mentions : mentioned_in
    entities ||--o{ graph_edges : source
    entities ||--o{ graph_edges : target
    documents ||--o{ graph_edges : context
    chat_sessions ||--o{ chat_messages : contains

    documents {
        uuid id PK
        string original_filename
        string file_hash
        string doc_type
        string project_name
        string station
        string unit
        string cluster
        text short_summary
        text purpose
        text tech_summary
        int page_count
        string status
        timestamp created_at
    }

    chunks {
        uuid id PK
        uuid document_id FK
        int page_number
        int chunk_index
        text content
        vector embedding
        int token_count
    }

    entities {
        uuid id PK
        string name
        string entity_type
        jsonb properties
    }

    graph_edges {
        uuid id PK
        uuid source_entity_id FK
        uuid target_entity_id FK
        string relation_type
        uuid document_id FK
    }
```

### Key Tables

| Table | Rows | Purpose |
|-------|------|---------|
| `documents` | ~100s | PDF metadata, AI-extracted summaries, file hash for dedup |
| `pages` | ~1000s | Per-page text content and render image path |
| `chunks` | ~10,000s | Text chunks with 768-dim pgvector embedding |
| `entities` | ~1000s | Equipment, instruments, valves extracted by VLM |
| `entity_mentions` | ~5000s | Links entities to specific chunks |
| `graph_edges` | ~3000s | Relationships between entities (adjacency table) |
| `annotations` | variable | User notes on specific pages with severity |
| `chat_sessions` | variable | Conversation history for RAG continuity |
| `chat_messages` | variable | Individual messages with citations |
| `users` | variable | Role-based access (Engineer/Admin) |
| `audit_logs` | append-only | Track all user actions |

---

## AI/LLM Pipeline

### Ingestion Flow

```
PDF File Upload
      │
      ▼
┌─────────────────┐
│ 1. PDF Extract   │  PyMuPDF: text, metadata, page renders (PNG)
│    (extractor.py)│  SHA-256 hash for duplicate detection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. VLM Extract   │  Ollama llava-phi3 (vision model):
│  (vlm_extractor) │  • Classify doc type (manual/pid/drawing/spec/report)
│                   │  • Extract project name & station
│                   │  • Generate structured summary (purpose, tech, location)
│                   │  • Extract entities (equipment, instruments, valves)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Chunk Text    │  Structure-aware splitting:
│   (chunker.py)   │  • Split by headings first (## / ### / ===)
│                   │  • Sub-split large blocks to ~500 tokens
│                   │  • 50-token overlap for context continuity
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Embed Chunks  │  Ollama nomic-embed-text:
│                   │  • 768-dimensional dense vectors
│                   │  • Stored in pgvector column
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Build Graph   │  Store entities + relations in PostgreSQL
│                   │  adjacency tables (no Neo4j needed)
└─────────────────┘
```

### RAG Retrieval Flow

```
User Question: "What caused the boiler tube failure at Jimah Unit 2?"
      │
      ▼
┌─────────────────┐
│ Embed Query      │  nomic-embed-text → 768-dim vector
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Search    │  pgvector cosine similarity
│                   │  SELECT * FROM chunks
│                   │  ORDER BY embedding <=> query_vector
│                   │  LIMIT 10
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build Context    │  Top-K chunks + document metadata
│                   │  + entity graph context
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate Answer  │  llava-phi3 with system prompt:
│                   │  "Answer based ONLY on provided context.
│                   │   Cite sources as [Doc: file, Page: N]"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Response  │  { answer, citations[], viewer_actions[] }
└─────────────────┘
```

---

## API Reference

### Document Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Repository statistics (doc count, chunk count, clusters) |
| `GET` | `/api/documents` | List documents with search, filter, pagination |
| `GET` | `/api/documents/:id` | Get single document with full metadata |
| `GET` | `/api/documents/:id/pages` | List all pages of a document |
| `GET` | `/api/documents/:id/pages/:n/render` | Serve rendered page as PNG |
| `GET` | `/api/documents/:id/chunks` | Search chunks within a document |
| `GET` | `/api/documents/:id/pdf` | Serve original PDF file |

### Ingestion & Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ingest` | Upload PDF files → triggers ingestion pipeline |
| `POST` | `/api/admin/refresh` | Scan storage directory for new PDFs |
| `POST` | `/api/admin/remove-duplicates` | Remove docs with duplicate SHA-256 hash |
| `DELETE` | `/api/admin/delete-all` | Delete all documents and associated data |

### Chat (RAG)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/query` | Send question → get AI answer with citations |

**Request body:**
```json
{
  "query": "What caused the boiler tube failure?",
  "session_id": "optional-uuid",
  "top_k": 10
}
```

**Response:**
```json
{
  "answer": "Based on the RCA report [Doc: RCA_JMJG_001.pdf, Page: 5]...",
  "citations": [
    {
      "document_id": "uuid",
      "filename": "RCA_JMJG_001.pdf",
      "page_number": 5,
      "snippet": "The root cause was identified as...",
      "relevance_score": 0.89
    }
  ],
  "viewer_actions": [
    { "action": "open_page", "document_id": "uuid", "page": 5 }
  ],
  "session_id": "uuid"
}
```

### Graph & Entities

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/entities` | List extracted entities (filterable by type) |
| `POST` | `/api/graph/query` | Query entity relationships |

### Annotations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/documents/:id/annotations` | List annotations for a document |
| `POST` | `/api/annotations` | Create annotation (warning/note/critical) |
| `DELETE` | `/api/annotations/:id` | Delete an annotation |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check (app + Ollama connectivity) |

---

## Frontend Pages

### 1. Library Page
- **TED TNB GENCO** corporate logo (top-right)
- Stats cards: Total Documents, Total Chunks
- Intelligent Clusters (AI-grouped document categories)
- Full-text search bar
- Filters: Station, Unit, Event Type
- Document tiles with AI-extracted summaries
- Admin action buttons: Refresh DB, Remove Duplicates, Delete All, Upload PDFs

### 2. Chatbot (RAG) Page
- Chat interface with AI Engineering Assistant persona
- Message bubbles with markdown formatting
- Citation links to source documents
- **Source Context panel** (right side): page preview, metadata, relevance score
- Conversation history with session persistence

### 3. Drawing Viewer Page
- **Left panel**: Document info, Layer toggles (Base/Electrical/Fluid), Annotations list
- **Center canvas**: PDF page rendering with zoom/pan, grid background, toolbar
- **Bottom bar**: Page navigation (1/14), zoom slider (25-200%), rotate/reset/fit
- **Right panel**: DOCS Assistant chat for drawing-specific queries

---

## Getting Started

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend build |
| PostgreSQL | 16 | Database with pgvector |
| Ollama | Latest | Local LLM inference |

### Step 1: Install Ollama Models

```bash
# Install Ollama from https://ollama.ai
ollama pull llava-phi3:3.8b-mini-q4_0    # Vision + chat model
ollama pull nomic-embed-text              # Embedding model (768-dim)
```

### Step 2: Set Up PostgreSQL with pgvector

```sql
-- Create database
CREATE DATABASE docsai;

-- Connect to docsai and enable pgvector
\c docsai
CREATE EXTENSION IF NOT EXISTS vector;
```

### Step 3: Start the Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment (edit .env as needed)
# DATABASE_URL=postgresql+asyncpg://docsai:docsai@localhost:5432/docsai
# OLLAMA_BASE_URL=http://localhost:11434

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API documentation will be available at: `http://localhost:8000/docs` (Swagger UI)

### Step 4: Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies /api to backend on port 8000)
npm run dev
```

The application will be available at: `http://localhost:3000`

### Step 5: Upload Documents

1. Open `http://localhost:3000`
2. Click the **Upload PDF(s)** button (blue)
3. Drag and drop PDF files or click to browse
4. Wait for the ingestion pipeline to process (extract → classify → chunk → embed)
5. Documents will appear as tiles in the Library

---

## Docker Deployment

### Quick Start

```bash
# Ensure Ollama is running on the host machine
ollama serve

# Start all services
docker-compose up -d

# Services:
#   db       → PostgreSQL + pgvector on port 5432
#   backend  → FastAPI on port 8000
#   frontend → React (nginx) on port 3000
```

### docker-compose.yml Services

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `db` | pgvector/pgvector:pg16 | 5432 | PostgreSQL with vector extension |
| `backend` | Custom (Python 3.12) | 8000 | FastAPI app with PyMuPDF + Tesseract |
| `frontend` | Custom (Node 20 → nginx) | 3000 | React SPA with API proxy |

> **Note**: Ollama runs on the host machine. The backend connects via `host.docker.internal:11434`.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://docsai:docsai@localhost:5432/docsai` | Async database connection |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_VISION_MODEL` | `llava-phi3:3.8b-mini-q4_0` | Model for classification + entity extraction |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model for text embedding (768-dim) |
| `OLLAMA_CHAT_MODEL` | `llava-phi3:3.8b-mini-q4_0` | Model for RAG chat responses |
| `STORAGE_PATH` | `./storage` | Root storage directory |
| `PDF_STORAGE_PATH` | `./storage/pdfs` | Uploaded PDF files |
| `RENDER_STORAGE_PATH` | `./storage/renders` | Rendered page images (PNG) |
| `DEBUG` | `true` | Enable debug logging |

---

## Roadmap

### Completed ✅
- [x] FastAPI backend scaffold with async SQLAlchemy
- [x] PostgreSQL schema with pgvector for embeddings
- [x] Ollama LLM provider abstraction
- [x] PDF ingestion pipeline (extract → chunk → VLM → embed → graph)
- [x] All API routes (documents, chat, annotations, graph, admin)
- [x] React frontend with 3 pages matching design specifications
- [x] Docker Compose for deployment
- [x] TED TNB GENCO corporate branding

### Upcoming 🔜
- [ ] End-to-end testing with real engineering PDFs
- [ ] Full RAG pipeline validation
- [ ] Alembic database migrations
- [ ] Role-based access control (Engineer vs Admin)
- [ ] Audit logging implementation
- [ ] Production Docker deployment
- [ ] Performance optimization (caching, batch embeddings)
- [ ] Export/download search results

---

## License

Internal use only – TNB Genco, Technology & Engineering Department (TED)
