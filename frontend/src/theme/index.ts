// ---------------------------------------------------------------------------
// MUI theme factory — enterprise slate design system
// ---------------------------------------------------------------------------

import { createTheme, responsiveFontSizes, type Theme } from '@mui/material/styles';
import { lightPalette, darkPalette } from './palette';
import { typography } from './typography';
import { components } from './components';

export type ThemeMode = 'light' | 'dark';

export function buildTheme(mode: ThemeMode): Theme {
    const isDark = mode === 'dark';
    let theme = createTheme({
        cssVariables: true,
        palette: isDark ? darkPalette : lightPalette,
        typography,
        components,
        shape: { borderRadius: 6 },
        transitions: {
            easing: {
                easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
                easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
                easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
                sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
            },
            duration: {
                shortest: 100,
                shorter: 150,
                short: 180,
                standard: 220,
                complex: 280,
                enteringScreen: 180,
                leavingScreen: 140,
            },
        },
        shadows: [
            'none',
            isDark ? '0 1px 3px rgba(1,4,9,0.30)' : '0 1px 3px rgba(31,35,40,0.06)',
            isDark ? '0 3px 8px rgba(1,4,9,0.35)' : '0 3px 8px rgba(31,35,40,0.08)',
            isDark ? '0 6px 16px rgba(1,4,9,0.40)' : '0 6px 16px rgba(31,35,40,0.10)',
            isDark ? '0 8px 24px rgba(1,4,9,0.45)' : '0 8px 24px rgba(31,35,40,0.12)',
            isDark ? '0 12px 32px rgba(1,4,9,0.50)' : '0 12px 32px rgba(31,35,40,0.14)',
            isDark ? '0 16px 40px rgba(1,4,9,0.55)' : '0 16px 40px rgba(31,35,40,0.16)',
            isDark ? '0 20px 48px rgba(1,4,9,0.58)' : '0 20px 48px rgba(31,35,40,0.18)',
            isDark ? '0 24px 56px rgba(1,4,9,0.60)' : '0 24px 56px rgba(31,35,40,0.20)',
            isDark ? '0 28px 64px rgba(1,4,9,0.62)' : '0 28px 64px rgba(31,35,40,0.22)',
            ...Array(15).fill(
                isDark ? '0 3px 10px rgba(1,4,9,0.40)' : '0 3px 10px rgba(31,35,40,0.08)',
            ),
        ] as Theme['shadows'],
    });
    theme = responsiveFontSizes(theme, { factor: 2 });
    return theme;
}
