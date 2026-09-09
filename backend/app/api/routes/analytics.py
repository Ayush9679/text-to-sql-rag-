"""Analytics and Text-to-SQL Query API routes."""

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, inspect, text

from app.api.dependencies import get_current_context, require_authenticated, require_csrf
from app.application import ApplicationQueryService, QueryRequest, QueryResponse
from app.auth import AuthenticatedContext
from app.config import get_settings
from app.dataset.service import tenant_schema_name
from app.schema_intelligence.service import SchemaIntelligenceService
from app.schema_retrieval.business_knowledge import BUSINESS_CONCEPTS
from app.schema_retrieval.documents import SchemaDocumentBuilder, build_business_documents
from app.schema_retrieval.serializer import SchemaSerializer
from app.sql_execution import SQLExecutionService
from app.analytics.engine import (
    AnalyticsEngine,
    TimeInterval,
    create_analytics_engine,
)

router = APIRouter(tags=["Analytics"])
settings = get_settings()

_services_cache: dict[str, ApplicationQueryService] = {}

# In-memory query history store (per-tenant)
_query_history: dict[str, list[dict[str, Any]]] = {}


def get_tenant_query_service(tenant_id: str = "default") -> ApplicationQueryService:
    if tenant_id in _services_cache:
        return _services_cache[tenant_id]

    base_schema_name = settings.POSTGRES_SCHEMA
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    schema_name = tenant_schema_name(tenant_id)

    if tenant_id == "default":
        uploaded_schema = SchemaIntelligenceService(engine).get_schema(schema_name)
        if not uploaded_schema.tables:
            schema_name = base_schema_name

    query_engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={schema_name},public"},
    )
    schema = SchemaIntelligenceService(query_engine).get_schema(schema_name)
    schema_documents = SchemaDocumentBuilder(SchemaSerializer()).build_documents(schema)
    documents = schema_documents + (build_business_documents(BUSINESS_CONCEPTS) if tenant_id == "default" else [])

    service = ApplicationQueryService(
        schema=schema,
        documents=documents,
        execution_service=SQLExecutionService(engine=query_engine),
    )
    _services_cache[tenant_id] = service
    return service


def _record_query_history(
    tenant_id: str,
    natural_query: str,
    generated_sql: str | None,
    query_status: str,
    confidence_score: float,
    execution_time_ms: int,
    row_count: int,
    category: str = "General",
) -> None:
    """Record a query execution into the in-memory history store."""
    if tenant_id not in _query_history:
        _query_history[tenant_id] = []

    import uuid
    _query_history[tenant_id].insert(0, {
        "id": f"hist-{uuid.uuid4().hex[:8]}",
        "natural_query": natural_query,
        "generated_sql": generated_sql,
        "status": query_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence_score": confidence_score,
        "execution_time_ms": execution_time_ms,
        "category": category,
        "row_count": row_count,
    })

    # Keep last 200 entries per tenant
    _query_history[tenant_id] = _query_history[tenant_id][:200]


@router.post("/query", response_model=QueryResponse)
@router.post("/api/analytics/query", response_model=QueryResponse)
def run_query(
    request: QueryRequest,
    context: AuthenticatedContext = Depends(require_authenticated),
    _csrf: None = Depends(require_csrf),
) -> QueryResponse:
    try:
        service = get_tenant_query_service(context.tenant_id)
        response = service.handle(request)

        # Record to query history
        query_status = "success"
        category = "General"
        confidence = 0.9
        exec_time = 0

        if response.status == "clarification_required":
            query_status = "clarified"
            category = "Ambiguity Resolution"
            confidence = 0.6
        elif response.status == "failed":
            query_status = "failed"
            category = "Error"
            confidence = 0.2

        metadata = response.metadata or {}
        exec_time = int(metadata.get("execution_time_ms", 0)) if isinstance(metadata.get("execution_time_ms"), (int, float)) else 0

        _record_query_history(
            tenant_id=context.tenant_id,
            natural_query=request.query,
            generated_sql=response.sql,
            query_status=query_status,
            confidence_score=confidence,
            execution_time_ms=exec_time,
            row_count=response.row_count,
            category=category,
        )

        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query service is unavailable.",
        ) from exc


