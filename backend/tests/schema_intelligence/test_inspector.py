import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from app.schema_intelligence.inspector import PostgreSQLSchemaInspector


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


def test_get_tables():
    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine
    )

    tables = inspector.get_tables(
        schema="analytics"
    )

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

    assert set(tables) == expected_tables


def test_get_columns():
    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine
    )

    columns = inspector.get_columns(
        schema="analytics",
        table="customers",
    )

    column_names = {
        column["name"]
        for column in columns
    }

    expected_columns = {
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "city",
        "state",
        "country",
        "signup_date",
        "customer_segment",
        "created_at",
    }

    assert column_names == expected_columns

def test_get_primary_key():
    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine
    )

    primary_key = inspector.get_primary_key(
        schema="analytics",
        table="customers",
    )

    print(primary_key)

    assert primary_key["constrained_columns"] == [
        "customer_id"
    ]

def test_get_foreign_keys():
    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine
    )

    foreign_keys = inspector.get_foreign_keys(
        schema="analytics",
        table="orders",
    )

    assert len(foreign_keys) == 1

    foreign_key = foreign_keys[0]

    assert foreign_key["constrained_columns"] == [
        "customer_id"
    ]

    assert foreign_key["referred_table"] == "customers"

    assert foreign_key["referred_columns"] == [
        "customer_id"
    ]
def test_get_check_constraints():
    engine = create_test_engine()

    inspector = PostgreSQLSchemaInspector(
        engine
    )

    constraints = inspector.get_check_constraints(
        schema="analytics",
        table="customers",
    )

    assert len(constraints) > 0

    constraint_sql = " ".join(
        constraint["sqltext"]
        for constraint in constraints
    )

    assert "customer_segment" in constraint_sql
