from dataclasses import dataclass
from time import perf_counter
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.sql_execution.models import ExecutionRequest
from app.sql_execution.safety import SQLExecutionSafetyValidator


class SQLExecutionError(Exception):
    """Controlled database execution failure without connection details."""


@dataclass(frozen=True)
class RawExecutionResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    execution_time_ms: float
    truncated: bool


class SQLExecutor:
    """Executes one safety-checked read-only query through the supplied engine."""

    def __init__(
        self,
        engine: Engine,
        safety_validator: SQLExecutionSafetyValidator | None = None,
    ):
        self.engine = engine
        self.safety_validator = safety_validator or SQLExecutionSafetyValidator()

    def execute(self, request: ExecutionRequest) -> RawExecutionResult:
        safety = self.safety_validator.validate(request.sql)
        if not safety.valid:
            raise SQLExecutionError("SQL execution safety check failed.")

        started_at = perf_counter()
        try:
            with self.engine.connect() as connection:
                self._enforce_read_only_transaction(connection)
                self._apply_timeout(connection, request.timeout)
                result = connection.execute(text(request.sql), request.parameters)
                columns = list(result.keys())
                mappings = result.mappings().fetchmany(request.max_rows + 1)
        except SQLAlchemyError as exc:
            raise SQLExecutionError("Database execution failed.") from exc
        except Exception as exc:
            raise SQLExecutionError("Database result retrieval failed.") from exc

        truncated = len(mappings) > request.max_rows
        rows = [dict(row) for row in mappings[:request.max_rows]]
        elapsed_ms = (perf_counter() - started_at) * 1000

        return RawExecutionResult(
            columns=columns,
            rows=rows,
            execution_time_ms=elapsed_ms,
            truncated=truncated,
        )

    def _enforce_read_only_transaction(self, connection) -> None:
        """Ask PostgreSQL to reject writes even if an earlier guard is bypassed."""

        if self.engine.dialect.name == "postgresql":
            connection.execute(text("SET TRANSACTION READ ONLY"))

    def _apply_timeout(self, connection, timeout: float | None) -> None:
        """Use PostgreSQL's transaction-local timeout when the engine supports it."""

        if timeout is None or self.engine.dialect.name != "postgresql":
            return

        milliseconds = max(1, round(timeout * 1000))
        connection.execute(
            text("SELECT set_config('statement_timeout', :timeout, true)"),
            {"timeout": f"{milliseconds}ms"},
        )
