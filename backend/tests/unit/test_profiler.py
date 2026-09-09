"""Unit tests for the DataProfiler and statistical/semantic inference."""

from app.dataset.profiler import DataProfiler


def test_profile_numeric_column():
    profiler = DataProfiler()
    values = ["10.5", "20.0", "30.5", "40.0", "50.0", "60.0", "70.0", "80.0", "90.0", "100.0"]
    profile = profiler.profile_column("sales_amt", "sales_amt", values, total_rows=10)

    assert profile.inferred_type == "NUMERIC"
    assert profile.semantic_type == "monetary"
    assert profile.null_count == 0
    assert profile.null_percentage == 0.0
    assert profile.stats["min"] == 10.5
    assert profile.stats["max"] == 100.0
    assert profile.stats["mean"] == 55.1
    assert profile.is_primary_key_candidate is False


def test_profile_primary_key_identifier():
    profiler = DataProfiler()
    values = [str(i) for i in range(1, 101)]
    profile = profiler.profile_column("customer_id", "customer_id", values, total_rows=100)

    assert profile.inferred_type == "INTEGER"
    assert profile.semantic_type == "identifier"
    assert profile.is_primary_key_candidate is True
    assert profile.unique_count == 100
    assert profile.cardinality_ratio == 1.0


def test_profile_date_column():
    profiler = DataProfiler()
    values = ["2026-01-15", "2026-02-20", "2026-03-25", "2026-04-30"]
    profile = profiler.profile_column("order_date", "order_date", values, total_rows=4)

    assert profile.inferred_type == "DATE"
    assert profile.semantic_type == "date"


def test_profile_table_with_anomalies_and_nulls():
    profiler = DataProfiler()
    headers = ["id", "product_name", "price", "notes"]
    norm_headers = ["id", "product_name", "price", "notes"]
    rows = [
        ["1", "Widget A", "$10.00", "Good"],
        ["2", "Widget B", "$12.50", ""],
        ["3", "Widget C", "$15.00", ""],
        ["4", "Widget D", "$9999.00", ""],
        ["5", "Widget E", "$11.00", ""],
        ["6", "Widget F", "$13.00", ""],
        ["7", "Widget G", "$14.00", ""],
        ["8", "Widget H", "$12.00", ""],
        ["9", "Widget I", "$10.50", ""],
        ["10", "Widget J", "$11.50", ""],
    ]
    tprofile = profiler.profile_table("products", headers, norm_headers, rows)

    assert tprofile.row_count == 10
    assert tprofile.column_count == 4
    assert "id" in tprofile.primary_key_candidates
    # notes has 90% nulls
    notes_col = next(c for c in tprofile.columns if c.normalized_name == "notes")
    assert notes_col.null_percentage == 90.0
