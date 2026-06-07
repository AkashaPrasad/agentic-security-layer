// ---------------------------------------------------------------------------
// Provider service — CRUD + validate
// ---------------------------------------------------------------------------

import api from './api';
import type {
    Provider,
    ProviderCreate,
    ProviderUpdate,
    ProviderList,
    ProviderValidationResult,
} from '@/types/provider';

export const providerService = {
    async getProviders(): Promise<ProviderList> {
        const res = await api.get<ProviderList>('/providers');
        return res.data;
    },

    async getProvider(id: string): Promise<Provider> {
        const res = await api.get<Provider>(`/providers/${id}`);
        return res.data;
    },

    async createProvider(data: ProviderCreate): Promise<Provider> {
        const res = await api.post<Provider>('/providers', data);
        return res.data;
    },

    async updateProvider(id: string, data: ProviderUpdate): Promise<Provider> {
        const res = await api.put<Provider>(`/providers/${id}`, data);
        return res.data;
    },

    async deleteProvider(id: string): Promise<void> {
        await api.delete(`/providers/${id}`);
    },

    async validateProvider(id: string): Promise<ProviderValidationResult> {
        const res = await api.post<ProviderValidationResult>(`/providers/${id}/validate`);
        return res.data;
    },
};
