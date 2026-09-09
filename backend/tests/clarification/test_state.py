from app.clarification.analyzer import QueryAnalyzer
from app.clarification.models import ClarificationQuestion
from app.clarification.state import ClarificationStateManager


def test_create_state():
    manager = ClarificationStateManager()
    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze("Show me the best customers")

    state = manager.create_state("Show me the best customers", analysis=analysis)
    assert state.conversation_id is not None
    assert state.original_query == "Show me the best customers"
    assert state.status == "awaiting_clarification"
    assert len(state.pending_clarifications) == 0
    assert len(state.resolved_fields) == 0
    assert len(state.clarification_history) == 0


def test_add_clarification_question():
    manager = ClarificationStateManager()
    state = manager.create_state("Show me the best customers")

    question = ClarificationQuestion(
        question="How would you like to define the best customers?",
        reason="Ranking metric required",
        options=["Total spending", "Number of orders"],
        target_field="ranking_metric",
        confidence=0.9,
    )

    state = manager.add_question(state, question)
    assert len(state.pending_clarifications) == 1
    assert state.status == "awaiting_clarification"


def test_resolve_clarification():
    manager = ClarificationStateManager()
    state = manager.create_state("Show me the best customers")

    question = ClarificationQuestion(
        question="How would you like to define the best customers?",
        reason="Ranking metric required",
        options=["Total spending", "Number of orders"],
        target_field="ranking_metric",
        confidence=0.9,
    )
    state = manager.add_question(state, question)

    state = manager.resolve_question(
        state=state,
        question=question,
        user_answer="By total spending",
        resolved_field="ranking_metric",
        resolved_value="total_spending",
    )

    assert state.status == "resolved"
    assert len(state.pending_clarifications) == 0
    assert state.resolved_fields["ranking_metric"] == "total_spending"
    assert len(state.clarification_history) == 1
    assert state.clarification_history[0].user_answer == "By total spending"


def test_cancel_state():
    manager = ClarificationStateManager()
    state = manager.create_state("Show me the best customers")
    state = manager.cancel_state(state)
    assert state.status == "cancelled"
