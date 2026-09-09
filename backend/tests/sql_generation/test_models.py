import pytest

from pydantic import ValidationError

from app.sql_generation.models import (
    SQLGenerationRequest,
    SQLGenerationResult,
    SQLGenerationError,
)


def test_sql_generation_request():

    request = SQLGenerationRequest(
        query="Return 10 customers",
        intent="customer_analysis",
        entities=["customers"],
        metrics=[],
        filters=[],
        limit=10,
    )

    assert request.query == (
        "Return 10 customers"
    )

    assert request.intent == (
        "customer_analysis"
    )

    assert "customers" in request.entities

    assert request.limit == 10

    assert request.dialect == "postgresql"


def test_sql_generation_request_with_context():

    request = SQLGenerationRequest(
        query=(
            "Give me the top 10 "
            "customers by spending"
        ),

        intent="customer_analysis",

        entities=[
            "customers"
        ],

        metrics=[
            "total_spending"
        ],

        aggregation="sum",

        sort_direction="desc",

        limit=10,

        schema_context=(
            "TABLE: analytics.customers\n"
            "TABLE: analytics.orders\n"
            "TABLE: analytics.order_items"
        ),

        business_context=(
            "Customer spending is "
            "the sum of order item value."
        ),
    )

    assert request.limit == 10

    assert (
        "analytics.customers"
        in request.schema_context
    )

    assert (
        "total_spending"
        in request.metrics
    )

    assert request.aggregation == "sum"

    assert request.sort_direction == "desc"


def test_sql_generation_result():

    result = SQLGenerationResult(
        sql=(
            "SELECT * "
            "FROM analytics.customers "
            "LIMIT 10;"
        ),

        tables_used=[
            "analytics.customers"
        ],

        columns_used=[
            "customer_id"
        ],

        confidence=0.95,
    )

    assert "SELECT" in result.sql

    assert (
        "analytics.customers"
        in result.tables_used
    )

    assert (
        "customer_id"
        in result.columns_used
    )

    assert result.dialect == "postgresql"

    assert 0.0 <= result.confidence <= 1.0


def test_sql_generation_error():

    error = SQLGenerationError(
        error_type="llm_unavailable",
        message="Groq API unavailable",
        retryable=True,
    )

    assert error.error_type == (
        "llm_unavailable"
    )

    assert error.message == (
        "Groq API unavailable"
    )

    assert error.retryable is True


def test_empty_query_rejected():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationRequest(
            query="   "
        )


def test_invalid_limit_rejected():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationRequest(
            query="Return customers",
            limit=-10,
        )


def test_invalid_dialect_rejected():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationRequest(
            query="Return customers",
            dialect="mysql",
        )


def test_empty_sql_is_a_valid_failure_value():

    result = SQLGenerationResult(sql="")

    assert result.sql == ""


def test_confidence_bounds():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(
            sql="SELECT 1",
            confidence=1.5,
        )

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(
            sql="SELECT 1",
            confidence=-0.1,
        )
