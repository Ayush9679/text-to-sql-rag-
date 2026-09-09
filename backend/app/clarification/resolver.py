import re
from typing import Any, Optional
from app.clarification.ambiguity import AmbiguityDetector
from app.clarification.analyzer import QueryAnalyzer
from app.clarification.decision import ClarificationDecisionEngine
from app.clarification.intent_validator import IntentValidator
from app.clarification.missing_information import MissingInformationDetector
from app.clarification.models import (
    ClarificationDecision,
    ClarificationQuestion,
    ClarificationState,
    QueryAnalysis,
)
from app.clarification.question_generator import ClarificationQuestionGenerator
from app.clarification.state import ClarificationStateManager
from app.schema_retrieval.context import RAGContext


class ClarificationResolver:
    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.validator = IntentValidator()
        self.ambiguity_detector = AmbiguityDetector()
        self.missing_detector = MissingInformationDetector()
        self.decision_engine = ClarificationDecisionEngine()
        self.question_generator = ClarificationQuestionGenerator()
        self.state_manager = ClarificationStateManager()

    def resolve(
        self,
        state: ClarificationState,
        user_answer: str,
        target_field: Optional[str] = None,
        rag_context: Optional[RAGContext] = None,
    ) -> tuple[ClarificationState, ClarificationDecision]:
        answer_clean = user_answer.strip()
        answer_lower = answer_clean.lower()

        # Identify which question/target_field is being answered
        target_question: Optional[ClarificationQuestion] = None
        if target_field:
            for q in state.pending_clarifications:
                if q.target_field == target_field:
                    target_question = q
                    break
        elif state.pending_clarifications:
            target_question = state.pending_clarifications[0]
            target_field = target_question.target_field
        else:
            target_field = "general"

        if not target_question:
            target_question = ClarificationQuestion(
                question="Clarification provided",
                reason="User provided answer",
                options=[],
                target_field=target_field or "general",
                confidence=1.0,
            )

        # Get existing analysis or recreate from original query
        analysis = state.analysis or self.analyzer.analyze(state.original_query)
        entities = list(analysis.entities)
        metrics = list(analysis.metrics)
        filters = list(analysis.filters)
        grouping = list(analysis.grouping)
        aggregation = analysis.aggregation
        sort_direction = analysis.sort_direction
        limit = analysis.limit

        resolved_value: Any = answer_clean

        # 1. Resolve ranking metric
        if target_field in {"ranking_metric", "ranking"}:
            if any(term in answer_lower for term in ["spending", "spend", "total spending"]):
                if "spending" not in metrics:
                    metrics.append("spending")
                resolved_value = "total_spending"
            elif any(term in answer_lower for term in ["order", "orders", "order count"]):
                if "order count" not in metrics:
                    metrics.append("order count")
                resolved_value = "order_count"
            elif any(term in answer_lower for term in ["revenue", "sales"]):
                if "revenue" not in metrics:
                    metrics.append("revenue")
                resolved_value = "revenue"
            elif "rating" in answer_lower:
                if "rating" not in metrics:
                    metrics.append("rating")
                resolved_value = "rating"
            elif "units" in answer_lower or "quantity" in answer_lower:
                if "quantity" not in metrics:
                    metrics.append("quantity")
                resolved_value = "quantity"
            else:
                metrics.append(answer_clean.lower())
                resolved_value = answer_clean.lower()

            if aggregation is None or aggregation == "count":
                aggregation = "ranking"
            if sort_direction is None:
                sort_direction = "descending"

        # 2. Resolve timeframe
        elif target_field == "timeframe":
            year_match = re.search(r"\b(19\d\d|20\d\d)\b", answer_clean)
            if year_match:
                year = year_match.group(1)
                if year not in filters:
                    filters.append(year)
                resolved_value = f"year={year}"
            elif "30 days" in answer_lower:
                filters.append("last_30_days")
                resolved_value = "last_30_days"
            elif "12 months" in answer_lower or "year" in answer_lower:
                filters.append("last_12_months")
                resolved_value = "last_12_months"
            elif "all time" in answer_lower or "all" in answer_lower:
                filters.append("all_time")
                resolved_value = "all_time"
            else:
                filters.append(answer_clean)
                resolved_value = answer_clean

        # 3. Resolve metric / performance_metric
        elif target_field in {"metric", "performance_metric", "metric_definition"}:
            if "revenue" in answer_lower:
                if "revenue" not in metrics:
                    metrics.append("revenue")
                resolved_value = "revenue"
            elif "order" in answer_lower:
                if "order count" not in metrics:
                    metrics.append("order count")
                resolved_value = "order_count"
            elif "unit" in answer_lower or "quantity" in answer_lower:
                if "quantity" not in metrics:
                    metrics.append("quantity")
                resolved_value = "quantity"
            elif "rating" in answer_lower:
                if "rating" not in metrics:
                    metrics.append("rating")
                resolved_value = "rating"
            else:
                metrics.append(answer_clean.lower())
                resolved_value = answer_clean.lower()

        # 4. Resolve grouping / comparison_dimension
        elif target_field in {"grouping", "comparison_dimension"}:
            if "category" in answer_lower:
                if "category" not in grouping:
                    grouping.append("category")
                resolved_value = "category"
            elif "month" in answer_lower:
                if "month" not in grouping:
                    grouping.append("month")
                resolved_value = "month"
            elif "year" in answer_lower:
                if "year" not in grouping:
                    grouping.append("year")
                resolved_value = "year"
            elif "segment" in answer_lower:
                if "customer_segment" not in grouping:
                    grouping.append("customer_segment")
                resolved_value = "customer_segment"

        # 5. Resolve operation / vague query
        elif target_field in {"operation", "operation_or_metric"}:
            if "count" in answer_lower or "total customer count" in answer_lower:
                if "count" not in metrics:
                    metrics.append("count")
                aggregation = "count"
                resolved_value = "count"
            elif "spending" in answer_lower or "top customers" in answer_lower or "best" in answer_lower:
                if "spending" not in metrics:
                    metrics.append("spending")
                aggregation = "ranking"
                sort_direction = "descending"
                resolved_value = "top_spending"
            elif "signup" in answer_lower:
                if "count" not in metrics:
                    metrics.append("count")
                if "year" not in grouping:
                    grouping.append("year")
                resolved_value = "signups_by_year"
            elif "revenue" in answer_lower:
                if "revenue" not in metrics:
                    metrics.append("revenue")
                aggregation = "sum"
                resolved_value = "revenue"

        # Update current query string representation
        updated_query = f"{state.original_query} [{target_field}: {answer_clean}]"

        # Re-derive intent if needed
        intent = analysis.intent
        if not intent:
            if "customers" in entities:
                intent = "customer_analysis"
            elif "products" in entities:
                intent = "product_analysis"
            elif "orders" in entities:
                intent = "order_analysis"
            elif "categories" in entities:
                intent = "category_analysis"
            elif "revenue" in metrics:
                intent = "revenue_analysis"

        # Re-evaluate ambiguities and missing information
        updated_analysis = QueryAnalysis(
            query=updated_query,
            intent=intent,
            entities=entities,
            metrics=metrics,
            filters=filters,
            grouping=grouping,
            aggregation=aggregation,
            sort_direction=sort_direction,
            limit=limit,
            ambiguities=[],
            missing_information=[],
            confidence=0.9,
        )

        # Check remaining ambiguities and missing information
        ambiguity_res = self.ambiguity_detector.detect(updated_analysis)
        missing_res = self.missing_detector.detect(updated_analysis)

        # Filter out resolved items from missing/ambiguity results
        all_resolved = set(state.resolved_fields.keys()) | {target_field}
        if "operation" in all_resolved:
            all_resolved.add("operation_or_metric")
        if "operation_or_metric" in all_resolved:
            all_resolved.add("operation")
        if "ranking_metric" in all_resolved:
            all_resolved.add("ranking")

        filtered_missing_req = [
            m for m in missing_res.required
            if m not in all_resolved
        ]

        # If ranking metric was resolved, remove vague ranking ambiguities
        if "ranking_metric" in all_resolved or "ranking" in all_resolved:
            ambiguity_res.ambiguity_types = [
                a for a in ambiguity_res.ambiguity_types if a != "vague_ranking"
            ]
            ambiguity_res.is_ambiguous = len(ambiguity_res.ambiguity_types) > 0

        # Update analysis with remaining items
        updated_analysis.missing_information = filtered_missing_req
        updated_analysis.ambiguities = ambiguity_res.ambiguity_types

        # Intent validation
        intent_val = self.validator.validate(updated_analysis)

        # Decision
        decision = self.decision_engine.decide(
            analysis=updated_analysis,
            intent_validation=intent_val,
            ambiguity=ambiguity_res,
            missing_info=missing_res,
            rag_context=rag_context,
        )

        # Update State
        state.current_query = updated_query
        state.analysis = updated_analysis
        self.state_manager.resolve_question(
            state=state,
            question=target_question,
            user_answer=user_answer,
            resolved_field=target_field,
            resolved_value=resolved_value,
        )

        if decision.action == "proceed":
            state.status = "resolved"
            state.pending_clarifications.clear()
        elif decision.action == "clarify":
            state.status = "awaiting_clarification"
            next_question = self.question_generator.generate(
                decision=decision,
                analysis=updated_analysis,
                rag_context=rag_context,
            )
            state.pending_clarifications = [next_question]

        return state, decision
