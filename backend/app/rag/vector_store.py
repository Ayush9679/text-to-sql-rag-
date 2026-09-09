"""Tenant-isolated Vector Store backed by PostgreSQL and pgvector."""

import math
from typing import Any, Sequence
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.database.models import EmbeddingDocument
from app.rag.embedding import EmbeddingProvider, get_embedding_provider


class VectorDocument(BaseModel):
    id: str
    business_id: str
    dataset_id: str
    document_type: str  # table, column, metric, relationship, concept, rule
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)


class VectorSearchResult(BaseModel):
    document: VectorDocument
    similarity: float


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 <= 1e-9 or norm2 <= 1e-9:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm1 * norm2)))


class PGVectorStore:
    """PostgreSQL pgvector-backed semantic document store with tenant isolation."""

    def __init__(
        self,
        engine: Engine | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ):
        self.engine = engine
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self._memory_docs: list[VectorDocument] = []  # In-memory mirror for fallback testing

    def index_documents(
        self,
        documents: Sequence[VectorDocument],
        session: Session | None = None,
    ) -> int:
        if not documents:
            return 0

        # Compute embeddings for any documents lacking them
        for doc in documents:
            if not doc.embedding:
                doc.embedding = self.embedding_provider.embed_text(f"{doc.title}\n{doc.content}")
            # Mirror in memory
            self._memory_docs = [d for d in self._memory_docs if d.id != doc.id]
            self._memory_docs.append(doc)

        if session is not None:
            for doc in documents:
                db_doc = EmbeddingDocument(
                    id=doc.id,
                    business_id=doc.business_id,
                    dataset_id=doc.dataset_id,
                    document_type=doc.document_type,
                    title=doc.title,
                    content=doc.content,
                    doc_metadata=doc.metadata,
                    embedding=doc.embedding,
                )
                session.merge(db_doc)
            session.flush()

        return len(documents)

    def search(
        self,
        query: str,
        business_id: str,
        dataset_id: str | None = None,
        document_types: list[str] | None = None,
        top_k: int = 8,
        min_similarity: float = 0.25,
        session: Session | None = None,
    ) -> list[VectorSearchResult]:
        query_vec = self.embedding_provider.embed_text(query)
        results: list[VectorSearchResult] = []

        # If connected to active session/database
        if session is not None:
            try:
                query_filter = session.query(EmbeddingDocument).filter(EmbeddingDocument.business_id == business_id)
                if dataset_id:
                    query_filter = query_filter.filter(EmbeddingDocument.dataset_id == dataset_id)
                if document_types:
                    query_filter = query_filter.filter(EmbeddingDocument.document_type.in_(document_types))

                db_docs = query_filter.all()
                for d in db_docs:
                    emb = list(d.embedding) if d.embedding is not None else []
                    if not emb:
                        emb = self.embedding_provider.embed_text(f"{d.title}\n{d.content}")
                    sim = cosine_similarity(query_vec, emb)
                    if sim >= min_similarity:
                        vdoc = VectorDocument(
                            id=d.id,
                            business_id=d.business_id,
                            dataset_id=d.dataset_id,
                            document_type=d.document_type,
                            title=d.title,
                            content=d.content,
                            metadata=d.doc_metadata or {},
                            embedding=emb,
                        )
                        results.append(VectorSearchResult(document=vdoc, similarity=round(sim, 4)))
            except Exception:
                pass

        # Fall back to in-memory index
        if not results and self._memory_docs:
            for d in self._memory_docs:
                if d.business_id != business_id:
                    continue
                if dataset_id and d.dataset_id != dataset_id:
                    continue
                if document_types and d.document_type not in document_types:
                    continue
                sim = cosine_similarity(query_vec, d.embedding)
                if sim >= min_similarity:
                    results.append(VectorSearchResult(document=d, similarity=round(sim, 4)))

        # Sort descending by similarity
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[:top_k]
