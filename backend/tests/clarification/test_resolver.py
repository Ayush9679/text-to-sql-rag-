from app.clarification.models import ClarificationQuestion
from app.clarification.resolver import ClarificationResolver
from app.clarification.state import ClarificationStateManager


def test_resolve_ranking_metric():
    resolver = ClarificationResolver()
    state_manager = ClarificationStateManager()

    original_query = "Show me the best customers"
    state = state_manager.create_state(original_query)
    question = ClarificationQuestion(
        question="How would you like to define the best customers?",
        reason="Ranking metric required",
        options=["Total spending", "Number of orders"],
        target_field="ranking_metric",
        confidence=0.9,
    )
    state = state_manager.add_question(state, question)

    updated_state, decision = resolver.resolve(
        state=state,
        user_answer="By total spending",
    )

    assert updated_state.status == "resolved"
    assert "total_spending" in str(updated_state.resolved_fields["ranking_metric"])
    assert "spending" in updated_state.analysis.metrics
    assert decision.action == "proceed"


def test_resolve_timeframe():
    resolver = ClarificationResolver()
    state_manager = ClarificationStateManager()

    original_query = "Show revenue"
    state = state_manager.create_state(original_query)
    question = ClarificationQuestion(
        question="What timeframe should I use?",
        reason="Timeframe required",
        options=["Year 2025", "All time"],
        target_field="timeframe",
        confidence=0.9,
    )
    state = state_manager.add_question(state, question)

    updated_state, decision = resolver.resolve(
        state=state,
        user_answer="For 2025",
    )

    assert updated_state.status == "resolved"
    assert "2025" in updated_state.analysis.filters
    assert decision.action == "proceed"


def test_resolve_operation():
    resolver = ClarificationResolver()
    state_manager = ClarificationStateManager()

    original_query = "Show me something about customers"
    state = state_manager.create_state(original_query)
    question = ClarificationQuestion(
        question="What customer insights would you like to see?",
        reason="Operation required",
        options=["Total customer count", "Top spending customers"],
        target_field="operation",
        confidence=0.9,
    )
    state = state_manager.add_question(state, question)

    updated_state, decision = resolver.resolve(
        state=state,
        user_answer="Total customer count",
    )

    assert updated_state.status == "resolved"
    assert "count" in updated_state.analysis.metrics
    assert decision.action == "proceed"
