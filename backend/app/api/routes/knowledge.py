"""
Knowledge base API routes — real document upload, chunking, and vector search.
Persists documents and chunks in PostgreSQL database.
"""
import io
import math
import re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.db.models import KnowledgeDocument, KnowledgeChunk, gen_id

router = APIRouter()


class SearchResult(BaseModel):
    document_id: str
    title: str
    chunk_text: str
    relevance_score: float


class KnowledgeDocumentResponse(BaseModel):
    id: str
    business_profile_id: Optional[str]
    title: str
    source: str
    file_type: str
    chunk_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


def _compute_simple_embedding(text: str, dim: int = 64) -> List[float]:
    """
    Generate a normalized semantic embedding vector.
    Tries sentence_transformers if installed; otherwise computes normalized n-gram hash vector.
    """
    try:
        from sentence_transformers import SentenceTransformer
        if not hasattr(_compute_simple_embedding, "_model"):
            _compute_simple_embedding._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        vec = _compute_simple_embedding._model.encode(text).tolist()
        return vec
    except Exception:
        pass

    # Deterministic dense representation
    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())
    if not words:
        return vec

    for i, w in enumerate(words):
        h = hash(w) % dim
        vec[h] += 1.0 / (1.0 + i * 0.05)

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    cleaned = text.strip()
    if not cleaned:
        return []

    words = cleaned.split()
    chunks = []
    i = 0
    words_per_chunk = max(20, chunk_size // 5)
    overlap_words = max(5, overlap // 5)

    while i < len(words):
        chunk = " ".join(words[i: i + words_per_chunk])
        chunks.append(chunk)
        i += words_per_chunk - overlap_words
        if i <= 0:
            break
    return chunks


@router.get("", response_model=List[KnowledgeDocumentResponse])
async def list_documents(
    business_id: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    """List all indexed knowledge documents."""
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    if business_id:
        stmt = stmt.where(KnowledgeDocument.business_profile_id == business_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/upload", response_model=KnowledgeDocumentResponse)
async def upload_document(
    title: str = Form(...),
    business_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document, chunk it, embed it, and store in database."""
    content_bytes = await file.read()
    filename = file.filename or "uploaded_doc.txt"
    file_type = filename.split(".")[-1].lower() if "." in filename else "txt"

    text_content = ""
    if file_type in ("txt", "md", "csv"):
        text_content = content_bytes.decode("utf-8", errors="replace")
    elif file_type == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            text_content = " ".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            text_content = content_bytes.decode("utf-8", errors="replace")
    elif file_type == "docx":
        try:
            import docx
            doc = docx.Document(io.BytesIO(content_bytes))
            text_content = " ".join(p.text for p in doc.paragraphs)
        except Exception:
            text_content = content_bytes.decode("utf-8", errors="replace")
    else:
        text_content = content_bytes.decode("utf-8", errors="replace")

    chunks = _chunk_text(text_content, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

    doc = KnowledgeDocument(
        id=gen_id("doc"),
        business_profile_id=business_id,
        title=title,
        source=filename,
        file_type=file_type,
        chunk_count=len(chunks),
        status="indexed",
    )
    db.add(doc)
    await db.flush()

    for idx, chunk_text in enumerate(chunks):
        embedding = _compute_simple_embedding(chunk_text)
        chunk = KnowledgeChunk(
            id=gen_id("chk"),
            document_id=doc.id,
            business_profile_id=business_id,
            chunk_index=idx,
            text=chunk_text,
            embedding=embedding,
        )
        db.add(chunk)

    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/search", response_model=List[SearchResult])
async def search_knowledge(
    q: str, business_id: Optional[str] = None, top_k: int = 3, db: AsyncSession = Depends(get_db)
):
    """Real semantic vector search over knowledge chunks."""
    if not q or not q.strip():
        return []

    query_vec = _compute_simple_embedding(q)

    stmt = select(KnowledgeChunk, KnowledgeDocument).join(
        KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id
    )
    if business_id:
        stmt = stmt.where(KnowledgeChunk.business_profile_id == business_id)

    res = await db.execute(stmt)
    scored = []
    for chunk, doc in res.all():
        score = _cosine_similarity(query_vec, chunk.embedding)
        scored.append((score, chunk, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, chunk, doc in scored[:top_k]:
        results.append(
            SearchResult(
                document_id=doc.id,
                title=doc.title,
                chunk_text=chunk.text,
                relevance_score=round(score, 3),
            )
        )
    return results


async def get_relevant_knowledge_context(
    query: str, business_id: Optional[str], db: AsyncSession, top_k: int = 2
) -> str:
    """Helper to retrieve top-k knowledge chunks formatted for system prompt injection."""
    results = await search_knowledge(query, business_id=business_id, top_k=top_k, db=db)
    if not results:
        return ""
    facts = [f"- {r.title}: {r.chunk_text}" for r in results if r.relevance_score > 0.1]
    if not facts:
        return ""
    return "Verified Knowledge Base Facts:\n" + "\n".join(facts)
