from dataclasses import dataclass

from app.application.models import QueryRequest, QueryStatus
from app.application.service import ApplicationQueryService
from app.clarification.models import ClarificationDecision, ClarificationQuestion, ClarificationState, QueryAnalysis
from app.schema_intelligence.models import ColumnMetadata, DatabaseSchema, TableMetadata
from app.schema_retrieval.context import RAGContext
from app.schema_retrieval.documents import SchemaDocument
from app.schema_retrieval.retriever import RetrievalResult
from app.sql_execution.models import ExecutionResult
from app.sql_generation.models import SQLGenerationResult


def schema():
    return DatabaseSchema(
        schema_name="analytics",
        tables=[TableMetadata(name="customers", columns=[ColumnMetadata(name="customer_id", data_type="INTEGER", nullable=False)])],
    )


DOCUMENTS = [SchemaDocument(
    document_id="analytics.customers", schema_name="analytics", table_name="customers", content="TABLE: customers"
)]


class FakeClarificationEngine:
    def __init__(self, calls, action="proceed"):
        self.calls, self.action = calls, action

    def process_query(self, query, conversation_id=None):
        self.calls.append("clarification")
        analysis = QueryAnalysis(query=query, intent="customer_analysis", entities=["customers"], metrics=["count"])
        state = ClarificationState(conversation_id=conversation_id or "test", original_query=query, current_query=query, analysis=analysis)
        decision = ClarificationDecision(action=self.action, reason=f"{self.action} decision")
        question = ClarificationQuestion(question="What metric?", reason="Missing metric", target_field="metric") if self.action == "clarify" else None
        return state, decision, question


class FakeRetrievalService:
    def __init__(self, calls, error=False):
        self.calls, self.error = calls, error

    def retrieve_context(self, **kwargs):
        self.calls.append("retrieval")
        if self.error:
            raise RuntimeError("not exposed")
        return RAGContext(query=kwargs["query"], documents=[RetrievalResult(document_id="analytics.customers", source_type="schema", title="customers", content="TABLE: customers", score=1.0)])


class FakeGenerationService:
    def __init__(self, calls, result):
        self.calls, self.result = calls, result

    def generate(self, request, schema):
        self.calls.append("generation")
        return self.result


class FakeExecutionService:
    def __init__(self, calls, result):
        self.calls, self.result, self.requests = calls, result, []

    def execute(self, request):
        self.calls.append("execution")
        self.requests.append(request)
        return self.result


def build_service(*, action="proceed", retrieval_error=False, generation=None, execution=None):
    calls = []
    generation = generation or SQLGenerationResult(sql="SELECT COUNT(*) AS count FROM analytics.customers", confidence=1.0, tables_used=["analytics.customers"], columns_used=["customer_id"])
    execution = execution or ExecutionResult(success=True, columns=["count"], rows=[{"count": 2}], row_count=1, execution_time_ms=3.5)
    service = ApplicationQueryService(
        schema=schema(), documents=DOCUMENTS,
        clarification_engine=FakeClarificationEngine(calls, action),
        retrieval_service=FakeRetrievalService(calls, retrieval_error),
        sql_generation_service=FakeGenerationService(calls, generation),
        execution_service=FakeExecutionService(calls, execution),
    )
    return service, calls


def test_service_coordinates_successful_pipeline_in_order():
    service, calls = build_service()
    result = service.handle(QueryRequest(query="How many customers signed up in 2025?", max_rows=10))

    assert result.status == QueryStatus.SUCCESS
    assert calls == ["clarification", "retrieval", "generation", "execution"]
    assert result.rows == [{"count": 2}]
    assert result.metadata["retrieved_document_ids"] == ["analytics.customers"]


def test_clarification_stops_generation_and_execution():
    service, calls = build_service(action="clarify")
    result = service.handle(QueryRequest(query="Show me the best customers."))

    assert result.status == QueryStatus.CLARIFICATION_REQUIRED
    assert result.clarification is not None
    assert calls == ["clarification"]


def test_unsupported_query_stops_pipeline():
    service, calls = build_service(action="unsupported")
    result = service.handle(QueryRequest(query="Do a quantum physics analysis."))

    assert result.status == QueryStatus.FAILED
    assert calls == ["clarification"]


def test_retrieval_failure_stops_generation():
    service, calls = build_service(retrieval_error=True)
    result = service.handle(QueryRequest(query="Return customers"))

    assert result.status == QueryStatus.FAILED
    assert result.explanation == "Schema retrieval failed."
    assert calls == ["clarification", "retrieval"]


def test_generation_failure_stops_execution():
    failed_generation = SQLGenerationResult(sql="", confidence=0.0, explanation="SQL validation failed.")
    service, calls = build_service(generation=failed_generation)
    result = service.handle(QueryRequest(query="Return customers"))

    assert result.status == QueryStatus.FAILED
    assert result.explanation == "SQL validation failed."
    assert calls == ["clarification", "retrieval", "generation"]


def test_execution_failure_is_controlled_and_preserves_sql():
    failed_execution = ExecutionResult(success=False, error="Database execution failed.")
    service, calls = build_service(execution=failed_execution)
    result = service.handle(QueryRequest(query="Return customers"))

    assert result.status == QueryStatus.FAILED
    assert result.sql == "SELECT COUNT(*) AS count FROM analytics.customers"
    assert result.explanation == "Database execution failed."
    assert calls == ["clarification", "retrieval", "generation", "execution"]
