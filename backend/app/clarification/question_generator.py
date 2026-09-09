from typing import Optional
from app.clarification.models import (
    ClarificationDecision,
    ClarificationQuestion,
    QueryAnalysis,
)
from app.schema_retrieval.context import RAGContext


class ClarificationQuestionGenerator:
    def generate(
        self,
        decision: ClarificationDecision,
        analysis: QueryAnalysis,
        rag_context: Optional[RAGContext] = None,
    ) -> ClarificationQuestion:
        query_lower = analysis.query.lower()
        missing = decision.missing_information
        ambiguities = decision.ambiguities

        # 1. Ranking metric missing or vague ranking (e.g. "best customers", "top customers", "worst products")
        if "ranking_metric" in missing or any(t in ambiguities for t in ["best", "worst", "top", "bottom"]):
            entity_name = "customers"
            if analysis.entities:
                entity_name = analysis.entities[0]
            elif "product" in query_lower:
                entity_name = "products"

            if entity_name == "customers":
                return ClarificationQuestion(
                    question=f"How would you like to define the {self._get_ranking_term(query_lower)} customers?",
                    reason="Customer ranking requires a specific metric to order by.",
                    options=[
                        "Total spending",
                        "Number of orders",
                        "Average order value",
                    ],
                    target_field="ranking_metric",
                    confidence=0.95,
                )
            elif entity_name == "products":
                return ClarificationQuestion(
                    question=f"How would you like to define the {self._get_ranking_term(query_lower)} products?",
                    reason="Product ranking requires a specific metric to order by.",
                    options=[
                        "Total revenue generated",
                        "Units sold",
                        "Average customer rating",
                    ],
                    target_field="ranking_metric",
                    confidence=0.95,
                )
            else:
                return ClarificationQuestion(
                    question=f"Which metric should be used for ranking {entity_name}?",
                    reason="Ranking requires a specified ordering metric.",
                    options=[
                        "Total revenue",
                        "Transaction count",
                        "Average value",
                    ],
                    target_field="ranking_metric",
                    confidence=0.9,
                )

        # 2. Performance metric missing (e.g. "product performance")
        if "performance_metric" in missing or "performance" in ambiguities:
            return ClarificationQuestion(
                question="How would you like to measure performance?",
                reason="Performance is a multi-faceted concept that requires choosing a metric.",
                options=[
                    "Total revenue",
                    "Units sold",
                    "Average rating",
                ],
                target_field="performance_metric",
                confidence=0.9,
            )

        # 3. Missing timeframe (e.g. "Show revenue", "revenue growth")
        if "timeframe" in missing or "missing_timeframe" in ambiguities:
            return ClarificationQuestion(
                question="What timeframe should I use for the calculation?",
                reason="A timeframe is needed to focus the analysis period.",
                options=[
                    "All time",
                    "Year 2025",
                    "Last 30 days",
                    "Last 12 months",
                ],
                target_field="timeframe",
                confidence=0.95,
            )

        # 4. Ambiguous sales term / metric definition
        if "metric_definition" in missing or "sales" in ambiguities:
            return ClarificationQuestion(
                question="How would you like to measure sales?",
                reason="The term 'sales' can refer to revenue, number of orders, or unit volume.",
                options=[
                    "Total revenue",
                    "Number of orders",
                    "Units sold",
                ],
                target_field="metric",
                confidence=0.9,
            )

        # 5. Missing comparison dimension
        if "comparison_dimension" in missing:
            return ClarificationQuestion(
                question="How would you like to group the comparison?",
                reason="Comparison requires a breakdown dimension.",
                options=[
                    "By product category",
                    "By year / month",
                    "By customer segment",
                ],
                target_field="grouping",
                confidence=0.9,
            )

        # 6. Vague query (e.g. "Show me something about customers", "Tell me something")
        if "operation_or_metric" in missing or "something" in query_lower:
            if "customers" in analysis.entities or "customer" in query_lower:
                return ClarificationQuestion(
                    question="What customer insights would you like to see?",
                    reason="Please select the specific customer metric or breakdown you want.",
                    options=[
                        "Total customer count",
                        "Top customers by spending",
                        "Customer signups by year",
                    ],
                    target_field="operation",
                    confidence=0.85,
                )
            return ClarificationQuestion(
                question="What specific analytical information are you looking for?",
                reason="Please clarify the topic or metric you would like to explore.",
                options=[
                    "Total revenue breakdown",
                    "Order volume summary",
                    "Top selling products",
                ],
                target_field="operation",
                confidence=0.8,
            )

        # Fallback question
        return ClarificationQuestion(
            question="Could you please provide more details on what you would like to analyze?",
            reason="Additional details are needed to generate an accurate query.",
            options=[
                "Show summary statistics",
                "Break down by category",
                "Filter by recent year",
            ],
            target_field="general",
            confidence=0.7,
        )

    def _get_ranking_term(self, query_lower: str) -> str:
        for term in ["best", "worst", "top", "bottom", "highest", "lowest", "most valuable"]:
            if term in query_lower:
                return term
        return "top"
