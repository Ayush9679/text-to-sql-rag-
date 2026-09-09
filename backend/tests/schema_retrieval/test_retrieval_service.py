from app.schema_retrieval.documents import (
    SchemaDocument,
)
from app.schema_retrieval.service import (
    SchemaRetrievalService,
)


def test_retrieve_context():

    documents = [
        SchemaDocument(
            document_id="analytics.customers",
            schema_name="analytics",
            table_name="customers",
            content=(
                "TABLE: customers\n"
                "COLUMNS:\n"
                "- customer_id\n"
                "- signup_date"
            ),
        ),
    ]

    service = SchemaRetrievalService()

    context = service.retrieve_context(
        query="customers signup",
        documents=documents,
        top_k=3,
    )

    assert context.query == (
        "customers signup"
    )

    assert len(context.documents) == 1

    assert (
        context.documents[0].document_id
        == "analytics.customers"
    )

    assert (
        "customers"
        in context.text
    )