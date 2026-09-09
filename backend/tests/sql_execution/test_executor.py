import pytest
from sqlalchemy import create_engine, text

from app.sql_execution.executor import SQLExecutionError, SQLExecutor
from app.sql_execution.models import ExecutionRequest


@pytest.fixture
def engine():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE customers (customer_id INTEGER, first_name TEXT)"))
        connection.execute(text("INSERT INTO customers VALUES (1, 'Ayush'), (2, 'Ada')"))
    return engine


def test_executor_fetches_columns_and_rows(engine):
    result = SQLExecutor(engine).execute(ExecutionRequest(sql="SELECT customer_id, first_name FROM customers"))

    assert result.columns == ["customer_id", "first_name"]
    assert len(result.rows) == 2
    assert result.execution_time_ms >= 0


def test_executor_handles_zero_rows_and_row_limit(engine):
    executor = SQLExecutor(engine)
    empty = executor.execute(ExecutionRequest(sql="SELECT customer_id FROM customers WHERE 1 = 0"))
    limited = executor.execute(ExecutionRequest(sql="SELECT customer_id FROM customers", max_rows=1))

    assert empty.rows == []
    assert limited.truncated is True
    assert len(limited.rows) == 1


def test_executor_wraps_database_errors(engine):
    with pytest.raises(SQLExecutionError, match="Database execution failed"):
        SQLExecutor(engine).execute(ExecutionRequest(sql="SELECT missing_column FROM customers"))


def test_unsafe_sql_never_reaches_the_database(engine, monkeypatch):
    executor = SQLExecutor(engine)
    called = False

    def fail_if_connected():
        nonlocal called
        called = True
        raise AssertionError("unsafe SQL must not open a connection")

    monkeypatch.setattr(engine, "connect", fail_if_connected)

    with pytest.raises(SQLExecutionError, match="safety check failed"):
        executor.execute(ExecutionRequest(sql="DELETE FROM customers"))

    assert called is False
