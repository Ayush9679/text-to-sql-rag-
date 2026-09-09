from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryAttempt:
    """
    Represents one failed SQL-generation attempt.
    """

    attempt: int
    sql: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryDecision:
    """
    Describes whether another SQL-generation attempt
    should be made.
    """

    should_retry: bool
    next_attempt: int
    reason: str


class SQLRecoveryManager:
    """
    Controls bounded recovery for failed SQL generation.

    Responsibilities:

    - Track failed generation attempts.
    - Decide whether another attempt is allowed.
    - Build structured feedback for the LLM.
    - Prevent infinite retry loops.

    This class does NOT:

    - call Groq
    - parse SQL
    - validate SQL
    - execute SQL
    - modify database state
    """

    DEFAULT_MAX_RETRIES = 2

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        if max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )

        self.max_retries = max_retries

        self._attempts: list[
            RecoveryAttempt
        ] = []

    @property
    def attempts(self) -> tuple[
        RecoveryAttempt,
        ...
    ]:
        """
        Return an immutable view of previous attempts.
        """

        return tuple(self._attempts)

    @property
    def attempt_count(self) -> int:
        """
        Number of failed attempts recorded.
        """

        return len(self._attempts)

    def reset(self) -> None:
        """
        Clear all recorded recovery attempts.
        """

        self._attempts.clear()

    def record_failure(
        self,
        sql: str,
        errors: list[str] | tuple[str, ...],
    ) -> RecoveryAttempt:
        """
        Record a failed SQL-generation attempt.
        """

        attempt = RecoveryAttempt(
            attempt=(
                len(self._attempts) + 1
            ),
            sql=sql,
            errors=tuple(errors),
        )

        self._attempts.append(
            attempt
        )

        return attempt

    def decide(
        self,
    ) -> RecoveryDecision:
        """
        Decide whether another attempt is allowed.

        max_retries represents retries after the
        initial generation attempt.

        Example:

            max_retries = 2

            initial attempt → attempt 1
            retry           → attempt 2
            retry           → attempt 3
            stop
        """

        failed_attempts = len(
            self._attempts
        )

        if failed_attempts <= self.max_retries:

            return RecoveryDecision(
                should_retry=True,
                next_attempt=(
                    failed_attempts + 1
                ),
                reason=(
                    "Another SQL generation "
                    "attempt is permitted."
                ),
            )

        return RecoveryDecision(
            should_retry=False,
            next_attempt=failed_attempts,
            reason=(
                "Maximum SQL generation "
                "retries exceeded."
            ),
        )

    def build_retry_prompt(
        self,
        original_query: str,
        sql: str,
        errors: list[str] | tuple[str, ...],
        schema_context: str | None = None,
        business_context: str | None = None,
    ) -> str:
        """
        Build a controlled recovery prompt.

        The prompt contains the original user request,
        the failed SQL, validation errors, and optional
        context.

        It explicitly instructs the LLM to correct the
        previous SQL rather than blindly generating an
        unrelated query.
        """

        lines: list[str] = []

        lines.append(
            "The previous SQL generation attempt "
            "failed validation."
        )

        lines.append("")

        lines.append(
            "Original user request:"
        )

        lines.append(
            original_query.strip()
        )

        lines.append("")

        lines.append(
            "Previous SQL:"
        )

        lines.append(
            sql.strip()
            if sql.strip()
            else "(no SQL was produced)"
        )

        lines.append("")

        lines.append(
            "Validation errors:"
        )

        for error in errors:

            lines.append(
                f"- {error}"
            )

        if schema_context:

            lines.append("")

            lines.append(
                "Available schema context:"
            )

            lines.append(
                schema_context.strip()
            )

        if business_context:

            lines.append("")

            lines.append(
                "Available business context:"
            )

            lines.append(
                business_context.strip()
            )

        lines.append("")

        lines.append(
            "Generate a corrected SQL statement."
        )

        lines.append(
            "Use only the available schema."
        )

        lines.append(
            "Do not invent tables or columns."
        )

        lines.append(
            "Do not use INSERT, UPDATE, DELETE, "
            "DROP, ALTER, TRUNCATE, or other "
            "destructive statements."
        )

        lines.append(
            "Return only the SQL statement."
        )

        lines.append(
            "Do not use Markdown code fences."
        )

        return "\n".join(lines)

    def recovery_summary(self) -> str:
        """
        Return a concise summary of previous failures.
        """

        if not self._attempts:

            return "No recovery attempts recorded."

        lines = []

        for attempt in self._attempts:

            lines.append(
                f"Attempt {attempt.attempt}:"
            )

            if attempt.sql:

                lines.append(
                    f"SQL: {attempt.sql}"
                )

            else:

                lines.append(
                    "SQL: (none)"
                )

            for error in attempt.errors:

                lines.append(
                    f"Error: {error}"
                )

        return "\n".join(lines)