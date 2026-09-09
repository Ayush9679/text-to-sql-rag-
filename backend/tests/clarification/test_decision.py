from app.clarification.ambiguity import AmbiguityDetector
from app.clarification.analyzer import QueryAnalyzer
from app.clarification.decision import ClarificationDecisionEngine
from app.clarification.intent_validator import IntentValidator
from app.clarification.missing_information import MissingInformationDetector


def evaluate_query(query: str):
    analyzer = QueryAnalyzer()
    validator = IntentValidator()
    ambiguity_detector = AmbiguityDetector()
    missing_detector = MissingInformationDetector()
    engine = ClarificationDecisionEngine()

    analysis = analyzer.analyze(query)
    intent_val = validator.validate(analysis)
    ambiguity = ambiguity_detector.detect(analysis)
    missing_info = missing_detector.detect(analysis)

    return engine.decide(
        analysis=analysis,
        intent_validation=intent_val,
        ambiguity=ambiguity,
        missing_info=missing_info,
    )


def test_proceed_well_specified():
    decision = evaluate_query("Show top 10 customers by total spending in 2025.")
    assert decision.action == "proceed"
    assert 0.0 <= decision.confidence <= 1.0


def test_clarify_ambiguous_ranking():
    decision = evaluate_query("Show me the best customers.")
    assert decision.action == "clarify"
    assert "ranking_metric" in decision.missing_information or "best" in decision.ambiguities


def test_clarify_vague_query():
    decision = evaluate_query("Tell me something.")
    assert decision.action == "clarify"


def test_unsupported_quantum():
    decision = evaluate_query("Perform quantum accounting analysis.")
    assert decision.action == "unsupported"


def test_clarify_bare_revenue():
    decision = evaluate_query("Show revenue.")
    assert decision.action == "clarify"
    assert "timeframe" in decision.missing_information
