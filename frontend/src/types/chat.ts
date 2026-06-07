// ---------------------------------------------------------------------------
// Chat Playground types
// ---------------------------------------------------------------------------

export interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

export interface ChatRequest {
    provider_id: string;
    messages: ChatMessage[];
    temperature: number;
    max_tokens: number;
}

export interface ChatResponse {
    content: string;
    model: string;
    provider_type: string;
    latency_ms: number;
}

export interface ChatProviderOption {
    id: string;
    name: string;
    provider_type: string;
    model: string | null;
    is_valid: boolean;
}
