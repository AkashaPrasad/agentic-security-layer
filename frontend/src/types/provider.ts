// ---------------------------------------------------------------------------
// Provider types (matches backend schemas/providers.py)
// ---------------------------------------------------------------------------

import type { UserBrief, PaginatedResponse } from './api';

export type ProviderType =
    | 'openai'
    | 'azure_openai'
    | 'groq'
    | 'anthropic'
    | 'gemini'
    | 'ollama'
    | 'mistral'
    | 'together'
    | 'deepseek'
    | 'perplexity'
    | 'fireworks'
    | 'xai'
    | 'cohere'
    | 'huggingface'
    | 'openai_compatible';

export const PROVIDER_OPTIONS: { value: ProviderType; label: string; needsEndpoint?: boolean; noKey?: boolean }[] = [
    { value: 'openai',           label: 'OpenAI' },
    { value: 'anthropic',        label: 'Anthropic (Claude)' },
    { value: 'gemini',           label: 'Google Gemini' },
    { value: 'groq',             label: 'Groq' },
    { value: 'mistral',          label: 'Mistral AI' },
    { value: 'together',         label: 'Together AI' },
    { value: 'deepseek',         label: 'DeepSeek' },
    { value: 'perplexity',       label: 'Perplexity AI' },
    { value: 'fireworks',        label: 'Fireworks AI' },
    { value: 'xai',              label: 'xAI (Grok)' },
    { value: 'cohere',           label: 'Cohere' },
    { value: 'huggingface',      label: 'HuggingFace' },
    { value: 'azure_openai',     label: 'Azure OpenAI', needsEndpoint: true },
    { value: 'ollama',           label: 'Ollama (Local)', noKey: true },
    { value: 'openai_compatible', label: 'OpenAI-Compatible', needsEndpoint: true },
];

export interface ProviderCreate {
    name: string;
    provider_type: ProviderType;
    api_key: string;
    endpoint_url?: string;
    model?: string;
    // Rate limiting
    requests_per_minute?: number | null;
    tokens_per_minute?: number | null;
    max_calls_per_experiment?: number | null;
    // Judge config
    judge_api_key?: string | null;
    judge_endpoint?: string | null;
    judge_model?: string | null;
    use_separate_judge?: boolean;
    // Default config
    default_target_endpoint?: string | null;
    default_system_prompt?: string | null;
    // Backup key failover
    backup_api_key?: string | null;
    backup_endpoint?: string | null;
    backup_model?: string | null;
    use_backup_key?: boolean;
}

export interface ProviderUpdate {
    name?: string;
    api_key?: string;
    endpoint_url?: string;
    model?: string;
    // Rate limiting
    requests_per_minute?: number | null;
    tokens_per_minute?: number | null;
    max_calls_per_experiment?: number | null;
    // Judge config
    judge_api_key?: string | null;
    judge_endpoint?: string | null;
    judge_model?: string | null;
    use_separate_judge?: boolean;
    // Default config
    default_target_endpoint?: string | null;
    default_system_prompt?: string | null;
    // Backup key failover
    backup_api_key?: string | null;
    backup_endpoint?: string | null;
    backup_model?: string | null;
    use_backup_key?: boolean;
}

export interface Provider {
    id: string;
    name: string;
    provider_type: ProviderType;
    endpoint_url: string | null;
    model: string | null;
    api_key_preview: string;
    is_valid: boolean | null;
    has_experiments: boolean;
    created_by: UserBrief | null;
    created_at: string;
    updated_at: string;
    // Rate limiting
    requests_per_minute?: number | null;
    tokens_per_minute?: number | null;
    max_calls_per_experiment?: number | null;
    // Judge config
    judge_api_key?: string | null;
    judge_endpoint?: string | null;
    judge_model?: string | null;
    use_separate_judge?: boolean;
    // Default config
    default_target_endpoint?: string | null;
    default_system_prompt?: string | null;
    // Backup key failover
    backup_api_key?: string | null;
    backup_endpoint?: string | null;
    backup_model?: string | null;
    use_backup_key?: boolean;
}

export type ProviderList = PaginatedResponse<Provider>;

export interface ProviderValidationResult {
    is_valid: boolean;
    message: string;
    latency_ms: number | null;
}
