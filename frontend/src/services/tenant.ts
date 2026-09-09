/**
 * The tenant context is intentionally application controlled. It is sent with
 * both dataset and query requests so a workspace always operates on one scope.
 */
export const ACTIVE_TENANT_ID = import.meta.env.VITE_TENANT_ID || 'default';
