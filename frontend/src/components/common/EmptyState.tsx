// ---------------------------------------------------------------------------
// EmptyState — placeholder with icon + CTA
// ---------------------------------------------------------------------------

import type { ReactNode } from 'react';
import Box from '@mui/material/Box';
import Fade from '@mui/material/Fade';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';

interface EmptyStateProps {
    icon?: ReactNode;
    title: string;
    description?: string;
    actionLabel?: string;
    onAction?: () => void;
}

export default function EmptyState({ icon, title, description, actionLabel, onAction }: EmptyStateProps) {
    return (
        <Fade in timeout={350}>
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    py: 10,
                    px: 3,
                    textAlign: 'center',
                }}
            >
                {icon && (
                    <Box
                        sx={{
                            mb: 2.5,
                            width: 64,
                            height: 64,
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            bgcolor: (t) => t.palette.mode === 'dark' ? '#21262D' : '#F0F3F6',
                            border: (t) => `1px solid ${t.palette.divider}`,
                            color: 'text.secondary',
                            '& > svg': { fontSize: 28 },
                        }}
                    >
                        {icon}
                    </Box>
                )}
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.75, color: 'text.primary' }}>
                    {title}
                </Typography>
                {description && (
                    <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 3, maxWidth: 380, lineHeight: 1.6 }}
                    >
                        {description}
                    </Typography>
                )}
                {actionLabel && onAction && (
                    <Button variant="outlined" startIcon={<AddIcon />} onClick={onAction} size="small">
                        {actionLabel}
                    </Button>
                )}
            </Box>
        </Fade>
    );
}
