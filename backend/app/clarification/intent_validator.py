from app.clarification.models import (
    IntentValidationResult,
    QueryAnalysis,
)


class IntentValidator:
    SUPPORTED_INTENTS = {
        "customer_analysis",
        "product_analysis",
        "order_analysis",
        "category_analysis",
        "revenue_analysis",
        "supplier_analysis",
        "payment_analysis",
        "review_analysis",
    }

    def validate(self, analysis: QueryAnalysis) -> IntentValidationResult:
        intent = analysis.intent
        ambiguities = list(analysis.ambiguities)
        missing_information = list(analysis.missing_information)

        # 1. If intent is missing or unsupported
        if not intent:
            return IntentValidationResult(
                valid=False,
                intent=None,
                ambiguities=ambiguities,
                missing_information=missing_information,
                confidence=0.0,
                reason="No recognizable analytical intent or entity detected.",
            )

        if intent not in self.SUPPORTED_INTENTS and not (intent.endswith("_analysis") and analysis.entities):
            return IntentValidationResult(
                valid=False,
                intent=intent,
                ambiguities=ambiguities,
                missing_information=missing_information,
                confidence=0.0,
                reason=f"Intent '{intent}' is not supported.",
            )

        # 2. Check if intent is incomplete / ambiguous
        if ambiguities or missing_information:
            return IntentValidationResult(
                valid=False,
                intent=intent,
                ambiguities=ambiguities,
                missing_information=missing_information,
                confidence=round(max(0.0, min(1.0, analysis.confidence)), 2),
                reason="Intent recognized but contains ambiguities or missing required information.",
            )

        # 3. Check if query has at least an entity or a metric or valid aggregate
        if not analysis.entities and not analysis.metrics:
            return IntentValidationResult(
                valid=False,
                intent=intent,
                ambiguities=ambiguities,
                missing_information=missing_information or ["analytical target"],
                confidence=0.2,
                reason="Intent is incomplete without specified entities or metrics.",
            )

        # 4. Valid intent
        return IntentValidationResult(
            valid=True,
            intent=intent,
            ambiguities=[],
            missing_information=[],
            confidence=round(max(0.0, min(1.0, max(analysis.confidence, 0.7))), 2),
            reason="Intent is valid and sufficiently specified.",
        )
