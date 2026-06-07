// ---------------------------------------------------------------------------
// ProvidersPage — manage LLM provider credentials
// ---------------------------------------------------------------------------

import { useState } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import Skeleton from '@mui/material/Skeleton';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import AddIcon from '@mui/icons-material/Add';
import PowerOffIcon from '@mui/icons-material/PowerOff';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import ProviderCard from '@/components/providers/ProviderCard';
import ProviderFormModal from '@/components/providers/ProviderFormModal';
import { useProviders } from '@/hooks/useProviders';
import type { Provider, ProviderCreate, ProviderUpdate } from '@/types/provider';

export default function ProvidersPage() {
    const { list, create, update, remove, validate } = useProviders();
    const providers = list.data?.items ?? [];

    const [formOpen, setFormOpen] = useState(false);
    const [editProvider, setEditProvider] = useState<Provider | null>(null);
    const [deleteTarget, setDeleteTarget] = useState<Provider | null>(null);
    const [validatingId, setValidatingId] = useState<string | null>(null);

    // Snackbar state
    const [snack, setSnack] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);

    const handleOpenCreate = () => {
        setEditProvider(null);
        setFormOpen(true);
    };

    const handleOpenEdit = (provider: Provider) => {
        setEditProvider(provider);
        setFormOpen(true);
    };

    const handleFormSubmit = (data: ProviderCreate | ProviderUpdate, isEdit: boolean) => {
        if (isEdit && editProvider) {
            update.mutate(
                { id: editProvider.id, data: data as ProviderUpdate },
                {
                    onSuccess: () => {
                        setFormOpen(false);
                        setSnack({ message: 'Provider updated.', severity: 'success' });
                    },
                    onError: () => setSnack({ message: 'Failed to update provider.', severity: 'error' }),
                },
            );
        } else {
            create.mutate(data as ProviderCreate, {
                onSuccess: () => {
                    setFormOpen(false);
                    setSnack({ message: 'Provider created.', severity: 'success' });
                },
                onError: () => setSnack({ message: 'Failed to create provider.', severity: 'error' }),
            });
        }
    };

    const handleValidate = (id: string) => {
        setValidatingId(id);
        validate.mutate(id, {
            onSuccess: (result) => {
                setValidatingId(null);
                setSnack({
                    message: result.is_valid
                        ? `Provider is valid${result.latency_ms != null ? ` (${result.latency_ms}ms)` : ''}.`
                        : `Validation failed: ${result.message}`,
                    severity: result.is_valid ? 'success' : 'error',
                });
            },
            onError: () => {
                setValidatingId(null);
                setSnack({ message: 'Validation request failed.', severity: 'error' });
            },
        });
    };

    const handleDelete = () => {
        if (!deleteTarget) return;
        remove.mutate(deleteTarget.id, {
            onSuccess: () => {
                setDeleteTarget(null);
                setSnack({ message: 'Provider deleted.', severity: 'success' });
            },
            onError: () => setSnack({ message: 'Failed to delete provider.', severity: 'error' }),
        });
    };

    return (
        <Box>
            <PageHeader
                title="Model Providers"
                subtitle="Configure LLM provider credentials for experiments and firewall"
                actions={
                    <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={handleOpenCreate}
                        sx={{ px: 3 }}
                    >
                        Add Provider
                    </Button>
                }
            />

            {/* Loading */}
            {list.isLoading && (
                <Grid container spacing={3}>
                    {[1, 2, 3].map((i) => (
                        <Grid key={i} size={{ xs: 12, sm: 6, md: 4 }}>
                            <Skeleton variant="rounded" height={240} sx={{ borderRadius: 4 }} />
                        </Grid>
                    ))}
                </Grid>
            )}

            {/* Empty */}
            {!list.isLoading && providers.length === 0 && (
                <EmptyState
                    icon={<PowerOffIcon />}
                    title="No model providers configured"
                    description="Add a provider to power experiments and the firewall."
                    actionLabel="Add Provider"
                    onAction={handleOpenCreate}
                />
            )}

            {/* Cards */}
            {!list.isLoading && providers.length > 0 && (
                <Grid container spacing={3}>
                    {providers.map((p) => (
                        <Grid key={p.id} size={{ xs: 12, sm: 6, md: 4 }}>
                            <ProviderCard
                                provider={p}
                                validating={validatingId === p.id}
                                onValidate={handleValidate}
                                onEdit={handleOpenEdit}
                                onDelete={setDeleteTarget}
                            />
                        </Grid>
                    ))}
                </Grid>
            )}

            {/* Form Modal */}
            <ProviderFormModal
                open={formOpen}
                provider={editProvider}
                loading={create.isPending || update.isPending}
                onSubmit={handleFormSubmit}
                onClose={() => setFormOpen(false)}
            />

            {/* Delete Confirmation */}
            <ConfirmDialog
                open={!!deleteTarget}
                title="Delete Provider?"
                message={`Are you sure you want to delete "${deleteTarget?.name}"? Experiments using this provider will no longer be able to run.`}
                confirmLabel="Delete"
                confirmColor="error"
                loading={remove.isPending}
                onConfirm={handleDelete}
                onCancel={() => setDeleteTarget(null)}
            />

            {/* Snackbar */}
            <Snackbar
                open={!!snack}
                autoHideDuration={4000}
                onClose={() => setSnack(null)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert
                    severity={snack?.severity}
                    onClose={() => setSnack(null)}
                    variant="filled"
                >
                    {snack?.message}
                </Alert>
            </Snackbar>
        </Box>
    );
}
