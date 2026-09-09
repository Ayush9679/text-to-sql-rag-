"""Unit tests for MetricEngine."""

from app.dataset.profiler import ColumnProfile, TableProfile
from app.schema_intelligence.metric_engine import MetricDefinition, MetricEngine


def test_infer_metrics_from_sales_table():
    engine = MetricEngine()
    sales_profile = TableProfile(
        table_name="sales",
        row_count=100,
        column_count=4,
        columns=[
            ColumnProfile(
                name="quantity",
                normalized_name="quantity",
                inferred_type="INTEGER",
                semantic_type="quantity",
                null_count=0,
                null_percentage=0.0,
                unique_count=20,
                cardinality_ratio=0.2,
                is_primary_key_candidate=False,
                is_foreign_key_candidate=False,
            ),
            ColumnProfile(
                name="unit_price",
                normalized_name="unit_price",
                inferred_type="NUMERIC",
                semantic_type="monetary",
                null_count=0,
                null_percentage=0.0,
                unique_count=15,
                cardinality_ratio=0.15,
                is_primary_key_candidate=False,
                is_foreign_key_candidate=False,
            ),
        ],
    )

    metrics = engine.infer_metrics_for_tables([sales_profile])
    metric_names = [m.name for m in metrics]

    assert "revenue" in metric_names
    assert "total_units_sold" in metric_names

    rev_metric = next(m for m in metrics if m.name == "revenue")
    assert rev_metric.sql_expression == "SUM(quantity * unit_price)"
    assert "sales" in rev_metric.synonyms


def test_register_and_format_custom_metric():
    engine = MetricEngine()
    metric = MetricDefinition(
        name="gross_margin",
        target_table="orders",
        formula="(revenue - cost) / revenue",
        sql_expression="SUM(revenue - cost) / SUM(revenue)",
        unit="percentage",
        description="Gross margin percentage",
        synonyms=["margin", "profit margin"],
    )
    engine.register_metric(metric)

    formatted = engine.format_metrics_for_prompt()
    assert "GROSS_MARGIN" in formatted
    assert "margin" in formatted
