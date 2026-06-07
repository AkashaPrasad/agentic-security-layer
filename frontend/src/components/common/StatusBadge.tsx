// ---------------------------------------------------------------------------
// StatusBadge — color-coded status chip with dot indicator
// ---------------------------------------------------------------------------

import Chip, { type ChipProps } from '@mui/material/Chip';
import Box from '@mui/material/Box';

type Status =
    | 'pass' | 'fail' | 'error' | 'running' | 'pending'
    | 'completed' | 'cancelled' | 'failed' | 'passed'
    | 'blocked' | 'active' | 'inactive';

const COLOR_MAP: Record<Status, ChipProps['color']> = {
    pass: 'success',
    passed: 'success',
    completed: 'success',
    active: 'success',
    fail: 'error',
    failed: 'error',
    blocked: 'error',
    inactive: 'default',
    error: 'warning',
    running: 'info',
    pending: 'default',
    cancelled: 'default',
};

const DOT_COLORS: Record<Status, string> = {
    pass: '#10b981',
    passed: '#10b981',
    completed: '#10b981',
    active: '#10b981',
    fail: '#ef4444',
    failed: '#ef4444',
    blocked: '#ef4444',
    inactive: '#94a3b8',
    error: '#f59e0b',
    running: '#3b82f6',
    pending: '#94a3b8',
    cancelled: '#94a3b8',
};

interface StatusBadgeProps {
    status: string;
    size?: 'small' | 'medium';
}

export default function StatusBadge({ status, size = 'small' }: StatusBadgeProps) {
    const color = COLOR_MAP[status as Status] ?? 'default';
    const dotColor = DOT_COLORS[status as Status] ?? '#94a3b8';
    const isRunning = status === 'running';

    return (
        <Chip
            label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                    <Box
                        sx={{
                            width: 7,
                            height: 7,
                            borderRadius: '50%',
                            bgcolor: dotColor,
                            flexShrink: 0,
                            transition: 'background-color 0.3s ease',
                            ...(isRunning && {
                                animation: 'statusPulse 1.4s ease-in-out infinite',
                                boxShadow: `0 0 6px ${dotColor}`,
                                '@keyframes statusPulse': {
                                    '0%, 100%': { opacity: 1, transform: 'scale(1)' },
                                    '50%': { opacity: 0.5, transform: 'scale(0.85)' },
                                },
                            }),
                        }}
                    />
                    {status.replace('_', ' ').charAt(0).toUpperCase() + status.replace('_', ' ').slice(1)}
                </Box>
            }
            color={color}
            size={size}
            variant="filled"
        />
    );
}
