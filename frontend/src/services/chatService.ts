// ---------------------------------------------------------------------------
// Chat service — playground API calls
// ---------------------------------------------------------------------------

import api from './api';
import type { ChatRequest, ChatResponse, ChatProviderOption } from '@/types/chat';

export const chatService = {
    async getProviders(): Promise<ChatProviderOption[]> {
        const res = await api.get<ChatProviderOption[]>('/chat/providers');
        return res.data;
    },

    async sendMessage(data: ChatRequest): Promise<ChatResponse> {
        const res = await api.post<ChatResponse>('/chat', data);
        return res.data;
    },
};
