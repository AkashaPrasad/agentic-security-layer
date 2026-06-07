// ---------------------------------------------------------------------------
// Axios instance — base API client with interceptors
// ---------------------------------------------------------------------------

import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const api = axios.create({
    baseURL: '/api/v1',
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
                    const { data } = await axios.post('/api/v1/auth/refresh', {
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
