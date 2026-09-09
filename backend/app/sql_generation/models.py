from pydantic import BaseModel, Field, field_validator


class SQLGenerationRequest(BaseModel):
    """
    Structured input to the SQL generation layer.

    This object combines:
    - the original user question
    - Phase 4's interpreted intent
    - Phase 3's retrieved schema context
    - business knowledge
    - PostgreSQL dialect information
    """

    query: str

    intent: str | None = None

    entities: list[str] = Field(
        default_factory=list
    )

    metrics: list[str] = Field(
        default_factory=list
    )

    filters: list[str] = Field(
        default_factory=list
    )

    aggregation: str | None = None

    sort_direction: str | None = None

    limit: int | None = None

    schema_context: str = ""

    business_context: str = ""

    dialect: str = "postgresql"

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "query cannot be empty"
            )

        return value

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, value: str) -> str:

        value = value.strip().lower()

        if value != "postgresql":
            raise ValueError(
                "Only PostgreSQL is supported"
            )

        return value

    @field_validator("limit")
    @classmethod
    def validate_limit(
        cls,
        value: int | None,
    ) -> int | None:

        if value is not None and value <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        return value


class SQLGenerationResult(BaseModel):
    """
    Structured output produced by the SQL generation layer.

    This is the contract between SQL generation
    and the later SQL validation/safety layers.
    """

    sql: str

    dialect: str = "postgresql"

    tables_used: list[str] = Field(
        default_factory=list
    )

    columns_used: list[str] = Field(
        default_factory=list
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    explanation: str | None = None

    @field_validator("sql")
    @classmethod
    def validate_sql(cls, value: str) -> str:

        # An empty string is the explicit, safe representation of a
        # generation failure.  It remains a string and is never executable.
        return value.strip()

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, value: str) -> str:

        value = value.strip().lower()

        if value != "postgresql":
            raise ValueError(
                "Only PostgreSQL is supported"
            )

        return value


class SQLGenerationError(BaseModel):
    """
    Structured representation of a SQL generation failure.
    """

    error_type: str

    message: str

    retryable: bool = False
