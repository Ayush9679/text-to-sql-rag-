from sqlalchemy import inspect
from sqlalchemy.engine import Engine


class PostgreSQLSchemaInspector:
    def __init__(self, engine: Engine):
        self.engine = engine

    def get_tables(self, schema: str) -> list[str]:
        inspector = inspect(self.engine)

        return inspector.get_table_names(
            schema=schema
        )

    def get_columns(self, schema: str, table: str) -> list[dict]:
        inspector = inspect(self.engine)

        return inspector.get_columns(
            table,
            schema=schema,
        )
    def get_primary_key(self, schema: str, table: str) -> dict:
        inspector = inspect(self.engine)

        return inspector.get_pk_constraint(
        table,
        schema=schema,
        )
    def get_foreign_keys(self, schema: str, table: str) -> list[dict]:
        inspector = inspect(self.engine)

        return inspector.get_foreign_keys(
        table,
        schema=schema,
    )
    def get_check_constraints(self,schema: str,table: str,) -> list[dict]:
        inspector = inspect(self.engine)

        return inspector.get_check_constraints(
        table,
        schema=schema,
        )