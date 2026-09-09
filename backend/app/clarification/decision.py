from typing import Optional
from app.clarification.models import (
    AmbiguityResult,
    ClarificationDecision,
    IntentValidationResult,
    MissingInformationResult,
    QueryAnalysis,
)
from app.schema_retrieval.context import RAGContext


class ClarificationDecisionEngine:
    UNSUPPORTED_DOMAINS = {
        "quantum",
        "physics",
        "weather",
        "astronomy",
        "chemistry",
        "biology",
        "medical",
        "gaming",
        "recipe",
        "cooking",
    }

    def decide(
        self,
        analysis: QueryAnalysis,
        intent_validation: IntentValidationResult,
        ambiguity: AmbiguityResult,
        missing_info: MissingInformationResult,
        rag_context: Optional[RAGContext] = None,
    ) -> ClarificationDecision:
        query_lower = analysis.query.lower()
        tokens = set(analysis.query.lower().split())

        # 1. Check for unsupported domain
        if any(term in query_lower for term in self.UNSUPPORTED_DOMAINS) or (
            not analysis.intent and not analysis.entities and not analysis.metrics and "something" not in tokens and "tell" not in tokens
        ):
            return ClarificationDecision(
                action="unsupported",
                reason="Query is outside the supported analytical domain.",
                confidence=0.0,
                missing_information=[],
                ambiguities=[],
            )

        # 2. Check for blocking ambiguities or required missing information
        has_ambiguity = ambiguity.is_ambiguous
        has_missing_req = len(missing_info.required) > 0

        if has_ambiguity or has_missing_req or not intent_validation.valid:
            # Combine missing info and ambiguities
            combined_missing = list(dict.fromkeys(missing_info.required + analysis.missing_information))
            combined_ambiguities = list(dict.fromkeys(ambiguity.ambiguous_terms + analysis.ambiguities))

            reasons: list[str] = []
            if combined_ambiguities:
                reasons.append(f"Ambiguities detected: {', '.join(combined_ambiguities)}")
            if combined_missing:
                reasons.append(f"Missing required information: {', '.join(combined_missing)}")
            if not reasons:
                reasons.append("Intent is incomplete or ambiguous.")

            return ClarificationDecision(
                action="clarify",
                reason="; ".join(reasons),
                confidence=round(max(0.0, min(1.0, analysis.confidence)), 2),
                missing_information=combined_missing,
                ambiguities=combined_ambiguities,
            )

        # 3. If intent is valid and no ambiguities or required missing information
        return ClarificationDecision(
            action="proceed",
            reason="Query is sufficiently specified and ready for SQL generation.",
            confidence=round(max(0.7, min(1.0, analysis.confidence)), 2),
            missing_information=[],
            ambiguities=[],
        )
