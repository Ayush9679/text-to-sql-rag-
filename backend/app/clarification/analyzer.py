import re
from app.clarification.models import QueryAnalysis


class QueryAnalyzer:
    ENTITY_TERMS = {
        "customers": {"customer", "customers", "client", "clients"},
        "products": {"product", "products", "item", "items"},
        "orders": {"order", "orders", "purchase", "purchases", "transaction", "transactions"},
        "categories": {"category", "categories", "product category", "product categories"},
        "suppliers": {"supplier", "suppliers", "vendor", "vendors"},
        "payments": {"payment", "payments"},
        "reviews": {"review", "reviews", "rating", "ratings"},
    }

    METRIC_TERMS = {
        "revenue": {"revenue", "income", "earnings"},
        "spending": {"spending", "spend", "total spending"},
        "sales": {"sales"},
        "order count": {"order count", "orders count", "number of orders"},
        "quantity": {"quantity", "units", "units sold"},
        "price": {"price", "unit price", "cost"},
        "order_value": {"order value", "order amount", "order total"},
        "average": {"average", "avg", "mean"},
        "total": {"total", "sum"},
        "count": {"count", "number of", "how many", "number"},
    }

    RANKING_DESC = {"top", "highest", "best", "most", "largest", "greatest"}
    RANKING_ASC = {"bottom", "lowest", "worst", "least", "smallest"}
    RANKING_ALL = RANKING_DESC | RANKING_ASC

    AMBIGUOUS_TERMS = {
        "best",
        "worst",
        "good",
        "bad",
        "popular",
        "successful",
        "valuable",
        "better",
        "performance",
    }

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

    def tokenize(self, query: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_]+", query.lower())

    def __init__(self):
        # Per-service schema terms make Phase 4 work with uploaded tables while
        # preserving the existing demo vocabulary as a baseline.
        self.schema_entity_terms: dict[str, set[str]] = {}
        self.schema_metric_terms: dict[str, set[str]] = {}

    def configure_schema(self, tables) -> None:
        self.schema_entity_terms = {}
        self.schema_metric_terms = {}
        for table in tables:
            table_name = table.name.lower()
            terms = {table_name, table_name.replace("_", " ")}
            if table_name.endswith("s"):
                terms.add(table_name[:-1])
            self.schema_entity_terms[table_name] = terms
            for column in table.columns:
                column_name = column.name.lower()
                self.schema_metric_terms[column_name] = {
                    column_name,
                    column_name.replace("_", " "),
                }

    def analyze(self, query: str) -> QueryAnalysis:
        query_clean = query.strip()
        query_lower = query_clean.lower()
        tokens = self.tokenize(query)
        token_set = set(tokens)

        entities: list[str] = []
        metrics: list[str] = []
        filters: list[str] = []
        grouping: list[str] = []
        ambiguities: list[str] = []
        missing_information: list[str] = []

        # -------------------------
        # Entity detection
        # -------------------------
        for entity_name, terms in self.ENTITY_TERMS.items():
            for term in terms:
                if " " in term:
                    if term in query_lower:
                        if entity_name not in entities:
                            entities.append(entity_name)
                        break
                elif term in token_set:
                    if entity_name not in entities:
                        entities.append(entity_name)
                    break

        for entity_name, terms in self.schema_entity_terms.items():
            if entity_name in entities:
                continue
            if any(term in query_lower if " " in term else term in token_set for term in terms):
                entities.append(entity_name)

        # -------------------------
        # Metric detection
        # -------------------------
        if "total spending" in query_lower:
            metrics.append("spending")
            if "total" not in metrics:
                metrics.append("total")
        elif "spending" in token_set or "spend" in token_set:
            metrics.append("spending")

        if "number of orders" in query_lower or "order count" in query_lower or "orders count" in query_lower:
            metrics.append("order count")
            if "orders" not in entities:
                entities.append("orders")

        if any(term in query_lower for term in ["how many", "number of"]) or "count" in token_set:
            if "count" not in metrics:
                metrics.append("count")

        for metric_name, terms in self.METRIC_TERMS.items():
            if metric_name in ["spending", "order count", "count"]:
                continue
            for term in terms:
                if " " in term:
                    if term in query_lower and metric_name not in metrics:
                        metrics.append(metric_name)
                        break
                elif term in token_set and metric_name not in metrics:
                    metrics.append(metric_name)
                    break

        for metric_name, terms in self.schema_metric_terms.items():
            if metric_name not in metrics and any(term in query_lower if " " in term else term in token_set for term in terms):
                metrics.append(metric_name)

        # -------------------------
        # Grouping detection
        # -------------------------
        if "monthly" in token_set or "by month" in query_lower:
            grouping.append("month")
        if "yearly" in token_set or "by year" in query_lower or "annually" in token_set:
            grouping.append("year")
        if "by category" in query_lower or "by product category" in query_lower:
            grouping.append("category")
            if "categories" not in entities:
                entities.append("categories")
        if "by product" in query_lower:
            grouping.append("product")
            if "products" not in entities:
                entities.append("products")
        if "by customer" in query_lower:
            grouping.append("customer")
            if "customers" not in entities:
                entities.append("customers")
        if "by supplier" in query_lower:
            grouping.append("supplier")
            if "suppliers" not in entities:
                entities.append("suppliers")

        # -------------------------
        # Filter detection
        # -------------------------
        # Year patterns: e.g. "in 2025", "for 2025", "2025"
        year_matches = re.findall(r"\b(19\d\d|20\d\d)\b", query)
        for year in year_matches:
            filters.append(year)

        # Status patterns
        for status in ["completed", "pending", "cancelled", "shipped", "delivered"]:
            if status in token_set:
                filters.append(f"status={status}")

        # -------------------------
        # Ranking & Aggregation detection
        # -------------------------
        is_ranking = bool(token_set & self.RANKING_ALL)
        sort_direction = None
        limit = None
        aggregation = None

        if is_ranking:
            aggregation = "ranking"
            if token_set & self.RANKING_DESC:
                sort_direction = "descending"
            elif token_set & self.RANKING_ASC:
                sort_direction = "ascending"

            # Check limit after top/bottom
            for index, token in enumerate(tokens):
                if token in self.RANKING_ALL:
                    if index + 1 < len(tokens):
                        next_token = tokens[index + 1]
                        if next_token.isdigit():
                            limit = int(next_token)
                    if index > 0 and tokens[index - 1].isdigit():
                        limit = int(tokens[index - 1])
            # Natural requests often place the quantity before the entity,
            # e.g. "10 customers with the smallest order value".
            if limit is None:
                leading_quantity = re.match(r"\s*(\d+)\b", query_clean)
                if leading_quantity:
                    limit = int(leading_quantity.group(1))
        elif "count" in metrics or "how many" in query_lower or "number of" in query_lower:
            aggregation = "count"
        elif "average" in metrics or token_set & {"average", "avg", "mean"}:
            aggregation = "average"
        elif "total" in metrics or "revenue" in metrics or "spending" in metrics or token_set & {"total", "sum"}:
            aggregation = "sum"
        elif "min" in token_set or "minimum" in token_set:
            aggregation = "min"
        elif "max" in token_set or "maximum" in token_set:
            aggregation = "max"

        if limit is None:
            # Check for "limit N" or "first N"
            for index, token in enumerate(tokens):
                if token in {"limit", "first"}:
                    if index + 1 < len(tokens) and tokens[index + 1].isdigit():
                        limit = int(tokens[index + 1])

        # -------------------------
        # Ambiguity detection
        # -------------------------
        for term in self.AMBIGUOUS_TERMS:
            if term in token_set or term in query_lower:
                ambiguities.append(f"'{term}' is ambiguous")

        if "sales" in token_set and "revenue" not in token_set and "spending" not in token_set:
            # "sales" can mean revenue, order count, or units sold
            if "total sales" not in query_lower and "revenue" not in metrics:
                ambiguities.append("'sales' can mean revenue, order count, or units sold")

        # -------------------------
        # Missing information
        # -------------------------
        explicit_metrics = [m for m in metrics if m not in {"count"}]
        if is_ranking and not explicit_metrics and "count" not in metrics:
            missing_information.append("ranking metric")

        # -------------------------
        # Intent mapping
        # -------------------------
        intent = None
        if token_set & self.UNSUPPORTED_DOMAINS:
            intent = None
        elif "customers" in entities:
            intent = "customer_analysis"
        elif "products" in entities:
            intent = "product_analysis"
        elif "orders" in entities:
            intent = "order_analysis"
        elif "categories" in entities:
            intent = "category_analysis"
        elif "suppliers" in entities:
            intent = "supplier_analysis"
        elif "payments" in entities:
            intent = "payment_analysis"
        elif "reviews" in entities:
            intent = "review_analysis"
        elif "revenue" in metrics or "spending" in metrics or "sales" in metrics:
            intent = "revenue_analysis"
        elif entities:
            intent = f"{entities[0][:-1] if entities[0].endswith('s') else entities[0]}_analysis"

        # -------------------------
        # Confidence calculation
        # -------------------------
        confidence = self._calculate_confidence(
            query=query,
            intent=intent,
            entities=entities,
            metrics=metrics,
            ambiguities=ambiguities,
            missing_information=missing_information,
            token_set=token_set,
        )

        return QueryAnalysis(
            query=query,
            intent=intent,
            entities=entities,
            metrics=metrics,
            filters=filters,
            grouping=grouping,
            aggregation=aggregation,
            sort_direction=sort_direction,
            limit=limit,
            ambiguities=ambiguities,
            missing_information=missing_information,
            confidence=confidence,
        )

    def _calculate_confidence(
        self,
        query: str,
        intent: str | None,
        entities: list[str],
        metrics: list[str],
        ambiguities: list[str],
        missing_information: list[str],
        token_set: set[str],
    ) -> float:
        if token_set & self.UNSUPPORTED_DOMAINS or not intent:
            return 0.0

        score = 0.5
        if entities:
            score += 0.2
        if metrics:
            score += 0.2
        if ambiguities:
            score -= 0.2
        if missing_information:
            score -= 0.2

        return max(0.0, min(1.0, round(score, 2)))
