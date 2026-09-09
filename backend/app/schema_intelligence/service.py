from sqlalchemy.engine import Engine

from .extractor import SchemaExtractor
from .inspector import PostgreSQLSchemaInspector
from .models import DatabaseSchema


class SchemaIntelligenceService:
    def __init__(self, engine: Engine):
        self.inspector = PostgreSQLSchemaInspector(
            engine
        )

        self.extractor = SchemaExtractor(
            self.inspector
        )

    def get_schema(
        self,
        schema: str,
    ) -> DatabaseSchema:
        return self.extractor.extract_schema(
            schema=schema
        )