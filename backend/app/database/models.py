"""PostgreSQL SQLAlchemy ORM Models for the Multi-Tenant Business Data Intelligence Platform."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None  # type: ignore


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base model class."""
    pass


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    schema_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list[User]] = relationship("User", back_populates="business", cascade="all, delete-orphan")
    datasets: Mapped[list[Dataset]] = relationship("Dataset", back_populates="business", cascade="all, delete-orphan")
    conversations: Mapped[list[Conversation]] = relationship("Conversation", back_populates="business", cascade="all, delete-orphan")
    embedding_docs: Mapped[list[EmbeddingDocument]] = relationship("EmbeddingDocument", back_populates="business", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(64), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="member", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    business: Mapped[Business] = relationship("Business", back_populates="users")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(64), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADED", nullable=False)
    total_tables: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    business: Mapped[Business] = relationship("Business", back_populates="datasets")
    files: Mapped[list[DatasetFile]] = relationship("DatasetFile", back_populates="dataset", cascade="all, delete-orphan")
    columns: Mapped[list[DatasetColumn]] = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    relationships: Mapped[list[DatasetRelationship]] = relationship("DatasetRelationship", back_populates="dataset", cascade="all, delete-orphan")
    entities: Mapped[list[SemanticEntity]] = relationship("SemanticEntity", back_populates="dataset", cascade="all, delete-orphan")
    metrics: Mapped[list[SemanticMetric]] = relationship("SemanticMetric", back_populates="dataset", cascade="all, delete-orphan")
    terms: Mapped[list[SemanticTerm]] = relationship("SemanticTerm", back_populates="dataset", cascade="all, delete-orphan")
    ingestion_jobs: Mapped[list[IngestionJob]] = relationship("IngestionJob", back_populates="dataset", cascade="all, delete-orphan")


class DatasetFile(Base):
    __tablename__ = "dataset_files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    table_name: Mapped[str] = mapped_column(String(64), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delimiter: Mapped[str] = mapped_column(String(8), default=",", nullable=False)
    encoding: Mapped[str] = mapped_column(String(32), default="utf-8", nullable=False)
    profile_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="files")


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    table_name: Mapped[str] = mapped_column(String(64), nullable=False)
    column_name: Mapped[str] = mapped_column(String(64), nullable=False)
    original_header: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(32), nullable=False)
    semantic_type: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    is_primary_key_candidate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_foreign_key_candidate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    null_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cardinality: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sample_values: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="columns")


class DatasetRelationship(Base):
    __tablename__ = "dataset_relationships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    source_table: Mapped[str] = mapped_column(String(64), nullable=False)
    source_column: Mapped[str] = mapped_column(String(64), nullable=False)
    target_table: Mapped[str] = mapped_column(String(64), nullable=False)
    target_column: Mapped[str] = mapped_column(String(64), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(32), default="MANY_TO_ONE", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="relationships")


class SemanticEntity(Base):
    __tablename__ = "semantic_entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    primary_table: Mapped[str] = mapped_column(String(64), nullable=False)
    identifier_column: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="entities")


class SemanticMetric(Base):
    __tablename__ = "semantic_metrics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    formula: Mapped[str] = mapped_column(String(255), nullable=False)
    sql_expression: Mapped[str] = mapped_column(Text, nullable=False)
    target_table: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="metrics")


class SemanticTerm(Base):
    __tablename__ = "semantic_terms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    term: Mapped[str] = mapped_column(String(128), nullable=False)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    synonyms: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    related_tables: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    related_columns: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="terms")


class EmbeddingDocument(Base):
    __tablename__ = "embedding_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(64), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # table, column, metric, relationship, concept
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    
    # Store pgvector embedding when available, plus raw vector fallback in JSON
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(384) if HAS_PGVECTOR and Vector is not None else JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    business: Mapped[Business] = relationship("Business", back_populates="embedding_docs")

    __table_args__ = (
        Index("ix_embedding_docs_business_dataset", "business_id", "dataset_id"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(64), ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New Analysis", nullable=False)
    state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    business: Mapped[Business] = relationship("Business", back_populates="conversations")
    messages: Mapped[list[ConversationMessage]] = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")
    queries: Mapped[list[QueryRecord]] = relationship("QueryRecord", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    msg_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")


class QueryRecord(Base):
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=True)
    business_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="RECEIVED", nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    generated_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assumptions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    query_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation: Mapped[Optional[Conversation]] = relationship("Conversation", back_populates="queries")
    result: Mapped[Optional[QueryResultRecord]] = relationship("QueryResultRecord", back_populates="query", uselist=False, cascade="all, delete-orphan")


class QueryResultRecord(Base):
    __tablename__ = "query_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id: Mapped[str] = mapped_column(String(64), ForeignKey("queries.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    columns: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    rows: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chart_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    query: Mapped[QueryRecord] = relationship("QueryRecord", back_populates="result")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    business_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADED", nullable=False)  # UPLOADED, VALIDATING, PROFILING, SCHEMA_INFERENCE, IMPORTING, INDEXING, EMBEDDING, READY, FAILED
    current_step: Mapped[str] = mapped_column(String(64), default="Initial Upload", nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="ingestion_jobs")
