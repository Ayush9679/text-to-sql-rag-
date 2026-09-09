from app.sql_generation.validator import (
    SQLValidator,
)


def test_valid_select():

    validator = SQLValidator()

    result = validator.validate(
        "SELECT * FROM analytics.customers;"
    )

    assert result.valid is True
    assert result.errors == ()


def test_valid_select_without_semicolon():

    validator = SQLValidator()

    result = validator.validate(
        "SELECT customer_id "
        "FROM analytics.customers"
    )

    assert result.valid is True


def test_valid_cte():

    validator = SQLValidator()

    sql = (
        "WITH customer_counts AS ("
        " SELECT customer_id, COUNT(*) "
        " FROM analytics.orders "
        " GROUP BY customer_id"
        ") "
        "SELECT * FROM customer_counts;"
    )

    result = validator.validate(sql)

    assert result.valid is True


def test_empty_sql_rejected():

    validator = SQLValidator()

    result = validator.validate("")

    assert result.valid is False

    assert (
        "SQL statement is empty."
        in result.errors
    )


def test_insert_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "INSERT INTO customers VALUES (1);"
    )

    assert result.valid is False


def test_update_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "UPDATE customers SET name = 'John';"
    )

    assert result.valid is False


def test_delete_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "DELETE FROM customers;"
    )

    assert result.valid is False


def test_drop_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "DROP TABLE customers;"
    )

    assert result.valid is False


def test_truncate_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "TRUNCATE TABLE customers;"
    )

    assert result.valid is False


def test_multiple_statements_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "SELECT * FROM customers; "
        "DROP TABLE customers;"
    )

    assert result.valid is False

    assert any(
        "Multiple SQL statements"
        in error
        for error in result.errors
    )


def test_select_without_from_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "SELECT;"
    )

    assert result.valid is False


def test_non_sql_statement_rejected():

    validator = SQLValidator()

    result = validator.validate(
        "Hello this is not SQL."
    )

    assert result.valid is False