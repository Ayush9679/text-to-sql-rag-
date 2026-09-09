from dataclasses import dataclass

from app.sql_generation.models import (
    SQLGenerationRequest,
)

from app.sql_generation.service import (
    SQLGenerationService,
)

from app.sql_generation.groq_client import (
    GroqClientError,
)

from app.schema_intelligence.models import (
    DatabaseSchema,
    TableMetadata,
    ColumnMetadata,
)


@dataclass
class FakeGroqClient:

    response: str

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_completion_tokens: int = 2048,
    ) -> str:

        return self.response


class FailingGroqClient:

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_completion_tokens: int = 2048,
    ) -> str:

        raise GroqClientError(
            "Groq is unavailable.",
            retryable=False,
        )


@dataclass
class SequentialFakeGroqClient:

    responses: list[str]

    def __post_init__(self):
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_completion_tokens: int = 2048,
    ) -> str:

        self.prompts.append(prompt)
        return self.responses.pop(0)


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

    return DatabaseSchema(
        schema_name="analytics",
        tables=[
            customers,
        ],
    )


def test_successful_generation():

    client = FakeGroqClient(
        response=(
            "```sql\n"
            "SELECT customer_id "
            "FROM analytics.customers "
            "LIMIT 10;\n"
            "```"
        )
    )

    service = SQLGenerationService(
        groq_client=client,
    )

    request = SQLGenerationRequest(
        query="Return 10 customers",
    )

    result = service.generate(
        request,
        build_schema(),
    )

    assert result.sql == (
        "SELECT customer_id "
        "FROM analytics.customers "
        "LIMIT 10;"
    )

    assert result.dialect == "postgresql"

    assert result.confidence == 1.0

    assert (
        "analytics.customers"
        in result.tables_used
    )


def test_parser_failure():

    client = FakeGroqClient(
        response="I cannot generate SQL."
    )

    service = SQLGenerationService(
        groq_client=client,
    )

    request = SQLGenerationRequest(
        query="Return customers",
    )

    result = service.generate(
        request,
        build_schema(),
    )

    assert result.sql == ""

    assert result.confidence == 0.0

    assert (
        result.explanation is not None
    )


def test_unsafe_sql_rejected():

    client = FakeGroqClient(
        response=(
            "SELECT customer_id "
            "FROM analytics.customers; "
            "DELETE FROM analytics.customers;"
        )
    )

    service = SQLGenerationService(
        groq_client=client,
    )

    request = SQLGenerationRequest(
        query="Delete customers",
    )

    result = service.generate(
        request,
        build_schema(),
    )

    assert result.confidence == 0.0

    assert (
        result.explanation is not None
    )

    assert (
        "validation"
        in result.explanation.lower()
    )


def test_groq_failure_returns_controlled_result():

    service = SQLGenerationService(
        groq_client=FailingGroqClient(),
    )

    result = service.generate(
        SQLGenerationRequest(query="Return customers"),
        build_schema(),
    )

    assert result.sql == ""
    assert result.confidence == 0.0
    assert result.explanation == (
        "SQL generation failed: Groq is unavailable."
    )


def test_schema_failure_is_recovered_by_a_valid_retry():

    client = SequentialFakeGroqClient([
        "SELECT customer_name FROM analytics.customers LIMIT 10;",
        "SELECT customer_id FROM analytics.customers LIMIT 10;",
    ])
    service = SQLGenerationService(groq_client=client)

    result = service.generate(
        SQLGenerationRequest(query="Return 10 customers"),
        build_schema(),
    )

    assert result.confidence == 1.0
    assert "customer_id" in result.sql
    assert "analytics.customers" in result.tables_used
    assert len(client.prompts) == 2


def test_two_failures_then_success_are_bounded_to_three_calls():

    client = SequentialFakeGroqClient([
        "SELECT customer_name FROM analytics.customers;",
        "SELECT customer_id FROM analytics.orders;",
        "SELECT customer_id FROM analytics.customers;",
    ])
    service = SQLGenerationService(groq_client=client)

    result = service.generate(
        SQLGenerationRequest(query="Return customers"),
        build_schema(),
    )

    assert result.confidence == 1.0
    assert len(client.prompts) == 3


