import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AuthGuard from '@/components/auth/AuthGuard';
import AuthLayout from '@/layouts/AuthLayout';
import DashboardLayout from '@/layouts/DashboardLayout';
import LoadingScreen from '@/components/common/LoadingScreen';

const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const ProvidersPage = lazy(() => import('@/pages/ProvidersPage'));
const ChatPlaygroundPage = lazy(() => import('@/pages/ChatPlaygroundPage'));
const AgentExplorerPage = lazy(() => import('@/pages/AgentExplorerPage'));
const AgentVerifyPage = lazy(() => import('@/pages/AgentVerifyPage'));

function Loadable({ children }: { children: React.ReactNode }) {
    return <Suspense fallback={<LoadingScreen />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
    {
        element: <AuthLayout />,
        children: [
            { path: '/login', element: <Loadable><LoginPage /></Loadable> },
            { path: '/register', element: <Loadable><RegisterPage /></Loadable> },
        ],
    },
    {
        element: (
            <AuthGuard>
                <DashboardLayout />
            </AuthGuard>
        ),
        children: [
            { path: '/', element: <Loadable><DashboardPage /></Loadable> },
            { path: '/explorer', element: <Loadable><AgentExplorerPage /></Loadable> },
            { path: '/verify/:agentId', element: <Loadable><AgentVerifyPage /></Loadable> },
            { path: '/playground', element: <Loadable><ChatPlaygroundPage /></Loadable> },
            { path: '/settings/providers', element: <Loadable><ProvidersPage /></Loadable> },
            // Legacy redirects
            { path: '/agentshield', element: <Navigate to="/" replace /> },
            { path: '/agentshield/explorer', element: <Navigate to="/explorer" replace /> },
            { path: '/agentshield/verify/:agentId', element: <Loadable><AgentVerifyPage /></Loadable> },
        ],
    },
    { path: '*', element: <Navigate to="/" replace /> },
]);
