"""Unit tests for ConfidenceEngine, AnswerGenerator, and ConversationManager."""

from app.confidence.engine import ConfidenceEngine
from app.conversation.manager import ConversationManager, ConversationTurn
from app.response.answer_generator import AnswerGenerator


def test_confidence_engine_scoring():
    engine = ConfidenceEngine()
    
    # High confidence scenario: perfect match, execution success
    eval_high = engine.evaluate(
        retrieval_score=0.95,
        schema_match_ratio=1.0,
        sql_valid=True,
        execution_success=True,
        row_count=10,
        ambiguity_detected=False,
        llm_confidence=0.95,
    )
    assert eval_high.composite_score >= 0.85
    assert eval_high.recommendation == "AUTO_EXECUTE"

    # Low confidence scenario: execution error
    eval_low = engine.evaluate(
        retrieval_score=0.30,
        schema_match_ratio=0.5,
        sql_valid=False,
        execution_success=False,
        row_count=0,
        ambiguity_detected=True,
        ambiguity_penalty=0.25,
        llm_confidence=0.40,
    )
    assert eval_low.composite_score < 0.60
    assert eval_low.recommendation == "CLARIFICATION_REQUIRED"


def test_answer_generator_formatting():
    gen = AnswerGenerator()

    # Single scalar metric
    ans1 = gen.generate_answer(
        query="What was total revenue?",
        sql="SELECT SUM(amount) AS revenue FROM sales",
        columns=["revenue"],
        rows=[[1250000.50]],
    )
    assert ans1.recommended_chart == "metric_card"
    assert "1,250,000.50" in ans1.summary

    # Multi-row categorical ranking
    ans2 = gen.generate_answer(
        query="Top 3 products by revenue",
        sql="SELECT name, revenue FROM ...",
        columns=["name", "revenue"],
        rows=[["Product X", 50000], ["Product Y", 30000], ["Product Z", 20000]],
    )
    assert ans2.recommended_chart == "bar_chart"
    assert "Product X" in ans2.summary


def test_conversation_manager_refinement():
    mgr = ConversationManager()
    conv_id = "conv-123"

    mgr.record_turn(
        conversation_id=conv_id,
        business_id="biz_1",
        turn=ConversationTurn(
            user_query="Who were our top 5 customers last month?",
            standalone_query="Who were our top 5 customers last month?",
            generated_sql="SELECT name, SUM(amt) FROM customers JOIN ...",
            tables_used=["customers", "sales"],
        ),
    )

    # Conversational follow-up
    refined = mgr.refine_query("Only show the ones from Delhi", conversation_id=conv_id)
    assert "top 5 customers" in refined
    assert "delhi" in refined
