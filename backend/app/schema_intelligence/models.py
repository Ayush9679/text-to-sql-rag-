from pydantic import BaseModel,Field
class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    nullable: bool
    default: str | None = None

class PrimaryKeyMetadata(BaseModel):
    name: str | None = None
    columns: list[str]


class ForeignKeyMetadata(BaseModel):
    name: str | None = None
    columns: list[str]
    referred_table: str
    referred_columns: list[str]


class CheckConstraintMetadata(BaseModel):
    name: str | None = None
    expression: str


class TableMetadata(BaseModel):
    name: str
    columns: list[ColumnMetadata]
    primary_key: PrimaryKeyMetadata | None = None
    foreign_keys: list[ForeignKeyMetadata] = Field(
        default_factory=list
    )
    check_constraints: list[CheckConstraintMetadata] = Field(
        default_factory=list
    )


class DatabaseSchema(BaseModel):
    schema_name: str
    tables: list[TableMetadata]

