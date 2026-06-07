// ---------------------------------------------------------------------------
// useProviders — provider CRUD queries / mutations
// ---------------------------------------------------------------------------

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { providerService } from '@/services/providerService';
import type { ProviderCreate, ProviderUpdate } from '@/types/provider';

const KEYS = {
    all: ['providers'] as const,
    detail: (id: string) => ['providers', id] as const,
};

export function useProviders() {
    const queryClient = useQueryClient();

    const list = useQuery({
        queryKey: KEYS.all,
        queryFn: () => providerService.getProviders(),
    });

    const create = useMutation({
        mutationFn: (data: ProviderCreate) => providerService.createProvider(data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: KEYS.all }),
    });

    const update = useMutation({
        mutationFn: ({ id, data }: { id: string; data: ProviderUpdate }) =>
            providerService.updateProvider(id, data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: KEYS.all }),
    });

    const remove = useMutation({
        mutationFn: (id: string) => providerService.deleteProvider(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: KEYS.all }),
    });

    const validate = useMutation({
        mutationFn: (id: string) => providerService.validateProvider(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: KEYS.all }),
    });

    return { list, create, update, remove, validate };
}
