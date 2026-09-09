from app.application.models import QueryRequest, QueryStatus
from app.application.service import ApplicationQueryService
from app.clarification.engine import ClarificationEngine
from app.schema_intelligence.models import ColumnMetadata, DatabaseSchema, TableMetadata
from app.schema_retrieval.context import RAGContext
from app.schema_retrieval.documents import SchemaDocument
from app.schema_retrieval.retriever import RetrievalResult
from app.sql_execution.models import ExecutionResult
from app.sql_generation.models import SQLGenerationResult


class Retrieval:
    def retrieve_context(self, query, documents):
        return RAGContext(query=query, documents=[RetrievalResult(document_id="analytics.customers", source_type="schema", title="customers", content="TABLE: customers", score=1.0)])


class Generator:
    def __init__(self, failed=False):
        self.failed, self.calls = failed, 0

    def generate(self, request, schema):
        self.calls += 1
        if self.failed:
            return SQLGenerationResult(sql="", confidence=0.0, explanation="SQL recovery exhausted.")
        return SQLGenerationResult(sql="SELECT customer_id FROM analytics.customers LIMIT 10", confidence=1.0)


class Executor:
    def __init__(self, failed=False):
        self.failed, self.calls = failed, 0

    def execute(self, request):
        self.calls += 1
        if self.failed:
            return ExecutionResult(success=False, error="Database execution failed.")
        return ExecutionResult(success=True, columns=["customer_id"], rows=[{"customer_id": 1}], row_count=1, execution_time_ms=2.0)


def service(generator=None, executor=None):
    schema = DatabaseSchema(schema_name="analytics", tables=[TableMetadata(name="customers", columns=[ColumnMetadata(name="customer_id", data_type="INTEGER", nullable=False)])])
    return ApplicationQueryService(
        schema=schema,
        documents=[SchemaDocument(document_id="analytics.customers", schema_name="analytics", table_name="customers", content="TABLE: customers")],
        clarification_engine=ClarificationEngine(),
        retrieval_service=Retrieval(),
        sql_generation_service=generator or Generator(),
        execution_service=executor or Executor(),
    )


def test_end_to_end_success():
    result = service().handle(QueryRequest(query="Show the top 10 customers by total spending in 2025."))

    assert result.status == QueryStatus.SUCCESS
    assert result.columns == ["customer_id"]
    assert result.row_count == 1
    assert result.sql is not None


def test_end_to_end_clarification_then_resolution():
    generator, executor = Generator(), Executor()
    app = service(generator, executor)
    initial = app.handle(QueryRequest(query="Show me the best customers."))

    assert initial.status == QueryStatus.CLARIFICATION_REQUIRED
    assert generator.calls == executor.calls == 0

    resolved = app.handle(QueryRequest(
        query="Show me the best customers.",
        clarification_state=initial.clarification_state,
        clarification_answer="Total revenue.",
    ))

    assert resolved.status == QueryStatus.SUCCESS
    assert generator.calls == executor.calls == 1


def test_sql_generation_failure_never_executes():
    generator, executor = Generator(failed=True), Executor()
    result = service(generator, executor).handle(QueryRequest(query="Show the top 10 customers by total spending in 2025."))

    assert result.status == QueryStatus.FAILED
    assert executor.calls == 0


def test_execution_failure_does_not_leak_traceback():
    result = service(executor=Executor(failed=True)).handle(QueryRequest(query="Show the top 10 customers by total spending in 2025."))

    assert result.status == QueryStatus.FAILED
    assert result.explanation == "Database execution failed."
    assert "Traceback" not in result.explanation
