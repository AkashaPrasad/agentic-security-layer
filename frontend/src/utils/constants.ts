// ---------------------------------------------------------------------------
// App-wide constants
// ---------------------------------------------------------------------------

/** How often to poll running experiments (ms) */
export const EXPERIMENT_POLL_INTERVAL = 3000;

/** Default page size for paginated lists */
export const DEFAULT_PAGE_SIZE = 12;

/** Default page size for cursor-paginated logs */
export const DEFAULT_LOG_PAGE_SIZE = 50;

/** Max comment length for feedback */
export const FEEDBACK_COMMENT_MAX_LENGTH = 150;

/** Sidebar width (px) */
export const SIDEBAR_WIDTH = 260;

/** Testing level metadata */
export const TESTING_LEVELS = {
    '50': { label: 'Quick (50)', tests: '50', duration: '1-3 min' },
    '100': { label: 'Small (100)', tests: '100', duration: '3-8 min' },
    '200': { label: 'Medium (200)', tests: '200', duration: '8-15 min' },
    '300': { label: 'Large (300)', tests: '300', duration: '15-25 min' },
    '400': { label: 'XL (400)', tests: '400', duration: '25-40 min' },
    basic: { label: 'Basic', tests: '~500', duration: '5–15 min' },
    moderate: { label: 'Moderate', tests: '~1,200', duration: '15–30 min' },
    aggressive: { label: 'Aggressive', tests: '~2,000', duration: '30–60 min' },
} as const;

/** Experiment sub-type labels */
export const SUB_TYPE_LABELS: Record<string, string> = {
    owasp_llm_top10: 'LLM Threats',
    owasp_agentic: 'Agent Threats',
    adaptive: 'Jailbreak',
    // Behavioural sub-types (backend values)
    functional: 'Baseline',
    user_interaction: 'Stress Test',
    scope_validation: 'Guardrails',
    // Legacy display names kept for backwards compatibility with older stored experiments
    happy_path: 'Baseline',
    edge_cases: 'Stress Test',
};

/** Severity colours */
export const SEVERITY_COLORS = {
    high: '#d32f2f',
    medium: '#ed6c02',
    low: '#2e7d32',
} as const;
