from app.sql_generation.groq_client import (
    GroqClientError,
    GroqLLMClient,
)

from app.sql_generation.models import (
    SQLGenerationRequest,
    SQLGenerationResult,
)

from app.sql_generation.parser import (
    SQLParseError,
    SQLResponseParser,
)

from app.sql_generation.prompt_builder import (
    SQLPromptBuilder,
)

from app.sql_generation.recovery import (
    SQLRecoveryManager,
)

from app.sql_generation.validator import (
    SQLValidator,
)

from app.sql_generation.schema_validator import (
    SchemaAwareSQLValidator,
)

from app.schema_intelligence.models import (
    DatabaseSchema,
)

import sqlglot
from sqlglot import exp


class SQLGenerationService:
    """
    Orchestrates the complete SQL generation pipeline.

    Pipeline:

        Request
          ↓
        Prompt Builder
          ↓
        Groq LLM
          ↓
        SQL Parser
          ↓
        Safety Validator
          ↓
        Schema Validator
          ↓
        SQLGenerationResult

    This service does NOT execute SQL.
    """

    def __init__(
        self,
        groq_client: GroqLLMClient | None = None,
        prompt_builder: SQLPromptBuilder | None = None,
        parser: SQLResponseParser | None = None,
        validator: SQLValidator | None = None,
        schema_validator: (
            SchemaAwareSQLValidator | None
        ) = None,
        recovery_manager: SQLRecoveryManager | None = None,
    ):

        self.groq_client = (
            groq_client
            or GroqLLMClient()
        )

        self.prompt_builder = (
            prompt_builder
            or SQLPromptBuilder()
        )

        self.parser = (
            parser
            or SQLResponseParser()
        )

        self.validator = (
            validator
            or SQLValidator()
        )

        self.schema_validator = (
            schema_validator
            or SchemaAwareSQLValidator()
        )

        self.recovery_manager = (
            recovery_manager
            or SQLRecoveryManager()
        )

    def generate(
        self,
        request: SQLGenerationRequest,
        schema: DatabaseSchema,
    ) -> SQLGenerationResult:

        # Recovery state belongs to one generation operation, even when the
        # service instance itself is reused.
        self.recovery_manager.reset()

        system_prompt, user_prompt = self.prompt_builder.build(request)
        prompt = user_prompt

        while True:
            try:
                raw_response = self.groq_client.generate(
                    prompt,
                    system_prompt=system_prompt,
                )
            except GroqClientError as exc:
                if not exc.retryable:
                    return self._failure_result(
                        request,
                        f"SQL generation failed: {exc.message}",
                    )

                failure_sql = ""
                errors = ("Retryable Groq generation failure.",)
                failure_explanation = "SQL generation failed: Groq request could not be completed."
            except Exception as exc:
                return self._failure_result(
                    request,
                    "SQL generation failed due to an unexpected "
                    f"{type(exc).__name__}.",
                )
            else:
                try:
                    sql = self.parser.parse(raw_response)
                except SQLParseError as exc:
                    failure_sql = ""
                    errors = (f"SQL parsing failed: {exc.message}",)
                    failure_explanation = errors[0]
                else:
                    validation = self.validator.validate(sql)

                    if not validation.valid:
                        failure_sql = sql
                        errors = validation.errors
                        failure_explanation = (
                            "SQL validation failed: "
                            f"{'; '.join(errors)}"
                        )
                    else:
                        schema_validation = self.schema_validator.validate(
                            sql,
                            schema,
                        )

                        if schema_validation.valid:
                            tables_used, columns_used = self._extract_metadata(sql)

                            return SQLGenerationResult(
                                sql=sql,
                                dialect=request.dialect,
                                tables_used=tables_used,
                                columns_used=columns_used,
                                confidence=1.0,
                                explanation=(
                                    "SQL generated and validated successfully."
                                ),
                            )

                        failure_sql = sql
                        errors = schema_validation.errors
                        failure_explanation = (
                            "Schema validation failed: "
                            f"{'; '.join(errors)}"
                        )

            self.recovery_manager.record_failure(
                sql=failure_sql,
                errors=errors,
            )

            decision = self.recovery_manager.decide()

            if not decision.should_retry:
                return self._failure_result(
                    request,
                    explanation=failure_explanation,
                    sql=failure_sql,
                )

            prompt = self.recovery_manager.build_retry_prompt(
                original_query=request.query,
                sql=failure_sql,
                errors=errors,
                schema_context=request.schema_context,
                business_context=request.business_context,
            )

    def _failure_result(
        self,
        request: SQLGenerationRequest,
        explanation: str,
        sql: str = "",
    ) -> SQLGenerationResult:
        """Create a valid, non-executable result for a failed generation."""

        tables_used, columns_used = self._extract_metadata(sql)

        return SQLGenerationResult(
            sql=sql,
            dialect=request.dialect,
            tables_used=tables_used,
            columns_used=columns_used,
            confidence=0.0,
            explanation=explanation,
        )

    @staticmethod
    def _extract_metadata(sql: str) -> tuple[list[str], list[str]]:
        """Extract unique table and column references without affecting results."""

        if not sql or not sql.strip():
            return [], []

        try:
            expression = sqlglot.parse_one(sql, read="postgres")
        except Exception:
            return [], []

        tables: list[str] = []
        columns: list[str] = []
        seen_tables: set[str] = set()
        seen_columns: set[str] = set()

        for table in expression.find_all(exp.Table):
            table_name = ".".join(
                part
                for part in (table.catalog, table.db, table.name)
                if part
            )
            if table_name and table_name not in seen_tables:
                seen_tables.add(table_name)
                tables.append(table_name)

        for column in expression.find_all(exp.Column):
            column_name = ".".join(
                part
                for part in (column.table, column.name)
                if part
            )
            if column_name and column_name not in seen_columns:
                seen_columns.add(column_name)
                columns.append(column_name)

        return tables, columns
