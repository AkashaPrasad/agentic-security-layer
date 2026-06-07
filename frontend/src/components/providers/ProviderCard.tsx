// ---------------------------------------------------------------------------
// ProviderCard — displays a single provider with actions
// ---------------------------------------------------------------------------

import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Box from '@mui/material/Box';
import Avatar from '@mui/material/Avatar';
import CircularProgress from '@mui/material/CircularProgress';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import LinkIcon from '@mui/icons-material/Link';
import PersonIcon from '@mui/icons-material/Person';
import VerifiedIcon from '@mui/icons-material/Verified';
import LockIcon from '@mui/icons-material/Lock';
import { formatDate } from '@/utils/formatters';
import type { Provider } from '@/types/provider';

interface ProviderCardProps {
    provider: Provider;
    validating?: boolean;
    onValidate: (id: string) => void;
    onEdit: (provider: Provider) => void;
    onDelete: (provider: Provider) => void;
}

const TYPE_GRADIENT: Record<string, string> = {
    openai:              'linear-gradient(135deg, #10b981, #34d399)',
    azure_openai:        'linear-gradient(135deg, #3b82f6, #60a5fa)',
    anthropic:           'linear-gradient(135deg, #f97316, #fb923c)',
    groq:                'linear-gradient(135deg, #FFB800, #FFC933)',
    ollama:              'linear-gradient(135deg, #6b7280, #9ca3af)',
    mistral:             'linear-gradient(135deg, #FFB800, #E6A600)',
    together:            'linear-gradient(135deg, #0ea5e9, #38bdf8)',
    deepseek:            'linear-gradient(135deg, #06b6d4, #22d3ee)',
    perplexity:          'linear-gradient(135deg, #14b8a6, #2dd4bf)',
    fireworks:           'linear-gradient(135deg, #ef4444, #f87171)',
    xai:                 'linear-gradient(135deg, #1a1a1a, #404040)',
    cohere:              'linear-gradient(135deg, #FFB800, #FCD34D)',
    huggingface:         'linear-gradient(135deg, #f59e0b, #fbbf24)',
    openai_compatible:   'linear-gradient(135deg, #64748b, #94a3b8)',
};

export default function ProviderCard({
    provider,
    validating,
    onValidate,
    onEdit,
    onDelete,
}: ProviderCardProps) {
    const typeLabelMap: Record<string, string> = {
        openai: 'OpenAI', azure_openai: 'Azure OpenAI', anthropic: 'Anthropic',
        groq: 'Groq', ollama: 'Ollama', mistral: 'Mistral', together: 'Together AI',
        deepseek: 'DeepSeek', perplexity: 'Perplexity', fireworks: 'Fireworks AI',
        xai: 'xAI (Grok)', cohere: 'Cohere', huggingface: 'HuggingFace',
        openai_compatible: 'OpenAI-Compatible',
    };
    const typeLabel = typeLabelMap[provider.provider_type] ?? provider.provider_type;
    const gradient = TYPE_GRADIENT[provider.provider_type] ?? 'linear-gradient(135deg, #FFB800, #E6A600)';

    return (
        <Card
            variant="outlined"
            sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
            }}
        >
            {/* Top accent */}
            <Box sx={{ height: 3, width: '100%', background: gradient, borderRadius: '18px 18px 0 0' }} />

            <CardContent sx={{ flex: 1, pt: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Avatar sx={{ width: 40, height: 40, background: gradient, fontSize: 18 }}>
                        <SmartToyIcon sx={{ fontSize: 20 }} />
                    </Avatar>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                            <Typography
                                variant="subtitle1"
                                sx={{
                                    fontWeight: 700,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                }}
                            >
                                {provider.name}
                            </Typography>
                            {provider.is_valid === true && (
                                <CheckCircleIcon color="success" sx={{ fontSize: 16 }} />
                            )}
                            {provider.is_valid === false && (
                                <CancelIcon color="error" sx={{ fontSize: 16 }} />
                            )}
                        </Box>
                        <Chip label={typeLabel} size="small" color="primary" sx={{ mt: 0.5, height: 20, fontSize: '0.7rem' }} />
                        {provider.has_experiments && (
                            <Tooltip title="Used in experiments — core settings locked">
                                <LockIcon sx={{ fontSize: 14, color: 'warning.main', ml: 0.5 }} />
                            </Tooltip>
                        )}
                    </Box>
                </Box>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                        <VpnKeyIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                        <Typography variant="caption" color="text.secondary">
                            {provider.api_key_preview}
                        </Typography>
                    </Box>

                    {provider.endpoint_url && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                            <LinkIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                            <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                            >
                                {provider.endpoint_url}
                            </Typography>
                        </Box>
                    )}

                    {provider.model && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                            <SmartToyIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">
                                {provider.model}
                            </Typography>
                        </Box>
                    )}

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mt: 0.5 }}>
                        <PersonIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                        <Typography variant="caption" color="text.secondary">
                            {provider.created_by?.email ? `${provider.created_by.email} · ` : ''}{formatDate(provider.created_at)}
                        </Typography>
                    </Box>

                    {/* Advanced config indicator chips */}
                    {(provider.use_backup_key || provider.use_separate_judge || provider.max_calls_per_experiment != null) && (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                            {provider.use_backup_key && (
                                <Chip label="Backup" size="small" color="warning" variant="outlined" sx={{ height: 18, fontSize: '0.68rem' }} />
                            )}
                            {provider.use_separate_judge && (
                                <Chip label="Judge config" size="small" color="info" variant="outlined" sx={{ height: 18, fontSize: '0.68rem' }} />
                            )}
                            {provider.max_calls_per_experiment != null && (
                                <Chip label={`Call limit: ${provider.max_calls_per_experiment}`} size="small" variant="outlined" sx={{ height: 18, fontSize: '0.68rem' }} />
                            )}
                        </Box>
                    )}
                </Box>
            </CardContent>

            <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2, pt: 0, gap: 0.5 }}>
                <Button
                    size="small"
                    variant="outlined"
                    onClick={() => onValidate(provider.id)}
                    disabled={validating}
                    startIcon={
                        validating ? <CircularProgress size={14} /> : <VerifiedIcon sx={{ fontSize: 16 }} />
                    }
                >
                    Validate
                </Button>
                <Tooltip title="Edit provider">
                    <IconButton size="small" onClick={() => onEdit(provider)}>
                        <EditIcon fontSize="small" />
                    </IconButton>
                </Tooltip>
                <Tooltip title="Delete provider">
                    <IconButton
                        size="small"
                        color="error"
                        onClick={() => onDelete(provider)}
                    >
                        <DeleteIcon fontSize="small" />
                    </IconButton>
                </Tooltip>
            </CardActions>
        </Card>
    );
}
