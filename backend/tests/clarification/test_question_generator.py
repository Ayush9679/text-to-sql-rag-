from app.clarification.ambiguity import AmbiguityDetector
from app.clarification.analyzer import QueryAnalyzer
from app.clarification.decision import ClarificationDecisionEngine
from app.clarification.intent_validator import IntentValidator
from app.clarification.missing_information import MissingInformationDetector
from app.clarification.question_generator import ClarificationQuestionGenerator


def generate_for_query(query: str):
    analyzer = QueryAnalyzer()
    validator = IntentValidator()
    ambiguity_detector = AmbiguityDetector()
    missing_detector = MissingInformationDetector()
    decision_engine = ClarificationDecisionEngine()
    generator = ClarificationQuestionGenerator()

    analysis = analyzer.analyze(query)
    intent_val = validator.validate(analysis)
    ambiguity = ambiguity_detector.detect(analysis)
    missing_info = missing_detector.detect(analysis)
    decision = decision_engine.decide(analysis, intent_val, ambiguity, missing_info)

    return generator.generate(decision, analysis)


def test_question_for_best_customers():
    question = generate_for_query("Show me the best customers")
    assert "best customers" in question.question.lower()
    assert question.target_field == "ranking_metric"
    assert len(question.options) >= 2
    assert "sql" not in question.question.lower()
    assert 0.0 <= question.confidence <= 1.0


def test_question_for_revenue_timeframe():
    question = generate_for_query("Show revenue")
    assert "timeframe" in question.question.lower() or question.target_field == "timeframe"
    assert len(question.options) >= 2
    assert "sql" not in question.question.lower()


def test_question_for_product_performance():
    question = generate_for_query("Show product performance")
    assert question.target_field == "performance_metric"
    assert len(question.options) >= 2


def test_question_for_vague_customers():
    question = generate_for_query("Show me something about customers")
    assert question.target_field == "operation"
    assert len(question.options) >= 2
