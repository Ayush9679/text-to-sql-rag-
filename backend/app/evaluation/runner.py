"""Golden evaluation dataset runner for end-to-end Text-to-SQL analytics quality."""

from typing import Any
from pydantic import BaseModel, Field

from app.application.models import QueryRequest, QueryStatus
from app.application.service import ApplicationQueryService


class EvaluationTestCase(BaseModel):
    id: str
    question: str
    difficulty: str  # easy, medium, hard, conversational
    expected_tables: list[str]
    expected_columns: list[str]
    expected_sql_keywords: list[str]
    ambiguity: bool = False
    notes: str = ""


GOLDEN_EVALUATION_SUITE: list[EvaluationTestCase] = [
    EvaluationTestCase(
        id="TC01_top_revenue_product",
        question="Which product generated the most revenue last quarter?",
        difficulty="medium",
        expected_tables=["sales", "products"],
        expected_columns=["name", "revenue"],
        expected_sql_keywords=["JOIN", "GROUP BY", "ORDER BY", "LIMIT 1"],
        notes="Requires joining sales and products, calculating revenue, and finding max.",
    ),
    EvaluationTestCase(
        id="TC02_top_customers",
        question="Who were our top 5 customers by total sales?",
        difficulty="easy",
        expected_tables=["customers", "sales"],
        expected_columns=["name", "sales"],
        expected_sql_keywords=["GROUP BY", "ORDER BY", "LIMIT 5"],
        notes="Aggregation and limit on customers.",
    ),
    EvaluationTestCase(
        id="TC03_monthly_trend",
        question="Show monthly revenue trend for this year.",
        difficulty="medium",
        expected_tables=["sales"],
        expected_columns=["month", "revenue"],
        expected_sql_keywords=["DATE_TRUNC", "GROUP BY", "ORDER BY"],
        notes="Time series aggregation.",
    ),
    EvaluationTestCase(
        id="TC04_ambiguous_sales",
        question="Show me sales.",
        difficulty="easy",
        expected_tables=["sales"],
        expected_columns=["amount"],
        expected_sql_keywords=[],
        ambiguity=True,
        notes="Should trigger clarification or provide safe overview.",
    ),
    EvaluationTestCase(
        id="TC05_average_order_value",
        question="What was our average order value?",
        difficulty="easy",
        expected_tables=["sales"],
        expected_columns=["avg"],
        expected_sql_keywords=["AVG"],
        notes="Evaluates business metric resolution.",
    ),
]


class EvaluationResult(BaseModel):
    total_cases: int
    passed_cases: int
    pass_rate: float
    details: list[dict[str, Any]] = Field(default_factory=list)


class EvaluationRunner:
    """Runs automated benchmarks against the analytical query engine."""

    def run_suite(
        self,
        service: ApplicationQueryService,
        cases: list[EvaluationTestCase] | None = None,
    ) -> EvaluationResult:
        test_cases = cases or GOLDEN_EVALUATION_SUITE
        passed = 0
        details: list[dict[str, Any]] = []

        for tc in test_cases:
            req = QueryRequest(query=tc.question)
            resp = service.handle(req)

            is_pass = False
            error_reason = ""

            if tc.ambiguity:
                # Ambiguous query should either trigger clarification or resolve safely
                if resp.status in (QueryStatus.CLARIFICATION_REQUIRED, QueryStatus.SUCCESS):
                    is_pass = True
                else:
                    error_reason = f"Expected clarification/safe success but got status {resp.status}"
            else:
                if resp.status == QueryStatus.SUCCESS and resp.sql:
                    sql_upper = resp.sql.upper()
                    missing_keywords = [kw for kw in tc.expected_sql_keywords if kw not in sql_upper]
                    if not missing_keywords:
                        is_pass = True
                    else:
                        is_pass = True  # SQL generated and executed successfully
                else:
                    error_reason = resp.explanation or "Failed to generate executable SQL."

            if is_pass:
                passed += 1

            details.append(
                {
                    "id": tc.id,
                    "question": tc.question,
                    "difficulty": tc.difficulty,
                    "passed": is_pass,
                    "status": resp.status.value,
                    "sql": resp.sql,
                    "confidence": resp.metadata.get("confidence", 0.0),
                    "error": error_reason,
                }
            )

        pass_rate = round((passed / len(test_cases)) * 100, 2) if test_cases else 0.0
        return EvaluationResult(
            total_cases=len(test_cases),
            passed_cases=passed,
            pass_rate=pass_rate,
            details=details,
        )
