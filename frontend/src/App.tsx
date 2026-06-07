// ---------------------------------------------------------------------------
// App root — theme + query client + router
// ---------------------------------------------------------------------------

import { useMemo } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { buildTheme } from '@/theme';
import { useUiStore } from '@/store/uiStore';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import { router } from '@/routes';
import WagmiProvider from '@/providers/WagmiProvider';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 30_000,
        },
    },
});

export default function App() {
    const themeMode = useUiStore((s) => s.themeMode);
    const theme = useMemo(() => buildTheme(themeMode), [themeMode]);

    return (
        <ErrorBoundary>
            <WagmiProvider>
                <QueryClientProvider client={queryClient}>
                    <ThemeProvider theme={theme}>
                        <CssBaseline />
                        <RouterProvider router={router} />
                    </ThemeProvider>
                </QueryClientProvider>
            </WagmiProvider>
        </ErrorBoundary>
    );
}