def test_retries_exhausted_returns_controlled_failure():

    client = SequentialFakeGroqClient([
        "SELECT customer_name FROM analytics.customers;",
        "SELECT customer_name FROM analytics.customers;",
        "SELECT customer_name FROM analytics.customers;",
    ])
    service = SQLGenerationService(groq_client=client)

    result = service.generate(
        SQLGenerationRequest(query="Return customers"),
        build_schema(),
    )

    assert result.confidence == 0.0
    assert isinstance(result.sql, str)
    assert result.explanation is not None
    assert len(client.prompts) == 3


def test_parser_failure_is_recovered():

    client = SequentialFakeGroqClient([
        "I cannot generate SQL.",
        "SELECT customer_id FROM analytics.customers LIMIT 10;",
    ])
    service = SQLGenerationService(groq_client=client)

    result = service.generate(
        SQLGenerationRequest(query="Return customers"),
        build_schema(),
    )

    assert result.confidence == 1.0
    assert len(client.prompts) == 2


def test_unsafe_sql_is_recovered_by_a_valid_retry():

    client = SequentialFakeGroqClient([
        "DELETE FROM analytics.customers;",
        "SELECT customer_id FROM analytics.customers LIMIT 10;",
    ])
    service = SQLGenerationService(groq_client=client)

    result = service.generate(
        SQLGenerationRequest(query="Return customers"),
        build_schema(),
    )

    assert result.confidence == 1.0
    assert len(client.prompts) == 2


def test_schema_failure_feedback_is_sent_to_recovery_prompt():

    client = SequentialFakeGroqClient([
        "SELECT customer_name FROM analytics.customers;",
        "SELECT customer_id FROM analytics.customers;",
    ])
    service = SQLGenerationService(groq_client=client)
    request = SQLGenerationRequest(
        query="Return customers",
        schema_context="TABLE: analytics.customers (customer_id)",
    )

    result = service.generate(request, build_schema())

    assert result.confidence == 1.0
    retry_prompt = client.prompts[1]
    assert request.query in retry_prompt
    assert "SELECT customer_name FROM analytics.customers;" in retry_prompt
    assert "Unknown column: customer_name" in retry_prompt
    assert request.schema_context in retry_prompt


def test_recovery_state_is_reset_between_generation_requests():

    client = SequentialFakeGroqClient([
        "SELECT customer_name FROM analytics.customers;",
        "SELECT customer_id FROM analytics.customers;",
        "SELECT customer_name FROM analytics.customers;",
        "SELECT customer_id FROM analytics.customers;",
    ])
    service = SQLGenerationService(groq_client=client)
    request = SQLGenerationRequest(query="Return customers")

    first = service.generate(request, build_schema())
    second = service.generate(request, build_schema())

    assert first.confidence == second.confidence == 1.0
    assert len(client.prompts) == 4
    assert service.recovery_manager.attempt_count == 1


def test_generation_never_uses_database_execution_apis():

    class ExecutionForbiddenClient(FakeGroqClient):

        def execute(self, *args, **kwargs):
            raise AssertionError("SQL must never be executed")

        def executemany(self, *args, **kwargs):
            raise AssertionError("SQL must never be executed")

    service = SQLGenerationService(
        groq_client=ExecutionForbiddenClient(
            response="SELECT customer_id FROM analytics.customers;"
        ),
    )

    result = service.generate(
        SQLGenerationRequest(query="Return customers"),
        build_schema(),
    )

    assert result.confidence == 1.0


def test_unknown_table_rejected():

    client = FakeGroqClient(
        response=(
            "SELECT customer_id "
            "FROM analytics.orders;"
        )
    )

    service = SQLGenerationService(
        groq_client=client,
    )

    request = SQLGenerationRequest(
        query="Return orders",
    )

    result = service.generate(
        request,
        build_schema(),
    )

    assert result.confidence == 0.0

    assert result.explanation is not None

    assert (
        "Unknown table"
        in result.explanation
    )


def test_unknown_column_rejected():

    client = FakeGroqClient(
        response=(
            "SELECT customer_name "
            "FROM analytics.customers;"
        )
    )

    service = SQLGenerationService(
        groq_client=client,
    )

    request = SQLGenerationRequest(
        query="Return customer names",
    )

    result = service.generate(
        request,
        build_schema(),
    )

    assert result.confidence == 0.0

    assert result.explanation is not None

    assert (
        "Unknown column"
        in result.explanation
    )
