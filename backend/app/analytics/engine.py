"""Dynamic Analytics Engine: discovers metrics, trends, and breakdowns from live database schema."""

from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import create_engine, inspect, text, func
from sqlalchemy.engine import Engine

from app.schema_intelligence.metric_engine import MetricDefinition, MetricEngine
from app.dataset.profiler import DataProfiler, TableProfile


class TimeInterval(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class DiscoveredMetric:
    name: str
    label: str
    value: float | int
    formatted_value: str
    unit: str
    source_table: str
    source_column: str
    calculation: str
    comparison: dict[str, Any] | None = None


@dataclass
class TimeSeriesPoint:
    period: str
    value: float
    formatted_value: str


@dataclass
class BreakdownPoint:
    label: str
    value: float
    formatted_value: str
    percentage: float


@dataclass
class QueryVolumePoint:
    period: str
    value: int


class AnalyticsEngine:
    """Schema-aware analytics engine that dynamically generates insights from tenant data."""

    def __init__(self, engine: Engine, schema_name: str):
        self.engine = engine
        self.schema_name = schema_name
        self.inspector = inspect(engine)
        self.metric_engine = MetricEngine()
        self.profiler = DataProfiler()

    def _get_table_profiles(self) -> list[TableProfile]:
        """Get profiled table metadata by querying actual data."""
        table_names = self.inspector.get_table_names(schema=self.schema_name)
        profiles = []

        for table_name in table_names:
            columns = self.inspector.get_columns(table_name, schema=self.schema_name)
            with self.engine.begin() as conn:
                # Get sample rows for profiling
                result = conn.execute(
                    text(f'SELECT * FROM "{self.schema_name}"."{table_name}" LIMIT 1000')
                )
                rows = [list(row) for row in result.fetchall()]

            if rows:
                headers = [c["name"] for c in columns]
                norm_headers = headers  # already normalized during ingestion
                profile = self.profiler.profile_table(table_name, headers, norm_headers, rows)
                profiles.append(profile)

        return profiles

    def discover_metrics(self) -> list[DiscoveredMetric]:
        """Discover and compute all meaningful KPIs from the schema."""
        profiles = self._get_table_profiles()
        self.metric_engine.infer_metrics_for_tables(profiles)

        metrics = []
        for profile in profiles:
            table_metrics = self.metric_engine.get_metrics_for_table(profile.table_name)
            for metric_def in table_metrics:
                value = self._execute_metric(metric_def)
                if value is not None:
                    comparison = self._calculate_comparison(metric_def)
                    metrics.append(
                        DiscoveredMetric(
                            name=metric_def.name,
                            label=self._format_label(metric_def.name),
                            value=value,
                            formatted_value=self._format_value(value, metric_def.unit),
                            unit=metric_def.unit,
                            source_table=metric_def.target_table,
                            source_column=self._extract_source_column(metric_def),
                            calculation=metric_def.sql_expression,
                            comparison=comparison,
                        )
                    )

        # If no business metrics found, add generic row count metrics
        if not metrics:
            for profile in profiles:
                row_count = self._get_table_row_count(profile.table_name)
                if row_count > 0:
                    metrics.append(
                        DiscoveredMetric(
                            name=f"total_{profile.table_name}",
                            label=self._format_label(profile.table_name),
                            value=row_count,
                            formatted_value=f"{row_count:,}",
                            unit="count",
                            source_table=profile.table_name,
                            source_column="*",
                            calculation=f"COUNT(*) FROM {profile.table_name}",
                        )
                    )

        return metrics

    def _execute_metric(self, metric_def: MetricDefinition) -> float | int | None:
        """Execute a metric's SQL expression against the database."""
        try:
            sql = f"SELECT {metric_def.sql_expression} AS value FROM \"{self.schema_name}\".\"{metric_def.target_table}\""
            with self.engine.begin() as conn:
                result = conn.execute(text(sql))
                row = result.fetchone()
                if row and row[0] is not None:
                    return float(row[0])
        except Exception:
            pass
        return None

    def _calculate_comparison(self, metric_def: MetricDefinition) -> dict[str, Any] | None:
        """Calculate period-over-period comparison for a metric."""
        try:
            # Find a date column in the table
            date_col = self._find_date_column(metric_def.target_table)
            if not date_col:
                return None

            # Determine date range
            with self.engine.begin() as conn:
                max_date_result = conn.execute(
                    text(
                        f'SELECT MAX("{date_col}") FROM "{self.schema_name}"."{metric_def.target_table}"'
                    )
                )
                max_date_row = max_date_result.fetchone()
                if not max_date_row or not max_date_row[0]:
                    return None

                max_date = max_date_row[0]
                if isinstance(max_date, str):
                    max_date = datetime.fromisoformat(max_date.replace("Z", "+00:00"))

            # Current period: last 30 days (or appropriate range)
            current_start = max_date - timedelta(days=30)
            previous_start = current_start - timedelta(days=30)
            previous_end = current_start

            current_val = self._execute_metric_in_period(
                metric_def, date_col, current_start, max_date
            )
            previous_val = self._execute_metric_in_period(
                metric_def, date_col, previous_start, previous_end
            )

            if current_val is not None and previous_val is not None and previous_val != 0:
                change_pct = ((current_val - previous_val) / previous_val) * 100
                return {
                    "period": "previous_period",
                    "value": previous_val,
                    "change_percent": round(change_pct, 2),
                }
        except Exception:
            pass
        return None

    def _execute_metric_in_period(
        self, metric_def: MetricDefinition, date_col: str, start: datetime, end: datetime
    ) -> float | int | None:
        """Execute metric within a specific date range."""
        try:
            sql = (
                f"SELECT {metric_def.sql_expression} AS value "
                f'FROM "{self.schema_name}"."{metric_def.target_table}" '
                f'WHERE "{date_col}" >= :start AND "{date_col}" < :end'
            )
            with self.engine.begin() as conn:
                result = conn.execute(text(sql), {"start": start, "end": end})
                row = result.fetchone()
                if row and row[0] is not None:
                    return float(row[0])
        except Exception:
            pass
        return None

    def _find_date_column(self, table_name: str) -> str | None:
        """Find the most relevant date column in a table."""
        columns = self.inspector.get_columns(table_name, schema=self.schema_name)
        date_columns = [
            c["name"]
            for c in columns
            if "date" in str(c["type"]).lower()
            or "timestamp" in str(c["type"]).lower()
            or "time" in str(c["type"]).lower()
        ]
        # Prefer created_at, then date, then first date column
        for preferred in ["created_at", "order_date", "date", "timestamp", "created"]:
            if preferred in date_columns:
                return preferred
        return date_columns[0] if date_columns else None

    def _find_numeric_column(self, table_name: str) -> str | None:
        """Find the most relevant numeric column for aggregation."""
        columns = self.inspector.get_columns(table_name, schema=self.schema_name)
        numeric_columns = [
            c["name"]
            for c in columns
            if any(t in str(c["type"]).lower() for t in ["int", "numeric", "float", "decimal", "bigint"])
        ]
        # Prefer amount, revenue, total, price
        for preferred in ["total_amount", "amount", "revenue", "price", "total", "sales", "cost"]:
            if preferred in numeric_columns:
                return preferred
        return numeric_columns[0] if numeric_columns else None

    def _find_categorical_column(self, table_name: str) -> str | None:
        """Find the most relevant categorical column for breakdown."""
        columns = self.inspector.get_columns(table_name, schema=self.schema_name)
        categorical_columns = [
            c["name"]
            for c in columns
            if c["name"] not in {"id", "created_at", "updated_at"}
            and ("text" in str(c["type"]).lower() or "varchar" in str(c["type"]).lower())
        ]
        # Prefer business-relevant categories
        for preferred in [
            "channel",
            "category",
            "region",
            "city",
            "state",
            "country",
            "department",
            "status",
            "type",
            "source",
            "payment_method",
            "segment",
        ]:
            if preferred in categorical_columns:
                return preferred
        return categorical_columns[0] if categorical_columns else None

    def _extract_source_column(self, metric_def: MetricDefinition) -> str:
        """Extract the primary source column from SQL expression."""
        import re
        match = re.search(r"SUM\(([^)]+)\)|AVG\(([^)]+)\)", metric_def.sql_expression)
        if match:
            return match.group(1) or match.group(2)
        return "multiple"

    def _format_label(self, name: str) -> str:
        """Convert metric/table name to human-readable label."""
        return name.replace("_", " ").title()

    def _format_value(self, value: float | int, unit: str) -> str:
        """Format value based on unit type."""
        if unit == "currency":
            if abs(value) >= 1_000_000:
                return f"${value / 1_000_000:.2f}M"
            elif abs(value) >= 1_000:
                return f"${value / 1_000:.1f}K"
            else:
                return f"${value:,.2f}"
        elif unit == "percentage":
            return f"{value:.1f}%"
        else:
            return f"{value:,.0f}"

    def _get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{self.schema_name}"."{table_name}"')
                )
                return result.scalar_one() or 0
        except Exception:
            return 0

    def discover_time_series(
        self, metric_name: str | None = None, interval: TimeInterval = TimeInterval.MONTH
    ) -> list[TimeSeriesPoint]:
        """Discover and compute time-series trend for the best metric."""
        profiles = self._get_table_profiles()

        # Find best metric and table
        best_metric = None
        best_table = None
        best_date_col = None
        best_numeric_col = None

        for profile in profiles:
            date_col = self._find_date_column(profile.table_name)
            numeric_col = self._find_numeric_column(profile.table_name)
            if date_col and numeric_col:
                best_table = profile.table_name
                best_date_col = date_col
                best_numeric_col = numeric_col
                if metric_name:
                    table_metrics = self.metric_engine.get_metrics_for_table(profile.table_name)
                    for m in table_metrics:
                        if m.name == metric_name:
                            best_metric = m
                            break
                if not best_metric:
                    # Create a simple sum metric
                    best_metric = MetricDefinition(
                        name="trend_metric",
                        target_table=profile.table_name,
                        formula=f"SUM({numeric_col})",
                        sql_expression=f"SUM({numeric_col})",
                        unit="currency" if "price" in numeric_col or "amount" in numeric_col else "count",
                    )
                break

        if not best_table or not best_date_col or not best_numeric_col or not best_metric:
            return []

        # Determine date truncation based on interval
        trunc_map = {
            TimeInterval.DAY: "DATE_TRUNC('day', {})",
            TimeInterval.WEEK: "DATE_TRUNC('week', {})",
            TimeInterval.MONTH: "DATE_TRUNC('month', {})",
            TimeInterval.QUARTER: "DATE_TRUNC('quarter', {})",
            TimeInterval.YEAR: "DATE_TRUNC('year', {})",
        }
        trunc_expr = trunc_map[interval].format(f'"{best_date_col}"')

        try:
            sql = (
                f"SELECT {trunc_expr} AS period, {best_metric.sql_expression} AS value "
                f'FROM "{self.schema_name}"."{best_table}" '
                f'WHERE "{best_date_col}" IS NOT NULL '
                f"GROUP BY period "
                f"ORDER BY period"
            )
            with self.engine.begin() as conn:
                result = conn.execute(text(sql))
                points = []
                for row in result.fetchall():
                    period_val = row[0]
                    value = float(row[1]) if row[1] is not None else 0
                    if isinstance(period_val, datetime):
                        period_str = period_val.strftime("%Y-%m-%d")
                    else:
                        period_str = str(period_val)
                    points.append(
                        TimeSeriesPoint(
                            period=period_str,
                            value=value,
                            formatted_value=self._format_value(value, best_metric.unit),
                        )
                    )
                return points
        except Exception:
            return []

    def discover_breakdown(self, metric_name: str | None = None) -> list[BreakdownPoint]:
        """Discover and compute categorical breakdown for the best metric."""
        profiles = self._get_table_profiles()

        best_table = None
        best_cat_col = None
        best_numeric_col = None
        best_metric = None

        for profile in profiles:
            cat_col = self._find_categorical_column(profile.table_name)
            numeric_col = self._find_numeric_column(profile.table_name)
            if cat_col and numeric_col:
                best_table = profile.table_name
                best_cat_col = cat_col
                best_numeric_col = numeric_col
                if metric_name:
                    table_metrics = self.metric_engine.get_metrics_for_table(profile.table_name)
                    for m in table_metrics:
                        if m.name == metric_name:
                            best_metric = m
                            break
                if not best_metric:
                    best_metric = MetricDefinition(
                        name="breakdown_metric",
                        target_table=profile.table_name,
                        formula=f"SUM({numeric_col})",
                        sql_expression=f"SUM({numeric_col})",
                        unit="currency" if "price" in numeric_col or "amount" in numeric_col else "count",
                    )
                break

        if not best_table or not best_cat_col or not best_numeric_col or not best_metric:
            return []

        try:
            sql = (
                f"SELECT \"{best_cat_col}\" AS label, {best_metric.sql_expression} AS value "
                f'FROM "{self.schema_name}"."{best_table}" '
                f'WHERE "{best_cat_col}" IS NOT NULL '
                f"GROUP BY label "
                f"ORDER BY value DESC "
                f"LIMIT 10"
            )
            with self.engine.begin() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                if not rows:
                    return []

                total = sum(float(r[1]) for r in rows if r[1] is not None)
                if total == 0:
                    return []

                points = []
                for row in rows:
                    label = str(row[0])
                    value = float(row[1]) if row[1] is not None else 0
                    points.append(
                        BreakdownPoint(
                            label=label,
                            value=value,
                            formatted_value=self._format_value(value, best_metric.unit),
                            percentage=round((value / total) * 100, 1) if total > 0 else 0,
                        )
                    )
                return points
        except Exception:
            return []

    def get_query_volume(self) -> list[QueryVolumePoint]:
        """Get query execution volume from actual query history."""
        # This would ideally come from a persistent query history table
        # For now, return empty - will be populated by the API layer
        return []


def create_analytics_engine(
    database_url: str, tenant_id: str = "default"
) -> AnalyticsEngine:
    """Factory function to create an analytics engine for a tenant."""
    from app.config import get_settings
    from app.dataset.service import tenant_schema_name

    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    schema_name = tenant_schema_name(tenant_id)
    return AnalyticsEngine(engine, schema_name)