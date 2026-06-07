// ---------------------------------------------------------------------------
// RegisterPage — name + email + password registration form
// ---------------------------------------------------------------------------

import { useForm, Controller } from 'react-hook-form';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Alert from '@mui/material/Alert';
import LoadingButton from '@mui/lab/LoadingButton';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { useAuth } from '@/hooks/useAuth';
import type { RegisterRequest } from '@/types/auth';
import { extractApiError } from '@/utils/errors';

export default function RegisterPage() {
    const { register: registerMut } = useAuth();

    const {
        control,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterRequest>({
        defaultValues: { full_name: '', email: '', password: '' },
    });

    const onSubmit = (data: RegisterRequest) => {
        registerMut.mutate(data);
    };

    return (
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <Typography variant="h5" sx={{ fontWeight: 700, textAlign: 'center', mb: 0.5 }}>
                Create your account
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mb: 1 }}>
                Start securing your AI systems today
            </Typography>

            {registerMut.isError && (
                <Alert severity="error" sx={{ borderRadius: 2 }}>
                    {extractApiError(registerMut.error, 'Registration failed. Please try again.')}
                </Alert>
            )}

            <Controller
                name="full_name"
                control={control}
                rules={{ required: 'Full name is required' }}
                render={({ field }) => (
                    <TextField
                        {...field}
                        label="Full Name"
                        autoComplete="name"
                        autoFocus
                        error={!!errors.full_name}
                        helperText={errors.full_name?.message}
                        fullWidth
                    />
                )}
            />

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
                        error={!!errors.email}
                        helperText={errors.email?.message}
                        fullWidth
                    />
                )}
            />

            <Controller
                name="password"
                control={control}
                rules={{
                    required: 'Password is required',
                    minLength: { value: 8, message: 'Minimum 8 characters' },
                }}
                render={({ field }) => (
                    <TextField
                        {...field}
                        label="Password"
                        type="password"
                        autoComplete="new-password"
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
                loading={registerMut.isPending}
                startIcon={<PersonAddIcon />}
                sx={{
                    py: 1.4,
                    mt: 0.5,
                    fontSize: '0.9375rem',
                }}
            >
                Create Account
            </LoadingButton>

            <Typography variant="body2" sx={{ textAlign: 'center', mt: 1 }}>
                Already have an account?{' '}
                <Link
                    component={RouterLink}
                    to="/login"
                    sx={{ fontWeight: 600, color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                >
                    Sign in
                </Link>
            </Typography>
        </Box>
    );
}
