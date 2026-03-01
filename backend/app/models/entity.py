"""Entity, EntityMention, and GraphEdge models for knowledge graph."""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, ForeignKey,
    JSON, Float, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class EntityType(str, enum.Enum):
    EQUIPMENT = "equipment"
    INSTRUMENT = "instrument"
    VALVE = "valve"
    LINE = "line"
    SYSTEM = "system"
    STATION = "station"
    UNIT = "unit"
    EVENT = "event"
    FAILURE_MODE = "failure_mode"
    PARAMETER = "parameter"


class RelationType(str, enum.Enum):
    HAS_PAGE = "HAS_PAGE"
    HAS_CHUNK = "HAS_CHUNK"
    MENTIONS_ENTITY = "MENTIONS_ENTITY"
    CONNECTED_TO = "CONNECTED_TO"
    LOCATED_IN = "LOCATED_IN"
    RELATES_TO_EVENT = "RELATES_TO_EVENT"
    AFFECTS = "AFFECTS"
    PART_OF = "PART_OF"
    UPSTREAM_OF = "UPSTREAM_OF"
    DOWNSTREAM_OF = "DOWNSTREAM_OF"


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(Enum(EntityType), nullable=False, index=True)
    entity_name = Column(String(500), nullable=False)
    normalized_name = Column(String(500), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    mentions = relationship("EntityMention", back_populates="entity", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_entity_type_name", "entity_type", "normalized_name", unique=True),
    )


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Float, default=1.0)
    bbox_json = Column(JSON, nullable=True)

    # Relationships
    entity = relationship("Entity", back_populates="mentions")
    chunk = relationship("Chunk", back_populates="entity_mentions")


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    src_type = Column(String(50), nullable=False)
    src_id = Column(Integer, nullable=False)
    rel_type = Column(Enum(RelationType), nullable=False)
    dst_type = Column(String(50), nullable=False)
    dst_id = Column(Integer, nullable=False)
    provenance_chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Float, default=1.0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_graph_src", "src_type", "src_id"),
        Index("ix_graph_dst", "dst_type", "dst_id"),
        Index("ix_graph_rel", "rel_type"),
    )
