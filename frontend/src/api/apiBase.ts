/**
 * Normalize API base URL from VITE_API_BASE.
 * - If empty/unset: return "/api" (Vite proxy).
 * - If value ends with "/api" (case-insensitive): use as-is, no extra "/api".
 * - Otherwise: append "/api".
 * Trailing slashes are always stripped before checking.
 */
export function getApiBase(envValue: string | undefined): string {
  const raw = typeof envValue === 'string' ? envValue.trim() : ''
  if (!raw) return '/api'
  const normalized = raw.replace(/\/+$/, '')
  const lower = normalized.toLowerCase()
  if (lower === '/api' || lower.endsWith('/api')) return normalized
  return `${normalized}/api`
}
