"""Public request and response contracts for the final application layer."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.clarification.models import ClarificationQuestion, ClarificationState
from app.sql_execution.models import DEFAULT_MAX_ROWS, MAX_ALLOWED_ROWS


class QueryStatus(str, Enum):
    SUCCESS = "success"
    CLARIFICATION_REQUIRED = "clarification_required"
    FAILED = "failed"


class QueryRequest(BaseModel):
    """A natural-language request accepted by the application orchestrator."""

    query: str
    conversation_id: str | None = None
    clarification_state: ClarificationState | None = None
    clarification_answer: str | None = None
    max_rows: int = Field(default=DEFAULT_MAX_ROWS, ge=1, le=MAX_ALLOWED_ROWS)
    dialect: str = "postgresql"

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query cannot be empty")
        return value

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, value: str) -> str:
        value = value.strip().lower()
        if value != "postgresql":
            raise ValueError("Only PostgreSQL is supported")
        return value


class QueryResponse(BaseModel):
    """Controlled result of a complete natural-language analytical request."""

    status: QueryStatus
    sql: str | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(default=0, ge=0)
    clarification: ClarificationQuestion | None = None
    clarification_state: ClarificationState | None = None
    explanation: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
