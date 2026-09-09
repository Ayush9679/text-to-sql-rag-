from pydantic import BaseModel

from app.schema_intelligence.models import DatabaseSchema
from app.schema_retrieval.knowledge import BusinessConcept
from app.schema_retrieval.serializer import SchemaSerializer


class SchemaDocument(BaseModel):
    document_id: str
    schema_name: str
    table_name: str
    content: str


class KnowledgeDocument(BaseModel):
    document_id: str
    source_type: str
    title: str
    content: str


class SchemaDocumentBuilder:

    def __init__(
        self,
        serializer: SchemaSerializer,
    ):
        self.serializer = serializer

    def build_documents(
        self,
        schema: DatabaseSchema,
    ) -> list[SchemaDocument]:

        documents = []

        for table in schema.tables:
            content = self.serializer.serialize_table(
                table
            )

            document = SchemaDocument(
                document_id=(
                    f"{schema.schema_name}.{table.name}"
                ),
                schema_name=schema.schema_name,
                table_name=table.name,
                content=content,
            )

            documents.append(document)

        return documents


def serialize_business_concept(
    concept: BusinessConcept,
) -> str:

    lines = [
        f"CONCEPT: {concept.name}",
        "",
        "DEFINITION:",
        concept.definition,
    ]

    if concept.related_tables:
        lines.extend([
            "",
            "RELATED TABLES:",
        ])

        for table in concept.related_tables:
            lines.append(f"- {table}")

    if concept.related_columns:
        lines.extend([
            "",
            "RELATED COLUMNS:",
        ])

        for column in concept.related_columns:
            lines.append(f"- {column}")

    if concept.calculation:
        lines.extend([
            "",
            "CALCULATION:",
            concept.calculation,
        ])

    return "\n".join(lines)


def build_business_documents(
    concepts: list[BusinessConcept],
) -> list[KnowledgeDocument]:

    documents = []

    for concept in concepts:

        document_id = (
            "concept."
            + concept.name.lower().replace(" ", "_")
        )

        document = KnowledgeDocument(
            document_id=document_id,
            source_type="business",
            title=concept.name,
            content=serialize_business_concept(
                concept
            ),
        )

        documents.append(document)

    return documents