from app.clarification.engine import ClarificationEngine


def test_flow_1_clear_query():
    """
    FLOW 1 — Clear query
    User: "Show the top 10 customers by total spending in 2025."
    Expected: PROCEED, No clarification required.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query(
        "Show the top 10 customers by total spending in 2025."
    )

    assert decision.action == "proceed"
    assert question is None
    assert state.status == "resolved"
    assert "customers" in state.analysis.entities
    assert "spending" in state.analysis.metrics
    assert state.analysis.limit == 10
    assert "2025" in state.analysis.filters
    assert 0.0 <= decision.confidence <= 1.0


def test_flow_2_ambiguous_ranking():
    """
    FLOW 2 — Ambiguous ranking
    User: "Show me the best customers."
    Expected: CLARIFY, Missing: ranking metric, Generated clarification asked.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query("Show me the best customers.")

    assert decision.action == "clarify"
    assert question is not None
    assert "best customers" in question.question.lower()
    assert question.target_field == "ranking_metric"
    assert len(question.options) >= 2
    assert state.status == "awaiting_clarification"
    assert "ranking_metric" in decision.missing_information or "best" in decision.ambiguities


def test_flow_3_resolve_ranking():
    """
    FLOW 3 — Resolve ranking
    User: "Show me the best customers."
    Assistant asks: "How would you like to define the best customers?"
    User: "By total spending."
    Expected: State becomes resolved, Metric: total_spending, Decision: PROCEED.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query("Show me the best customers.")
    assert decision.action == "clarify"

    updated_state, updated_decision, next_question = engine.resolve_clarification(
        state=state,
        user_answer="By total spending.",
    )

    assert updated_decision.action == "proceed"
    assert updated_state.status == "resolved"
    assert next_question is None
    assert "spending" in updated_state.analysis.metrics
    assert "total_spending" in str(updated_state.resolved_fields.get("ranking_metric"))
    assert len(updated_state.clarification_history) == 1


def test_flow_4_missing_timeframe():
    """
    FLOW 4 — Missing timeframe
    User: "Show revenue."
    Expected: CLARIFY, Missing: timeframe.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query("Show revenue.")

    assert decision.action == "clarify"
    assert question is not None
    assert question.target_field == "timeframe"
    assert "timeframe" in decision.missing_information
    assert state.status == "awaiting_clarification"


def test_flow_5_resolve_timeframe():
    """
    FLOW 5 — Resolve timeframe
    User: "Show revenue."
    Assistant: "What timeframe should I use?"
    User: "For 2025."
    Expected: Filter: year = 2025 / 2025, Decision: PROCEED.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query("Show revenue.")
    assert decision.action == "clarify"

    updated_state, updated_decision, next_question = engine.resolve_clarification(
        state=state,
        user_answer="For 2025.",
    )

    assert updated_decision.action == "proceed"
    assert updated_state.status == "resolved"
    assert "2025" in updated_state.analysis.filters
    assert next_question is None


def test_flow_6_unsupported_intent():
    """
    FLOW 6 — Unsupported intent
    User: "Do a quantum physics analysis."
    Expected: UNSUPPORTED, No SQL generation.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query("Do a quantum physics analysis.")

    assert decision.action == "unsupported"
    assert question is None
    assert state.status == "unsupported"


def test_flow_7_vague_query():
    """
    FLOW 7 — Vague query
    User: "Show me something about customers."
    Expected: CLARIFY, Missing analytical operation/metric.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query("Show me something about customers.")

    assert decision.action == "clarify"
    assert question is not None
    assert question.target_field in {"operation", "operation_or_metric"}
    assert state.status == "awaiting_clarification"


def test_flow_8_multidimensional_query():
    """
    FLOW 8 — Multi-dimensional query
    User: "Show monthly revenue by product category for 2025."
    Expected: PROCEED
    Recognize: entity: categories/products, metric: revenue, aggregation: sum,
    grouping: month, category, filter: 2025.
    """
    engine = ClarificationEngine()
    state, decision, question = engine.process_query(
        "Show monthly revenue by product category for 2025."
    )

    assert decision.action == "proceed"
    assert question is None
    assert state.status == "resolved"
    assert "categories" in state.analysis.entities
    assert "revenue" in state.analysis.metrics
    assert state.analysis.aggregation == "sum"
    assert "month" in state.analysis.grouping
    assert "category" in state.analysis.grouping
    assert "2025" in state.analysis.filters
