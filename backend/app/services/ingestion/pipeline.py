"""Full ingestion pipeline orchestrator."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.models.document import Document, Page, Chunk, DocType
from app.models.entity import Entity, EntityMention, GraphEdge, EntityType, RelationType
from app.services.ingestion.extractor import pdf_extractor
from app.services.ingestion.chunker import text_chunker
from app.services.ingestion.vlm_extractor import vlm_extractor
from app.services.llm.provider import llm_provider

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrate full document ingestion: extract → chunk → embed → store."""

    async def ingest_document(self, db: AsyncSession, file_path: str,
                              original_filename: str) -> Document:
        """Full ingestion pipeline for a single PDF."""
        logger.info(f"Starting ingestion: {original_filename}")

        # 1. Compute file hash for dedup
        file_hash = self._compute_hash(file_path)

        # 2. Check for duplicates
        existing = await db.execute(
            select(Document).where(Document.file_hash == file_hash)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Duplicate document: {original_filename} (same hash exists)")

        # 3. Extract PDF metadata
        pdf_meta = pdf_extractor.extract_metadata(file_path)

        # 4. Create document record
        doc = Document(
            filename=Path(file_path).name,
            original_filename=original_filename,
            file_hash=file_hash,
            file_path=file_path,
            page_count=pdf_meta["page_count"],
            file_size=Path(file_path).stat().st_size,
            status="processing",
        )
        db.add(doc)
        await db.flush()

        try:
            # 5. Extract text per page and render to PNG
            pages_data = pdf_extractor.extract_text_per_page(file_path)
            render_dir = Path(settings.render_storage_path) / str(doc.id)
            render_dir.mkdir(parents=True, exist_ok=True)

            full_text = ""
            page_records = []

            for page_data in pages_data:
                pnum = page_data["page_number"]

                # Render to PNG
                render_path = str(render_dir / f"page_{pnum}.png")
                pdf_extractor.render_page_to_png(file_path, pnum, render_path)

                page = Page(
                    document_id=doc.id,
                    page_number=pnum,
                    text=page_data["text"],
                    render_path=render_path,
                    width=page_data.get("width"),
                    height=page_data.get("height"),
                )
                db.add(page)
                page_records.append(page)
                full_text += page_data["text"] + "\n\n"

            await db.flush()

            # 6. VLM extraction (classification + summary + entities)
            if full_text.strip():
                await self._vlm_extract(db, doc, full_text)

            # 7. Chunk text and generate embeddings
            await self._chunk_and_embed(db, doc, page_records)

            # 8. Extract entities and build graph
            if full_text.strip():
                await self._extract_entities_and_graph(db, doc, full_text)

            doc.status = "ready"
            logger.info(f"Ingestion complete: {original_filename} (id={doc.id})")

        except Exception as e:
            doc.status = "error"
            doc.error_message = str(e)
            logger.error(f"Ingestion failed for {original_filename}: {e}")
            raise

        await db.flush()
        return doc

    async def _vlm_extract(self, db: AsyncSession, doc: Document, full_text: str):
        """Run VLM extraction for classification, summary, etc."""
        try:
            # Classify
            doc_type = await vlm_extractor.classify_document(full_text)
            doc.doc_type = DocType(doc_type) if doc_type in DocType.__members__.values() else DocType.OTHER

            # Project name
            doc.project_name = await vlm_extractor.extract_project_name(full_text)

            # Structured summary
            summary = await vlm_extractor.extract_structured_summary(full_text)
            doc.short_summary = summary.get("short_summary", "")
            doc.purpose = summary.get("purpose", "")
            doc.tech_summary = summary.get("tech_summary", "")
            doc.location = summary.get("location", "")
            doc.station = summary.get("station", "")
            doc.unit = summary.get("unit", "")
            if summary.get("doc_date"):
                try:
                    from datetime import datetime
                    doc.doc_date = datetime.strptime(summary["doc_date"], "%Y-%m-%d")
                except (ValueError, TypeError):
                    pass

        except Exception as e:
            logger.warning(f"VLM extraction partial failure: {e}")

    async def _chunk_and_embed(self, db: AsyncSession, doc: Document,
                               page_records: list[Page]):
        """Chunk document text and generate embeddings."""
        chunk_index = 0
        for page in page_records:
            if not page.text or len(page.text.strip()) < 20:
                continue

            chunks = text_chunker.chunk_text(page.text, page.page_number)

            for chunk_data in chunks:
                # Generate embedding
                try:
                    embedding = await llm_provider.embed(chunk_data["chunk_text"])
                except Exception as e:
                    logger.warning(f"Embedding failed for chunk {chunk_index}: {e}")
                    embedding = None

                chunk = Chunk(
                    document_id=doc.id,
                    page_id=page.id,
                    chunk_index=chunk_index,
                    chunk_text=chunk_data["chunk_text"],
                    embedding=embedding,
                    start_char=chunk_data.get("start_char"),
                    end_char=chunk_data.get("end_char"),
                    token_count=len(chunk_data["chunk_text"].split()),
                )
                db.add(chunk)
                chunk_index += 1

        await db.flush()
        logger.info(f"Created {chunk_index} chunks for document {doc.id}")

    async def _extract_entities_and_graph(self, db: AsyncSession, doc: Document,
                                          full_text: str):
        """Extract entities and build knowledge graph edges."""
        try:
            entities_raw = await vlm_extractor.extract_entities(full_text)

            for ent_data in entities_raw:
                ent_type_str = ent_data.get("type", "equipment")
                try:
                    ent_type = EntityType(ent_type_str)
                except ValueError:
                    ent_type = EntityType.EQUIPMENT

                ent_name = ent_data.get("name", "")
                if not ent_name:
                    continue

                # Upsert entity
                existing = await db.execute(
                    select(Entity).where(
                        Entity.entity_type == ent_type,
                        Entity.normalized_name == ent_name.upper()
                    )
                )
                entity = existing.scalar_one_or_none()
                if not entity:
                    entity = Entity(
                        entity_type=ent_type,
                        entity_name=ent_name,
                        normalized_name=ent_name.upper(),
                    )
                    db.add(entity)
                    await db.flush()

                # Create graph edge: Document MENTIONS_ENTITY
                edge = GraphEdge(
                    src_type="document",
                    src_id=doc.id,
                    rel_type=RelationType.MENTIONS_ENTITY,
                    dst_type="entity",
                    dst_id=entity.id,
                )
                db.add(edge)

            await db.flush()

        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")

    def _compute_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


ingestion_pipeline = IngestionPipeline()
