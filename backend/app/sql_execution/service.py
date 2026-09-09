from sqlalchemy.engine import Engine

from app.sql_execution.executor import RawExecutionResult, SQLExecutionError, SQLExecutor
from app.sql_execution.models import DEFAULT_MAX_ROWS, ExecutionRequest, ExecutionResult
from app.sql_execution.normalizer import ResultNormalizer
from app.sql_execution.safety import SQLExecutionSafetyValidator


class SQLExecutionService:
    """Safety-checks, executes, and normalizes already-generated read-only SQL."""

    def __init__(
        self,
        engine: Engine | None = None,
        executor: SQLExecutor | None = None,
        safety_validator: SQLExecutionSafetyValidator | None = None,
        normalizer: ResultNormalizer | None = None,
    ):
        if executor is None and engine is None:
            raise ValueError("An engine or executor must be provided.")

        self.safety_validator = safety_validator or SQLExecutionSafetyValidator()
        self.executor = executor or SQLExecutor(
            engine,
            safety_validator=self.safety_validator,
        )
        self.normalizer = normalizer or ResultNormalizer()

    def execute(
        self,
        request: ExecutionRequest | str,
        *,
        parameters: dict | None = None,
        max_rows: int = DEFAULT_MAX_ROWS,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """Execute a request, or construct one from a SQL string, without rewriting SQL."""

        if isinstance(request, str):
            request = ExecutionRequest(
                sql=request,
                parameters=parameters or {},
                max_rows=max_rows,
                timeout=timeout,
            )

        safety = self.safety_validator.validate(request.sql)
        if not safety.valid:
            return self._failure("; ".join(safety.errors))

        try:
            raw_result = self.executor.execute(request)
            rows = self.normalizer.normalize_rows(raw_result.rows)
        except SQLExecutionError as exc:
            return self._failure(str(exc))
        except Exception:
            return self._failure("Database result normalization failed.")

        return ExecutionResult(
            success=True,
            columns=raw_result.columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=raw_result.execution_time_ms,
            truncated=raw_result.truncated,
            error=None,
        )

    @staticmethod
    def _failure(error: str) -> ExecutionResult:
        return ExecutionResult(success=False, error=error)
