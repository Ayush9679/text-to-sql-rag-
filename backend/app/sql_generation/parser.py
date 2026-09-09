import re


class SQLParseError(Exception):
    """
    Raised when an LLM response cannot be converted
    into a usable SQL statement.
    """

    def __init__(
        self,
        message: str,
    ):
        super().__init__(message)

        self.message = message


class SQLResponseParser:
    """
    Extracts and normalizes SQL from an LLM response.

    This class does NOT validate whether the SQL is
    correct or safe. That belongs to later phases.

    Its responsibility is only:

        raw LLM response
                 ↓
             clean SQL
    """

    SQL_FENCE_PATTERN = re.compile(
        r"```(?:sql|postgresql)?\s*(.*?)```",
        re.IGNORECASE | re.DOTALL,
    )

    SQL_START_PATTERN = re.compile(
        r"\b(SELECT|WITH)\b",
        re.IGNORECASE,
    )

    def parse(
        self,
        response: str,
    ) -> str:
        """
        Extract and normalize SQL from an LLM response.
        """

        if not response:
            raise SQLParseError(
                "LLM response is empty."
            )

        text = response.strip()

        if not text:
            raise SQLParseError(
                "LLM response is empty."
            )

        text = self._extract_code_block(
            text
        )

        text = self._remove_prefix(
            text
        )

        sql = self._extract_sql(
            text
        )

        sql = self._normalize(
            sql
        )

        if not sql:
            raise SQLParseError(
                "No SQL statement found."
            )

        return sql

    def _extract_code_block(
        self,
        text: str,
    ) -> str:

        match = self.SQL_FENCE_PATTERN.search(
            text
        )

        if match:
            return match.group(1).strip()

        return text

    @staticmethod
    def _remove_prefix(
        text: str,
    ) -> str:

        prefixes = (
            "Here is the SQL:",
            "Here is the query:",
            "SQL:",
            "Query:",
        )

        result = text.strip()

        changed = True

        while changed:

            changed = False

            for prefix in prefixes:

                if result.lower().startswith(
                    prefix.lower()
                ):

                    result = (
                        result[len(prefix):]
                        .strip()
                    )

                    changed = True

        return result

    def _extract_sql(
        self,
        text: str,
    ) -> str:

        match = self.SQL_START_PATTERN.search(
            text
        )

        if not match:
            raise SQLParseError(
                "Response does not contain "
                "a SELECT or WITH statement."
            )

        return text[
            match.start():
        ].strip()

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

        sql = sql.strip()

        if sql.endswith(";"):
            return sql

        return sql + ";"