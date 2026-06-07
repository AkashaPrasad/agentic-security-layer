// ---------------------------------------------------------------------------
// ConfirmDialog — reusable confirmation modal
// ---------------------------------------------------------------------------

import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import LoadingButton from '@mui/lab/LoadingButton';

interface ConfirmDialogProps {
    open: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    confirmColor?: 'error' | 'primary' | 'warning';
    loading?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmDialog({
    open,
    title,
    message,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    confirmColor = 'error',
    loading = false,
    onConfirm,
    onCancel,
}: ConfirmDialogProps) {
    return (
        <Dialog open={open} onClose={onCancel} maxWidth="xs" fullWidth>
            <DialogTitle>{title}</DialogTitle>
            <DialogContent>
                <Typography variant="body2">{message}</Typography>
            </DialogContent>
            <DialogActions>
                <Button onClick={onCancel} disabled={loading}>
                    {cancelLabel}
                </Button>
                <LoadingButton
                    onClick={onConfirm}
                    color={confirmColor}
                    variant="contained"
                    loading={loading}
                >
                    {confirmLabel}
                </LoadingButton>
            </DialogActions>
        </Dialog>
    );
}
