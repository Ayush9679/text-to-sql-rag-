from .models import (
    ColumnMetadata,
    PrimaryKeyMetadata,
    ForeignKeyMetadata,
    CheckConstraintMetadata,
    TableMetadata,
    DatabaseSchema,
)

class SchemaExtractor:
    def __init__(self, inspector):
        self.inspector = inspector

    def extract_table(
        self,
        schema: str,
        table: str,
    ) -> TableMetadata:

        raw_columns = self.inspector.get_columns(
            schema,
            table,
        )

        columns = [
            ColumnMetadata(
                name=column["name"],
                data_type=str(column["type"]),
                nullable=column["nullable"],
                default=(
                    str(column["default"])
                    if column["default"] is not None
                    else None
                ),
            )
            for column in raw_columns
        ]

        raw_primary_key = (
            self.inspector.get_primary_key(
                schema,
                table,
            )
        )

        primary_key = None

        if raw_primary_key.get(
            "constrained_columns"
        ):
            primary_key = PrimaryKeyMetadata(
                name=raw_primary_key.get("name"),
                columns=raw_primary_key[
                    "constrained_columns"
                ],
            )

        raw_foreign_keys = (
            self.inspector.get_foreign_keys(
                schema,
                table,
            )
        )

        foreign_keys = [
            ForeignKeyMetadata(
                name=foreign_key.get("name"),
                columns=foreign_key[
                    "constrained_columns"
                ],
                referred_table=foreign_key[
                    "referred_table"
                ],
                referred_columns=foreign_key[
                    "referred_columns"
                ],
            )
            for foreign_key in raw_foreign_keys
        ]

        raw_constraints = (
            self.inspector.get_check_constraints(
                schema,
                table,
            )
        )

        check_constraints = [
            CheckConstraintMetadata(
                name=constraint.get("name"),
                expression=constraint["sqltext"],
            )
            for constraint in raw_constraints
            if constraint.get("sqltext")
        ]

        return TableMetadata(
            name=table,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            check_constraints=check_constraints,
        )
    def extract_schema(self,schema: str) -> DatabaseSchema:
        tables = self.inspector.get_tables(schema=schema)
        table_metadata = [self.extract_table(schema=schema,table=table,)for table in tables]
        return DatabaseSchema(schema_name=schema,tables=table_metadata)