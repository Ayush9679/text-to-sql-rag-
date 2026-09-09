import re
from dataclasses import dataclass


class SQLValidationError(Exception):
    """
    Raised when generated SQL fails validation.
    """

    def __init__(
        self,
        message: str,
    ):
        super().__init__(message)

        self.message = message


@dataclass(frozen=True)
class SQLValidationResult:
    """
    Result returned by the SQL validator.
    """

    valid: bool
    sql: str
    errors: tuple[str, ...]


class SQLValidator:
    """
    Performs basic safety and structural validation
    on generated PostgreSQL SQL.

    This validator does NOT execute SQL.

    Responsibilities:

    - reject empty SQL
    - allow SELECT / WITH queries
    - reject destructive operations
    - reject multiple statements
    - perform basic structural checks
    """

    ALLOWED_STARTS = (
        "SELECT",
        "WITH",
    )

    FORBIDDEN_KEYWORDS = (
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE",
        "COMMENT",
    )

    def validate(
        self,
        sql: str,
    ) -> SQLValidationResult:

        errors: list[str] = []

        # -----------------------------------------
        # 1. Empty SQL
        # -----------------------------------------

        if not sql or not sql.strip():

            errors.append(
                "SQL statement is empty."
            )

            return SQLValidationResult(
                valid=False,
                sql=sql or "",
                errors=tuple(errors),
            )

        # -----------------------------------------
        # 2. Normalize SQL
        # -----------------------------------------

        normalized = self._normalize(sql)

        # -----------------------------------------
        # 3. Check statement type
        # -----------------------------------------

        self._check_statement_start(
            normalized,
            errors,
        )

        # -----------------------------------------
        # 4. Check dangerous operations
        # -----------------------------------------

        self._check_forbidden_keywords(
            normalized,
            errors,
        )

        # -----------------------------------------
        # 5. Check multiple statements
        # -----------------------------------------

        self._check_multiple_statements(
            normalized,
            errors,
        )

        # -----------------------------------------
        # 6. Check basic SQL structure
        # -----------------------------------------

        self._check_basic_structure(
            normalized,
            errors,
        )

        return SQLValidationResult(
            valid=not errors,
            sql=normalized,
            errors=tuple(errors),
        )

    @staticmethod
    def _normalize(
        sql: str,
    ) -> str:

        sql = sql.strip()

        sql = re.sub(
            r"\s+",
            " ",
            sql,
        )

        return sql

    def _check_statement_start(
        self,
        sql: str,
        errors: list[str],
    ):

        upper_sql = sql.upper().lstrip()

        if not upper_sql.startswith(
            self.ALLOWED_STARTS
        ):

            errors.append(
                "Only SELECT or WITH statements "
                "are allowed."
            )

    def _check_forbidden_keywords(
        self,
        sql: str,
        errors: list[str],
    ):

        upper_sql = sql.upper()

        for keyword in self.FORBIDDEN_KEYWORDS:

            pattern = (
                rf"\b{keyword}\b"
            )

            if re.search(
                pattern,
                upper_sql,
            ):

                errors.append(
                    f"Forbidden SQL operation: "
                    f"{keyword}."
                )

    @staticmethod
    def _check_multiple_statements(
        sql: str,
        errors: list[str],
    ):

        statement = sql.rstrip()

        # A single trailing semicolon is allowed.
        if statement.endswith(";"):

            statement = (
                statement[:-1]
                .rstrip()
            )

        # Any remaining semicolon means there
        # is another statement.
        if ";" in statement:

            errors.append(
                "Multiple SQL statements "
                "are not allowed."
            )

    @staticmethod
    def _check_basic_structure(
        sql: str,
        errors: list[str],
    ):

        upper_sql = (
            sql.upper().strip()
        )

        if upper_sql.startswith(
            "SELECT"
        ):

            if not re.search(
                r"\bFROM\b",
                upper_sql,
            ):

                errors.append(
                    "SELECT statement is missing "
                    "a FROM clause."
                )

        elif upper_sql.startswith(
            "WITH"
        ):

            if not re.search(
                r"\bSELECT\b",
                upper_sql,
            ):

                errors.append(
                    "WITH query does not contain "
                    "a SELECT statement."
                )