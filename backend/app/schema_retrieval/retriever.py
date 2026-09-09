from pydantic import BaseModel

from app.schema_retrieval.documents import (
    KnowledgeDocument,
    SchemaDocument,
)

from app.schema_retrieval.scorer import (
    RelevanceScorer,
)


class RetrievalResult(BaseModel):
    document_id: str
    source_type: str
    title: str
    content: str
    score: float


class SchemaRetriever:

    def __init__(
        self,
        scorer: RelevanceScorer | None = None,
    ):
        self.scorer = scorer or RelevanceScorer()

    def retrieve(
        self,
        query: str,
        documents: list[
            SchemaDocument | KnowledgeDocument
        ],
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        query_terms = set(
            query.lower().split()
        )

        results=[]

        for document in documents:

            score = self.scorer.score(
                query=query,
                content=document.content,
            )

            if score <= 0:
                continue

            if isinstance(
                document,
                SchemaDocument,
            ):
                source_type = "schema"
                title = document.table_name
            else:
                source_type = document.source_type
                title = document.title

            results.append(
                RetrievalResult(
                    document_id=document.document_id,
                    source_type=source_type,
                    title=title,
                    content=document.content,
                    score=score,
                )
            )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:top_k]