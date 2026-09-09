"""Dataset upload, profiling, schema inspection, and metadata routes."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_context, require_authenticated, require_csrf
from app.auth import AuthenticatedContext
from app.config import get_settings
from app.database.session import get_db, get_engine
from app.dataset import DatasetError, DatasetIngestionService
from app.dataset.service import tenant_schema_name
from app.schema_intelligence.relationship_detector import RelationshipDetector
from app.schema_intelligence.service import SchemaIntelligenceService

router = APIRouter(prefix="/datasets", tags=["Datasets"])
settings = get_settings()


class UploadDatasetPayload(BaseModel):
    filename: str
    csv_text: str


@router.get("")
def list_datasets(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        inspector = inspect(engine)
        datasets = []
        with engine.begin() as connection:
            for table_name in inspector.get_table_names(schema=schema_name):
                row_count = connection.execute(text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')).scalar_one()
                columns = inspector.get_columns(table_name, schema=schema_name)
                datasets.append(
                    {
                        "table_name": table_name,
                        "row_count": row_count,
                        "columns": [{"name": column["name"], "type": str(column["type"])} for column in columns],
                    }
                )
        return {"datasets": datasets}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Datasets are unavailable.")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_dataset(
    payload: UploadDatasetPayload,
    context: AuthenticatedContext = Depends(require_authenticated),
    _csrf: None = Depends(require_csrf),
) -> dict:
    if not payload.filename or not payload.csv_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="filename and csv_text are required.",
        )
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        result = DatasetIngestionService(engine).ingest_csv(
            tenant_id=context.tenant_id,
            filename=payload.filename,
            content=payload.csv_text.encode("utf-8"),
        )
        return result.model_dump(mode="json")
    except DatasetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dataset upload failed.") from exc


@router.get("/schema")
def get_tenant_schema(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return the full tenant schema with relationships, row counts, and enriched column metadata."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    schema = SchemaIntelligenceService(engine).get_schema(schema_name)
    inspector = inspect(engine)

    # Build enriched table list with row counts and column flags
    tables = []
    for table in schema.tables:
        fk_columns: dict[str, dict] = {}
        for fk in table.foreign_keys:
            for col in fk.columns:
                fk_columns[col] = {"table": fk.referred_table, "column": fk.referred_columns[0] if fk.referred_columns else col}

        pk_cols = set(table.primary_key.columns) if table.primary_key else set()

        row_count = 0
        try:
            with engine.begin() as connection:
                row_count = connection.execute(text(f'SELECT COUNT(*) FROM "{schema_name}"."{table.name}"')).scalar_one()
        except Exception:
            pass

        columns = []
        for col in table.columns:
            columns.append({
                "name": col.name,
                "type": col.data_type,
                "isPrimaryKey": col.name in pk_cols,
                "isForeignKey": col.name in fk_columns,
                "isNullable": col.nullable,
                "foreignKeyTarget": fk_columns.get(col.name),
            })

        tables.append({
            "name": table.name,
            "schema": schema_name,
            "description": f"Table {table.name} with {len(table.columns)} columns.",
            "rowCount": row_count,
            "columns": columns,
        })

    # Build relationships from foreign keys
    relationships = []
    rel_idx = 0
    for table in schema.tables:
        for fk in table.foreign_keys:
            for i, col in enumerate(fk.columns):
                rel_idx += 1
                referred_col = fk.referred_columns[i] if i < len(fk.referred_columns) else col
                relationships.append({
                    "id": f"rel-{rel_idx}",
                    "sourceTable": table.name,
                    "sourceColumn": col,
                    "targetTable": fk.referred_table,
                    "targetColumn": referred_col,
                    "type": "many-to-one",
                })

    return {
        "name": schema_name,
        "dialect": "postgresql",
        "version": "16",
        "tables": tables,
        "relationships": relationships,
    }
