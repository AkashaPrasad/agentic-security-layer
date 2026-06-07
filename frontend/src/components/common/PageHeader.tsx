// ---------------------------------------------------------------------------
// PageHeader — page title + optional action buttons
// ---------------------------------------------------------------------------

import type { ReactNode } from 'react';
import Box from '@mui/material/Box';
import Fade from '@mui/material/Fade';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';

interface PageHeaderProps {
    title: string;
    subtitle?: string;
    actions?: ReactNode;
    children?: ReactNode;
}

export default function PageHeader({ title, subtitle, actions, children }: PageHeaderProps) {
    return (
        <Fade in timeout={250}>
            <Box sx={{ mb: 3 }}>
                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: 2,
                        pb: 2,
                    }}
                >
                    <Box>
                        <Typography
                            variant="h4"
                            component="h1"
                            sx={{ fontWeight: 600, color: 'text.primary', letterSpacing: '-0.01em' }}
                        >
                            {title}
                        </Typography>
                        {subtitle && (
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                {subtitle}
                            </Typography>
                        )}
                        {children}
                    </Box>
                    {actions && (
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>{actions}</Box>
                    )}
                </Box>
                <Divider />
            </Box>
        </Fade>
    );
}
