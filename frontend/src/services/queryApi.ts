export interface BackendClarification {
  question: string;
  reason: string;
  options: string[];
  target_field: string;
  confidence: number;
}

export interface BackendQueryResponse {
  status: 'success' | 'clarification_required' | 'failed';
  sql?: string | null;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  clarification?: BackendClarification | null;
  clarification_state?: Record<string, unknown> | null;
  explanation?: string | null;
  metadata: Record<string, unknown>;
}

const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function submitQuery(
  payload: Record<string, unknown>,
): Promise<BackendQueryResponse> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 30_000);

  try {
    const response = await fetch(`${apiBaseUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(getCsrfToken() ? { 'X-CSRF-Token': getCsrfToken() as string } : {}) },
      body: JSON.stringify(payload),
      signal: controller.signal,
      credentials: 'include',
    });
    const body: unknown = await response.json().catch(() => null);

    if (!response.ok || !body || typeof body !== 'object') {
      const error = body && typeof body === 'object' && 'error' in body && typeof body.error === 'string'
        ? body.error
        : 'The query could not be completed.';
      throw new Error(error);
    }
    return body as BackendQueryResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('The query timed out. Please try again.');
    }
    if (error instanceof Error) throw error;
    throw new Error('Unable to reach the query service.');
  } finally {
    window.clearTimeout(timeout);
  }
}
import { getCsrfToken } from './auth';
