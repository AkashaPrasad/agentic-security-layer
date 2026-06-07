// ---------------------------------------------------------------------------
// MUI component overrides — enterprise slate / GitHub-dark design system
// ---------------------------------------------------------------------------

import type { Components, Theme } from '@mui/material/styles';

const MONO = "'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace";
const TRANSITION = 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)';

export const components: Components<Theme> = {
    // ── Global baseline ───────────────────────────────────────────────────
    MuiCssBaseline: {
        styleOverrides: {
            '*, *::before, *::after': { boxSizing: 'border-box' },
            html: { scrollBehavior: 'smooth' },
            body: {
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgba(139,148,158,0.20) transparent',
                '&::-webkit-scrollbar': { width: 6, height: 6 },
                '&::-webkit-scrollbar-track': { background: 'transparent' },
                '&::-webkit-scrollbar-thumb': {
                    borderRadius: 4,
                    backgroundColor: 'rgba(139,148,158,0.20)',
                    '&:hover': { backgroundColor: 'rgba(139,148,158,0.35)' },
                },
            },
        },
    },

    // ── Buttons ───────────────────────────────────────────────────────────
    MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: {
            root: {
                borderRadius: 6,
                fontWeight: 500,
                padding: '6px 16px',
                fontSize: '0.875rem',
                transition: TRANSITION,
                '&:active': { transform: 'scale(0.98)' },
            },
            containedPrimary: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? '#238636' : '#1A7F37',
                color: '#ffffff',
                border: `1px solid ${theme.palette.mode === 'dark' ? '#2EA043' : '#1F8B3E'}`,
                '&:hover': {
                    backgroundColor: theme.palette.mode === 'dark' ? '#2EA043' : '#1F8B3E',
                },
            }),
            outlined: ({ theme }) => ({
                borderWidth: 1,
                borderColor: theme.palette.divider,
                color: theme.palette.text.primary,
                '&:hover': {
                    borderColor: theme.palette.mode === 'dark' ? '#8B949E' : '#8C959F',
                    backgroundColor: theme.palette.action.hover,
                },
            }),
            text: ({ theme }) => ({
                color: theme.palette.mode === 'dark' ? '#58A6FF' : '#0969DA',
                '&:hover': { backgroundColor: theme.palette.action.hover },
            }),
            sizeLarge: { padding: '10px 20px', fontSize: '0.9375rem' },
            sizeSmall: { padding: '3px 10px', fontSize: '0.8125rem', borderRadius: 5 },
        },
    },

    // ── Cards ─────────────────────────────────────────────────────────────
    MuiCard: {
        defaultProps: { variant: 'outlined' },
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: 6,
                border: `1px solid ${theme.palette.divider}`,
                backgroundColor: theme.palette.background.paper,
                backgroundImage: 'none',
                transition: TRANSITION,
                '&:hover': {
                    borderColor: theme.palette.mode === 'dark' ? '#444C56' : '#B0BAC6',
                },
            }),
        },
    },

    // ── Paper ─────────────────────────────────────────────────────────────
    MuiPaper: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: 6,
                backgroundImage: 'none',
                ...(theme.palette.mode === 'dark' && {
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                }),
                ...(theme.palette.mode === 'light' && {
                    boxShadow: '0 1px 3px rgba(31,35,40,0.06), 0 0 0 1px rgba(31,35,40,0.04)',
                }),
            }),
            outlined: ({ theme }) => ({
                border: `1px solid ${theme.palette.divider}`,
            }),
        },
    },

    // ── AppBar ────────────────────────────────────────────────────────────
    MuiAppBar: {
        styleOverrides: {
            root: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark'
                    ? '#161B22'
                    : '#FFFFFF',
                backdropFilter: 'none',
                borderBottom: `1px solid ${theme.palette.divider}`,
                boxShadow: 'none',
                color: theme.palette.text.primary,
            }),
        },
    },

    // ── Drawer ────────────────────────────────────────────────────────────
    MuiDrawer: {
        styleOverrides: {
            paper: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? '#0D1117' : '#F6F8FA',
                borderRight: `1px solid ${theme.palette.divider}`,
            }),
        },
    },

    // ── Dialog ────────────────────────────────────────────────────────────
    MuiDialog: {
        styleOverrides: {
            paper: ({ theme }) => ({
                borderRadius: 8,
                boxShadow: theme.palette.mode === 'dark'
                    ? '0 16px 48px rgba(1,4,9,0.70)'
                    : '0 16px 48px rgba(31,35,40,0.16)',
                border: `1px solid ${theme.palette.divider}`,
                backgroundImage: 'none',
            }),
            backdrop: {
                backgroundColor: 'rgba(1, 4, 9, 0.50)',
                backdropFilter: 'blur(4px)',
            },
        },
    },

    // ── Chips ─────────────────────────────────────────────────────────────
    MuiChip: {
        styleOverrides: {
            root: {
                borderRadius: 4,
                fontSize: '0.6875rem',
                fontFamily: MONO,
                fontWeight: 500,
                height: 22,
                transition: TRANSITION,
            },
            colorSuccess: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(63,185,80,0.15)' : 'rgba(26,127,55,0.10)',
                color: theme.palette.success.main,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(63,185,80,0.35)' : 'rgba(26,127,55,0.25)'}`,
            }),
            colorError: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(248,81,73,0.15)' : 'rgba(207,34,46,0.10)',
                color: theme.palette.error.main,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(248,81,73,0.35)' : 'rgba(207,34,46,0.25)'}`,
            }),
            colorWarning: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(210,153,34,0.15)' : 'rgba(154,103,0,0.10)',
                color: theme.palette.warning.main,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(210,153,34,0.35)' : 'rgba(154,103,0,0.25)'}`,
            }),
            colorInfo: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(88,166,255,0.15)' : 'rgba(9,105,218,0.10)',
                color: theme.palette.info.main,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(88,166,255,0.35)' : 'rgba(9,105,218,0.25)'}`,
            }),
            colorPrimary: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? 'rgba(47,129,247,0.15)' : 'rgba(9,105,218,0.10)',
                color: theme.palette.primary.main,
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(47,129,247,0.35)' : 'rgba(9,105,218,0.25)'}`,
            }),
        },
    },

    // ── Tables ────────────────────────────────────────────────────────────
    MuiTableHead: {
        styleOverrides: {
            root: ({ theme }) => ({
                '& .MuiTableCell-head': {
                    fontFamily: MONO,
                    fontWeight: 500,
                    fontSize: '0.6875rem',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase' as const,
                    color: theme.palette.text.secondary,
                    backgroundColor: theme.palette.mode === 'dark' ? '#0D1117' : '#F6F8FA',
                    borderBottom: `1px solid ${theme.palette.divider}`,
                    padding: '10px 16px',
                },
            }),
        },
    },
    MuiTableCell: {
        styleOverrides: {
            root: ({ theme }) => ({
                fontSize: '0.8125rem',
                borderBottom: `1px solid ${theme.palette.divider}`,
                padding: '12px 16px',
            }),
        },
    },
    MuiTableRow: {
        styleOverrides: {
            root: ({ theme }) => ({
                transition: 'background-color 0.10s ease',
                '&:hover': {
                    backgroundColor: theme.palette.action.hover,
                },
                '&:last-of-type .MuiTableCell-root': { borderBottom: 0 },
            }),
        },
    },

    // ── Form inputs ───────────────────────────────────────────────────────
    MuiTextField: {
        defaultProps: { variant: 'outlined', fullWidth: true, size: 'small' },
        styleOverrides: {
            root: ({ theme }) => ({
                '& input:-webkit-autofill, & input:-webkit-autofill:hover, & input:-webkit-autofill:focus': {
                    WebkitBoxShadow: theme.palette.mode === 'dark'
                        ? '0 0 0 100px #161B22 inset'
                        : '0 0 0 100px #ffffff inset',
                    WebkitTextFillColor: theme.palette.mode === 'dark' ? '#E6EDF3' : '#1F2328',
                    caretColor: theme.palette.mode === 'dark' ? '#E6EDF3' : '#1F2328',
                    transition: 'background-color 5000s ease-in-out 0s',
                },
            }),
        },
    },
    MuiOutlinedInput: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: 6,
                fontSize: '0.875rem',
                transition: TRANSITION,
                backgroundColor: theme.palette.mode === 'dark' ? '#0D1117' : '#FFFFFF',
                '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: theme.palette.mode === 'dark' ? '#8B949E' : '#8C959F',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderWidth: 2,
                    borderColor: theme.palette.primary.main,
                },
                '& input:-webkit-autofill, & input:-webkit-autofill:hover, & input:-webkit-autofill:focus': {
                    WebkitBoxShadow: theme.palette.mode === 'dark'
                        ? '0 0 0 100px #0D1117 inset'
                        : '0 0 0 100px #ffffff inset',
                    WebkitTextFillColor: theme.palette.mode === 'dark' ? '#E6EDF3' : '#1F2328',
                    caretColor: theme.palette.mode === 'dark' ? '#E6EDF3' : '#1F2328',
                    transition: 'background-color 5000s ease-in-out 0s',
                },
            }),
            notchedOutline: ({ theme }) => ({
                borderColor: theme.palette.divider,
                transition: TRANSITION,
            }),
        },
    },
    MuiInputLabel: {
        styleOverrides: {
            root: ({ theme }) => ({
                fontSize: '0.875rem',
                color: theme.palette.text.secondary,
                '&.Mui-focused': { color: theme.palette.primary.main },
            }),
        },
    },
    MuiSelect: {
        styleOverrides: {
            root: { borderRadius: 6 },
        },
    },

    // ── Tooltips ──────────────────────────────────────────────────────────
    MuiTooltip: {
        defaultProps: { arrow: true, enterDelay: 500 },
        styleOverrides: {
            tooltip: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? '#2D333B' : '#1F2328',
                color: '#E6EDF3',
                fontSize: '0.75rem',
                fontWeight: 400,
                borderRadius: 4,
                padding: '6px 12px',
                border: `1px solid ${theme.palette.mode === 'dark' ? '#444C56' : '#30363D'}`,
                boxShadow: '0 8px 24px rgba(1,4,9,0.30)',
            }),
            arrow: ({ theme }) => ({
                color: theme.palette.mode === 'dark' ? '#2D333B' : '#1F2328',
            }),
        },
    },

    // ── Progress bars ─────────────────────────────────────────────────────
    MuiLinearProgress: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: 2,
                height: 4,
                backgroundColor: theme.palette.mode === 'dark' ? '#21262D' : '#E2E5E9',
            }),
            bar: ({ theme }) => ({
                borderRadius: 2,
                backgroundColor: theme.palette.primary.main,
            }),
        },
    },
    MuiCircularProgress: {
        styleOverrides: {
            root: ({ theme }) => ({
                color: theme.palette.primary.main,
            }),
        },
    },

    // ── Tabs ──────────────────────────────────────────────────────────────
    MuiTabs: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderBottom: `1px solid ${theme.palette.divider}`,
                minHeight: 40,
            }),
            indicator: ({ theme }) => ({
                height: 2,
                borderRadius: '2px 2px 0 0',
                backgroundColor: theme.palette.primary.main,
            }),
        },
    },
    MuiTab: {
        styleOverrides: {
            root: ({ theme }) => ({
                textTransform: 'none',
                fontWeight: 500,
                fontSize: '0.875rem',
                minHeight: 40,
                padding: '8px 16px',
                color: theme.palette.text.secondary,
                transition: 'color 0.15s ease',
                '&.Mui-selected': { color: theme.palette.text.primary, fontWeight: 600 },
            }),
        },
    },

    // ── Avatars ───────────────────────────────────────────────────────────
    MuiAvatar: {
        styleOverrides: {
            root: {
                fontWeight: 600,
                fontSize: '0.8125rem',
                fontFamily: "'IBM Plex Sans', sans-serif",
            },
            colorDefault: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark' ? '#21262D' : '#E2E5E9',
                color: theme.palette.text.secondary,
            }),
        },
    },

    // ── List items ────────────────────────────────────────────────────────
    MuiListItemButton: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: 6,
                margin: '1px 6px',
                padding: '7px 12px',
                fontSize: '0.875rem',
                transition: TRANSITION,
                '&.Mui-selected': {
                    backgroundColor: theme.palette.mode === 'dark'
                        ? 'rgba(47,129,247,0.12)'
                        : 'rgba(9,105,218,0.08)',
                    color: theme.palette.primary.main,
                    '& .MuiListItemIcon-root': { color: theme.palette.primary.main },
                    '&:hover': {
                        backgroundColor: theme.palette.mode === 'dark'
                            ? 'rgba(47,129,247,0.18)'
                            : 'rgba(9,105,218,0.12)',
                    },
                },
                '&:hover': { backgroundColor: theme.palette.action.hover },
            }),
        },
    },
    MuiListItemIcon: {
        styleOverrides: {
            root: ({ theme }) => ({
                minWidth: 36,
                color: theme.palette.text.secondary,
            }),
        },
    },

    // ── Alerts ────────────────────────────────────────────────────────────
    MuiAlert: {
        styleOverrides: {
            root: { borderRadius: 6, fontSize: '0.875rem' },
            standardError: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark'
                    ? 'rgba(248,81,73,0.10)' : 'rgba(207,34,46,0.06)',
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(248,81,73,0.30)' : 'rgba(207,34,46,0.20)'}`,
                color: theme.palette.mode === 'dark' ? '#FF7B72' : '#A40E26',
            }),
            standardSuccess: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark'
                    ? 'rgba(63,185,80,0.10)' : 'rgba(26,127,55,0.06)',
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(63,185,80,0.30)' : 'rgba(26,127,55,0.20)'}`,
                color: theme.palette.mode === 'dark' ? '#3FB950' : '#116329',
            }),
            standardWarning: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark'
                    ? 'rgba(210,153,34,0.10)' : 'rgba(154,103,0,0.06)',
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(210,153,34,0.30)' : 'rgba(154,103,0,0.20)'}`,
                color: theme.palette.mode === 'dark' ? '#E3B341' : '#7D4E00',
            }),
            standardInfo: ({ theme }) => ({
                backgroundColor: theme.palette.mode === 'dark'
                    ? 'rgba(88,166,255,0.10)' : 'rgba(9,105,218,0.06)',
                border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(88,166,255,0.30)' : 'rgba(9,105,218,0.20)'}`,
                color: theme.palette.mode === 'dark' ? '#58A6FF' : '#0550AE',
            }),
        },
    },

    // ── Skeletons ─────────────────────────────────────────────────────────
    MuiSkeleton: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: 4,
                backgroundColor: theme.palette.mode === 'dark' ? '#21262D' : '#EAECEF',
            }),
        },
    },

    // ── Pagination ────────────────────────────────────────────────────────
    MuiPagination: {
        styleOverrides: {
            root: {
                '& .MuiPaginationItem-root': {
                    borderRadius: 4,
                    fontFamily: MONO,
                    fontSize: '0.8125rem',
                    fontWeight: 500,
                },
            },
        },
    },

    // ── Breadcrumbs ───────────────────────────────────────────────────────
    MuiBreadcrumbs: {
        styleOverrides: {
            root: { fontSize: '0.8125rem' },
        },
    },

    // ── Dividers ──────────────────────────────────────────────────────────
    MuiDivider: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderColor: theme.palette.divider,
            }),
        },
    },

    // ── Menu ──────────────────────────────────────────────────────────────
    MuiMenu: {
        styleOverrides: {
            paper: ({ theme }) => ({
                borderRadius: 6,
                border: `1px solid ${theme.palette.divider}`,
                boxShadow: theme.palette.mode === 'dark'
                    ? '0 8px 24px rgba(1,4,9,0.40)'
                    : '0 8px 24px rgba(31,35,40,0.12)',
                marginTop: 4,
                minWidth: 180,
                backgroundImage: 'none',
                backgroundColor: theme.palette.mode === 'dark' ? '#161B22' : '#FFFFFF',
            }),
        },
    },
    MuiMenuItem: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: 4,
                margin: '2px 4px',
                padding: '7px 12px',
                fontSize: '0.875rem',
                transition: 'background-color 0.10s ease',
                '&:hover': { backgroundColor: theme.palette.action.hover },
            }),
        },
    },

    // ── Backdrop ──────────────────────────────────────────────────────────
    MuiBackdrop: {
        styleOverrides: {
            root: {
                backgroundColor: 'rgba(1, 4, 9, 0.50)',
            },
        },
    },

    // ── Switches ──────────────────────────────────────────────────────────
    MuiSwitch: {
        styleOverrides: {
            root: { padding: 7 },
            track: ({ theme }) => ({
                borderRadius: 11,
                backgroundColor: theme.palette.mode === 'dark' ? '#30363D' : '#D0D7DE',
                opacity: 1,
            }),
            thumb: ({ theme }) => ({
                boxShadow: 'none',
                width: 16,
                height: 16,
                margin: 2,
                color: theme.palette.mode === 'dark' ? '#8B949E' : '#FFFFFF',
            }),
        },
    },

    // ── Icon Button ───────────────────────────────────────────────────────
    MuiIconButton: {
        styleOverrides: {
            root: {
                borderRadius: 6,
                transition: TRANSITION,
            },
        },
    },

    // ── Accordion ────────────────────────────────────────────────────────
    MuiAccordion: {
        styleOverrides: {
            root: ({ theme }) => ({
                borderRadius: '6px !important',
                border: `1px solid ${theme.palette.divider}`,
                '&:before': { display: 'none' },
                backgroundImage: 'none',
            }),
        },
    },
};
