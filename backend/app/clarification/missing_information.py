import re
from app.clarification.models import MissingInformationResult, QueryAnalysis


class MissingInformationDetector:
    def detect(self, query_or_analysis: str | QueryAnalysis) -> MissingInformationResult:
        if isinstance(query_or_analysis, QueryAnalysis):
            query = query_or_analysis.query
            analysis = query_or_analysis
        else:
            query = query_or_analysis
            from app.clarification.analyzer import QueryAnalyzer
            analysis = QueryAnalyzer().analyze(query)

        query_lower = query.lower()
        tokens = set(re.findall(r"[a-zA-Z0-9_]+", query_lower))

        required: list[str] = []
        optional: list[str] = []
        reasons: dict[str, str] = {}

        # 1. Ranking without explicit metric (e.g. "best customers", "top customers", "worst products")
        is_ranking = bool(tokens & {"top", "bottom", "highest", "lowest", "best", "worst", "most", "least"}) or analysis.aggregation == "ranking"
        has_ranking_metric = any(m in ["spending", "revenue", "order count", "count", "quantity", "price", "order_value", "rating"] for m in analysis.metrics)
        if "by total spending" in query_lower or "by spending" in query_lower or "by revenue" in query_lower or "by order count" in query_lower or "by order value" in query_lower or "based on order value" in query_lower:
            has_ranking_metric = True

        if is_ranking and not has_ranking_metric:
            required.append("ranking_metric")
            reasons["ranking_metric"] = "Ranking queries require an explicit metric to sort by (e.g., total spending, order count, revenue)."

        # 2. Performance queries (e.g. "Show product performance")
        if "performance" in tokens and not has_ranking_metric and not analysis.metrics:
            required.append("performance_metric")
            reasons["performance_metric"] = "Performance analysis requires a defined metric such as revenue, sales volume, or review rating."

        # 3. Vague query (e.g. "Show me something about customers", "Show me something")
        # Only missing if no metrics, no ranking, no explicit aggregate
        if not analysis.metrics and not is_ranking and not analysis.aggregation:
            if "something" in tokens or "tell" in tokens or (len(analysis.entities) > 0 and not tokens & {"all", "list"}):
                required.append("operation_or_metric")
                reasons["operation_or_metric"] = "The query lacks a specific analytical metric or operation to perform."

        # 4. Comparison queries (e.g. "Compare sales")
        if "compare" in tokens:
            if not analysis.grouping and not any(dim in query_lower for dim in ["by category", "by product", "by customer", "by year", "by month"]):
                required.append("comparison_dimension")
                reasons["comparison_dimension"] = "Comparison queries require dimensions to compare across (e.g. by category, by region, by year)."
            if not has_ranking_metric and "sales" in tokens:
                required.append("metric_definition")
                reasons["metric_definition"] = "Comparing sales requires defining whether sales means revenue, order count, or units sold."
            if not analysis.filters:
                optional.append("timeframe")
                reasons["timeframe"] = "A timeframe helps restrict the comparison period."

        # 5. Bare metric queries without timeframe or dimension (e.g. "Show revenue", "Show total revenue")
        if "revenue" in analysis.metrics and not analysis.filters and not analysis.grouping and not analysis.entities:
            required.append("timeframe")
            reasons["timeframe"] = "Calculating total revenue requires a specific timeframe (e.g. 2025, last 30 days, all-time)."
        elif "revenue" in analysis.metrics and not analysis.filters and len(analysis.entities) == 0:
            optional.append("timeframe")
            reasons["timeframe"] = "Specifying a timeframe helps filter the revenue data."

        # Check for growth/trend missing timeframe
        if tokens & {"growth", "trend", "trends"} and not analysis.filters and "timeframe" not in required:
            required.append("timeframe")
            reasons["timeframe"] = "Growth and trend analysis require a specific timeframe or baseline."

        missing = list(dict.fromkeys(required + optional))
        confidence = 0.9 if missing else 1.0

        return MissingInformationResult(
            missing=missing,
            required=required,
            optional=optional,
            reasons=reasons,
            confidence=confidence,
        )
