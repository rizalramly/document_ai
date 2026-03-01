# DOCS.ai – Engineering Document Intelligence Platform

> Browse, search, chat with, and visually inspect PDF engineering documents, drawings & P&IDs for TNB Genco power generation.

## Architecture

```
┌─────────────────────┐
│   React Frontend    │  Port 3000
│  (Vite + Tailwind)  │
└────────┬────────────┘
         │ API calls
┌────────▼────────────┐
│   FastAPI Backend   │  Port 8000
│  (Python 3.12+)     │
├─────────────────────┤
│  PostgreSQL + pgvec │  Port 5432
└────────┬────────────┘
         │ HTTP
┌────────▼────────────┐
│   Ollama (Local)    │  Port 11434
│  llava-phi3 + nomic │
└─────────────────────┘
```

## Quick Start (Docker Compose)

```bash
# 1. Make sure Ollama is running with required models
ollama pull llava-phi3:3.8b-mini-q4_0
ollama pull nomic-embed-text

# 2. Start all services
docker-compose up -d

# 3. Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Development Setup (Without Docker)

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 with pgvector extension
- Ollama running locally

### Database Setup
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Repository statistics |
| GET | `/api/documents` | List/search documents |
| GET | `/api/documents/:id` | Document details |
| POST | `/api/ingest` | Upload & ingest PDFs |
| POST | `/api/admin/refresh` | Re-scan storage for new PDFs |
| POST | `/api/admin/remove-duplicates` | Remove duplicate docs |
| DELETE | `/api/admin/delete-all` | Delete all documents |
| POST | `/api/chat/query` | RAG chat with citations |
| POST | `/api/graph/query` | Graph entity query |
| GET | `/api/entities` | List extracted entities |
| GET/POST/DELETE | `/api/annotations` | Annotation CRUD |
| GET | `/api/documents/:id/pages/:n/render` | Rendered page PNG |
| GET | `/api/documents/:id/pdf` | Original PDF file |

## Features

### Library Page
- TED TNB GENCO branding (top-right logo)
- Document tiles with AI-extracted metadata & summary
- Hybrid search (lexical + vector)
- Filter by Station, Unit, Document Type
- Intelligent Clusters with counts
- Admin: **Refresh DB** / **Remove Duplicates** / **Delete All** / **Upload PDFs**

### Chatbot (RAG)
- Graph RAG + Vector RAG hybrid retrieval
- Citations with document/page/chunk references
- Source Context panel with page preview & relevance score

### Drawing Viewer
- PDF page rendering with zoom/pan controls
- Layer toggles (Base Schematic, Electrical, Fluid)
- Annotation system (Warning / Note / Critical)
- DOCS Assistant chat panel

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite 6, Tailwind CSS 3 |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async) |
| Database | PostgreSQL 16 + pgvector |
| LLM | Ollama (llava-phi3 + nomic-embed-text) |
| PDF | PyMuPDF (rendering + text extraction) |
| Container | Docker Compose |

## Project Structure

```
01_docs.ai/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic (ingestion, LLM, etc.)
│   │   ├── config.py     # Environment configuration
│   │   ├── database.py   # Async SQLAlchemy setup
│   │   └── main.py       # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── public/images/    # TED TNB GENCO logo
│   ├── src/
│   │   ├── components/   # Sidebar, UploadModal
│   │   ├── pages/        # LibraryPage, ChatbotPage, ViewerPage
│   │   ├── api.js        # Axios API client
│   │   ├── App.jsx       # Root component
│   │   └── main.jsx      # Entry point
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```
