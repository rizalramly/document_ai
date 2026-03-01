"""Annotation CRUD API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.annotation import Annotation, Severity
from app.schemas.schemas import AnnotationIn, AnnotationOut

router = APIRouter(prefix="/api", tags=["annotations"])


@router.get("/documents/{doc_id}/annotations", response_model=list[AnnotationOut])
async def list_annotations(doc_id: int, db: AsyncSession = Depends(get_db)):
    """List annotations for a document."""
    result = await db.execute(
        select(Annotation)
        .where(Annotation.document_id == doc_id)
        .order_by(Annotation.created_at.desc())
    )
    return [AnnotationOut.model_validate(a) for a in result.scalars().all()]


@router.post("/annotations", response_model=AnnotationOut)
async def create_annotation(data: AnnotationIn, db: AsyncSession = Depends(get_db)):
    """Create a new annotation."""
    annotation = Annotation(
        document_id=data.document_id,
        page_number=data.page_number,
        bbox_json=data.bbox_json,
        severity=Severity(data.severity) if data.severity in [s.value for s in Severity] else Severity.NOTE,
        text=data.text,
        author=data.author,
    )
    db.add(annotation)
    await db.flush()
    await db.refresh(annotation)
    return AnnotationOut.model_validate(annotation)


@router.delete("/annotations/{ann_id}")
async def delete_annotation(ann_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an annotation."""
    annotation = await db.get(Annotation, ann_id)
    if not annotation:
        raise HTTPException(404, "Annotation not found")
    await db.delete(annotation)
    return {"success": True, "message": "Annotation deleted"}
