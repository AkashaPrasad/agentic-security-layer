// ---------------------------------------------------------------------------
// LoginPage — email + password login form
// ---------------------------------------------------------------------------

import { useForm, Controller } from 'react-hook-form';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Alert from '@mui/material/Alert';
import LoadingButton from '@mui/lab/LoadingButton';
import LoginIcon from '@mui/icons-material/Login';
import { useAuth } from '@/hooks/useAuth';
import type { LoginRequest } from '@/types/auth';
import { extractApiError } from '@/utils/errors';

export default function LoginPage() {
    const { login } = useAuth();

    const {
        control,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginRequest>({
        defaultValues: { email: '', password: '' },
    });

    const onSubmit = (data: LoginRequest) => {
        login.mutate(data);
    };

    return (
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, textAlign: 'center', mb: 0.5 }}>
                Welcome back
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mb: 1 }}>
                Enter your credentials to access your account
            </Typography>

            {login.isError && (
                <Alert severity="error" sx={{ borderRadius: 2 }}>
                    {extractApiError(login.error, 'Login failed. Please check your credentials.')}
                </Alert>
            )}

            <Controller
                name="email"
                control={control}
                rules={{
                    required: 'Email is required',
                    pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Invalid email' },
                }}
                render={({ field }) => (
                    <TextField
                        {...field}
                        label="Email"
                        type="email"
                        autoComplete="email"
                        autoFocus
                        error={!!errors.email}
                        helperText={errors.email?.message}
                        fullWidth
                    />
                )}
            />

            <Controller
                name="password"
                control={control}
                rules={{ required: 'Password is required' }}
                render={({ field }) => (
                    <TextField
                        {...field}
                        label="Password"
                        type="password"
                        autoComplete="current-password"
                        error={!!errors.password}
                        helperText={errors.password?.message}
                        fullWidth
                    />
                )}
            />

            <LoadingButton
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                loading={login.isPending}
                startIcon={<LoginIcon />}
                sx={{
                    py: 1.4,
                    mt: 0.5,
                    fontSize: '0.9375rem',
                }}
            >
                Sign In
            </LoadingButton>

            <Typography variant="body2" sx={{ textAlign: 'center', mt: 1 }}>
                Don&apos;t have an account?{' '}
                <Link
                    component={RouterLink}
                    to="/register"
                    sx={{ fontWeight: 600, color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                >
                    Create account
                </Link>
            </Typography>
        </Box>
    );
}
