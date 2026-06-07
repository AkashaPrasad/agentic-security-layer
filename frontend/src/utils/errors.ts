// ---------------------------------------------------------------------------
// API error helpers
// ---------------------------------------------------------------------------

/**
 * Extract a human-readable error string from an API response.
 *
 * FastAPI / Pydantic returns `detail` as either:
 *   - a plain string  →  "Not found"
 *   - an array of validation error objects  →  [{type, loc, msg, input, ctx}, …]
 *
 * This helper normalises both cases into a single string safe for rendering
 * as a React child.
 */
export function extractApiError(
    error: unknown,
    fallback = 'An unexpected error occurred.',
): string {
    const detail = (error as any)?.response?.data?.detail;
    if (!detail) return fallback;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail
            .map((d: any) => {
                const loc = Array.isArray(d.loc) ? d.loc.join(' → ') : '';
                const msg = d.msg ?? '';
                return loc ? `${loc}: ${msg}` : msg;
            })
            .join('; ') || fallback;
    }
    return String(detail);
}
