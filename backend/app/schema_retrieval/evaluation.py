from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    question: str
    expected_documents: tuple[str, ...]


EVALUATION_CASES = [
    RetrievalEvaluationCase(
        question="How many customers signed up in 2025?",
        expected_documents=(
            "analytics.customers",
            "concept.customer",
        ),
    ),

    RetrievalEvaluationCase(
        question="Which product categories generated the most revenue?",
        expected_documents=(
            "analytics.categories",
            "analytics.products",
            "analytics.order_items",
            "concept.product_category",
            "concept.revenue",
        ),
    ),

    RetrievalEvaluationCase(
        question="Which customers placed the most orders?",
        expected_documents=(
            "analytics.customers",
            "analytics.orders",
            "concept.customer",
            "concept.order",
        ),
    ),

    RetrievalEvaluationCase(
        question="What products are available in each category?",
        expected_documents=(
            "analytics.products",
            "analytics.categories",
            "concept.product",
            "concept.product_category",
        ),
    ),

    RetrievalEvaluationCase(
        question="What is the average order value?",
        expected_documents=(
            "analytics.orders",
            "analytics.order_items",
            "concept.average_order_value",
        ),
    ),
]


def hit_at_k(
    retrieved_ids: list[str],
    expected_ids: tuple[str, ...],
    k: int,
) -> bool:

    retrieved_top_k = set(
        retrieved_ids[:k]
    )

    return any(
        document_id in retrieved_top_k
        for document_id in expected_ids
    )


def recall_at_k(
    retrieved_ids: list[str],
    expected_ids: tuple[str, ...],
    k: int,
) -> float:

    retrieved_top_k = set(
        retrieved_ids[:k]
    )

    if not expected_ids:
        return 0.0

    relevant_found = sum(
        1
        for document_id in expected_ids
        if document_id in retrieved_top_k
    )

    return relevant_found / len(expected_ids)


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

        results.append(
            {
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
            }
        )

    return results