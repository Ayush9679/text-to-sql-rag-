/**
 * Dashboard API — fetches real, dynamic data from backend endpoints.
 * No mock/static data. If the API returns empty, the UI shows empty states.
 */

import { getCsrfToken } from './auth';

const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

// ── Types ────────────────────────────────────────────────────────

export interface DashboardSummary {
  tables_count: number;
  total_rows: number;
  total_columns: number;
  recent_queries: number;
}

export interface QueryHistoryEntry {
  id: string;
  natural_query: string;
  generated_sql: string | null;
  status: 'success' | 'clarified' | 'failed';
  timestamp: string;
  confidence_score: number;
  execution_time_ms: number;
  category: string;
  row_count: number;
}

export interface SchemaColumn {
  name: string;
  type: string;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  isNullable: boolean;
  foreignKeyTarget?: { table: string; column: string };
}

export interface SchemaTable {
  name: string;
  schema: string;
  description: string;
  rowCount: number;
  columns: SchemaColumn[];
}

export interface SchemaRelationship {
  id: string;
  sourceTable: string;
  sourceColumn: string;
  targetTable: string;
  targetColumn: string;
  type: string;
}

export interface DatabaseSchemaResponse {
  name: string;
  dialect: string;
  version: string;
  tables: SchemaTable[];
  relationships: SchemaRelationship[];
}

export interface MetricEntry {
  name: string;
  target_table: string;
  formula: string;
  sql_expression: string;
  unit: string;
  description: string;
  synonyms: string[];
}

// Dynamic Analytics Types
export interface DynamicKPI {
  id: string;
  label: string;
  value: number;
  formatted_value: string;
  unit: string;
  source_table: string;
  source_column: string;
  calculation: string;
  comparison?: {
    period: string;
    value: number;
    change_percent: number;
  };
}

export interface TrendPoint {
  period: string;
  value: number;
  formatted_value: string;
}

export interface BreakdownPoint {
  label: string;
  value: number;
  formatted_value: string;
  percentage: number;
}

export interface QueryVolumePoint {
  period: string;
  value: number;
}

export interface AvailableMetric {
  name: string;
  label: string;
  table: string;
  unit: string;
  description: string;
  synonyms: string[];
}

export interface AvailableDimension {
  table: string;
  column: string;
  label: string;
}

// ── Helpers ──────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(getCsrfToken() ? { 'X-CSRF-Token': getCsrfToken() as string } : {}),
  };

  const response = await fetch(`${apiBaseUrl}${path}`, {
    credentials: 'include',
    headers,
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API ${path} failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

// ── Endpoints ────────────────────────────────────────────────────

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>('/api/analytics/dashboard');
}

export async function fetchQueryHistory(): Promise<QueryHistoryEntry[]> {
  const data = await apiFetch<{ history: QueryHistoryEntry[] }>('/api/analytics/query-history');
  return data.history ?? [];
}

export async function fetchTenantSchema(): Promise<DatabaseSchemaResponse> {
  return apiFetch<DatabaseSchemaResponse>('/datasets/schema');
}

export async function fetchMetrics(): Promise<MetricEntry[]> {
  const data = await apiFetch<{ metrics: MetricEntry[] }>('/metrics');
  return data.metrics ?? [];
}

// Dynamic Analytics Endpoints
export async function fetchDashboardKPIs(): Promise<DynamicKPI[]> {
  const data = await apiFetch<{ kpis: DynamicKPI[] }>('/api/analytics/kpis');
  return data.kpis ?? [];
}

export async function fetchDashboardTrends(
  interval: 'day' | 'week' | 'month' | 'quarter' | 'year' = 'month',
  metric?: string
): Promise<TrendPoint[]> {
  const params = new URLSearchParams({ interval });
  if (metric) params.set('metric', metric);
  const data = await apiFetch<{ trends: TrendPoint[] }>(`/api/analytics/trends?${params.toString()}`);
  return data.trends ?? [];
}

export async function fetchDashboardBreakdowns(metric?: string): Promise<BreakdownPoint[]> {
  const params = metric ? `?metric=${encodeURIComponent(metric)}` : '';
  const data = await apiFetch<{ breakdowns: BreakdownPoint[] }>(`/api/analytics/breakdowns${params}`);
  return data.breakdowns ?? [];
}

export async function fetchQueryVolume(): Promise<QueryVolumePoint[]> {
  const data = await apiFetch<{ volume: QueryVolumePoint[] }>('/api/analytics/query-volume');
  return data.volume ?? [];
}

export async function fetchAvailableMetrics(): Promise<AvailableMetric[]> {
  const data = await apiFetch<{ metrics: AvailableMetric[] }>('/api/analytics/available-metrics');
  return data.metrics ?? [];
}

export async function fetchAvailableDimensions(): Promise<AvailableDimension[]> {
  const data = await apiFetch<{ dimensions: AvailableDimension[] }>('/api/analytics/available-dimensions');
  return data.dimensions ?? [];
}

export async function fetchAnalyticsSchema(): Promise<DatabaseSchemaResponse> {
  return apiFetch<DatabaseSchemaResponse>('/api/analytics/schema');
}