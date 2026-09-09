from dataclasses import dataclass

import sqlglot
from sqlglot import exp

from app.schema_intelligence.models import (
    DatabaseSchema,
)


class SchemaValidationError(Exception):
    """
    Raised when SQL cannot be validated against
    the available database schema.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class SchemaValidationResult:
    """
    Result of schema-aware SQL validation.
    """

    valid: bool
    sql: str
    errors: tuple[str, ...]


class SchemaAwareSQLValidator:
    """
    Validates generated SQL against the known database schema.

    Responsibilities:

    - Parse SQL using SQLGlot.
    - Verify referenced tables exist.
    - Verify referenced columns exist.
    - Resolve table aliases.
    - Support qualified columns.
    - Support unqualified columns.
    - Support SELECT queries and CTEs.
    - Never execute SQL.

    This class complements SQLValidator.

    SQLValidator:
        checks safety and basic SQL structure.

    SchemaAwareSQLValidator:
        checks compatibility with the actual schema.
    """

    def validate(
        self,
        sql: str,
        schema: DatabaseSchema,
    ) -> SchemaValidationResult:

        if not sql or not sql.strip():

            return SchemaValidationResult(
                valid=False,
                sql=sql or "",
                errors=(
                    "SQL statement is empty.",
                ),
            )

        try:
            expression = sqlglot.parse_one(
                sql,
                read="postgres",
            )

        except Exception as exc:

            return SchemaValidationResult(
                valid=False,
                sql=sql,
                errors=(
                    f"Invalid PostgreSQL SQL: {exc}",
                ),
            )

        errors: list[str] = []

        tables = self._build_table_map(
            schema
        )

        self._validate_tables(
            expression=expression,
            tables=tables,
            active_schema=schema.schema_name,
            errors=errors,
        )

        self._validate_columns(
            expression=expression,
            tables=tables,
            errors=errors,
        )

        return SchemaValidationResult(
            valid=not errors,
            sql=sql,
            errors=tuple(errors),
        )

    # ==================================================
    # TABLE MAP
    # ==================================================

    @staticmethod
    def _build_table_map(
        schema: DatabaseSchema,
    ) -> dict[str, object]:

        table_map: dict[str, object] = {}

        for table in schema.tables:

            full_name = table.name.lower()

            table_map[full_name] = table

            if "." in full_name:

                short_name = (
                    full_name.rsplit(
                        ".",
                        1,
                    )[-1]
                )

                table_map.setdefault(
                    short_name,
                    table,
                )

        return table_map

    # ==================================================
    # TABLE VALIDATION
    # ==================================================

    def _validate_tables(
        self,
        expression: exp.Expression,
        tables: dict[str, object],
        active_schema: str,
        errors: list[str],
    ) -> None:

        for table in expression.find_all(
            exp.Table
        ):

            table_name = (
                table.name.lower()
            )

            database_name = table.db

            # A generated query may only name the active schema.  Falling
            # back to a short table name is useful for normal validation, but
            # must never make an explicitly-qualified foreign tenant table
            # appear valid.
            if database_name and database_name.lower() != active_schema.lower():
                errors.append(f"Table is outside the active schema: {database_name}.{table_name}")
                continue

            if database_name:

                referenced_name = (
                    f"{database_name}.{table_name}"
                    .lower()
                )

            else:

                referenced_name = table_name

            if (
                referenced_name not in tables
                and table_name not in tables
            ):

                errors.append(
                    "Unknown table: "
                    f"{referenced_name}"
                )

    # ==================================================
    # COLUMN VALIDATION
    # ==================================================

    def _validate_columns(
        self,
        expression: exp.Expression,
        tables: dict[str, object],
        errors: list[str],
    ) -> None:

        query_tables = (
            self._get_query_tables(
                expression,
                tables,
            )
        )

        table_aliases = (
            self._build_alias_map(
                expression,
                tables,
            )
        )
        select_aliases = {
            alias.alias.lower()
            for alias in expression.find_all(exp.Alias)
            if alias.alias
        }

        for column in expression.find_all(
            exp.Column
        ):

            column_name = (
                column.name.lower()
            )

            table_reference = (
                column.table
            )

            # ------------------------------------------
            # Qualified column
            #
            # Example:
            #
            # c.customer_id
            # ------------------------------------------

            if table_reference:

                table_reference = (
                    table_reference.lower()
                )

                table_metadata = (
                    table_aliases.get(
                        table_reference
                    )
                )

                if table_metadata is None:

                    errors.append(
                        "Unknown table or alias "
                        f"'{table_reference}' "
                        f"for column "
                        f"'{column_name}'."
                    )

                    continue

                if not self._column_exists(
                    table_metadata,
                    column_name,
                ):

                    errors.append(
                        "Unknown column "
                        f"'{column_name}' "
                        f"in table "
                        f"'{table_metadata.name}'."
                    )

                continue

            # ------------------------------------------
            # Unqualified column
            #
            # Example:
            #
            # SELECT customer_id
            # FROM analytics.customers
            # ------------------------------------------

            # PostgreSQL permits SELECT aliases in ORDER BY.  Those aliases
            # are derived expressions, not schema columns, so accept them
            # only in their unqualified form after normal table validation.
            if column_name in select_aliases:
                continue

            matches = (
                self._find_column_matches(
                    query_tables,
                    column_name,
                )
            )

            if not matches:

                errors.append(
                    "Unknown column: "
                    f"{column_name}"
                )

            elif len(matches) > 1:

                errors.append(
                    "Ambiguous column: "
                    f"{column_name}"
                )

    # ==================================================
    # QUERY TABLE EXTRACTION
    # ==================================================

    @staticmethod
    def _get_query_tables(
        expression: exp.Expression,
        tables: dict[str, object],
    ) -> list[object]:

        query_tables: list[object] = []

        seen: set[int] = set()

        for table in expression.find_all(
            exp.Table
        ):

            table_name = (
                table.name.lower()
            )

            database_name = table.db

            if database_name:

                full_name = (
                    f"{database_name}.{table_name}"
                    .lower()
                )

            else:

                full_name = table_name

            metadata = (
                tables.get(full_name)
                or tables.get(table_name)
            )

            if metadata is None:
                continue

            table_id = id(metadata)

            if table_id in seen:
                continue

            seen.add(table_id)

            query_tables.append(
                metadata
            )

        return query_tables

    # ==================================================
    # ALIAS MAP
    # ==================================================

    def _build_alias_map(
        self,
        expression: exp.Expression,
        tables: dict[str, object],
    ) -> dict[str, object]:

        aliases: dict[str, object] = {}

        for table in expression.find_all(
            exp.Table
        ):

            table_name = (
                table.name.lower()
            )

            database_name = table.db

            if database_name:

                full_name = (
                    f"{database_name}.{table_name}"
                    .lower()
                )

            else:

                full_name = table_name

            metadata = (
                tables.get(full_name)
                or tables.get(table_name)
            )

            if metadata is None:
                continue

            # ------------------------------------------
            # Table name
            # ------------------------------------------

            aliases[
                table_name
            ] = metadata

            # ------------------------------------------
            # Fully qualified name
            # ------------------------------------------

            aliases[
                full_name
            ] = metadata

            # ------------------------------------------
            # Alias
            # ------------------------------------------

            alias = table.alias

            if alias:

                aliases[
                    alias.lower()
                ] = metadata

        return aliases

    # ==================================================
    # COLUMN EXISTENCE
    # ==================================================

    @staticmethod
    def _column_exists(
        table_metadata,
        column_name: str,
    ) -> bool:

        for column in table_metadata.columns:

            if (
                column.name.lower()
                == column_name
            ):

                return True

        return False

    # ==================================================
    # COLUMN MATCHING
    # ==================================================

    @staticmethod
    def _find_column_matches(
        tables: list[object],
        column_name: str,
    ) -> list[object]:

        matches: list[object] = []

        for table in tables:

            if SchemaAwareSQLValidator._column_exists(
                table,
                column_name,
            ):

                matches.append(table)

        return matches
