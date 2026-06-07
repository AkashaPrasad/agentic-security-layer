// ---------------------------------------------------------------------------
// LoadingScreen — full-page loading indicator
// ---------------------------------------------------------------------------

import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Fade from '@mui/material/Fade';
import Typography from '@mui/material/Typography';

export default function LoadingScreen() {
    return (
        <Fade in timeout={300}>
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '60vh',
                    gap: 2,
                }}
            >
                <CircularProgress
                    size={32}
                    thickness={2.5}
                    sx={{
                        color: 'primary.main',
                        '& .MuiCircularProgress-circle': { strokeLinecap: 'round' },
                    }}
                />
                <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ letterSpacing: '0.06em', textTransform: 'uppercase' }}
                >
                    Loading
                </Typography>
            </Box>
        </Fade>
    );
}
