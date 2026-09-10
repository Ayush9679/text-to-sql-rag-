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

// ── DataQuery AI ──────────────────────────────────────────────────

export interface DataQueryChartSuggestion {
  type: 'bar' | 'line' | 'pie' | 'table' | 'none';
  x?: string | null;
  y?: string | null;
}


export interface AlternativeQuery {
  label: string;
  sql: string;
}

export interface DataQueryRequest {
  query: string;
  /** Specific table to query — defaults to the tenant's first available table. */
  table_name?: string;
}

export interface DataQueryResponse {
  answer: string | null;
  query_type: 'sql' | 'semantic_search' | 'hybrid' | null;
  sql: string | null;
  semantic_query: string | null;
  data: Record<string, unknown>[];
  columns: string[];
  row_count_returned: number;
  chart_suggestion: DataQueryChartSuggestion;
  assumptions: string[];
  needs_clarification: boolean;
  clarification_question: string | null;
  /** v2: pre-generated alternative SQL interpretations (no dead-ends). */
  alternatives: AlternativeQuery[];
  table_name: string | null;
  error?: string | null;
}

export interface ExecuteAlternativeSqlResponse {
  data: Record<string, unknown>[];
  columns: string[];
  row_count: number;
  error?: string | null;
}

export async function submitDataQuery(
  payload: DataQueryRequest,
): Promise<DataQueryResponse> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20_000);

  try {
    const csrfToken = getCsrfToken();
    const response = await fetch(`${apiBaseUrl}/api/dataquery`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
      credentials: 'include',
    });

    const body: unknown = await response.json().catch(() => null);

    if (!response.ok || !body || typeof body !== 'object') {
      const errMsg =
        body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
          ? body.detail
          : 'DataQuery request failed.';
      throw new Error(errMsg);
    }

    return body as DataQueryResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('DataQuery timed out. Please try again.');
    }
    if (error instanceof Error) throw error;
    throw new Error('Unable to reach the DataQuery service.');
  } finally {
    window.clearTimeout(timeout);
  }
}

/**
 * Execute a pre-generated alternate SQL statement — no LLM call.
 * Used when the user clicks an alternative-interpretation chip.
 */
export async function executeAlternativeSql(
  sql: string,
  tableName: string,
): Promise<ExecuteAlternativeSqlResponse> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15_000);

  try {
    const csrfToken = getCsrfToken();
    const response = await fetch(`${apiBaseUrl}/api/dataquery/execute-sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      },
      body: JSON.stringify({ sql, table_name: tableName }),
      signal: controller.signal,
      credentials: 'include',
    });

    const body: unknown = await response.json().catch(() => null);

    if (!response.ok || !body || typeof body !== 'object') {
      const errMsg =
        body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
          ? body.detail
          : 'Alternate SQL execution failed.';
      throw new Error(errMsg);
    }

    return body as ExecuteAlternativeSqlResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Alternate query timed out.');
    }
    if (error instanceof Error) throw error;
    throw new Error('Unable to reach the execute-sql service.');
  } finally {
    window.clearTimeout(timeout);
  }
}