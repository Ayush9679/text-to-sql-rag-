from typing import Any
from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
    query: str
    intent: str | None = None
    entities: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    grouping: list[str] = Field(default_factory=list)
    aggregation: str | None = None
    sort_direction: str | None = None
    limit: int | None = None
    ambiguities: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class IntentValidationResult(BaseModel):
    valid: bool
    intent: str | None = None
    ambiguities: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    reason: str | None = None


class AmbiguityResult(BaseModel):
    is_ambiguous: bool = False
    ambiguity_types: list[str] = Field(default_factory=list)
    ambiguous_terms: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class MissingInformationResult(BaseModel):
    missing: list[str] = Field(default_factory=list)
    required: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)
    reasons: dict[str, str] = Field(default_factory=dict)
    confidence: float = 1.0


class ClarificationDecision(BaseModel):
    action: str  # "proceed", "clarify", "unsupported"
    reason: str
    confidence: float = 0.0
    missing_information: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class ClarificationQuestion(BaseModel):
    question: str
    reason: str
    options: list[str] = Field(default_factory=list)
    target_field: str
    confidence: float = 0.0


class ClarificationTurn(BaseModel):
    question: ClarificationQuestion
    user_answer: str | None = None
    resolved_field: str | None = None
    resolved_value: Any = None
    timestamp: str | None = None


class ClarificationState(BaseModel):
    conversation_id: str
    original_query: str
    current_query: str
    analysis: QueryAnalysis | None = None
    pending_clarifications: list[ClarificationQuestion] = Field(
        default_factory=list
    )
    resolved_fields: dict[str, Any] = Field(default_factory=dict)
    clarification_history: list[ClarificationTurn] = Field(
        default_factory=list
    )
    status: str = "awaiting_clarification"  # "awaiting_clarification", "resolved", "cancelled"