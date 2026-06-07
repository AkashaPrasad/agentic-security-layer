// ---------------------------------------------------------------------------
// useAuth — login / register mutations, user query
// ---------------------------------------------------------------------------

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';
import type { LoginRequest, RegisterRequest } from '@/types/auth';

export function useAuth() {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const { setTokens, setUser, logout: clearAuth, isAuthenticated } = useAuthStore();

    const userQuery = useQuery({
        queryKey: ['auth', 'me'],
        queryFn: () => authService.getMe(),
        enabled: isAuthenticated,
        retry: false,
        staleTime: 5 * 60 * 1000,
    });

    // Keep store in sync with fetched user
    if (userQuery.data && !useAuthStore.getState().user) {
        setUser(userQuery.data);
    }

    const loginMutation = useMutation({
        mutationFn: (data: LoginRequest) => authService.login(data),
        onSuccess: async (tokens) => {
            setTokens(tokens.access_token, tokens.refresh_token);
            const user = await authService.getMe();
            setUser(user);
            queryClient.setQueryData(['auth', 'me'], user);
            navigate('/');
        },
    });

    const registerMutation = useMutation({
        mutationFn: (data: RegisterRequest) => authService.register(data),
        onSuccess: async (tokens) => {
            setTokens(tokens.access_token, tokens.refresh_token);
            const user = await authService.getMe();
            setUser(user);
            queryClient.setQueryData(['auth', 'me'], user);
            navigate('/');
        },
    });

    const logout = () => {
        clearAuth();
        queryClient.clear();
        navigate('/login');
    };

    return {
        user: userQuery.data ?? useAuthStore.getState().user,
        isAuthenticated,
        isLoading: userQuery.isLoading,
        login: loginMutation,
        register: registerMutation,
        logout,
    };
}
