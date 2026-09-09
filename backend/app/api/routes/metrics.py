"""Business metrics management routes."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.dependencies import require_authenticated, require_csrf
from app.auth import AuthenticatedContext
from app.schema_intelligence.metric_engine import MetricDefinition, MetricEngine

router = APIRouter(prefix="/metrics", tags=["Business Metrics"])
metric_engine = MetricEngine()


class RegisterMetricPayload(BaseModel):
    name: str
    target_table: str
    formula: str
    sql_expression: str
    unit: str = "currency"
    description: str = ""
    synonyms: list[str] = Field(default_factory=list)


@router.get("")
def list_metrics(
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    return {"metrics": [m.model_dump() for m in metric_engine.metrics]}


@router.post("", status_code=status.HTTP_201_CREATED)
def register_metric(
    payload: RegisterMetricPayload,
    context: AuthenticatedContext = Depends(require_authenticated),
    _csrf: None = Depends(require_csrf),
) -> dict:
    definition = MetricDefinition(**payload.model_dump())
    metric_engine.register_metric(definition)
    return {"status": "created", "metric": definition.model_dump()}
