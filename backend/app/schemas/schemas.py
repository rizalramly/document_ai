"""Pydantic schemas for API request/response."""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


# ── Document ──────────────────────────────────────────────────
class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    doc_type: Optional[str] = "other"
    project_name: Optional[str] = None
    station: Optional[str] = None
    unit: Optional[str] = None
    cluster: Optional[str] = None
    doc_date: Optional[datetime] = None
    short_summary: Optional[str] = None
    purpose: Optional[str] = None
    tech_summary: Optional[str] = None
    location: Optional[str] = None
    page_count: int = 0
    file_size: int = 0


class DocumentOut(DocumentBase):
    id: int
    status: str
    file_path: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListOut(BaseModel):
    documents: List[DocumentOut]
    total: int
    page: int
    page_size: int


# ── Stats ─────────────────────────────────────────────────────
class StatsOut(BaseModel):
    total_documents: int
    total_chunks: int
    total_pages: int
    clusters: List[ClusterCount]
    stations: List[str]
    units: List[str]
    doc_types: List[str]


class ClusterCount(BaseModel):
    name: str
    count: int

# Fix forward reference
StatsOut.model_rebuild()


# ── Page ──────────────────────────────────────────────────────
class PageOut(BaseModel):
    id: int
    page_number: int
    text: Optional[str] = None
    render_path: Optional[str] = None

    class Config:
        from_attributes = True


# ── Chunk ─────────────────────────────────────────────────────
class ChunkOut(BaseModel):
    id: int
    document_id: int
    page_number: Optional[int] = None
    chunk_text: str
    keywords: Optional[List[str]] = None
    token_count: int = 0

    class Config:
        from_attributes = True


# ── Chat ──────────────────────────────────────────────────────
class ChatQueryIn(BaseModel):
    query: str
    session_id: Optional[int] = None
    context_scope: Optional[str] = None  # "global" or "document:123"
    filters: Optional[dict] = None


class Citation(BaseModel):
    document_id: int
    filename: str
    page_number: Optional[int] = None
    chunk_id: Optional[int] = None
    snippet: str
    relevance_score: Optional[float] = None
    bbox: Optional[dict] = None


class ViewerAction(BaseModel):
    action: str  # "open_page", "highlight_region"
    document_id: int
    page_number: Optional[int] = None
    bbox: Optional[dict] = None


class ChatResponseOut(BaseModel):
    answer: str
    citations: List[Citation] = []
    viewer_actions: List[ViewerAction] = []
    session_id: int


# ── Graph ─────────────────────────────────────────────────────
class GraphQueryIn(BaseModel):
    query: str
    entity_type: Optional[str] = None
    max_hops: int = 2


class GraphNodeOut(BaseModel):
    id: int
    node_type: str
    name: str
    metadata: Optional[dict] = None


class GraphEdgeOut(BaseModel):
    src: GraphNodeOut
    rel_type: str
    dst: GraphNodeOut


class GraphQueryOut(BaseModel):
    nodes: List[GraphNodeOut] = []
    edges: List[GraphEdgeOut] = []
    answer: Optional[str] = None


# ── Annotation ────────────────────────────────────────────────
class AnnotationIn(BaseModel):
    document_id: int
    page_number: Optional[int] = None
    bbox_json: Optional[dict] = None
    severity: str = "note"
    text: str
    author: Optional[str] = None


class AnnotationOut(BaseModel):
    id: int
    document_id: int
    page_number: Optional[int] = None
    bbox_json: Optional[dict] = None
    severity: str
    text: str
    author: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Ingest ────────────────────────────────────────────────────
class IngestResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    message: str


class BulkIngestResponse(BaseModel):
    results: List[IngestResponse]
    total_uploaded: int
    duplicates_skipped: int


# ── Admin actions ─────────────────────────────────────────────
class ActionResponse(BaseModel):
    success: bool
    message: str
    affected_count: int = 0
