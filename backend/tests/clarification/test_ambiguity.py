from app.clarification.ambiguity import AmbiguityDetector
from app.clarification.analyzer import QueryAnalyzer


def test_vague_ranking_best_customers():
    detector = AmbiguityDetector()
    result = detector.detect("Show me the best customers")

    assert result.is_ambiguous is True
    assert "vague_ranking" in result.ambiguity_types
    assert "best" in result.ambiguous_terms
    assert 0.0 <= result.confidence <= 1.0


def test_vague_ranking_worst_products():
    detector = AmbiguityDetector()
    result = detector.detect("Show the worst products")

    assert result.is_ambiguous is True
    assert "vague_ranking" in result.ambiguity_types
    assert "worst" in result.ambiguous_terms


def test_vague_comparison_popular_products():
    detector = AmbiguityDetector()
    result = detector.detect("Show popular products")

    assert result.is_ambiguous is True
    assert "vague_comparison" in result.ambiguity_types
    assert "popular" in result.ambiguous_terms


def test_undefined_metric_valuable_customers():
    detector = AmbiguityDetector()
    result = detector.detect("Show most valuable customers")

    assert result.is_ambiguous is True
    assert "undefined_business_metric" in result.ambiguity_types
    assert any("valuable" in t for t in result.ambiguous_terms)


def test_missing_timeframe_growth():
    detector = AmbiguityDetector()
    result = detector.detect("Show revenue growth")

    assert result.is_ambiguous is True
    assert "missing_timeframe" in result.ambiguity_types
    assert "growth" in result.ambiguous_terms


def test_ambiguous_terminology_sales():
    detector = AmbiguityDetector()
    result = detector.detect("Show sales")

    assert result.is_ambiguous is True
    assert "ambiguous_terminology" in result.ambiguity_types
    assert "sales" in result.ambiguous_terms


def test_unambiguous_query():
    analyzer = QueryAnalyzer()
    detector = AmbiguityDetector()

    analysis = analyzer.analyze("Show top 10 customers by total spending in 2025")
    result = detector.detect(analysis)

    assert result.is_ambiguous is False
    assert len(result.ambiguity_types) == 0
