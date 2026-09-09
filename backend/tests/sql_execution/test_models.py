import pytest
from pydantic import ValidationError

from app.sql_execution.models import ExecutionRequest, ExecutionResult


def test_valid_execution_models():
    request = ExecutionRequest(sql="SELECT 1", max_rows=10, timeout=1.5)
    result = ExecutionResult(success=True, columns=["value"], rows=[{"value": 1}], row_count=1)

    assert request.dialect == "postgresql"
    assert result.model_dump(mode="json")["rows"] == [{"value": 1}]


@pytest.mark.parametrize("sql", ["", "   "])
def test_empty_sql_is_rejected(sql):
    with pytest.raises(ValidationError):
        ExecutionRequest(sql=sql)


@pytest.mark.parametrize("max_rows", [0, -1, 10_001])
def test_invalid_row_limit_is_rejected(max_rows):
    with pytest.raises(ValidationError):
        ExecutionRequest(sql="SELECT 1", max_rows=max_rows)
