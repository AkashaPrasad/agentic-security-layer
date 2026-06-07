// ---------------------------------------------------------------------------
// Auth types
// ---------------------------------------------------------------------------

export interface User {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    full_name: string;
}

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: 'bearer';
}
