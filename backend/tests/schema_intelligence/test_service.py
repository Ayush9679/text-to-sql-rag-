import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from app.schema_intelligence.models import DatabaseSchema
from app.schema_intelligence.service import (
    SchemaIntelligenceService,
)


load_dotenv()


def create_test_engine():
    database_url = (
        f"postgresql+psycopg://"
        f"{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )

    return create_engine(database_url)


def test_get_schema():
    engine = create_test_engine()

    service = SchemaIntelligenceService(
        engine
    )

    schema = service.get_schema(
        "analytics"
    )

    assert isinstance(
        schema,
        DatabaseSchema,
    )

    assert schema.schema_name == "analytics"

    table_names = {
        table.name
        for table in schema.tables
    }

    expected_tables = {
        "categories",
        "customers",
        "suppliers",
        "products",
        "orders",
        "order_items",
        "payments",
        "reviews",
    }

    assert table_names == expected_tables