from typing import Any

from pydantic import BaseModel, Field, field_validator


DEFAULT_MAX_ROWS = 1_000
MAX_ALLOWED_ROWS = 10_000


class ExecutionRequest(BaseModel):
    """Read-only SQL and the bounded execution options accepted by Phase 6."""

    sql: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    max_rows: int = Field(default=DEFAULT_MAX_ROWS, ge=1, le=MAX_ALLOWED_ROWS)
    timeout: float | None = Field(default=None, gt=0)
    dialect: str = "postgresql"

    @field_validator("sql")
    @classmethod
    def validate_sql(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("sql cannot be empty")
        return value

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, value: str) -> str:
        value = value.strip().lower()
        if value != "postgresql":
            raise ValueError("Only PostgreSQL is supported")
        return value


class ExecutionResult(BaseModel):
    """JSON-safe result returned by the read-only execution service."""

    success: bool
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(default=0, ge=0)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    truncated: bool = False
    error: str | None = None
