from app.clarification.analyzer import QueryAnalyzer
from app.clarification.intent_validator import IntentValidator


def test_valid_customer_query():
    analyzer = QueryAnalyzer()
    validator = IntentValidator()

    analysis = analyzer.analyze("How many customers signed up in 2025?")
    result = validator.validate(analysis)

    assert result.valid is True
    assert result.intent == "customer_analysis"
    assert result.confidence > 0.0
    assert not result.ambiguities
    assert not result.missing_information


def test_invalid_best_customers():
    analyzer = QueryAnalyzer()
    validator = IntentValidator()

    analysis = analyzer.analyze("Show me the best customers")
    result = validator.validate(analysis)

    assert result.valid is False
    assert result.intent == "customer_analysis"
    assert result.ambiguities or result.missing_information


def test_invalid_vague_something():
    analyzer = QueryAnalyzer()
    validator = IntentValidator()

    analysis = analyzer.analyze("Show me something.")
    result = validator.validate(analysis)

    assert result.valid is False
    assert result.intent is None
    assert result.confidence == 0.0


def test_valid_total_products():
    analyzer = QueryAnalyzer()
    validator = IntentValidator()

    analysis = analyzer.analyze("Show the total products")
    result = validator.validate(analysis)

    assert result.valid is True
    assert result.intent == "product_analysis"
    assert result.confidence > 0.0


def test_unsupported_intent():
    analyzer = QueryAnalyzer()
    validator = IntentValidator()

    analysis = analyzer.analyze("Do a quantum physics analysis")
    result = validator.validate(analysis)

    assert result.valid is False
    assert result.intent is None
