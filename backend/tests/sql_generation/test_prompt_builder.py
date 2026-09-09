from app.sql_generation.models import (
    SQLGenerationRequest,
)

from app.sql_generation.prompt_builder import (
    SQLPromptBuilder,
)


def test_build_basic_sql_prompt():

    request = SQLGenerationRequest(
        query="Return 10 customers",
        intent="customer_analysis",
        entities=["customers"],
        limit=10,
        schema_context=(
            "TABLE: analytics.customers\n"
            "COLUMNS:\n"
            "- customer_id\n"
            "- first_name\n"
            "- last_name"
        ),
    )

    builder = SQLPromptBuilder()

    system_prompt, user_prompt = (
        builder.build(request)
    )

    assert (
        "PostgreSQL"
        in system_prompt
    )

    assert (
        "Return 10 customers"
        in user_prompt
    )

    assert (
        "analytics.customers"
        in user_prompt
    )

    assert (
        "customer_analysis"
        in user_prompt
    )

    assert (
        "Limit: 10"
        in user_prompt
    )


def test_build_prompt_with_business_context():

    request = SQLGenerationRequest(
        query=(
            "Show the top 10 "
            "customers by spending"
        ),
        intent="customer_analysis",
        entities=["customers"],
        metrics=["total_spending"],
        aggregation="sum",
        sort_direction="desc",
        limit=10,
        schema_context=(
            "TABLE: analytics.customers\n"
            "TABLE: analytics.orders\n"
            "TABLE: analytics.order_items"
        ),
        business_context=(
            "Customer spending equals "
            "SUM(quantity * unit_price)."
        ),
    )

    builder = SQLPromptBuilder()

    _, user_prompt = builder.build(
        request
    )

    assert (
        "total_spending"
        in user_prompt
    )

    assert (
        "sum"
        in user_prompt
    )

    assert (
        "desc"
        in user_prompt
    )

    assert (
        "Customer spending equals"
        in user_prompt
    )

    assert (
        "analytics.order_items"
        in user_prompt
    )


def test_empty_context_is_handled():

    request = SQLGenerationRequest(
        query="Return customers",
    )

    builder = SQLPromptBuilder()

    _, user_prompt = builder.build(
        request
    )

    assert (
        "No schema context provided."
        in user_prompt
    )

    assert (
        "No business knowledge provided."
        in user_prompt
    )


def test_prompt_forces_select_only():

    request = SQLGenerationRequest(
        query="Return 10 customers",
    )

    builder = SQLPromptBuilder()

    system_prompt, _ = (
        builder.build(request)
    )

    assert (
        "SELECT"
        in system_prompt
    )

    assert (
        "INSERT"
        in system_prompt
    )

    assert (
        "UPDATE"
        in system_prompt
    )

    assert (
        "DELETE"
        in system_prompt
    )

    assert (
        "DROP"
        in system_prompt
    )


def test_markdown_is_forbidden():

    builder = SQLPromptBuilder()

    assert (
        "Markdown code fences"
        in builder.SYSTEM_PROMPT
    )