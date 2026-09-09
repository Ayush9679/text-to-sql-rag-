from app.schema_retrieval.scorer import (
    RelevanceScorer,
)


def test_exact_relevance():

    scorer = RelevanceScorer()

    score = scorer.score(
        query="customer signup",
        content=(
            "TABLE: customers\n"
            "COLUMNS:\n"
            "- customer_id\n"
            "- signup_date"
        ),
    )

    assert score > 0.0
    assert score <= 1.0


def test_irrelevant_document():

    scorer = RelevanceScorer()

    score = scorer.score(
        query="customer signup",
        content=(
            "TABLE: products\n"
            "COLUMNS:\n"
            "- product_id\n"
            "- product_name"
        ),
    )

    assert score == 0.0


def test_stop_words_are_ignored():

    scorer = RelevanceScorer()

    score = scorer.score(
        query="how many customers",
        content=(
            "TABLE: customers\n"
            "COLUMNS:\n"
            "- customer_id"
        ),
    )

    assert score == 1.0