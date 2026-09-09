from pydantic import BaseModel, Field


class BusinessConcept(BaseModel):
    name: str
    definition: str
    related_tables: list[str] = Field(
        default_factory=list
    )
    related_columns: list[str] = Field(
        default_factory=list
    )
    calculation: str | None = None