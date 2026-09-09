"""Analytics module for dynamic, schema-aware business intelligence."""

from .engine import (
    AnalyticsEngine,
    TimeInterval,
    DiscoveredMetric,
    TimeSeriesPoint,
    BreakdownPoint,
    QueryVolumePoint,
    create_analytics_engine,
)

__all__ = [
    "AnalyticsEngine",
    "TimeInterval",
    "DiscoveredMetric",
    "TimeSeriesPoint",
    "BreakdownPoint",
    "QueryVolumePoint",
    "create_analytics_engine",
]