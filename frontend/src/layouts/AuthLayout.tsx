import { Outlet } from 'react-router-dom';
import Box from '@mui/material/Box';
import Fade from '@mui/material/Fade';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import AgentShieldLogo from '@/components/common/AgentShieldLogo';

export default function AuthLayout() {
    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                p: 3,
                bgcolor: 'background.default',
                backgroundImage: (t) => t.palette.mode === 'dark'
                    ? 'radial-gradient(circle, rgba(48,54,61,0.5) 1px, transparent 1px)'
                    : 'radial-gradient(circle, rgba(208,215,222,0.6) 1px, transparent 1px)',
                backgroundSize: '24px 24px',
            }}
        >
            <Fade in timeout={300}>
                <Box sx={{ width: '100%', maxWidth: 400 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3, justifyContent: 'center' }}>
                        <AgentShieldLogo size={32} />
                        <Typography
                            variant="h6"
                            sx={{ fontWeight: 700, fontSize: '1.1rem', color: 'text.primary', letterSpacing: '-0.02em' }}
                        >
                            AgentShield
                        </Typography>
                    </Box>

                    <Paper variant="outlined" sx={{ p: { xs: 3, sm: 4 }, borderRadius: '8px' }}>
                        <Outlet />
                    </Paper>

                    <Typography
                        variant="caption"
                        sx={{ display: 'block', textAlign: 'center', mt: 3, color: 'text.secondary' }}
                    >
                        On-Chain AI Security for the Monad Agent Economy
                    </Typography>
                </Box>
            </Fade>
        </Box>
    );
}
