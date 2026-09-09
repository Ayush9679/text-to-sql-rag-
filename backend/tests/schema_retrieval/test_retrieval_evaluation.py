import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from app.schema_intelligence.inspector import (
    PostgreSQLSchemaInspector,
)
from app.schema_intelligence.extractor import (
    SchemaExtractor,
)
from app.schema_retrieval.documents import (
    SchemaDocumentBuilder,
    build_business_documents,
)
from app.schema_retrieval.business_knowledge import (
    BUSINESS_CONCEPTS,
)
from app.schema_retrieval.retriever import (
    SchemaRetriever,
)
from app.schema_retrieval.evaluation import (
    EVALUATION_CASES,
    evaluate_retriever,
)
from app.schema_retrieval.serializer import (
    SchemaSerializer,
)


load_dotenv()


def create_test_engine():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")

    if not all(
        [
            user,
            password,
            host,
            port,
            database,
        ]
    ):
        raise RuntimeError(
            "PostgreSQL environment variables are missing."
        )

    return create_engine(
        f"postgresql+psycopg://"
        f"{user}:{password}@"
        f"{host}:{port}/{database}"
    )


def test_retrieval_evaluation():

    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine=engine
    )

    extractor = SchemaExtractor(
        inspector=inspector
    )

    database_schema = extractor.extract_schema(
        schema="analytics"
    )

    serializer = SchemaSerializer()

    builder = SchemaDocumentBuilder(
        serializer=serializer
    )

    schema_documents = builder.build_documents(
        database_schema
    )

    business_documents = build_business_documents(
        BUSINESS_CONCEPTS
    )

    documents = (
        schema_documents
        + business_documents
    )

    retriever = SchemaRetriever()

    results = evaluate_retriever(
        retriever=retriever,
        documents=documents,
        cases=EVALUATION_CASES,
        k=5,
    )

    assert len(results) == len(
        EVALUATION_CASES
    )

    print("\n")
    print("=" * 70)
    print("RETRIEVAL EVALUATION")
    print("=" * 70)

    for result in results:

        print("\nQuestion:")
        print(result["question"])

        print(
            f"Hit@5: {result['hit_at_k']}"
        )

        print(
            f"Recall@5: "
            f"{result['recall_at_k']:.2f}"
        )

        print("Retrieved documents:")

        for document_id in result[
            "retrieved_documents"
        ]:
            print(
                f"  - {document_id}"
            )

    hit_rate = sum(
        result["hit_at_k"]
        for result in results
    ) / len(results)

    average_recall = sum(
        result["recall_at_k"]
        for result in results
    ) / len(results)

    print("\n")
    print("-" * 70)
    print(
        f"Overall Hit@5: "
        f"{hit_rate:.2%}"
    )
    print(
        f"Average Recall@5: "
        f"{average_recall:.2%}"
    )
    print("=" * 70)

    assert hit_rate > 0.0

    engine.dispose()