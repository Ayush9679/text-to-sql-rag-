from app.sql_generation.models import (
    SQLGenerationRequest,
)


class SQLPromptBuilder:
    """
    Builds controlled prompts for the SQL-generation LLM.

    This class does not call Groq.
    It only constructs the prompt.
    """

    SYSTEM_PROMPT = """
You are a PostgreSQL SQL generation assistant.

Your job is to convert a user's analytical request
into valid PostgreSQL SQL.

Rules:

1. Generate SQL for PostgreSQL only.
2. Use only tables and columns provided in the schema context.
3. Never invent tables, columns, relationships, or values.
4. Respect the user's requested filters, metrics,
   aggregation, sorting, grouping, and limit.
5. Use the provided business definitions when available.
6. Generate SELECT statements only.
7. Do not perform INSERT, UPDATE, DELETE, DROP,
   ALTER, TRUNCATE, or other destructive operations.
8. Return only the SQL statement.
9. Do not wrap the SQL in Markdown code fences.
10. Do not provide explanations outside the SQL statement.
""".strip()

    def build(
        self,
        request: SQLGenerationRequest,
    ) -> tuple[str, str]:
        """
        Build the system prompt and user prompt.
        """

        user_prompt = self._build_user_prompt(
            request
        )

        return (
            self.SYSTEM_PROMPT,
            user_prompt,
        )

    def _build_user_prompt(
        self,
        request: SQLGenerationRequest,
    ) -> str:

        sections: list[str] = []

        sections.append(
            "USER REQUEST:\n"
            f"{request.query}"
        )

        sections.append(
            "QUERY ANALYSIS:\n"
            f"Intent: {request.intent or 'unknown'}\n"
            f"Entities: {self._format_list(request.entities)}\n"
            f"Metrics: {self._format_list(request.metrics)}\n"
            f"Filters: {self._format_list(request.filters)}\n"
            f"Aggregation: {request.aggregation or 'none'}\n"
            f"Sort direction: "
            f"{request.sort_direction or 'none'}\n"
            f"Limit: "
            f"{request.limit if request.limit is not None else 'none'}"
        )

        sections.append(
            "DATABASE SCHEMA:\n"
            f"{request.schema_context or 'No schema context provided.'}"
        )

        sections.append(
            "BUSINESS KNOWLEDGE:\n"
            f"{request.business_context or 'No business knowledge provided.'}"
        )

        sections.append(
            "DATABASE DIALECT:\n"
            f"{request.dialect}"
        )

        sections.append(
            "TASK:\n"
            "Generate one valid PostgreSQL SELECT query "
            "that answers the user's request."
        )

        return "\n\n".join(sections)

    @staticmethod
    def _format_list(
        values: list[str],
    ) -> str:

        if not values:
            return "none"

        return ", ".join(values)