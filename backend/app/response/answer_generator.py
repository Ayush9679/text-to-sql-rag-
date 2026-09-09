"""Natural-language business answer generator and visualization selector."""

from typing import Any
from pydantic import BaseModel, Field


class AnswerPayload(BaseModel):
    summary: str
    recommended_chart: str = "table"  # metric_card, bar_chart, line_chart, pie_chart, table
    formatted_data: list[dict[str, Any]] = Field(default_factory=list)
    key_highlights: list[str] = Field(default_factory=list)


class AnswerGenerator:
    """Produces user-friendly natural-language explanations and chart recommendations."""

    def generate_answer(
        self,
        query: str,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
        intent: str = "aggregation",
    ) -> AnswerPayload:
        row_count = len(rows)

        if row_count == 0:
            return AnswerPayload(
                summary="No records were found matching your criteria in the dataset.",
                recommended_chart="table",
                formatted_data=[],
                key_highlights=["0 rows returned"],
            )

        # Convert rows into dictionary list
        formatted_data = [
            {col: row[idx] for idx, col in enumerate(columns)}
            for row in rows
        ]

        # 1. Single scalar result (e.g. SELECT COUNT(*), SELECT SUM(amount))
        if row_count == 1 and len(columns) == 1:
            val = rows[0][0]
            col_name = columns[0].replace("_", " ").title()
            formatted_val = self._format_value(val)
            summary = f"The {col_name.lower()} is {formatted_val}."
            return AnswerPayload(
                summary=summary,
                recommended_chart="metric_card",
                formatted_data=formatted_data,
                key_highlights=[f"{col_name}: {formatted_val}"],
            )

        # 2. Single record with entity + metric (e.g. SELECT name, MAX(revenue) LIMIT 1)
        if row_count == 1 and len(columns) == 2:
            entity_name = str(rows[0][0])
            metric_val = self._format_value(rows[0][1])
            metric_col = columns[1].replace("_", " ").title()
            summary = f"{entity_name} recorded the highest {metric_col.lower()} of {metric_val}."
            return AnswerPayload(
                summary=summary,
                recommended_chart="metric_card",
                formatted_data=formatted_data,
                key_highlights=[f"Top {columns[0].replace('_', ' ').title()}: {entity_name}", f"{metric_col}: {metric_val}"],
            )

        # 3. Multi-row ranking or breakdown
        chart_type = self._detect_chart_type(columns, rows)
        first_entity = str(rows[0][0]) if len(columns) > 0 else ""
        first_metric = self._format_value(rows[0][1]) if len(columns) > 1 else ""

        if len(columns) >= 2 and first_metric:
            summary = f"Here are the results for your query. Top record is {first_entity} with {columns[1].replace('_', ' ')} of {first_metric}."
        else:
            summary = f"Retrieved {row_count} matching records."

        highlights = [f"Total rows: {row_count}"]
        if first_entity and first_metric:
            highlights.append(f"Leader: {first_entity} ({first_metric})")

        return AnswerPayload(
            summary=summary,
            recommended_chart=chart_type,
            formatted_data=formatted_data,
            key_highlights=highlights,
        )

    def _detect_chart_type(self, columns: list[str], rows: list[list[Any]]) -> str:
        row_count = len(rows)
        col_count = len(columns)

        if col_count == 2:
            col0_lower = columns[0].lower()
            if any(k in col0_lower for k in ("date", "month", "year", "time", "day", "period")):
                return "line_chart"
            if row_count <= 15:
                return "bar_chart"
            return "table"

        if col_count == 3 and any(k in columns[0].lower() for k in ("date", "month", "year", "time")):
            return "line_chart"

        return "table"

    @staticmethod
    def _format_value(val: Any) -> str:
        if val is None:
            return "N/A"
        if isinstance(val, (int, float)):
            if isinstance(val, float):
                return f"{val:,.2f}"
            return f"{val:,}"
        return str(val)
