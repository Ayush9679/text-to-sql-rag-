from app.schema_intelligence.models import (
    DatabaseSchema,
    TableMetadata,
    ColumnMetadata,
)

from app.sql_generation.schema_validator import (
    SchemaAwareSQLValidator,
)


def build_schema():

    customers = TableMetadata(
        name="analytics.customers",
        columns=[
            ColumnMetadata(
                name="customer_id",
                data_type="BIGINT",
                nullable=False,
            ),
            ColumnMetadata(
                name="first_name",
                data_type="VARCHAR",
                nullable=True,
            ),
            ColumnMetadata(
                name="signup_date",
                data_type="DATE",
                nullable=True,
            ),
        ],
    )

    orders = TableMetadata(
        name="analytics.orders",
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
    )
    return DatabaseSchema(
    schema_name="analytics",
    tables=[
        customers,
        orders,
    ],
    )


def test_valid_table_and_columns():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        """
        SELECT customer_id, signup_date
        FROM analytics.customers;
        """,
        build_schema(),
    )

    assert result.valid is True
    assert result.errors == ()


def test_unknown_table():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        """
        SELECT customer_id
        FROM analytics.products;
        """,
        build_schema(),
    )

    assert result.valid is False

    assert any(
        "Unknown table"
        in error
        for error in result.errors
    )


def test_unknown_column():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        """
        SELECT customer_name
        FROM analytics.customers;
        """,
        build_schema(),
    )

    assert result.valid is False

    assert any(
        "Unknown column"
        in error
        for error in result.errors
    )


def test_table_alias():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        """
        SELECT c.customer_id
        FROM analytics.customers AS c;
        """,
        build_schema(),
    )

    assert result.valid is True


def test_select_aggregate_alias_is_allowed_in_order_by():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        """
        SELECT customer_id, COUNT(order_id) AS total_orders
        FROM analytics.orders
        GROUP BY customer_id
        ORDER BY total_orders ASC
        LIMIT 2;
        """,
        build_schema(),
    )

    assert result.valid is True


def test_unknown_alias():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        """
        SELECT x.customer_id
        FROM analytics.customers AS c;
        """,
        build_schema(),
    )

    assert result.valid is False


def test_unknown_sql():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        "THIS IS NOT SQL",
        build_schema(),
    )

    assert result.valid is False


def test_empty_sql():

    validator = SchemaAwareSQLValidator()

    result = validator.validate(
        "",
        build_schema(),
    )

    assert result.valid is False
