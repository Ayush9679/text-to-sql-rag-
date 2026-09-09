from app.schema_retrieval.context import (
    RAGContext,
)
from app.schema_retrieval.documents import (
    KnowledgeDocument,
    SchemaDocument,
)
from app.schema_retrieval.retriever import (
    SchemaRetriever,
)


class SchemaRetrievalService:

    def __init__(
        self,
        retriever: SchemaRetriever | None = None,
    ):
        self.retriever = (
            retriever
            or SchemaRetriever()
        )

    def retrieve_context(
        self,
        query: str,
        documents: list[
            SchemaDocument | KnowledgeDocument
        ],
        top_k: int = 5,
    ) -> RAGContext:

        results = self.retriever.retrieve(
            query=query,
            documents=documents,
            top_k=top_k,
        )

        return RAGContext(
            query=query,
            documents=results,
        )