"""Annotation model for document/drawing annotations."""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class Severity(str, enum.Enum):
    WARNING = "warning"
    NOTE = "note"
    CRITICAL = "critical"


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True)
    page_number = Column(Integer, nullable=True)
    bbox_json = Column(JSON, nullable=True)  # {x, y, w, h}
    severity = Column(Enum(Severity), default=Severity.NOTE)
    text = Column(Text, nullable=False)
    author = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="annotations")
