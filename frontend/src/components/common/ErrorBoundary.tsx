// ---------------------------------------------------------------------------
// ErrorBoundary — React error boundary with fallback UI
// ---------------------------------------------------------------------------

import { Component, type ErrorInfo, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, info: ErrorInfo) {
        console.error('ErrorBoundary caught:', error, info);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) return this.props.fallback;

            return (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                    <Typography variant="h5" gutterBottom>
                        Something went wrong
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {this.state.error?.message ?? 'An unexpected error occurred.'}
                    </Typography>
                    <Button variant="outlined" onClick={this.handleReset}>
                        Try Again
                    </Button>
                </Box>
            );
        }

        return this.props.children;
    }
}
