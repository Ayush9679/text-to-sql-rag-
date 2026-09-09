from app.schema_retrieval.business_knowledge import (
    BUSINESS_CONCEPTS,
)
from app.schema_retrieval.knowledge import (
    BusinessConcept,
)


def test_business_concepts_exist():
    assert len(BUSINESS_CONCEPTS) > 0

    assert all(
        isinstance(
            concept,
            BusinessConcept,
        )
        for concept in BUSINESS_CONCEPTS
    )


def test_revenue_concept():
    revenue = next(
        concept
        for concept in BUSINESS_CONCEPTS
        if concept.name == "Revenue"
    )

    assert revenue.definition

    assert "orders" in revenue.related_tables
    assert "order_items" in revenue.related_tables

    assert (
        "order_items.quantity"
        in revenue.related_columns
    )

    assert (
        "order_items.unit_price"
        in revenue.related_columns
    )

    assert revenue.calculation is not None