// ---------------------------------------------------------------------------
// UI store — Zustand (client-only UI state)
// ---------------------------------------------------------------------------

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ThemeMode } from '@/theme';

interface UiState {
    sidebarOpen: boolean;
    themeMode: ThemeMode;

    toggleSidebar: () => void;
    setSidebarOpen: (open: boolean) => void;
    toggleTheme: () => void;
    setThemeMode: (mode: ThemeMode) => void;
}

export const useUiStore = create<UiState>()(
    persist(
        (set) => ({
            sidebarOpen: true,
            themeMode: 'light',

            toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
            setSidebarOpen: (open) => set({ sidebarOpen: open }),
            toggleTheme: () =>
                set((s) => ({ themeMode: s.themeMode === 'light' ? 'dark' : 'light' })),
            setThemeMode: (mode) => set({ themeMode: mode }),
        }),
        {
            name: 'art-ui',
        },
    ),
);
