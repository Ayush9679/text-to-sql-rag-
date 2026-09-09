from app.schema_intelligence.models import (
    ColumnMetadata,
    PrimaryKeyMetadata,
    ForeignKeyMetadata,
    TableMetadata,
)

from app.schema_retrieval.serializer import (
    SchemaSerializer,
)
from app.schema_intelligence.models import (
    DatabaseSchema,
)

from app.schema_retrieval.documents import (
    SchemaDocumentBuilder,
)


def test_serialize_table():
    table = TableMetadata(
        name="customers",
        columns=[
            ColumnMetadata(
                name="customer_id",
                data_type="BIGINT",
                nullable=False,
            ),
            ColumnMetadata(
                name="email",
                data_type="VARCHAR",
                nullable=False,
            ),
        ],
        primary_key=PrimaryKeyMetadata(
            name="customers_pkey",
            columns=["customer_id"],
        ),
    )

    serializer = SchemaSerializer()

    result = serializer.serialize_table(
        table
    )

    assert "TABLE: customers" in result
    assert "customer_id" in result
    assert "email" in result
    assert "PRIMARY KEY:" in result

def test_build_schema_documents():
    schema = DatabaseSchema(
        schema_name="analytics",
        tables=[
            TableMetadata(
                name="customers",
                columns=[
                    ColumnMetadata(
                        name="customer_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                ],
                primary_key=PrimaryKeyMetadata(
                    name="customers_pkey",
                    columns=["customer_id"],
                ),
            ),
            TableMetadata(
                name="products",
                columns=[
                    ColumnMetadata(
                        name="product_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                ],
            ),
        ],
    )

    serializer = SchemaSerializer()

    builder = SchemaDocumentBuilder(
        serializer
    )

    documents = builder.build_documents(
        schema
    )

    assert len(documents) == 2

    assert documents[0].document_id == (
        "analytics.customers"
    )

    assert documents[0].table_name == "customers"

    assert "TABLE: customers" in (
        documents[0].content
    )

    assert documents[1].document_id == (
        "analytics.products"
    )

def test_serialize_relationships():
    table = TableMetadata(
        name="orders",
        columns=[
            ColumnMetadata(
                name="order_id",
                data_type="BIGINT",
                nullable=False,
            ),
            ColumnMetadata(
                name="customer_id",
                data_type="BIGINT",
                nullable=False,
            ),
        ],
        primary_key=PrimaryKeyMetadata(
            name="orders_pkey",
            columns=["order_id"],
        ),
        foreign_keys=[
            ForeignKeyMetadata(
                name="orders_customer_id_fkey",
                columns=["customer_id"],
                referred_table="customers",
                referred_columns=["customer_id"],
            )
        ],
    )

    serializer = SchemaSerializer()

    result = serializer.serialize_table(table)

    assert "RELATIONSHIPS:" in result

    assert (
        "orders.customer_id -> customers.customer_id"
        in result
    )