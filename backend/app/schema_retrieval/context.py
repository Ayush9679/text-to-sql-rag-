from pydantic import BaseModel

from app.schema_retrieval.retriever import (
    RetrievalResult,
)


class RAGContext(BaseModel):
    query: str
    documents: list[RetrievalResult]

    @property
    def text(self) -> str:
        sections = [
            "RETRIEVED KNOWLEDGE",
            "",
        ]

        for index, document in enumerate(
            self.documents,
            start=1,
        ):
            sections.extend(
                [
                    f"[DOCUMENT {index}]",
                    f"ID: {document.document_id}",
                    f"SOURCE: {document.source_type}",
                    f"TITLE: {document.title}",
                    f"SCORE: {document.score:.4f}",
                    "",
                    document.content,
                    "",
                    "-" * 60,
                    "",
                ]
            )

        return "\n".join(sections)