"""Business Metric Engine: formal metric definitions and automatic metric discovery."""

from typing import Any
from pydantic import BaseModel, Field
from app.dataset.profiler import TableProfile


class MetricDefinition(BaseModel):
    name: str
    target_table: str
    formula: str
    sql_expression: str
    unit: str = "currency"  # currency, count, percentage, ratio
    description: str = ""
    synonyms: list[str] = Field(default_factory=list)


class MetricEngine:
    """Manages curated and automatically inferred business metrics."""

    def __init__(self, custom_metrics: list[MetricDefinition] | None = None):
        self.metrics: list[MetricDefinition] = custom_metrics or []

    def register_metric(self, metric: MetricDefinition) -> None:
        # Avoid duplicate metric names for the same table
        self.metrics = [m for m in self.metrics if not (m.name.lower() == metric.name.lower() and m.target_table == metric.target_table)]
        self.metrics.append(metric)

    def infer_metrics_for_tables(self, table_profiles: list[TableProfile]) -> list[MetricDefinition]:
        """Automatically discovers high-confidence business metrics based on table columns."""
        inferred: list[MetricDefinition] = []

        for table in table_profiles:
            cols = {c.normalized_name: c for c in table.columns}
            tname = table.table_name

            # 1. Revenue: quantity * unit_price or price * units or existing amount
            qty_col = next((c for c in cols if c in {"quantity", "qty", "units_sold", "units", "item_count"}), None)
            price_col = next((c for c in cols if c in {"unit_price", "price", "rate", "cost_per_unit"}), None)
            amt_col = next((c for c in cols if c in {"amount", "amt", "total_amount", "revenue", "sales_amount", "subtotal", "total"}), None)

            if qty_col and price_col:
                inferred.append(
                    MetricDefinition(
                        name="revenue",
                        target_table=tname,
                        formula=f"{qty_col} * {price_col}",
                        sql_expression=f"SUM({qty_col} * {price_col})",
                        unit="currency",
                        description=f"Total monetary revenue calculated as {qty_col} multiplied by {price_col}",
                        synonyms=["sales", "sales revenue", "gross revenue", "total sales", "turnover", "income"],
                    )
                )
            elif amt_col:
                inferred.append(
                    MetricDefinition(
                        name="revenue",
                        target_table=tname,
                        formula=amt_col,
                        sql_expression=f"SUM({amt_col})",
                        unit="currency",
                        description=f"Total monetary revenue summed from {amt_col}",
                        synonyms=["sales", "sales revenue", "gross revenue", "total sales", "turnover", "amount", "total amount"],
                    )
                )

            # 2. Profit / Margin: revenue - cost
            cost_col = next((c for c in cols if c in {"cost", "unit_cost", "total_cost", "expenses"}), None)
            if cost_col and (qty_col and price_col):
                inferred.append(
                    MetricDefinition(
                        name="profit",
                        target_table=tname,
                        formula=f"({qty_col} * {price_col}) - ({qty_col} * {cost_col})",
                        sql_expression=f"SUM(({qty_col} * {price_col}) - ({qty_col} * {cost_col}))",
                        unit="currency",
                        description="Net profit before taxes calculated as revenue minus cost",
                        synonyms=["net profit", "gross profit", "earnings", "net earnings"],
                    )
                )

            # 3. Average Order Value / Average Transaction: AVG(amount)
            if amt_col:
                inferred.append(
                    MetricDefinition(
                        name="average_order_value",
                        target_table=tname,
                        formula=f"AVG({amt_col})",
                        sql_expression=f"AVG({amt_col})",
                        unit="currency",
                        description=f"Average monetary value per transaction on {amt_col}",
                        synonyms=["aov", "average order size", "avg ticket", "average ticket size"],
                    )
                )

            # 4. Total Volume / Items: SUM(quantity)
            if qty_col:
                inferred.append(
                    MetricDefinition(
                        name="total_units_sold",
                        target_table=tname,
                        formula=f"SUM({qty_col})",
                        sql_expression=f"SUM({qty_col})",
                        unit="count",
                        description=f"Total number of physical units sold summed from {qty_col}",
                        synonyms=["units sold", "volume", "total volume", "item count", "quantity sold"],
                    )
                )

        # Merge inferred into registered metrics
        for m in inferred:
            self.register_metric(m)

        return self.metrics

    def get_metrics_for_table(self, table_name: str) -> list[MetricDefinition]:
        return [m for m in self.metrics if m.target_table == table_name]

    def format_metrics_for_prompt(self) -> str:
        if not self.metrics:
            return "No custom business metrics defined."
        lines = []
        for m in self.metrics:
            syns = f" (Synonyms: {', '.join(m.synonyms)})" if m.synonyms else ""
            lines.append(f"- **{m.name.upper()}** [{m.target_table}]: `{m.sql_expression}` — {m.description}{syns}")
        return "\n".join(lines)
