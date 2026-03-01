"""Document, Page, and Chunk models with pgvector embeddings."""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, ForeignKey,
    JSON, Float, Index, func
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.config import settings


class DocType(str, enum.Enum):
    MANUAL = "manual"
    PID = "pid"
    SPEC = "spec"
    LOGBOOK = "logbook"
    DRAWING = "drawing"
    REPORT = "report"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False, index=True)
    original_filename = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA256 for dedup
    doc_type = Column(Enum(DocType), default=DocType.OTHER)
    project_name = Column(String(500), nullable=True)
    station = Column(String(200), nullable=True, index=True)
    unit = Column(String(100), nullable=True, index=True)
    cluster = Column(String(200), nullable=True, index=True)
    doc_date = Column(DateTime, nullable=True)
    short_summary = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    tech_summary = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    page_count = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    file_path = Column(String(1000), nullable=False)
    status = Column(String(50), default="pending")  # pending / processing / ready / error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_documents_station_unit", "station", "unit"),
        Index("ix_documents_doc_type", "doc_type"),
    )


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    render_path = Column(String(1000), nullable=True)  # Path to rendered PNG
    image_path = Column(String(1000), nullable=True)    # Original image for VLM
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="pages")
    chunks = relationship("Chunk", back_populates="page", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_pages_doc_page", "document_id", "page_number", unique=True),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=True, index=True)
    chunk_index = Column(Integer, default=0)  # Order within document
    chunk_text = Column(Text, nullable=False)
    bbox_json = Column(JSON, nullable=True)  # {x, y, w, h} on page
    embedding = Column(Vector(settings.embedding_dim), nullable=True)
    keywords = Column(JSON, nullable=True)   # List of extracted keywords
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")
    page = relationship("Page", back_populates="chunks")
    entity_mentions = relationship("EntityMention", back_populates="chunk", cascade="all, delete-orphan")
