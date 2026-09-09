import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from app.schema_intelligence.inspector import (
    PostgreSQLSchemaInspector,
)
from app.schema_intelligence.extractor import (
    SchemaExtractor,
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


def test_extract_customers_table():
    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine
    )

    extractor = SchemaExtractor(
        inspector
    )

    table = extractor.extract_table(
        schema="analytics",
        table="customers",
    )

    assert table.name == "customers"

    assert table.primary_key is not None

    assert table.primary_key.columns == [
        "customer_id"
    ]

    column_names = {
        column.name
        for column in table.columns
    }

    assert "customer_id" in column_names
    assert "first_name" in column_names
    assert "email" in column_names

    assert isinstance(
        table.foreign_keys,
        list,
    )

    assert isinstance(
        table.check_constraints,
        list,
    )
def test_extract_full_schema():
    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine
    )

    extractor = SchemaExtractor(
        inspector
    )

    database_schema = extractor.extract_schema(
        schema="analytics"
    )

    assert database_schema.schema_name == "analytics"

    table_names = {
        table.name
        for table in database_schema.tables
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