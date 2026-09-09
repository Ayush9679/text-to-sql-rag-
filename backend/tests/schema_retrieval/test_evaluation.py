from app.schema_retrieval.evaluation import (
    EVALUATION_CASES,
    hit_at_k,
    recall_at_k,
)


def test_hit_at_k():

    retrieved = [
        "analytics.products",
        "analytics.customers",
        "concept.revenue",
    ]

    expected = (
        "analytics.customers",
        "concept.customer",
    )

    assert hit_at_k(
        retrieved,
        expected,
        3,
    )


def test_hit_at_k_false():

    retrieved = [
        "analytics.products",
        "analytics.orders",
    ]

    expected = (
        "analytics.customers",
    )

    assert not hit_at_k(
        retrieved,
        expected,
        2,
    )


def test_recall_at_k():

    retrieved = [
        "analytics.customers",
        "analytics.orders",
        "concept.customer",
        "concept.order",
    ]

    expected = (
        "analytics.customers",
        "analytics.orders",
        "concept.customer",
        "concept.order",
    )

    assert recall_at_k(
        retrieved,
        expected,
        4,
    ) == 1.0

def evaluate_retriever(
    retriever,
    documents,
    cases=EVALUATION_CASES,
    k=5,
):
    results = []

    for case in cases:
        retrieved = retriever.retrieve(
            query=case.question,
            documents=documents,
            top_k=k,
        )

        retrieved_ids = [
            result.document_id
            for result in retrieved
        ]

        results.append({
            "question": case.question,
            "hit_at_k": hit_at_k(
                retrieved_ids,
                case.expected_documents,
                k,
            ),
            "recall_at_k": recall_at_k(
                retrieved_ids,
                case.expected_documents,
                k,
            ),
            "retrieved_documents": retrieved_ids,
        })

    return results
