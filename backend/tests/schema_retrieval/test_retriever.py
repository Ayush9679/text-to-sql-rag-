from app.schema_retrieval.retriever import (
    SchemaRetriever,
)
from app.schema_retrieval.documents import (
    SchemaDocument,
)
from app.schema_retrieval.business_knowledge import (
    BUSINESS_CONCEPTS,
)

from app.schema_retrieval.documents import (
    build_business_documents,
)

from app.schema_retrieval.documents import (
    KnowledgeDocument,
)


def test_retrieve_relevant_document():

    documents = [
        SchemaDocument(
            document_id="analytics.customers",
            schema_name="analytics",
            table_name="customers",
            content=(
                "TABLE: customers\n"
                "COLUMNS:\n"
                "- customer_id\n"
                "- signup_date\n"
                "- customer_segment"
            ),
        ),
        SchemaDocument(
            document_id="analytics.products",
            schema_name="analytics",
            table_name="products",
            content=(
                "TABLE: products\n"
                "COLUMNS:\n"
                "- product_id\n"
                "- product_name"
                "- category_id"
            ),
        ),
    ]

    retriever = SchemaRetriever()

    results = retriever.retrieve(
        query="customers signup date",
        documents=documents,
        top_k=2,
    )

    assert len(results) == 1

    assert (
        results[0].document_id
        == "analytics.customers"
    )

    assert results[0].score > 0

def test_build_business_documents():

    documents = build_business_documents(
        BUSINESS_CONCEPTS
    )

    assert len(documents) == len(
        BUSINESS_CONCEPTS
    )

    revenue_document = next(
        document
        for document in documents
        if document.title == "Revenue"
    )

    assert (
        revenue_document.source_type
        == "business"
    )

    assert "Revenue" in (
        revenue_document.content
    )

    assert "order_items.quantity" in (
        revenue_document.content
    )

def test_retrieve_mixed_knowledge():

    documents = [
        SchemaDocument(
            document_id="analytics.customers",
            schema_name="analytics",
            table_name="customers",
            content=(
                "TABLE: customers\n"
                "COLUMNS:\n"
                "- customer_id\n"
                "- signup_date\n"
                "- customer_segment"
            ),
        ),

        SchemaDocument(
            document_id="analytics.products",
            schema_name="analytics",
            table_name="products",
            content=(
                "TABLE: products\n"
                "COLUMNS:\n"
                "- product_id\n"
                "- product_name\n"
                "- category_id"
            ),
        ),

        KnowledgeDocument(
            document_id="concept.revenue",
            source_type="business",
            title="Revenue",
            content=(
                "CONCEPT: Revenue\n"
                "DEFINITION:\n"
                "Monetary value generated from "
                "purchased order items.\n"
                "RELATED TABLES:\n"
                "- orders\n"
                "- order_items"
            ),
        ),
    ]

    retriever = SchemaRetriever()

    results = retriever.retrieve(
        query="revenue order items",
        documents=documents,
        top_k=5,
    )

    assert len(results) >= 1

    assert (
        results[0].document_id
        == "concept.revenue"
    )

    assert (
        results[0].source_type
        == "business"
    )

    assert (
        results[0].title
        == "Revenue"
    )

def test_unified_retrieval_returns_schema_source():

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

        KnowledgeDocument(
            document_id="concept.customer",
            source_type="business",
            title="Customer",
            content=(
                "CONCEPT: Customer\n"
                "DEFINITION:\n"
                "A person represented in customer records."
            ),
        ),
    ]

    retriever = SchemaRetriever()

    results = retriever.retrieve(
        query="customers signup_date",
        documents=documents,
        top_k=5,
    )

    assert len(results) >= 1

    customer_table = next(
        result
        for result in results
        if result.document_id
        == "analytics.customers"
    )

    assert customer_table.source_type == "schema"
    assert customer_table.title == "customers"