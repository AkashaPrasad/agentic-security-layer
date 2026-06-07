// ---------------------------------------------------------------------------
// Axios instance — base API client with interceptors
// ---------------------------------------------------------------------------

import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

// VITE_API_URL is injected at build time on Railway (e.g. https://backend.up.railway.app/api/v1)
// Falls back to '/api/v1' for local dev (vite proxy handles it)
const BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1';

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ── Request interceptor: attach JWT token ──
api.interceptors.request.use((config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ── Response interceptor: handle 401 & refresh ──
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config;

        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;

            const refreshToken = useAuthStore.getState().refreshToken;
            if (refreshToken) {
                try {
                    const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });
                    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
                    original.headers.Authorization = `Bearer ${data.access_token}`;
                    return api(original);
                } catch {
                    useAuthStore.getState().logout();
                }
            } else {
                useAuthStore.getState().logout();
            }
        }

        return Promise.reject(error);
    },
);

export default api;
