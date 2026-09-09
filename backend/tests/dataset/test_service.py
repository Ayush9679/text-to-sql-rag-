from types import SimpleNamespace

import pytest
from sqlalchemy.sql.dml import Insert

from app.dataset.service import DatasetError, DatasetIngestionService, normalize_identifier, tenant_schema_name
from app.sql_generation.schema_validator import SchemaAwareSQLValidator
from app.schema_intelligence.models import ColumnMetadata, DatabaseSchema, TableMetadata


class _Connection:
    def __init__(self, engine):
        self.engine = engine
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement, parameters=None):
        self.executions.append((statement, parameters))


class _Dialect:
    name = "postgresql"

    def __init__(self, engine):
        self.engine = engine

    def has_table(self, _connection, table_name, schema=None):
        return (schema, table_name) in self.engine.tables


class _Engine:
    def __init__(self):
        self.tables = set()
        self.connection = _Connection(self)
        self.dialect = _Dialect(self)

    def begin(self):
        return self.connection


@pytest.fixture
def ingestion(monkeypatch):
    engine = _Engine()

    def create(table, connection):
        connection.engine.tables.add((table.schema, table.name))

    monkeypatch.setattr("app.dataset.service.Table.create", create)
    return DatasetIngestionService(engine, batch_size=2), engine


def test_ingests_csv_with_safe_identifiers_types_and_parameterized_batches(ingestion):
    service, engine = ingestion

    result = service.ingest_csv(
        tenant_id="Acme West",
        filename="Customer Orders.csv",
        content=b"Customer ID,Order Value,Active,Placed At\n1,1299.50,true,2026-08-20T08:30:00\n2,500.00,false,2026-08-21T09:00:00\n3,3.00,true,2026-08-22T10:00:00\n",
    )

    assert result.schema_name == "tenant_acme_west"
    assert result.table_name == "customer_orders"
    assert result.row_count == 3
    assert [(column.database_name, column.postgres_type) for column in result.columns] == [
        ("customer_id", "INTEGER"), ("order_value", "NUMERIC"), ("active", "BOOLEAN"), ("placed_at", "TIMESTAMP"),
    ]
    inserts = [(statement, values) for statement, values in engine.connection.executions if isinstance(statement, Insert)]
    assert [len(values) for _, values in inserts] == [2, 1]
    assert inserts[0][1][0]["order_value"].as_tuple().digits == (1, 2, 9, 9, 5, 0)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"", "empty"),
        (b"name,age\n\"unclosed,1\n", "malformed"),
        (b"name,name\nA,B\n", "unique"),
        (b"name,\nA,B\n", "cannot be empty"),
        (b"name,age\nA\n", "same number"),
        (b"name\n\xff\n", "UTF-8"),
        (b"name,age\n", "at least one data row"),
    ],
)
def test_csv_validation_failures_are_controlled(ingestion, content, message):
    service, _ = ingestion
    with pytest.raises(DatasetError, match=message):
        service.ingest_csv(tenant_id="acme", filename="people.csv", content=content)


def test_duplicate_table_is_rejected_without_overwrite(ingestion):
    service, _ = ingestion
    content = b"id,name\n1,A\n"
    service.ingest_csv(tenant_id="acme", filename="customers.csv", content=content)
    with pytest.raises(DatasetError, match="already exists"):
        service.ingest_csv(tenant_id="acme", filename="customers.csv", content=content)


def test_identifier_normalization_and_tenant_schema_isolation():
    assert normalize_identifier("DROP TABLE users;", prefix="column") == "drop_table_users"
    assert normalize_identifier("123", prefix="table") == "table_123"
    assert tenant_schema_name("business A") != tenant_schema_name("business B")
    with pytest.raises(DatasetError):
        normalize_identifier("!!!", prefix="column")


def test_different_tenant_schema_cannot_be_referenced_by_generated_sql():
    schema = DatabaseSchema(
        schema_name="tenant_acme",
        tables=[TableMetadata(name="customers", columns=[ColumnMetadata(name="id", data_type="INTEGER", nullable=True)])],
    )
    result = SchemaAwareSQLValidator().validate("SELECT id FROM tenant_other.customers", schema)
    assert not result.valid
    assert "outside the active schema" in result.errors[0]

