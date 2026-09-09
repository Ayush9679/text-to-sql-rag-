"""Multi-signal confidence scoring engine for Text-to-SQL analytics."""

from pydantic import BaseModel, Field
from app.config import get_settings


class ConfidenceBreakdown(BaseModel):
    composite_score: float
    retrieval_score: float = 1.0
    schema_score: float = 1.0
    sql_validation_score: float = 1.0
    execution_score: float = 1.0
    ambiguity_penalty: float = 0.0
    llm_reported_score: float = 1.0
    recommendation: str = "AUTO_EXECUTE"  # AUTO_EXECUTE, EXECUTE_WITH_ASSUMPTION, CLARIFICATION_REQUIRED, REJECT
    reasons: list[str] = Field(default_factory=list)


class ConfidenceEngine:
    """Calculates weighted multi-signal confidence scores for analytical queries."""

    def __init__(
        self,
        w_retrieval: float = 0.15,
        w_schema: float = 0.25,
        w_sql_valid: float = 0.25,
        w_exec: float = 0.25,
        w_llm: float = 0.10,
    ):
        self.w_retrieval = w_retrieval
        self.w_schema = w_schema
        self.w_sql_valid = w_sql_valid
        self.w_exec = w_exec
        self.w_llm = w_llm
        self.settings = get_settings()

    def evaluate(
        self,
        retrieval_score: float = 1.0,
        schema_match_ratio: float = 1.0,
        sql_valid: bool = True,
        execution_success: bool = True,
        row_count: int = 1,
        ambiguity_detected: bool = False,
        ambiguity_penalty: float = 0.0,
        llm_confidence: float = 0.90,
    ) -> ConfidenceBreakdown:
        reasons: list[str] = []

        # 1. Retrieval signal
        ret_score = max(0.0, min(1.0, retrieval_score))
        if ret_score < 0.5:
            reasons.append(f"Low semantic retrieval relevance ({ret_score:.2f}).")

        # 2. Schema match signal
        sch_score = max(0.0, min(1.0, schema_match_ratio))
        if sch_score < 1.0:
            reasons.append(f"Some referenced schema elements were partially matched ({sch_score:.2f}).")

        # 3. SQL validation signal
        val_score = 1.0 if sql_valid else 0.0
        if not sql_valid:
            reasons.append("SQL validation checks failed.")

        # 4. Execution signal
        if not execution_success:
            exec_score = 0.0
            reasons.append("Database execution failed.")
        elif row_count == 0:
            exec_score = 0.70  # Valid query, but returned empty data
            reasons.append("Query executed successfully but returned 0 rows.")
        else:
            exec_score = 1.0

        # 5. Ambiguity penalty
        penalty = ambiguity_penalty if ambiguity_detected else 0.0
        if ambiguity_detected:
            reasons.append("Query has multiple plausible business interpretations.")

        # Weighted calculation
        raw_composite = (
            self.w_retrieval * ret_score
            + self.w_schema * sch_score
            + self.w_sql_valid * val_score
            + self.w_exec * exec_score
            + self.w_llm * max(0.0, min(1.0, llm_confidence))
        ) - penalty

        composite_score = round(max(0.0, min(1.0, raw_composite)), 3)

        # Recommendation based on configured thresholds
        if composite_score >= self.settings.CONFIDENCE_AUTO_EXECUTE:
            recommendation = "AUTO_EXECUTE"
        elif composite_score >= self.settings.CONFIDENCE_CLARIFICATION_REQUIRED:
            recommendation = "EXECUTE_WITH_ASSUMPTION"
        else:
            recommendation = "CLARIFICATION_REQUIRED"

        return ConfidenceBreakdown(
            composite_score=composite_score,
            retrieval_score=ret_score,
            schema_score=sch_score,
            sql_validation_score=val_score,
            execution_score=exec_score,
            ambiguity_penalty=penalty,
            llm_reported_score=llm_confidence,
            recommendation=recommendation,
            reasons=reasons,
        )
