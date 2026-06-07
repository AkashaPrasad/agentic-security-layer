// ---------------------------------------------------------------------------
// ProviderFormModal — create / edit provider dialog
// ---------------------------------------------------------------------------

import { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import InputAdornment from '@mui/material/InputAdornment';
import IconButton from '@mui/material/IconButton';
import LoadingButton from '@mui/lab/LoadingButton';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import Alert from '@mui/material/Alert';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Collapse from '@mui/material/Collapse';
import type { Provider, ProviderCreate, ProviderUpdate, ProviderType } from '@/types/provider';
import { PROVIDER_OPTIONS } from '@/types/provider';

interface ProviderFormModalProps {
    open: boolean;
    provider?: Provider | null;
    loading?: boolean;
    onSubmit: (data: ProviderCreate | ProviderUpdate, isEdit: boolean) => void;
    onClose: () => void;
}

interface FormValues {
    provider_type: ProviderType;
    name: string;
    api_key: string;
    endpoint_url: string;
    model: string;
    // Rate limiting
    requests_per_minute: string;
    tokens_per_minute: string;
    max_calls_per_experiment: string;
    // Judge config
    judge_api_key: string;
    judge_endpoint: string;
    judge_model: string;
    use_separate_judge: boolean;
    // Default config
    default_target_endpoint: string;
    default_system_prompt: string;
    // Backup key failover
    backup_api_key: string;
    backup_endpoint: string;
    backup_model: string;
    use_backup_key: boolean;
}

export default function ProviderFormModal({
    open,
    provider,
    loading,
    onSubmit,
    onClose,
}: ProviderFormModalProps) {
    const isEdit = Boolean(provider);
    const locked = Boolean(provider?.has_experiments);
    const [showKey, setShowKey] = useState(false);
    const [showJudgeKey, setShowJudgeKey] = useState(false);
    const [showBackupKey, setShowBackupKey] = useState(false);

    const {
        control,
        handleSubmit,
        reset,
        watch,
        formState: { errors },
    } = useForm<FormValues>({
        defaultValues: {
            provider_type: 'openai',
            name: '',
            api_key: '',
            endpoint_url: '',
            model: '',
            requests_per_minute: '',
            tokens_per_minute: '',
            max_calls_per_experiment: '',
            judge_api_key: '',
            judge_endpoint: '',
            judge_model: '',
            use_separate_judge: false,
            default_target_endpoint: '',
            default_system_prompt: '',
            backup_api_key: '',
            backup_endpoint: '',
            backup_model: '',
            use_backup_key: false,
        },
    });

    const providerType = watch('provider_type');
    const useSeparateJudge = watch('use_separate_judge');
    const useBackupKey = watch('use_backup_key');
    const selectedOption = PROVIDER_OPTIONS.find((o) => o.value === providerType);
    const needsEndpoint = selectedOption?.needsEndpoint ?? false;
    const noKey = selectedOption?.noKey ?? false;

    useEffect(() => {
        if (open) {
            if (provider) {
                reset({
                    provider_type: provider.provider_type,
                    name: provider.name,
                    api_key: '',
                    endpoint_url: provider.endpoint_url ?? '',
                    model: provider.model ?? '',
                    requests_per_minute: provider.requests_per_minute != null ? String(provider.requests_per_minute) : '',
                    tokens_per_minute: provider.tokens_per_minute != null ? String(provider.tokens_per_minute) : '',
                    max_calls_per_experiment: provider.max_calls_per_experiment != null ? String(provider.max_calls_per_experiment) : '',
                    judge_api_key: '',
                    judge_endpoint: provider.judge_endpoint ?? '',
                    judge_model: provider.judge_model ?? '',
                    use_separate_judge: provider.use_separate_judge ?? false,
                    default_target_endpoint: provider.default_target_endpoint ?? '',
                    default_system_prompt: provider.default_system_prompt ?? '',
                    backup_api_key: '',
                    backup_endpoint: provider.backup_endpoint ?? '',
                    backup_model: provider.backup_model ?? '',
                    use_backup_key: provider.use_backup_key ?? false,
                });
            } else {
                reset({
                    provider_type: 'openai',
                    name: '',
                    api_key: '',
                    endpoint_url: '',
                    model: '',
                    requests_per_minute: '',
                    tokens_per_minute: '',
                    max_calls_per_experiment: '',
                    judge_api_key: '',
                    judge_endpoint: '',
                    judge_model: '',
                    use_separate_judge: false,
                    default_target_endpoint: '',
                    default_system_prompt: '',
                    backup_api_key: '',
                    backup_endpoint: '',
                    backup_model: '',
                    use_backup_key: false,
                });
            }
            setShowKey(false);
            setShowJudgeKey(false);
            setShowBackupKey(false);
        }
    }, [open, provider, reset]);

    const parseOptionalInt = (val: string): number | null | undefined => {
        if (!val || !val.trim()) return undefined;
        const n = parseInt(val, 10);
        return isNaN(n) ? undefined : n;
    };

    const onFormSubmit = (values: FormValues) => {
        if (isEdit) {
            const data: ProviderUpdate = {};
            if (values.name !== provider?.name) data.name = values.name;
            if (values.api_key) data.api_key = values.api_key;
            if (!locked) {
                if (values.endpoint_url !== (provider?.endpoint_url ?? '')) data.endpoint_url = values.endpoint_url || undefined;
                if (values.model !== (provider?.model ?? '')) data.model = values.model || undefined;
            }
            // Advanced fields
            const rpm = parseOptionalInt(values.requests_per_minute);
            if (rpm !== undefined) data.requests_per_minute = rpm;
            const tpm = parseOptionalInt(values.tokens_per_minute);
            if (tpm !== undefined) data.tokens_per_minute = tpm;
            const maxCalls = parseOptionalInt(values.max_calls_per_experiment);
            if (maxCalls !== undefined) data.max_calls_per_experiment = maxCalls;
            data.use_separate_judge = values.use_separate_judge;
            if (values.judge_api_key) data.judge_api_key = values.judge_api_key;
            if (values.judge_endpoint !== (provider?.judge_endpoint ?? '')) data.judge_endpoint = values.judge_endpoint || undefined;
            if (values.judge_model !== (provider?.judge_model ?? '')) data.judge_model = values.judge_model || undefined;
            if (values.default_target_endpoint !== (provider?.default_target_endpoint ?? '')) data.default_target_endpoint = values.default_target_endpoint || undefined;
            if (values.default_system_prompt !== (provider?.default_system_prompt ?? '')) data.default_system_prompt = values.default_system_prompt || undefined;
            data.use_backup_key = values.use_backup_key;
            if (values.backup_api_key) data.backup_api_key = values.backup_api_key;
            if (values.backup_endpoint !== (provider?.backup_endpoint ?? '')) data.backup_endpoint = values.backup_endpoint || undefined;
            if (values.backup_model !== (provider?.backup_model ?? '')) data.backup_model = values.backup_model || undefined;
            onSubmit(data, true);
        } else {
            const data: ProviderCreate = {
                provider_type: values.provider_type,
                name: values.name,
                api_key: values.api_key,
                ...(values.endpoint_url ? { endpoint_url: values.endpoint_url } : {}),
                ...(values.model ? { model: values.model } : {}),
                // Advanced fields
                requests_per_minute: parseOptionalInt(values.requests_per_minute),
                tokens_per_minute: parseOptionalInt(values.tokens_per_minute),
                max_calls_per_experiment: parseOptionalInt(values.max_calls_per_experiment),
                use_separate_judge: values.use_separate_judge,
                ...(values.judge_api_key ? { judge_api_key: values.judge_api_key } : {}),
                ...(values.judge_endpoint ? { judge_endpoint: values.judge_endpoint } : {}),
                ...(values.judge_model ? { judge_model: values.judge_model } : {}),
                ...(values.default_target_endpoint ? { default_target_endpoint: values.default_target_endpoint } : {}),
                ...(values.default_system_prompt ? { default_system_prompt: values.default_system_prompt } : {}),
                use_backup_key: values.use_backup_key,
                ...(values.backup_api_key ? { backup_api_key: values.backup_api_key } : {}),
                ...(values.backup_endpoint ? { backup_endpoint: values.backup_endpoint } : {}),
                ...(values.backup_model ? { backup_model: values.backup_model } : {}),
            };
            onSubmit(data, false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>{isEdit ? 'Edit Provider' : 'Add Model Provider'}</DialogTitle>
            <form onSubmit={handleSubmit(onFormSubmit)}>
                <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                    {locked && (
                        <Alert severity="info" variant="outlined">
                            This provider is used in experiments. Only the name can be changed.
                        </Alert>
                    )}

                    {/* Provider Type */}
                    <Controller
                        name="provider_type"
                        control={control}
                        render={({ field }) => (
                            <FormControl fullWidth disabled={locked || isEdit}>
                                <InputLabel>Provider Type</InputLabel>
                                <Select {...field} label="Provider Type">
                                    {PROVIDER_OPTIONS.map((opt) => (
                                        <MenuItem key={opt.value} value={opt.value}>
                                            {opt.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        )}
                    />

                    {/* Name */}
                    <Controller
                        name="name"
                        control={control}
                        rules={{ required: 'Name is required' }}
                        render={({ field }) => (
                            <TextField
                                {...field}
                                label="Name"
                                placeholder='e.g. "Production OpenAI"'
                                error={!!errors.name}
                                helperText={errors.name?.message}
                                fullWidth
                            />
                        )}
                    />

                    {/* API Key — hidden for no-key providers like Ollama */}
                    {!noKey && (
                        <Controller
                            name="api_key"
                            control={control}
                            rules={{ required: isEdit ? false : 'API key is required' }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="API Key"
                                    placeholder={isEdit ? '(unchanged)' : 'sk-...'}
                                    type={showKey ? 'text' : 'password'}
                                    disabled={locked}
                                    error={!!errors.api_key}
                                    helperText={errors.api_key?.message}
                                    fullWidth
                                    slotProps={{
                                        input: {
                                            endAdornment: (
                                                <InputAdornment position="end">
                                                    <IconButton
                                                        onClick={() => setShowKey((p) => !p)}
                                                        edge="end"
                                                        size="small"
                                                    >
                                                        {showKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                                    </IconButton>
                                                </InputAdornment>
                                            ),
                                        },
                                    }}
                                />
                            )}
                        />
                    )}

                    {/* Endpoint URL — for Azure, OpenAI-compatible, Ollama */}
                    {(needsEndpoint || providerType === 'ollama') && (
                        <Controller
                            name="endpoint_url"
                            control={control}
                            rules={{
                                required: providerType === 'azure_openai' ? 'Endpoint URL is required for Azure' : false,
                            }}
                            render={({ field }) => (
                                <TextField
                                    {...field}
                                    label="Endpoint URL"
                                    disabled={locked}
                                    placeholder={
                                        providerType === 'azure_openai'
                                            ? 'https://myai.openai.azure.com/...'
                                            : providerType === 'ollama'
                                            ? 'http://localhost:11434/v1 (optional)'
                                            : 'https://your-server/v1'
                                    }
                                    error={!!errors.endpoint_url}
                                    helperText={errors.endpoint_url?.message}
                                    fullWidth
                                />
                            )}
                        />
                    )}

                    {/* Model Override */}
                    <Controller
                        name="model"
                        control={control}
                        render={({ field }) => (
                            <TextField
                                {...field}
                                label="Model Override (optional)"
                                disabled={locked}
                                placeholder={
                                    providerType === 'anthropic'
                                        ? 'e.g. "claude-opus-4-6"'
                                        : providerType === 'gemini'
                                        ? 'e.g. "gemini-2.0-flash"'
                                        : providerType === 'mistral'
                                        ? 'e.g. "mistral-large-latest"'
                                        : 'e.g. "gpt-4o"'
                                }
                                fullWidth
                            />
                        )}
                    />

                    {/* ── Advanced Section ── */}
                    <Accordion
                        disableGutters
                        elevation={0}
                        sx={{
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 2,
                            '&:before': { display: 'none' },
                        }}
                    >
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="body2" fontWeight={600}>
                                Advanced Configuration
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>

                            {/* Rate Limits */}
                            <Box>
                                <Typography variant="caption" color="text.secondary" fontWeight={700} sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                    Rate Limits
                                </Typography>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 1 }}>
                                    <Controller
                                        name="requests_per_minute"
                                        control={control}
                                        render={({ field }) => (
                                            <TextField
                                                {...field}
                                                label="Requests per minute limit"
                                                type="number"
                                                fullWidth
                                                size="small"
                                                helperText="Leave blank to use defaults"
                                                inputProps={{ min: 1 }}
                                            />
                                        )}
                                    />
                                    <Controller
                                        name="tokens_per_minute"
                                        control={control}
                                        render={({ field }) => (
                                            <TextField
                                                {...field}
                                                label="Tokens per minute limit"
                                                type="number"
                                                fullWidth
                                                size="small"
                                                inputProps={{ min: 100 }}
                                            />
                                        )}
                                    />
                                    <Controller
                                        name="max_calls_per_experiment"
                                        control={control}
                                        render={({ field }) => (
                                            <TextField
                                                {...field}
                                                label="Max API calls per experiment"
                                                type="number"
                                                fullWidth
                                                size="small"
                                                inputProps={{ min: 1 }}
                                            />
                                        )}
                                    />
                                </Box>
                            </Box>

                            <Divider />

                            {/* Default Config */}
                            <Box>
                                <Typography variant="caption" color="text.secondary" fontWeight={700} sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                    Default Config (prefills experiments)
                                </Typography>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 1 }}>
                                    <Controller
                                        name="default_target_endpoint"
                                        control={control}
                                        render={({ field }) => (
                                            <TextField
                                                {...field}
                                                label="Default target endpoint (prefills experiments)"
                                                fullWidth
                                                size="small"
                                                placeholder="https://api.example.com/v1/chat"
                                            />
                                        )}
                                    />
                                    <Controller
                                        name="default_system_prompt"
                                        control={control}
                                        render={({ field }) => (
                                            <TextField
                                                {...field}
                                                label="Default system prompt (prefills experiments)"
                                                multiline
                                                rows={3}
                                                fullWidth
                                                size="small"
                                                placeholder="You are a helpful assistant..."
                                            />
                                        )}
                                    />
                                </Box>
                            </Box>

                            <Divider />

                            {/* Judge Config */}
                            <Box>
                                <Typography variant="caption" color="text.secondary" fontWeight={700} sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                    Separate Judge Config
                                </Typography>
                                <Controller
                                    name="use_separate_judge"
                                    control={control}
                                    render={({ field }) => (
                                        <FormControlLabel
                                            control={
                                                <Switch
                                                    checked={Boolean(field.value)}
                                                    onChange={(e) => field.onChange(e.target.checked)}
                                                    size="small"
                                                />
                                            }
                                            label={
                                                <Typography variant="body2">
                                                    Use separate config for judge/evaluation tasks
                                                </Typography>
                                            }
                                            sx={{ mt: 0.5, mb: 0.5 }}
                                        />
                                    )}
                                />
                                <Collapse in={useSeparateJudge}>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 1 }}>
                                        <Controller
                                            name="judge_api_key"
                                            control={control}
                                            render={({ field }) => (
                                                <TextField
                                                    {...field}
                                                    label="Judge API key"
                                                    type={showJudgeKey ? 'text' : 'password'}
                                                    fullWidth
                                                    size="small"
                                                    placeholder={isEdit ? '(unchanged)' : 'sk-...'}
                                                    slotProps={{
                                                        input: {
                                                            endAdornment: (
                                                                <InputAdornment position="end">
                                                                    <IconButton onClick={() => setShowJudgeKey((p) => !p)} edge="end" size="small">
                                                                        {showJudgeKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                                                    </IconButton>
                                                                </InputAdornment>
                                                            ),
                                                        },
                                                    }}
                                                />
                                            )}
                                        />
                                        <Controller
                                            name="judge_endpoint"
                                            control={control}
                                            render={({ field }) => (
                                                <TextField
                                                    {...field}
                                                    label="Judge endpoint (optional)"
                                                    fullWidth
                                                    size="small"
                                                />
                                            )}
                                        />
                                        <Controller
                                            name="judge_model"
                                            control={control}
                                            render={({ field }) => (
                                                <TextField
                                                    {...field}
                                                    label="Judge model"
                                                    fullWidth
                                                    size="small"
                                                    placeholder="e.g. gpt-4o-mini"
                                                />
                                            )}
                                        />
                                    </Box>
                                </Collapse>
                            </Box>

                            <Divider />

                            {/* Backup Key */}
                            <Box>
                                <Typography variant="caption" color="text.secondary" fontWeight={700} sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                    Backup Key Failover
                                </Typography>
                                <Controller
                                    name="use_backup_key"
                                    control={control}
                                    render={({ field }) => (
                                        <FormControlLabel
                                            control={
                                                <Switch
                                                    checked={Boolean(field.value)}
                                                    onChange={(e) => field.onChange(e.target.checked)}
                                                    size="small"
                                                />
                                            }
                                            label={
                                                <Typography variant="body2">
                                                    Enable backup key failover
                                                </Typography>
                                            }
                                            sx={{ mt: 0.5, mb: 0.5 }}
                                        />
                                    )}
                                />
                                <Collapse in={useBackupKey}>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 1 }}>
                                        <Controller
                                            name="backup_api_key"
                                            control={control}
                                            render={({ field }) => (
                                                <TextField
                                                    {...field}
                                                    label="Backup API key"
                                                    type={showBackupKey ? 'text' : 'password'}
                                                    fullWidth
                                                    size="small"
                                                    placeholder={isEdit ? '(unchanged)' : 'sk-...'}
                                                    slotProps={{
                                                        input: {
                                                            endAdornment: (
                                                                <InputAdornment position="end">
                                                                    <IconButton onClick={() => setShowBackupKey((p) => !p)} edge="end" size="small">
                                                                        {showBackupKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                                                    </IconButton>
                                                                </InputAdornment>
                                                            ),
                                                        },
                                                    }}
                                                />
                                            )}
                                        />
                                        <Controller
                                            name="backup_endpoint"
                                            control={control}
                                            render={({ field }) => (
                                                <TextField
                                                    {...field}
                                                    label="Backup endpoint (optional)"
                                                    fullWidth
                                                    size="small"
                                                />
                                            )}
                                        />
                                        <Controller
                                            name="backup_model"
                                            control={control}
                                            render={({ field }) => (
                                                <TextField
                                                    {...field}
                                                    label="Backup model (optional)"
                                                    fullWidth
                                                    size="small"
                                                    placeholder="e.g. gpt-4o"
                                                />
                                            )}
                                        />
                                    </Box>
                                </Collapse>
                            </Box>

                        </AccordionDetails>
                    </Accordion>
                </DialogContent>

                <DialogActions sx={{ px: 3, pb: 2 }}>
                    <Button onClick={onClose}>Cancel</Button>
                    <LoadingButton type="submit" variant="contained" loading={loading}>
                        Save Provider
                    </LoadingButton>
                </DialogActions>
            </form>
        </Dialog>
    );
}
