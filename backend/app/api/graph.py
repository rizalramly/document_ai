"""Graph query API for entity resolution and traversal."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from app.database import get_db
from app.models.entity import Entity, EntityMention, GraphEdge, EntityType
from app.models.document import Document, Chunk
from app.schemas.schemas import GraphQueryIn, GraphQueryOut, GraphNodeOut, GraphEdgeOut

router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/entities")
async def list_entities(
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List entities, optionally filtered by type or search term."""
    query = select(Entity)
    if entity_type:
        try:
            query = query.where(Entity.entity_type == EntityType(entity_type))
        except ValueError:
            pass
    if search:
        query = query.where(Entity.entity_name.ilike(f"%{search}%"))
    query = query.limit(limit)

    result = await db.execute(query)
    entities = result.scalars().all()
    return [{"id": e.id, "type": e.entity_type.value, "name": e.entity_name,
             "normalized": e.normalized_name} for e in entities]


@router.post("/graph/query", response_model=GraphQueryOut)
async def graph_query(req: GraphQueryIn, db: AsyncSession = Depends(get_db)):
    """Query the knowledge graph for entity relationships."""
    # 1. Find matching entities
    entities = await db.execute(
        select(Entity).where(
            Entity.entity_name.ilike(f"%{req.query}%") |
            Entity.normalized_name.ilike(f"%{req.query.upper()}%")
        )
    )
    found_entities = entities.scalars().all()

    if not found_entities:
        return GraphQueryOut(answer=f"No entities found matching '{req.query}'")

    nodes = []
    edges = []

    for entity in found_entities:
        nodes.append(GraphNodeOut(
            id=entity.id, node_type=entity.entity_type.value,
            name=entity.entity_name, metadata=entity.metadata_json
        ))

        # Find edges from this entity
        edge_results = await db.execute(
            select(GraphEdge).where(
                or_(
                    (GraphEdge.src_type == "entity") & (GraphEdge.src_id == entity.id),
                    (GraphEdge.dst_type == "entity") & (GraphEdge.dst_id == entity.id),
                )
            )
        )

        for edge in edge_results.scalars().all():
            # Resolve the other end
            if edge.src_type == "entity" and edge.src_id == entity.id:
                dst_node = await _resolve_node(db, edge.dst_type, edge.dst_id)
            else:
                dst_node = await _resolve_node(db, edge.src_type, edge.src_id)

            if dst_node:
                src_gnode = GraphNodeOut(
                    id=entity.id, node_type=entity.entity_type.value,
                    name=entity.entity_name
                )
                edges.append(GraphEdgeOut(
                    src=src_gnode, rel_type=edge.rel_type.value, dst=dst_node
                ))
                if dst_node not in nodes:
                    nodes.append(dst_node)

    return GraphQueryOut(nodes=nodes, edges=edges)


async def _resolve_node(db: AsyncSession, node_type: str, node_id: int) -> GraphNodeOut | None:
    """Resolve a graph node by type and ID."""
    if node_type == "entity":
        entity = await db.get(Entity, node_id)
        if entity:
            return GraphNodeOut(
                id=entity.id, node_type=entity.entity_type.value,
                name=entity.entity_name
            )
    elif node_type == "document":
        doc = await db.get(Document, node_id)
        if doc:
            return GraphNodeOut(
                id=doc.id, node_type="document",
                name=doc.original_filename
            )
    return None
