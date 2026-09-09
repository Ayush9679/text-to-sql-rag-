from app.clarification.analyzer import QueryAnalyzer
from app.clarification.missing_information import MissingInformationDetector


def test_missing_ranking_metric_best_customers():
    detector = MissingInformationDetector()
    result = detector.detect("Show me the best customers")

    assert "ranking_metric" in result.required
    assert "ranking_metric" in result.missing
    assert "ranking_metric" in result.reasons
    assert 0.0 <= result.confidence <= 1.0


def test_missing_ranking_metric_top_customers():
    detector = MissingInformationDetector()
    result = detector.detect("Show the top 10 customers")

    assert "ranking_metric" in result.required


def test_explicit_order_value_prevents_ranking_clarification():
    analysis = QueryAnalyzer().analyze("Give me 10 least customers based on order value.")
    result = MissingInformationDetector().detect(analysis)

    assert "ranking_metric" not in result.required
    assert "ranking_metric" not in result.missing


def test_missing_timeframe_show_revenue():
    detector = MissingInformationDetector()
    result = detector.detect("Show revenue")

    assert "timeframe" in result.required
    assert "timeframe" in result.missing


def test_missing_performance_metric():
    detector = MissingInformationDetector()
    result = detector.detect("Show product performance")

    assert "performance_metric" in result.required
    assert "performance_metric" in result.missing


def test_missing_comparison_information():
    detector = MissingInformationDetector()
    result = detector.detect("Compare sales")

    assert "comparison_dimension" in result.required
    assert "metric_definition" in result.required
    assert "comparison_dimension" in result.missing


def test_missing_operation_for_vague_query():
    detector = MissingInformationDetector()
    result = detector.detect("Show me something about customers")

    assert "operation_or_metric" in result.required


def test_no_missing_information_complete_query():
    analyzer = QueryAnalyzer()
    detector = MissingInformationDetector()

    analysis = analyzer.analyze("Show top 10 customers by total spending in 2025")
    result = detector.detect(analysis)

    assert len(result.required) == 0
    assert len(result.missing) == 0
