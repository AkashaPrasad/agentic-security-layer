// ---------------------------------------------------------------------------
// MUI typography — IBM Plex Sans + IBM Plex Mono (enterprise technical)
// ---------------------------------------------------------------------------

import type { ThemeOptions } from '@mui/material/styles';

const SANS = "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
const MONO = "'IBM Plex Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace";

export const typography: NonNullable<ThemeOptions['typography']> = {
    fontFamily: SANS,
    h1: {
        fontWeight: 700,
        fontSize: '1.875rem',
        lineHeight: 1.25,
        letterSpacing: '-0.02em',
    },
    h2: {
        fontWeight: 600,
        fontSize: '1.5rem',
        lineHeight: 1.3,
        letterSpacing: '-0.015em',
    },
    h3: {
        fontWeight: 600,
        fontSize: '1.25rem',
        lineHeight: 1.35,
        letterSpacing: '-0.01em',
    },
    h4: {
        fontWeight: 600,
        fontSize: '1.125rem',
        lineHeight: 1.4,
        letterSpacing: '-0.008em',
    },
    h5: {
        fontWeight: 600,
        fontSize: '1rem',
        lineHeight: 1.5,
        letterSpacing: '-0.005em',
    },
    h6: {
        fontWeight: 600,
        fontSize: '0.9375rem',
        lineHeight: 1.5,
    },
    subtitle1: {
        fontSize: '0.9375rem',
        fontWeight: 500,
        lineHeight: 1.5,
    },
    subtitle2: {
        fontSize: '0.875rem',
        fontWeight: 500,
        lineHeight: 1.5,
        letterSpacing: '0.005em',
    },
    body1: {
        fontSize: '0.9375rem',
        lineHeight: 1.6,
        letterSpacing: '0.005em',
    },
    body2: {
        fontSize: '0.8125rem',
        lineHeight: 1.6,
        letterSpacing: '0.005em',
    },
    caption: {
        fontFamily: MONO,
        fontSize: '0.6875rem',
        lineHeight: 1.5,
        fontWeight: 400,
        letterSpacing: '0.02em',
    },
    overline: {
        fontFamily: MONO,
        fontSize: '0.625rem',
        fontWeight: 500,
        letterSpacing: '0.10em',
        textTransform: 'uppercase',
    },
    button: {
        textTransform: 'none',
        fontWeight: 500,
        letterSpacing: '0.01em',
        fontSize: '0.875rem',
    },
};

export const MONO_FONT = MONO;
