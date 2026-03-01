"""Document API routes: CRUD, search, filters, stats, admin actions."""

import os
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, text, distinct

from app.database import get_db
from app.config import settings
from app.models.document import Document, Page, Chunk
from app.schemas.schemas import (
    DocumentOut, DocumentListOut, StatsOut, ClusterCount,
    PageOut, ChunkOut, IngestResponse, BulkIngestResponse, ActionResponse
)
from app.services.ingestion.pipeline import ingestion_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["documents"])


# ── Stats ─────────────────────────────────────────────────────
@router.get("/stats", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get repository statistics."""
    doc_count = await db.scalar(select(func.count(Document.id)))
    chunk_count = await db.scalar(select(func.count(Chunk.id)))
    page_count = await db.scalar(select(func.count(Page.id)))

    # Cluster counts
    cluster_rows = await db.execute(
        select(Document.cluster, func.count(Document.id))
        .where(Document.cluster.isnot(None))
        .group_by(Document.cluster)
    )
    clusters = [ClusterCount(name=row[0], count=row[1]) for row in cluster_rows.all()]

    # Unique stations
    station_rows = await db.execute(
        select(distinct(Document.station)).where(Document.station.isnot(None))
    )
    stations = [row[0] for row in station_rows.all()]

    # Unique units
    unit_rows = await db.execute(
        select(distinct(Document.unit)).where(Document.unit.isnot(None))
    )
    units = [row[0] for row in unit_rows.all()]

    # Unique doc types
    type_rows = await db.execute(
        select(distinct(Document.doc_type)).where(Document.doc_type.isnot(None))
    )
    doc_types = [str(row[0].value) if row[0] else "other" for row in type_rows.all()]

    return StatsOut(
        total_documents=doc_count or 0,
        total_chunks=chunk_count or 0,
        total_pages=page_count or 0,
        clusters=clusters,
        stations=stations,
        units=units,
        doc_types=doc_types,
    )


# ── List + Search + Filter ───────────────────────────────────
@router.get("/documents", response_model=DocumentListOut)
async def list_documents(
    search: Optional[str] = None,
    station: Optional[str] = None,
    unit: Optional[str] = None,
    doc_type: Optional[str] = None,
    cluster: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List documents with filters and search."""
    query = select(Document).order_by(Document.created_at.desc())

    if station:
        query = query.where(Document.station == station)
    if unit:
        query = query.where(Document.unit == unit)
    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if cluster:
        query = query.where(Document.cluster == cluster)
    if search:
        query = query.where(
            Document.original_filename.ilike(f"%{search}%") |
            Document.short_summary.ilike(f"%{search}%") |
            Document.project_name.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    docs = result.scalars().all()

    return DocumentListOut(
        documents=[DocumentOut.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Get Document ──────────────────────────────────────────────
@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Get document details."""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return DocumentOut.model_validate(doc)


# ── Get Document Pages ────────────────────────────────────────
@router.get("/documents/{doc_id}/pages", response_model=list[PageOut])
async def get_pages(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Get all pages for a document."""
    result = await db.execute(
        select(Page).where(Page.document_id == doc_id).order_by(Page.page_number)
    )
    return [PageOut.model_validate(p) for p in result.scalars().all()]


# ── Render Page ─────────────────────────────────────────────
@router.get("/documents/{doc_id}/pages/{page_num}/render")
async def render_page(doc_id: int, page_num: int, db: AsyncSession = Depends(get_db)):
    """Get rendered PNG for a document page."""
    from fastapi.responses import FileResponse
    result = await db.execute(
        select(Page).where(Page.document_id == doc_id, Page.page_number == page_num)
    )
    page = result.scalar_one_or_none()
    if not page or not page.render_path:
        raise HTTPException(404, "Page render not found")
    if not os.path.exists(page.render_path):
        raise HTTPException(404, "Render file missing")
    return FileResponse(page.render_path, media_type="image/png")


# ── Search Chunks ─────────────────────────────────────────────
@router.get("/documents/{doc_id}/chunks", response_model=list[ChunkOut])
async def search_chunks(
    doc_id: int,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Search chunks within a document."""
    query = select(Chunk).where(Chunk.document_id == doc_id)
    if search:
        query = query.where(Chunk.chunk_text.ilike(f"%{search}%"))
    query = query.order_by(Chunk.chunk_index)
    result = await db.execute(query)
    chunks = result.scalars().all()
    return [ChunkOut(
        id=c.id,
        document_id=c.document_id,
        page_number=None,
        chunk_text=c.chunk_text,
        keywords=c.keywords,
        token_count=c.token_count,
    ) for c in chunks]


# ── Upload / Ingest ───────────────────────────────────────────
@router.post("/ingest", response_model=BulkIngestResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload and ingest PDF files."""
    results = []
    dups = 0

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append(IngestResponse(
                document_id=0, filename=file.filename or "unknown",
                status="error", message="Not a PDF file"
            ))
            continue

        # Save file
        safe_name = file.filename.replace(" ", "_")
        file_path = str(settings.pdf_storage_path / safe_name)

        # Handle name collision
        counter = 1
        base_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(base_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        try:
            doc = await ingestion_pipeline.ingest_document(
                db, file_path, file.filename or safe_name
            )
            results.append(IngestResponse(
                document_id=doc.id, filename=file.filename or safe_name,
                status=doc.status, message="Ingested successfully"
            ))
        except ValueError as e:
            if "Duplicate" in str(e):
                dups += 1
                os.remove(file_path)
                results.append(IngestResponse(
                    document_id=0, filename=file.filename or safe_name,
                    status="skipped", message=str(e)
                ))
            else:
                results.append(IngestResponse(
                    document_id=0, filename=file.filename or safe_name,
                    status="error", message=str(e)
                ))
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            results.append(IngestResponse(
                document_id=0, filename=file.filename or safe_name,
                status="error", message=str(e)
            ))

    return BulkIngestResponse(
        results=results,
        total_uploaded=sum(1 for r in results if r.status == "ready"),
        duplicates_skipped=dups,
    )


# ── Admin: Refresh DB ────────────────────────────────────────
@router.post("/admin/refresh", response_model=ActionResponse)
async def refresh_database(db: AsyncSession = Depends(get_db)):
    """Re-scan storage directory and ingest any new PDFs not yet in DB."""
    pdf_dir = settings.pdf_storage_path
    existing_files = set()
    result = await db.execute(select(Document.filename))
    for row in result.scalars().all():
        existing_files.add(row)

    new_count = 0
    for pdf_file in pdf_dir.glob("*.pdf"):
        if pdf_file.name not in existing_files:
            try:
                await ingestion_pipeline.ingest_document(db, str(pdf_file), pdf_file.name)
                new_count += 1
            except Exception as e:
                logger.error(f"Refresh ingestion failed for {pdf_file.name}: {e}")

    return ActionResponse(success=True, message=f"Refreshed: {new_count} new documents ingested", affected_count=new_count)


# ── Admin: Remove Duplicates ─────────────────────────────────
@router.post("/admin/remove-duplicates", response_model=ActionResponse)
async def remove_duplicates(db: AsyncSession = Depends(get_db)):
    """Remove duplicate documents (same file_hash), keeping the earliest."""
    # Find duplicate hashes
    dup_query = (
        select(Document.file_hash, func.count(Document.id).label("cnt"))
        .where(Document.file_hash.isnot(None))
        .group_by(Document.file_hash)
        .having(func.count(Document.id) > 1)
    )
    dup_rows = await db.execute(dup_query)
    removed = 0

    for row in dup_rows.all():
        file_hash = row[0]
        # Get all docs with this hash, ordered by id (keep first)
        docs = await db.execute(
            select(Document)
            .where(Document.file_hash == file_hash)
            .order_by(Document.id)
        )
        all_docs = docs.scalars().all()
        for doc in all_docs[1:]:  # Skip first (keep it)
            # Delete file
            if doc.file_path and os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            # Delete renders
            render_dir = settings.render_storage_path / str(doc.id)
            if render_dir.exists():
                shutil.rmtree(render_dir)
            await db.delete(doc)
            removed += 1

    await db.flush()
    return ActionResponse(success=True, message=f"Removed {removed} duplicate documents", affected_count=removed)


# ── Admin: Delete All ─────────────────────────────────────────
@router.delete("/admin/delete-all", response_model=ActionResponse)
async def delete_all_documents(db: AsyncSession = Depends(get_db)):
    """Delete ALL documents and their associated data."""
    count = await db.scalar(select(func.count(Document.id)))

    # Delete all files
    if settings.pdf_storage_path.exists():
        for f in settings.pdf_storage_path.glob("*.pdf"):
            f.unlink(missing_ok=True)

    # Delete all renders
    if settings.render_storage_path.exists():
        shutil.rmtree(settings.render_storage_path, ignore_errors=True)
        settings.render_storage_path.mkdir(parents=True, exist_ok=True)

    # Delete from DB (cascades handle pages, chunks, etc.)
    await db.execute(delete(Document))
    await db.flush()

    return ActionResponse(success=True, message=f"Deleted all {count} documents", affected_count=count or 0)


# ── Serve PDF file ────────────────────────────────────────────
@router.get("/documents/{doc_id}/pdf")
async def serve_pdf(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Serve the original PDF file."""
    from fastapi.responses import FileResponse
    doc = await db.get(Document, doc_id)
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(404, "PDF not found")
    return FileResponse(doc.file_path, media_type="application/pdf",
                        filename=doc.original_filename)
