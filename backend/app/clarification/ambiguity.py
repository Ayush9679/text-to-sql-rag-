import re
from app.clarification.models import AmbiguityResult, QueryAnalysis


class AmbiguityDetector:
    VAGUE_RANKING_TERMS = {"best", "worst", "top", "bottom", "highest", "lowest", "most", "least"}
    VAGUE_COMPARISON_TERMS = {"better", "worse", "popular", "trending", "compare"}
    UNDEFINED_METRIC_TERMS = {
        "valuable",
        "most valuable",
        "successful",
        "good",
        "bad",
        "performance",
        "high value",
        "high-value",
    }
    TIMEFRAME_DEPENDENT_TERMS = {"growth", "trend", "trends", "increase", "decrease", "rate"}
    AMBIGUOUS_TERMINOLOGY = {
        "sales": "Term 'sales' is ambiguous and can refer to total revenue, order count, or units sold.",
    }

    def detect(self, query_or_analysis: str | QueryAnalysis) -> AmbiguityResult:
        if isinstance(query_or_analysis, QueryAnalysis):
            query = query_or_analysis.query
            metrics = query_or_analysis.metrics
            filters = query_or_analysis.filters
            entities = query_or_analysis.entities
        else:
            query = query_or_analysis
            query_lower = query.lower()
            metrics = []
            if "spending" in query_lower:
                metrics.append("spending")
            if "revenue" in query_lower:
                metrics.append("revenue")
            if "count" in query_lower or "how many" in query_lower or "number of" in query_lower:
                metrics.append("count")
            filters = re.findall(r"\b(19\d\d|20\d\d)\b", query)
            entities = []
            for e in ["customers", "products", "orders", "categories", "suppliers", "payments", "reviews"]:
                if e[:-1] in query_lower:
                    entities.append(e)

        query_lower = query.lower()
        tokens = set(re.findall(r"[a-zA-Z0-9_]+", query_lower))

        ambiguity_types: list[str] = []
        ambiguous_terms: list[str] = []
        explanations: list[str] = []

        # 1. Vague ranking terms (e.g., "best customers", "worst products")
        for term in self.VAGUE_RANKING_TERMS:
            if term in tokens:
                # If it's a ranking word without an explicit metric (like total spending / revenue / count)
                # Note: "best" and "worst" are always inherently ambiguous subjective terms unless clarified
                if term in {"best", "worst"}:
                    ambiguity_types.append("vague_ranking")
                    ambiguous_terms.append(term)
                    explanations.append(
                        f"'{term}' is a subjective ranking term without a defined analytical metric."
                    )
                elif not metrics and not any(m in query_lower for m in ["spending", "revenue", "count", "price"]):
                    ambiguity_types.append("vague_ranking")
                    ambiguous_terms.append(term)
                    explanations.append(
                        f"Ranking term '{term}' is used without specifying a ranking metric."
                    )

        # 2. Vague comparison (e.g., "better products", "popular products")
        for term in self.VAGUE_COMPARISON_TERMS:
            if term in tokens or term in query_lower:
                ambiguity_types.append("vague_comparison")
                ambiguous_terms.append(term)
                explanations.append(
                    f"'{term}' is a vague comparative term without an explicit comparison criterion."
                )

        # 3. Undefined business metric (e.g., "valuable customers", "successful customers")
        for term in self.UNDEFINED_METRIC_TERMS:
            if (" " in term or "-" in term) and term in query_lower:
                ambiguity_types.append("undefined_business_metric")
                ambiguous_terms.append(term)
                explanations.append(
                    f"'{term}' is an undefined business concept that requires an explicit metric definition."
                )
            elif term in tokens:
                ambiguity_types.append("undefined_business_metric")
                ambiguous_terms.append(term)
                explanations.append(
                    f"'{term}' is an undefined business concept that requires an explicit metric definition."
                )

        # 4. Missing timeframe where timeframe is required (e.g., "revenue growth")
        for term in self.TIMEFRAME_DEPENDENT_TERMS:
            if term in tokens:
                if not filters and not any(
                    w in query_lower for w in ["month", "year", "2024", "2025", "daily", "quarter"]
                ):
                    ambiguity_types.append("missing_timeframe")
                    ambiguous_terms.append(term)
                    explanations.append(
                        f"'{term}' requires a defined timeframe or baseline period."
                    )

        # 5. Ambiguous terminology (e.g., "sales")
        for term, explanation in self.AMBIGUOUS_TERMINOLOGY.items():
            if term in tokens:
                # "sales" without explicit "total revenue", "revenue", "spending", or "order count"
                if "revenue" not in query_lower and "spending" not in query_lower and "order" not in query_lower:
                    ambiguity_types.append("ambiguous_terminology")
                    ambiguous_terms.append(term)
                    explanations.append(explanation)

        is_ambiguous = len(ambiguity_types) > 0
        confidence = 0.9 if is_ambiguous else 1.0

        return AmbiguityResult(
            is_ambiguous=is_ambiguous,
            ambiguity_types=list(dict.fromkeys(ambiguity_types)),
            ambiguous_terms=list(dict.fromkeys(ambiguous_terms)),
            explanation=explanations,
            confidence=confidence,
        )
