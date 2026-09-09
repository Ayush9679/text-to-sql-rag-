from app.schema_retrieval.context import (
    RAGContext,
)
from app.schema_retrieval.retriever import (
    RetrievalResult,
)


def test_rag_context():

    result = RetrievalResult(
        document_id="analytics.customers",
        source_type="schema",
        title="customers",
        content=(
            "TABLE: customers\n"
            "COLUMNS:\n"
            "- customer_id\n"
            "- signup_date"
        ),
        score=1.0,
    )

    context = RAGContext(
        query="How many customers signed up?",
        documents=[result],
    )

    assert context.query == (
        "How many customers signed up?"
    )

    assert (
        "RETRIEVED KNOWLEDGE"
        in context.text
    )

    assert (
        "analytics.customers"
        in context.text
    )

    assert (
        "signup_date"
        in context.text
    )

    assert "SCORE: 1.0000" in context.text