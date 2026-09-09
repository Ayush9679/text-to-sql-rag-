import pytest

from app.clarification.analyzer import QueryAnalyzer


def test_customer_query():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("How many customers signed up in 2025?")

    assert result.intent == "customer_analysis"
    assert "customers" in result.entities
    assert "count" in result.metrics
    assert result.aggregation == "count"
    assert "2025" in result.filters
    assert 0.0 <= result.confidence <= 1.0
    assert result.confidence > 0.0


def test_revenue_query():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Show total revenue from sales")

    assert "revenue" in result.metrics
    assert result.aggregation == "sum"
    assert 0.0 <= result.confidence <= 1.0
    assert result.confidence > 0.0


def test_ambiguous_best_customers():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Show me the best customers")

    assert "customers" in result.entities
    assert result.ambiguities
    assert result.missing_information
    assert "ranking metric" in result.missing_information
    assert result.sort_direction == "descending"
    assert 0.0 <= result.confidence <= 1.0


def test_top_n_query():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Show the top 10 customers")

    assert result.intent == "customer_analysis"
    assert result.limit == 10
    assert result.sort_direction == "descending"
    assert result.aggregation == "ranking"
    assert "ranking metric" in result.missing_information
    assert 0.0 <= result.confidence <= 1.0


def test_least_customers_by_order_value_is_an_ascending_ranked_query():
    result = QueryAnalyzer().analyze("Give me 10 least customers based on order value.")

    assert result.entities == ["customers", "orders"]
    assert "order_value" in result.metrics
    assert result.aggregation == "ranking"
    assert result.sort_direction == "ascending"
    assert result.limit == 10
    assert result.missing_information == []


@pytest.mark.parametrize(
    ("query", "expected_direction"),
    [
        ("top 10 customers by revenue", "descending"),
        ("10 highest customers by revenue", "descending"),
        ("10 least customers by revenue", "ascending"),
        ("10 lowest customers by revenue", "ascending"),
        ("bottom 10 customers by revenue", "ascending"),
        ("10 customers with the smallest order value", "ascending"),
    ],
)
def test_explicit_ranking_direction_is_deterministic(query, expected_direction):
    result = QueryAnalyzer().analyze(query)
    assert result.sort_direction == expected_direction
    assert result.limit == 10
    assert result.missing_information == []


def test_multi_word_phrases():
    analyzer = QueryAnalyzer()

    # "How many" phrase
    r1 = analyzer.analyze("How many orders were placed?")
    assert "orders" in r1.entities
    assert "count" in r1.metrics
    assert r1.aggregation == "count"

    # "Total spending"
    r2 = analyzer.analyze("Show top 5 customers by total spending in 2025")
    assert "customers" in r2.entities
    assert "spending" in r2.metrics
    assert r2.limit == 5
    assert "2025" in r2.filters

    # "Number of orders"
    r3 = analyzer.analyze("Show number of orders by product category")
    assert "orders" in r3.entities
    assert "categories" in r3.entities
    assert "category" in r3.grouping


def test_multidimensional_query():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Show monthly revenue by product category for 2025")

    assert "categories" in result.entities
    assert "revenue" in result.metrics
    assert "month" in result.grouping
    assert "category" in result.grouping
    assert "2025" in result.filters
    assert result.aggregation == "sum"
    assert 0.0 <= result.confidence <= 1.0


def test_unsupported_query():
    analyzer = QueryAnalyzer()
    result = analyzer.analyze("Do a quantum physics analysis")

    assert result.intent is None
    assert result.confidence == 0.0
