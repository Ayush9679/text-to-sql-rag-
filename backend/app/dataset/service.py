"""Controlled CSV-to-PostgreSQL ingestion with deep profiling and tenant isolation."""

import csv
import hashlib
import io
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import PurePath
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, MetaData, Numeric, Table, Text
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text

from app.dataset.profiler import ColumnProfile, DataProfiler, TableProfile


MAX_CSV_BYTES = 50 * 1024 * 1024
IDENTIFIER_LIMIT = 63
POSTGRES_RESERVED = {"select", "from", "where", "table", "schema", "user", "order", "group", "limit"}


class DatasetError(ValueError):
    """A controlled, user-safe dataset onboarding failure."""


class ColumnMapping(BaseModel):
    original_name: str
    database_name: str
    postgres_type: str
    semantic_type: str = "unknown"
    sample_values: list[Any] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class DatasetUploadResult(BaseModel):
    tenant_id: str
    schema_name: str
    table_name: str
    row_count: int
    file_hash: str = ""
    columns: list[ColumnMapping] = Field(default_factory=list)
    primary_key_candidates: list[str] = Field(default_factory=list)
    foreign_key_candidates: list[str] = Field(default_factory=list)
    data_quality_issues: list[str] = Field(default_factory=list)


def normalize_identifier(value: str, *, prefix: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    if not normalized:
        raise DatasetError("The filename or column name does not contain usable characters.")
    if normalized[0].isdigit() or normalized in POSTGRES_RESERVED:
        normalized = f"{prefix}_{normalized}"
    return normalized[:IDENTIFIER_LIMIT]


def tenant_schema_name(tenant_id: str) -> str:
    return f"tenant_{normalize_identifier(tenant_id, prefix='tenant')}"[:IDENTIFIER_LIMIT]


class DatasetIngestionService:
    """Validates, profiles, and inserts one or more CSVs into the caller's schema."""

    def __init__(self, engine: Engine, *, max_bytes: int = MAX_CSV_BYTES, batch_size: int = 1_000):
        self.engine = engine
        self.max_bytes = max_bytes
        self.batch_size = batch_size
        self.profiler = DataProfiler()

    def ingest_csv(self, *, tenant_id: str, filename: str, content: bytes) -> DatasetUploadResult:
        schema_name = tenant_schema_name(tenant_id)
        table_name = self._table_name(filename)
        file_hash = hashlib.sha256(content).hexdigest()

        headers, rows = self._parse(content)
        norm_headers = [normalize_identifier(h, prefix="column") for h in headers]
        
        # Verify unique normalized names
        if len(set(norm_headers)) != len(norm_headers):
            raise DatasetError("CSV column names normalize to duplicate database identifiers.")

        table_profile = self.profiler.profile_table(table_name, headers, norm_headers, rows)
        mappings = self._mappings_from_profile(table_profile)

        metadata = MetaData(schema=schema_name)
        table = Table(
            table_name,
            metadata,
            *(Column(mapping.database_name, self._sqlalchemy_type(mapping.postgres_type), nullable=True) for mapping in mappings),
        )

        try:
            with self.engine.begin() as connection:
                connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                if self.engine.dialect.has_table(connection, table_name, schema=schema_name):
                    raise DatasetError(f"A table named '{table_name}' already exists for this dataset. Upload a differently named file.")
                table.create(connection)
                for index in range(0, len(rows), self.batch_size):
                    batch = [
                        {mapping.database_name: self._coerce(row[position], mapping.postgres_type) for position, mapping in enumerate(mappings)}
                        for row in rows[index : index + self.batch_size]
                    ]
                    connection.execute(table.insert(), batch)
        except DatasetError:
            raise
        except Exception as exc:
            raise DatasetError("The CSV could not be stored in the database.") from exc

        return DatasetUploadResult(
            tenant_id=tenant_id,
            schema_name=schema_name,
            table_name=table_name,
            row_count=len(rows),
            file_hash=file_hash,
            columns=mappings,
            primary_key_candidates=table_profile.primary_key_candidates,
            foreign_key_candidates=table_profile.foreign_key_candidates,
            data_quality_issues=table_profile.data_quality_issues,
        )

    def _table_name(self, filename: str) -> str:
        path = PurePath(filename)
        if path.name != filename or not filename.lower().endswith(".csv"):
            raise DatasetError("Upload a single .csv file with a safe filename.")
        return normalize_identifier(path.stem, prefix="table")

    def _parse(self, content: bytes) -> tuple[list[str], list[list[str]]]:
        if not content:
            raise DatasetError("The CSV file is empty.")
        if len(content) > self.max_bytes:
            raise DatasetError("The CSV file exceeds the allowed size.")
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DatasetError("The CSV must be UTF-8 encoded.") from exc
        try:
            records = list(csv.reader(io.StringIO(decoded, newline=""), strict=True))
        except csv.Error as exc:
            raise DatasetError("The CSV contains malformed rows.") from exc
        if not records or not any(cell.strip() for cell in records[0]):
            raise DatasetError("The CSV must include a header row.")
        headers = [cell.strip() for cell in records[0]]
        if any(not header for header in headers):
            raise DatasetError("CSV column names cannot be empty.")
        if len(set(headers)) != len(headers):
            raise DatasetError("CSV column names must be unique.")
        rows = [row for row in records[1:] if any(cell.strip() for cell in row)]
        if not rows:
            raise DatasetError("The CSV must include at least one data row.")
        if any(len(row) != len(headers) for row in rows):
            raise DatasetError("All CSV rows must have the same number of columns as the header.")
        return headers, rows

    def _mappings_from_profile(self, profile: TableProfile) -> list[ColumnMapping]:
        mappings: list[ColumnMapping] = []
        for cp in profile.columns:
            mappings.append(
                ColumnMapping(
                    original_name=cp.name,
                    database_name=cp.normalized_name,
                    postgres_type=cp.inferred_type,
                    semantic_type=cp.semantic_type,
                    sample_values=cp.sample_values,
                    stats=cp.stats,
                    description=cp.description,
                )
            )
        return mappings

    @staticmethod
    def _sqlalchemy_type(postgres_type: str):
        return {
            "INTEGER": Integer,
            "BIGINT": BigInteger,
            "NUMERIC": Numeric,
            "BOOLEAN": Boolean,
            "DATE": Date,
            "TIMESTAMP": DateTime,
            "TEXT": Text,
        }[postgres_type]()

    @staticmethod
    def _coerce(value: str, postgres_type: str):
        value = value.strip()
        if not value:
            return None
        cleaned = value.replace("$", "").replace("₹", "").replace("€", "").replace("£", "").replace(",", "")
        if postgres_type in {"INTEGER", "BIGINT"}:
            return int(cleaned)
        if postgres_type == "NUMERIC":
            return Decimal(cleaned)
        if postgres_type == "BOOLEAN":
            return value.lower() in {"true", "yes", "1", "t"}
        if postgres_type == "DATE":
            parsed_d = DataProfiler._parse_date(value)
            return parsed_d or date.fromisoformat(value)
        if postgres_type == "TIMESTAMP":
            parsed_dt = DataProfiler._parse_datetime(value)
            return parsed_dt or datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