@router.get("/api/analytics/dashboard")
def get_dashboard_summary(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return real aggregate KPI summary from the tenant's uploaded datasets."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        inspector = inspect(engine)
        table_names = inspector.get_table_names(schema=schema_name)

        tables_count = len(table_names)
        total_rows = 0
        total_columns = 0

        if tables_count > 0:
            with engine.begin() as connection:
                for table_name in table_names:
                    row_count = connection.execute(
                        text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')
                    ).scalar_one()
                    total_rows += row_count

                    columns = inspector.get_columns(table_name, schema=schema_name)
                    total_columns += len(columns)

        recent_queries = len(_query_history.get(tenant_id, []))

        return {
            "tables_count": tables_count,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "recent_queries": recent_queries,
        }
    except Exception:
        return {
            "tables_count": 0,
            "total_rows": 0,
            "total_columns": 0,
            "recent_queries": 0,
        }


@router.get("/api/analytics/kpis")
def get_dashboard_kpis(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return dynamically discovered and computed KPIs from the tenant's data."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        analytics = AnalyticsEngine(engine, schema_name)
        metrics = analytics.discover_metrics()

        return {
            "kpis": [
                {
                    "id": m.name,
                    "label": m.label,
                    "value": m.value,
                    "formatted_value": m.formatted_value,
                    "unit": m.unit,
                    "source_table": m.source_table,
                    "source_column": m.source_column,
                    "calculation": m.calculation,
                    "comparison": m.comparison,
                }
                for m in metrics
            ]
        }
    except Exception as e:
        return {"kpis": [], "error": str(e)}


@router.get("/api/analytics/trends")
def get_dashboard_trends(
    interval: str = Query(default="month", pattern="^(day|week|month|quarter|year)$"),
    metric: str | None = Query(default=None),
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return dynamically computed time-series trend data."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        analytics = AnalyticsEngine(engine, schema_name)
        points = analytics.discover_time_series(
            metric_name=metric,
            interval=TimeInterval(interval),
        )

        return {
            "trends": [
                {
                    "period": p.period,
                    "value": p.value,
                    "formatted_value": p.formatted_value,
                }
                for p in points
            ],
            "interval": interval,
        }
    except Exception as e:
        return {"trends": [], "interval": interval, "error": str(e)}


@router.get("/api/analytics/breakdowns")
def get_dashboard_breakdowns(
    metric: str | None = Query(default=None),
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return dynamically computed categorical breakdown data."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        analytics = AnalyticsEngine(engine, schema_name)
        points = analytics.discover_breakdown(metric_name=metric)

        return {
            "breakdowns": [
                {
                    "label": p.label,
                    "value": p.value,
                    "formatted_value": p.formatted_value,
                    "percentage": p.percentage,
                }
                for p in points
            ]
        }
    except Exception as e:
        return {"breakdowns": [], "error": str(e)}


@router.get("/api/analytics/query-volume")
def get_query_volume(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return real query execution volume from query history."""
    tenant_id = context.tenant_id
    history = _query_history.get(tenant_id, [])

    # Aggregate by week
    from collections import defaultdict
    weekly_counts = defaultdict(int)
    for entry in history:
        try:
            ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            week_key = ts.strftime("%Y-W%U")
            weekly_counts[week_key] += 1
        except Exception:
            pass

    # Sort and format
    sorted_weeks = sorted(weekly_counts.items())
    volume = [
        {"period": week, "value": count}
        for week, count in sorted_weeks[-12:]  # Last 12 weeks
    ]

    return {"volume": volume}


@router.get("/api/analytics/available-metrics")
def get_available_metrics(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return list of available metrics that can be analyzed."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        analytics = AnalyticsEngine(engine, schema_name)
        profiles = analytics._get_table_profiles()
        analytics.metric_engine.infer_metrics_for_tables(profiles)

        metrics_info = []
        for m in analytics.metric_engine.metrics:
            metrics_info.append({
                "name": m.name,
                "label": m.name.replace("_", " ").title(),
                "table": m.target_table,
                "unit": m.unit,
                "description": m.description,
                "synonyms": m.synonyms,
            })

        return {"metrics": metrics_info}
    except Exception as e:
        return {"metrics": [], "error": str(e)}


@router.get("/api/analytics/available-dimensions")
def get_available_dimensions(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return list of available categorical dimensions for breakdown analysis."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        inspector = inspect(engine)
        table_names = inspector.get_table_names(schema=schema_name)

        dimensions = []
        for table_name in table_names:
            columns = inspector.get_columns(table_name, schema=schema_name)
            for col in columns:
                col_type = str(col["type"]).lower()
                if ("text" in col_type or "varchar" in col_type) and col["name"] not in {"id", "created_at", "updated_at"}:
                    dimensions.append({
                        "table": table_name,
                        "column": col["name"],
                        "label": col["name"].replace("_", " ").title(),
                    })

        return {"dimensions": dimensions}
    except Exception as e:
        return {"dimensions": [], "error": str(e)}


@router.get("/api/analytics/schema")
def get_tenant_schema(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return the tenant's database schema."""
    tenant_id = context.tenant_id
    schema_name = tenant_schema_name(tenant_id)
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        schema = SchemaIntelligenceService(engine).get_schema(schema_name)

        return {
            "name": schema.schema_name,
            "tables": [
                {
                    "name": t.name,
                    "columns": [
                        {
                            "name": c.name,
                            "type": c.data_type,
                            "nullable": c.nullable,
                        }
                        for c in t.columns
                    ],
                }
                for t in schema.tables
            ],
        }
    except Exception as e:
        return {"name": schema_name, "tables": [], "error": str(e)}


@router.get("/api/analytics/query-history")
def get_query_history(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    """Return the real query execution history for this tenant."""
    tenant_id = context.tenant_id
    history = _query_history.get(tenant_id, [])
    return {"history": history}