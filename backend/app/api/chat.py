"""Chat/RAG API routes."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector

from app.database import get_db
from app.models.document import Document, Chunk
from app.schemas.schemas import ChatQueryIn, ChatResponseOut, Citation, ViewerAction
from app.services.llm.provider import llm_provider
from app.services.llm.prompts import CHAT_SYSTEM_PROMPT, CHAT_RAG_PROMPT
from app.models.chat import ChatSession, ChatMessage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/query", response_model=ChatResponseOut)
async def chat_query(req: ChatQueryIn, db: AsyncSession = Depends(get_db)):
    """RAG query: embed query → retrieve chunks → generate answer with citations."""

    # 1. Create or get session
    if req.session_id:
        session = await db.get(ChatSession, req.session_id)
        if not session:
            session = ChatSession(context_scope=req.context_scope or "global")
            db.add(session)
            await db.flush()
    else:
        session = ChatSession(context_scope=req.context_scope or "global")
        db.add(session)
        await db.flush()

    # 2. Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=req.query)
    db.add(user_msg)
    await db.flush()

    # 3. Embed query
    try:
        query_embedding = await llm_provider.embed(req.query)
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        return ChatResponseOut(
            answer="I'm unable to process your query at the moment. Please try again.",
            session_id=session.id,
        )

    # 4. Vector similarity search
    retrieved_chunks = await _vector_search(db, query_embedding, req.filters, top_k=10)

    # 5. Build evidence context
    evidence_parts = []
    citations = []
    for i, (chunk, doc, score) in enumerate(retrieved_chunks):
        evidence_parts.append(
            f"[Source {i + 1}] Document: {doc.original_filename}, "
            f"Page: {chunk.page_id or 'N/A'}\n{chunk.chunk_text}"
        )
        citations.append(Citation(
            document_id=doc.id,
            filename=doc.original_filename,
            page_number=chunk.page_id,
            chunk_id=chunk.id,
            snippet=chunk.chunk_text[:200],
            relevance_score=round(score, 3) if score else None,
        ))

    evidence = "\n\n---\n\n".join(evidence_parts) if evidence_parts else "No relevant documents found."

    # 6. Generate answer with RAG prompt
    rag_prompt = CHAT_RAG_PROMPT.format(evidence=evidence, query=req.query)

    try:
        answer = await llm_provider.generate(
            prompt=rag_prompt,
            system=CHAT_SYSTEM_PROMPT,
            temperature=0.2
        )
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        answer = "I could not generate a response. Please try again."

    # 7. Detect viewer actions (if query mentions "show", "diagram", "drawing")
    viewer_actions = []
    show_keywords = ["show", "diagram", "drawing", "view", "open", "display", "image"]
    if any(kw in req.query.lower() for kw in show_keywords) and citations:
        viewer_actions.append(ViewerAction(
            action="open_page",
            document_id=citations[0].document_id,
            page_number=citations[0].page_number,
        ))

    # 8. Save assistant message
    asst_msg = ChatMessage(
        session_id=session.id, role="assistant", content=answer,
        citations_json=[c.model_dump() for c in citations],
        viewer_actions_json=[v.model_dump() for v in viewer_actions],
    )
    db.add(asst_msg)
    await db.flush()

    return ChatResponseOut(
        answer=answer,
        citations=citations,
        viewer_actions=viewer_actions,
        session_id=session.id,
    )


async def _vector_search(db: AsyncSession, query_embedding: list[float],
                          filters: dict | None, top_k: int = 10):
    """Perform vector similarity search using pgvector."""
    # Build raw SQL for pgvector cosine distance
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    filter_clause = ""
    if filters:
        if filters.get("station"):
            filter_clause += f" AND d.station = '{filters['station']}'"
        if filters.get("unit"):
            filter_clause += f" AND d.unit = '{filters['unit']}'"
        if filters.get("doc_type"):
            filter_clause += f" AND d.doc_type = '{filters['doc_type']}'"

    sql = text(f"""
        SELECT c.id, c.document_id, c.chunk_text, c.page_id, c.keywords,
               d.original_filename, d.id as doc_id, d.station, d.unit,
               c.embedding <=> '{embedding_str}'::vector AS distance
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL {filter_clause}
        ORDER BY distance ASC
        LIMIT :top_k
    """)

    result = await db.execute(sql, {"top_k": top_k})
    rows = result.all()

    chunks_with_docs = []
    for row in rows:
        chunk = await db.get(Chunk, row[0])
        doc = await db.get(Document, row[1])
        score = 1 - row[9]  # Convert distance to similarity
        chunks_with_docs.append((chunk, doc, score))

    return chunks_with_docs
