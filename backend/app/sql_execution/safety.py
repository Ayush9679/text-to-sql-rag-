from dataclasses import dataclass

import sqlglot
from sqlglot import exp


@dataclass(frozen=True)
class ExecutionSafetyResult:
    valid: bool
    errors: tuple[str, ...]


class SQLExecutionSafetyValidator:
    """Final, non-executing boundary that permits one read-only query only."""

    # A SELECT can contain data-modifying CTEs, so checking only the root
    # expression is insufficient.  These nodes are rejected anywhere in the
    # parsed statement before it reaches a database connection.
    FORBIDDEN_EXPRESSIONS = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.TruncateTable,
        exp.Create,
        exp.Grant,
        exp.Revoke,
        exp.Copy,
        exp.Command,
        exp.Transaction,
        exp.Commit,
        exp.Rollback,
        exp.Merge,
    )

    def validate(self, sql: str) -> ExecutionSafetyResult:
        if not sql or not sql.strip():
            return ExecutionSafetyResult(False, ("SQL statement is empty.",))

        try:
            statements = sqlglot.parse(sql, read="postgres")
        except Exception:
            return ExecutionSafetyResult(False, ("SQL statement could not be parsed.",))

        if len(statements) != 1:
            return ExecutionSafetyResult(False, ("Multiple SQL statements are not allowed.",))

        statement = statements[0]
        if not isinstance(statement, exp.Select):
            return ExecutionSafetyResult(
                False,
                ("Only SELECT or WITH read-only statements are allowed.",),
            )

        if statement.find(self.FORBIDDEN_EXPRESSIONS):
            return ExecutionSafetyResult(
                False,
                ("Data-modifying or administrative SQL is not allowed.",),
            )

        if any(statement.find(node) for node in (exp.Lock, exp.Into)):
            return ExecutionSafetyResult(
                False,
                ("Locking and SELECT INTO statements are not allowed.",),
            )

        return ExecutionSafetyResult(True, ())
