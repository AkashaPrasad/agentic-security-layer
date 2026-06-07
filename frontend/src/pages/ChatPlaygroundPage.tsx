// ---------------------------------------------------------------------------
// ChatPlaygroundPage — interactive LLM chat with any configured provider
// ---------------------------------------------------------------------------

import { useState, useRef, useEffect, useCallback } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Slider from '@mui/material/Slider';
import Chip from '@mui/material/Chip';
import Avatar from '@mui/material/Avatar';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import SendIcon from '@mui/icons-material/Send';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import TuneIcon from '@mui/icons-material/Tune';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { useQuery, useMutation } from '@tanstack/react-query';
import { chatService } from '@/services/chatService';
import type { ChatMessage } from '@/types/chat';
import { extractApiError } from '@/utils/errors';

interface DisplayMessage extends ChatMessage {
    id: string;
    latency_ms?: number;
    model?: string;
    error?: string;
}

export default function ChatPlaygroundPage() {
    const [providerId, setProviderId] = useState('');
    const [input, setInput] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [messages, setMessages] = useState<DisplayMessage[]>([]);
    const [temperature, setTemperature] = useState(0.7);
    const [maxTokens, setMaxTokens] = useState(2048);
    const [showSettings, setShowSettings] = useState(false);
    const [copied, setCopied] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const providers = useQuery({
        queryKey: ['chat', 'providers'],
        queryFn: () => chatService.getProviders(),
    });

    const validProviders = providers.data?.filter((p) => p.is_valid) ?? [];

    // Auto-select first valid provider
    useEffect(() => {
        if (!providerId && validProviders.length > 0) {
            setProviderId(validProviders[0].id);
        }
    }, [validProviders, providerId]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMutation = useMutation({
        mutationFn: chatService.sendMessage,
        onSuccess: (res) => {
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: res.content,
                    latency_ms: res.latency_ms,
                    model: res.model,
                },
            ]);
        },
        onError: (err: any) => {
            const detail = extractApiError(err, 'Request failed');
            setMessages((prev) => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: '',
                    error: detail,
                },
            ]);
        },
    });

    const handleSend = useCallback(() => {
        const text = input.trim();
        if (!text || !providerId || sendMutation.isPending) return;

        const userMsg: DisplayMessage = {
            id: crypto.randomUUID(),
            role: 'user',
            content: text,
        };
        const newMessages = [...messages, userMsg];
        setMessages(newMessages);
        setInput('');

        // Build conversation for API
        const apiMessages: ChatMessage[] = [];
        if (systemPrompt.trim()) {
            apiMessages.push({ role: 'system', content: systemPrompt.trim() });
        }
        for (const m of newMessages) {
            apiMessages.push({ role: m.role, content: m.content });
        }

        sendMutation.mutate({
            provider_id: providerId,
            messages: apiMessages,
            temperature,
            max_tokens: maxTokens,
        });
    }, [input, providerId, messages, systemPrompt, temperature, maxTokens, sendMutation]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleClear = () => {
        setMessages([]);
    };

    const handleCopy = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopied(id);
        setTimeout(() => setCopied(null), 1500);
    };

    const selectedProvider = validProviders.find((p) => p.id === providerId);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 88px)', gap: 0 }}>
            {/* Top bar */}
            <Paper
                elevation={0}
                sx={{
                    px: 3,
                    py: 1.5,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    borderRadius: 0,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                    flexWrap: 'wrap',
                }}
            >
                <SmartToyIcon sx={{ color: 'primary.main', fontSize: 28 }} />
                <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: '-0.02em', mr: 'auto' }}>
                    Chat Playground
                </Typography>

                <FormControl size="small" sx={{ minWidth: 200 }}>
                    <InputLabel>Provider</InputLabel>
                    <Select
                        value={providerId}
                        label="Provider"
                        onChange={(e) => setProviderId(e.target.value)}
                    >
                        {validProviders.map((p) => (
                            <MenuItem key={p.id} value={p.id}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Chip
                                        label={p.provider_type}
                                        size="small"
                                        sx={{ fontSize: '0.65rem', height: 20, fontWeight: 700 }}
                                        color={
                                            p.provider_type === 'groq'
                                                ? 'warning'
                                                : p.provider_type === 'openai'
                                                    ? 'success'
                                                    : 'info'
                                        }
                                    />
                                    {p.name}
                                </Box>
                            </MenuItem>
                        ))}
                        {validProviders.length === 0 && (
                            <MenuItem disabled>No valid providers</MenuItem>
                        )}
                    </Select>
                </FormControl>

                {selectedProvider && (
                    <Chip
                        label={selectedProvider.model ?? 'default model'}
                        size="small"
                        variant="outlined"
                        sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}
                    />
                )}

                <Tooltip title="Settings">
                    <IconButton onClick={() => setShowSettings(!showSettings)} size="small">
                        {showSettings ? <ExpandLessIcon /> : <TuneIcon />}
                    </IconButton>
                </Tooltip>

                <Tooltip title="Clear chat">
                    <IconButton onClick={handleClear} size="small" color="error" disabled={messages.length === 0}>
                        <DeleteSweepIcon />
                    </IconButton>
                </Tooltip>
            </Paper>

            {/* Settings panel */}
            <Collapse in={showSettings}>
                <Paper
                    elevation={0}
                    sx={{
                        px: 3,
                        py: 2,
                        borderRadius: 0,
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                        display: 'flex',
                        gap: 4,
                        flexWrap: 'wrap',
                        alignItems: 'flex-start',
                    }}
                >
                    <TextField
                        label="System Prompt"
                        value={systemPrompt}
                        onChange={(e) => setSystemPrompt(e.target.value)}
                        multiline
                        minRows={2}
                        maxRows={4}
                        sx={{ flex: 2, minWidth: 280 }}
                        placeholder="You are a helpful assistant..."
                        size="small"
                    />
                    <Box sx={{ flex: 1, minWidth: 160 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom sx={{ display: 'block' }}>
                            Temperature: {temperature.toFixed(1)}
                        </Typography>
                        <Slider
                            value={temperature}
                            onChange={(_, v) => setTemperature(v as number)}
                            min={0}
                            max={2}
                            step={0.1}
                            size="small"
                            marks={[
                                { value: 0, label: '0' },
                                { value: 1, label: '1' },
                                { value: 2, label: '2' },
                            ]}
                        />
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 160 }}>
                        <Typography variant="caption" color="text.secondary" gutterBottom sx={{ display: 'block' }}>
                            Max Tokens: {maxTokens}
                        </Typography>
                        <Slider
                            value={maxTokens}
                            onChange={(_, v) => setMaxTokens(v as number)}
                            min={64}
                            max={16384}
                            step={64}
                            size="small"
                            marks={[
                                { value: 64, label: '64' },
                                { value: 8192, label: '8K' },
                                { value: 16384, label: '16K' },
                            ]}
                        />
                    </Box>
                </Paper>
            </Collapse>

            {/* No providers warning */}
            {providers.isSuccess && validProviders.length === 0 && (
                <Alert severity="warning" sx={{ mx: 3, mt: 2, borderRadius: 2 }}>
                    No valid providers configured. Go to <strong>Providers</strong> to add and validate your Groq, OpenAI, or Azure key first.
                </Alert>
            )}

            {/* Messages area */}
            <Box
                sx={{
                    flex: 1,
                    overflow: 'auto',
                    px: 3,
                    py: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                }}
            >
                {messages.length === 0 && (
                    <Box
                        sx={{
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 2,
                            opacity: 0.5,
                        }}
                    >
                        <SmartToyIcon sx={{ fontSize: 64, color: 'primary.main' }} />
                        <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 600 }}>
                            Start a conversation
                        </Typography>
                        <Typography variant="body2" color="text.secondary" align="center" sx={{ maxWidth: 400 }}>
                            Select a provider and type a message below. Your Groq key gives you free access to models like Llama 3.3 70B.
                        </Typography>
                    </Box>
                )}

                {messages.map((msg) => (
                    <Box
                        key={msg.id}
                        sx={{
                            display: 'flex',
                            gap: 1.5,
                            flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                            alignItems: 'flex-start',
                        }}
                    >
                        <Avatar
                            sx={{
                                width: 32,
                                height: 32,
                                mt: 0.5,
                                background:
                                    msg.role === 'user'
                                        ? 'linear-gradient(135deg, #FFB800, #E6A600)'
                                        : 'linear-gradient(135deg, #10b981, #059669)',
                                fontSize: 14,
                            }}
                        >
                            {msg.role === 'user' ? <PersonIcon sx={{ fontSize: 18 }} /> : <SmartToyIcon sx={{ fontSize: 18 }} />}
                        </Avatar>

                        <Paper
                            elevation={0}
                            sx={{
                                px: 2,
                                py: 1.5,
                                maxWidth: '75%',
                                borderRadius: 3,
                                bgcolor: msg.role === 'user' ? 'primary.main' : 'action.hover',
                                color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                                position: 'relative',
                            }}
                        >
                            {msg.error ? (
                                <Typography variant="body2" color="error.main" sx={{ fontStyle: 'italic' }}>
                                    {msg.error}
                                </Typography>
                            ) : (
                                <Typography
                                    variant="body2"
                                    sx={{
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        lineHeight: 1.7,
                                        '& code': {
                                            fontFamily: 'monospace',
                                            bgcolor: msg.role === 'user' ? 'rgba(255,255,255,0.15)' : 'action.selected',
                                            px: 0.5,
                                            borderRadius: 0.5,
                                            fontSize: '0.85em',
                                        },
                                    }}
                                >
                                    {msg.content}
                                </Typography>
                            )}

                            {/* Meta info for assistant messages */}
                            {msg.role === 'assistant' && !msg.error && (
                                <Box
                                    sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 1,
                                        mt: 1,
                                        pt: 1,
                                        borderTop: '1px solid',
                                        borderColor: 'divider',
                                    }}
                                >
                                    {msg.model && (
                                        <Chip
                                            label={msg.model}
                                            size="small"
                                            variant="outlined"
                                            sx={{ fontSize: '0.65rem', height: 20, fontFamily: 'monospace' }}
                                        />
                                    )}
                                    {msg.latency_ms != null && (
                                        <Typography variant="caption" color="text.secondary">
                                            {msg.latency_ms}ms
                                        </Typography>
                                    )}
                                    <Tooltip title={copied === msg.id ? 'Copied!' : 'Copy'}>
                                        <IconButton
                                            size="small"
                                            onClick={() => handleCopy(msg.content, msg.id)}
                                            sx={{ ml: 'auto', opacity: 0.6, '&:hover': { opacity: 1 } }}
                                        >
                                            <ContentCopyIcon sx={{ fontSize: 14 }} />
                                        </IconButton>
                                    </Tooltip>
                                </Box>
                            )}
                        </Paper>
                    </Box>
                ))}

                {/* Typing indicator */}
                {sendMutation.isPending && (
                    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
                        <Avatar
                            sx={{
                                width: 32,
                                height: 32,
                                mt: 0.5,
                                background: 'linear-gradient(135deg, #10b981, #059669)',
                                fontSize: 14,
                            }}
                        >
                            <SmartToyIcon sx={{ fontSize: 18 }} />
                        </Avatar>
                        <Paper
                            elevation={0}
                            sx={{ px: 2.5, py: 2, borderRadius: 3, bgcolor: 'action.hover' }}
                        >
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                                {[0, 1, 2].map((i) => (
                                    <Box
                                        key={i}
                                        sx={{
                                            width: 8,
                                            height: 8,
                                            borderRadius: '50%',
                                            bgcolor: 'text.secondary',
                                            animation: 'pulse 1.4s infinite',
                                            animationDelay: `${i * 0.2}s`,
                                            '@keyframes pulse': {
                                                '0%, 80%, 100%': { opacity: 0.3, transform: 'scale(0.8)' },
                                                '40%': { opacity: 1, transform: 'scale(1)' },
                                            },
                                        }}
                                    />
                                ))}
                            </Box>
                        </Paper>
                    </Box>
                )}

                <div ref={messagesEndRef} />
            </Box>

            {/* Input area */}
            <Divider />
            <Paper
                elevation={0}
                sx={{
                    px: 3,
                    py: 2,
                    borderRadius: 0,
                    display: 'flex',
                    gap: 1.5,
                    alignItems: 'flex-end',
                }}
            >
                <TextField
                    inputRef={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={
                        validProviders.length === 0
                            ? 'Add a provider first...'
                            : 'Type a message... (Enter to send, Shift+Enter for newline)'
                    }
                    multiline
                    maxRows={6}
                    fullWidth
                    disabled={validProviders.length === 0}
                    size="small"
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            borderRadius: 3,
                        },
                    }}
                />
                <Button
                    variant="contained"
                    onClick={handleSend}
                    disabled={!input.trim() || !providerId || sendMutation.isPending}
                    sx={{
                        minWidth: 48,
                        height: 40,
                        borderRadius: 3,
                        px: 2,
                    }}
                >
                    {sendMutation.isPending ? (
                        <CircularProgress size={20} color="inherit" />
                    ) : (
                        <SendIcon fontSize="small" />
                    )}
                </Button>
            </Paper>
        </Box>
    );
}
