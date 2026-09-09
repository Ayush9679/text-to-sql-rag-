from sqlalchemy import create_engine, text

from app.sql_execution.service import SQLExecutionService


def test_read_only_execution_flow_end_to_end():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE customers (customer_id INTEGER, first_name TEXT)"))
        connection.execute(text("INSERT INTO customers VALUES (1, 'Ayush')"))

    result = SQLExecutionService(engine=engine).execute(
        "SELECT customer_id, first_name FROM customers LIMIT 10"
    )

    assert result.success is True
    assert result.columns == ["customer_id", "first_name"]
    assert result.rows == [{"customer_id": 1, "first_name": "Ayush"}]
    assert result.row_count == 1
    assert result.truncated is False
