// ---------------------------------------------------------------------------
// Auth service — login, register, refresh, getMe
// ---------------------------------------------------------------------------

import api from './api';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types/auth';

export const authService = {
    async login(data: LoginRequest): Promise<TokenResponse> {
        const res = await api.post<TokenResponse>('/auth/login', data);
        return res.data;
    },

    async register(data: RegisterRequest): Promise<TokenResponse> {
        const res = await api.post<TokenResponse>('/auth/register', data);
        return res.data;
    },

    async refresh(refreshToken: string): Promise<TokenResponse> {
        const res = await api.post<TokenResponse>('/auth/refresh', {
            refresh_token: refreshToken,
        });
        return res.data;
    },

    async getMe(): Promise<User> {
        const res = await api.get<User>('/auth/me');
        return res.data;
    },
};
