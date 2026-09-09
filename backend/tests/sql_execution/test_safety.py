import pytest

from app.sql_execution.safety import SQLExecutionSafetyValidator


@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "WITH customers AS (SELECT 1 AS id) SELECT id FROM customers",
])
def test_read_only_queries_are_allowed(sql):
    assert SQLExecutionSafetyValidator().validate(sql).valid is True


@pytest.mark.parametrize("sql", [
    "INSERT INTO customers VALUES (1)", "UPDATE customers SET id = 1",
    "DELETE FROM customers", "DROP TABLE customers", "ALTER TABLE customers ADD id INT",
    "TRUNCATE TABLE customers", "CREATE TABLE customers (id INT)",
    "GRANT SELECT ON customers TO public", "REVOKE SELECT ON customers FROM public",
    "SELECT 1; DELETE FROM customers", "  dElEtE FROM customers  ", "CALL cleanup()",
    "WITH removed AS (DELETE FROM customers RETURNING customer_id) SELECT * FROM removed",
    "WITH changed AS (UPDATE customers SET id = 1 RETURNING id) SELECT * FROM changed",
    "SELECT * FROM customers FOR UPDATE", "SELECT * INTO archive FROM customers",
])
def test_non_read_only_sql_is_rejected(sql):
    assert SQLExecutionSafetyValidator().validate(sql).valid is False
