// ---------------------------------------------------------------------------
// MUI palette — enterprise slate: GitHub-dark backgrounds + enterprise blue
// ---------------------------------------------------------------------------

import type { PaletteOptions } from '@mui/material/styles';

export const lightPalette: PaletteOptions = {
    mode: 'light',
    primary: {
        main: '#0969DA',
        light: '#2188FF',
        dark: '#0550AE',
        contrastText: '#ffffff',
    },
    secondary: {
        main: '#6E40C9',
        light: '#8A63D2',
        dark: '#5A32A3',
        contrastText: '#ffffff',
    },
    error: {
        main: '#CF222E',
        light: '#FF818266',
        dark: '#A40E26',
        contrastText: '#ffffff',
    },
    warning: {
        main: '#9A6700',
        light: '#D4A72C',
        dark: '#7D4E00',
        contrastText: '#ffffff',
    },
    success: {
        main: '#1A7F37',
        light: '#2DA44E',
        dark: '#116329',
        contrastText: '#ffffff',
    },
    info: {
        main: '#0550AE',
        light: '#0969DA',
        dark: '#033D8B',
        contrastText: '#ffffff',
    },
    background: {
        default: '#F6F8FA',
        paper: '#FFFFFF',
    },
    text: {
        primary: '#1F2328',
        secondary: '#656D76',
    },
    divider: '#D0D7DE',
    action: {
        hover: 'rgba(9, 105, 218, 0.05)',
        selected: 'rgba(9, 105, 218, 0.08)',
        focus: 'rgba(9, 105, 218, 0.12)',
        disabledBackground: 'rgba(31, 35, 40, 0.05)',
        disabled: 'rgba(31, 35, 40, 0.38)',
    },
};

export const darkPalette: PaletteOptions = {
    mode: 'dark',
    primary: {
        main: '#2F81F7',
        light: '#58A6FF',
        dark: '#1F6FEB',
        contrastText: '#ffffff',
    },
    secondary: {
        main: '#BC8CFF',
        light: '#D2A8FF',
        dark: '#A371F7',
        contrastText: '#0D1117',
    },
    error: {
        main: '#F85149',
        light: '#FF7B72',
        dark: '#DA3633',
        contrastText: '#ffffff',
    },
    warning: {
        main: '#D29922',
        light: '#E3B341',
        dark: '#BB8009',
        contrastText: '#0D1117',
    },
    success: {
        main: '#3FB950',
        light: '#56D364',
        dark: '#2EA043',
        contrastText: '#0D1117',
    },
    info: {
        main: '#58A6FF',
        light: '#79C0FF',
        dark: '#388BFD',
        contrastText: '#0D1117',
    },
    background: {
        default: '#0D1117',
        paper: '#161B22',
    },
    text: {
        primary: '#E6EDF3',
        secondary: '#8B949E',
    },
    divider: '#30363D',
    action: {
        hover: 'rgba(177, 186, 196, 0.08)',
        selected: 'rgba(177, 186, 196, 0.12)',
        focus: 'rgba(47, 129, 247, 0.20)',
        disabledBackground: 'rgba(177, 186, 196, 0.06)',
        disabled: 'rgba(177, 186, 196, 0.30)',
    },
};
