const apiBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export interface AuthenticatedUser {
  id?: string;
  name: string;
  email: string;
  businessName?: string;
}

type ApiUser = Record<string, unknown>;
let csrfToken: string | undefined;

function asText(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() ? value : undefined;
}

function normalizeUser(payload: unknown): AuthenticatedUser | null {
  if (!payload || typeof payload !== 'object') return null;
  const root = payload as ApiUser;
  const user = (root.user && typeof root.user === 'object' ? root.user : root) as ApiUser;
  const business = (root.business && typeof root.business === 'object' ? root.business : {}) as ApiUser;
  const name = asText(user.name) || asText(user.full_name) || asText(user.email);
  const email = asText(user.email);
  if (!name || !email) return null;
  csrfToken = asText(root.csrf_token) || asText(root.csrfToken);
  return {
    id: asText(user.id) || asText(user.user_id),
    name,
    email,
    businessName: asText(business.name) || asText(user.business_name) || asText(user.businessName) || asText(root.business_name) || asText(root.businessName),
  };
}

export async function getCurrentUser(): Promise<AuthenticatedUser | null> {
  const response = await fetch(`${apiBaseUrl}/auth/me`, { credentials: 'include' });
  if (response.status === 401 || response.status === 403) return null;
  if (!response.ok) throw new Error('We could not verify your session. Please try again.');
  return normalizeUser(await response.json().catch(() => null));
}

export async function logout(): Promise<void> {
  const headers = csrfToken ? { 'X-CSRF-Token': csrfToken } : undefined;
  const response = await fetch(`${apiBaseUrl}/auth/logout`, { method: 'POST', headers, credentials: 'include' });
  csrfToken = undefined;
  if (!response.ok) throw new Error('Unable to sign out. Please try again.');
}

export function beginGoogleLogin(): void {
  window.location.assign(`${apiBaseUrl}/auth/login`);
}

export function getCsrfToken(): string | undefined {
  return csrfToken;
}
