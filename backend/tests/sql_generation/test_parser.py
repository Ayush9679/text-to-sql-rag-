import pytest

from app.sql_generation.parser import (
    SQLParseError,
    SQLResponseParser,
)


def test_parse_plain_sql():
    parser = SQLResponseParser()

    result = parser.parse(
        "SELECT * FROM analytics.customers;"
    )

    assert result == (
        "SELECT * FROM analytics.customers;"
    )


def test_parse_markdown_sql():
    parser = SQLResponseParser()

    response = (
        "Here is the SQL:\n\n"
        "```sql\n"
        "SELECT *\n"
        "FROM analytics.customers\n"
        "LIMIT 10;\n"
        "```"
    )

    result = parser.parse(response)

    assert result == (
        "SELECT * FROM analytics.customers LIMIT 10;"
    )


def test_parse_postgresql_code_block():
    parser = SQLResponseParser()

    response = (
        "```postgresql\n"
        "SELECT customer_id\n"
        "FROM analytics.customers\n"
        "LIMIT 10\n"
        "```"
    )

    result = parser.parse(response)

    assert result == (
        "SELECT customer_id "
        "FROM analytics.customers "
        "LIMIT 10;"
    )


def test_parse_sql_prefix():
    parser = SQLResponseParser()

    response = (
        "SQL:\n\n"
        "SELECT *\n"
        "FROM analytics.customers\n"
        "LIMIT 10"
    )

    result = parser.parse(response)

    assert result == (
        "SELECT * FROM analytics.customers LIMIT 10;"
    )


def test_parse_query_prefix():
    parser = SQLResponseParser()

    response = (
        "Query:\n\n"
        "SELECT customer_id\n"
        "FROM analytics.customers"
    )

    result = parser.parse(response)

    assert result == (
        "SELECT customer_id "
        "FROM analytics.customers;"
    )


def test_parse_with_cte():
    parser = SQLResponseParser()

    response = (
        "```sql\n"
        "WITH customer_counts AS (\n"
        "    SELECT customer_id, COUNT(*) AS orders\n"
        "    FROM analytics.orders\n"
        "    GROUP BY customer_id\n"
        ")\n"
        "SELECT *\n"
        "FROM customer_counts;\n"
        "```"
    )

    result = parser.parse(response)

    assert result.startswith(
        "WITH customer_counts"
    )

    assert result.endswith(";")

    assert "COUNT(*)" in result


def test_semicolon_is_added():
    parser = SQLResponseParser()

    result = parser.parse(
        "SELECT * FROM analytics.customers"
    )

    assert result.endswith(";")


def test_empty_response_rejected():
    parser = SQLResponseParser()

    with pytest.raises(SQLParseError):
        parser.parse("")


def test_whitespace_response_rejected():
    parser = SQLResponseParser()

    with pytest.raises(SQLParseError):
        parser.parse("   ")


def test_non_sql_response_rejected():
    parser = SQLResponseParser()

    with pytest.raises(SQLParseError):
        parser.parse(
            "I cannot generate SQL."
        )