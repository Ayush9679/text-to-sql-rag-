from app.schema_intelligence.models import (
    DatabaseSchema,
    TableMetadata,
)


class SchemaSerializer:

    def serialize_table(
        self,
        table: TableMetadata,
    ) -> str:
        lines = [
            f"TABLE: {table.name}",
            "",
            "COLUMNS:",
        ]

        for column in table.columns:
            nullable = (
                "NULLABLE"
                if column.nullable
                else "NOT NULL"
            )

            lines.append(
                f"- {column.name}: "
                f"{column.data_type}, "
                f"{nullable}"
            )

        if table.primary_key:
            lines.extend([
                "",
                "PRIMARY KEY:",
                ", ".join(
                    table.primary_key.columns
                ),
            ])

        if table.foreign_keys:
            lines.extend([
                "",
                "RELATIONSHIPS:",
            ])

            for foreign_key in table.foreign_keys:
                for column, referred_column in zip(
                    foreign_key.columns,
                    foreign_key.referred_columns,
                ):
                    lines.append(
                        f"- {table.name}.{column} "
                        f"-> "
                        f"{foreign_key.referred_table}."
                        f"{referred_column}"
                    )

        if table.check_constraints:
            lines.extend([
                "",
                "CHECK CONSTRAINTS:",
            ])

            for constraint in table.check_constraints:
                lines.append(
                    f"- {constraint.expression}"
                )

        return "\n".join(lines)

    def serialize_schema(
        self,
        schema: DatabaseSchema,
    ) -> str:
        documents = [
            f"SCHEMA: {schema.schema_name}",
            "",
        ]

        for table in schema.tables:
            documents.append(
                self.serialize_table(table)
            )
            documents.append("")
            documents.append("=" * 60)
            documents.append("")

        return "\n".join(documents)