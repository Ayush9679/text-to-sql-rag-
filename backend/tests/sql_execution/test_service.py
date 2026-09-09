from decimal import Decimal

from app.sql_execution.executor import RawExecutionResult, SQLExecutionError
from app.sql_execution.models import ExecutionRequest
from app.sql_execution.service import SQLExecutionService


class FakeExecutor:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.result


def test_service_executes_and_normalizes_results():
    executor = FakeExecutor(RawExecutionResult(
        columns=["amount"], rows=[{"amount": Decimal("12.50")}],
        execution_time_ms=4.2, truncated=False,
    ))
    result = SQLExecutionService(executor=executor).execute(
        ExecutionRequest(sql="SELECT amount FROM invoices", max_rows=5)
    )

    assert result.success is True
    assert result.rows == [{"amount": "12.50"}]
    assert result.execution_time_ms == 4.2
    assert executor.requests[0].max_rows == 5


def test_service_rejects_unsafe_sql_before_executor():
    executor = FakeExecutor()
    result = SQLExecutionService(executor=executor).execute("DELETE FROM customers")

    assert result.success is False
    assert executor.requests == []


def test_service_handles_executor_failure():
    result = SQLExecutionService(executor=FakeExecutor(error=SQLExecutionError("Database execution failed."))).execute(
        "SELECT customer_id FROM customers"
    )

    assert result.success is False
    assert result.error == "Database execution failed."
