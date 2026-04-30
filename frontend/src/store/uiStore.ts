import { create } from 'zustand';
import type { AppTab, UserRole } from '../utils/access';

export type { AppTab, UserRole };

interface UIState {
  activeTab: AppTab;
  setActiveTab: (tab: AppTab) => void;
  currentUserId: string;
  setCurrentUserId: (userId: string) => void;
  currentRole: UserRole;
  setCurrentRole: (role: UserRole) => void;
  themeMode: 'dark' | 'light';
  setThemeMode: (mode: 'dark' | 'light') => void;
  focusMode: boolean;
  setFocusMode: (enabled: boolean) => void;
  toggleFocusMode: () => void;
  videoGuideOpen: boolean;
  setVideoGuideOpen: (open: boolean) => void;
  apiStatus: 'online' | 'offline' | 'demo';
  setApiStatus: (status: 'online' | 'offline' | 'demo') => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'chat',
  setActiveTab: (activeTab) => set({ activeTab }),
  currentUserId: 'u1',
  setCurrentUserId: (currentUserId) => set({ currentUserId }),
  currentRole: 'engineer',
  setCurrentRole: (currentRole) => set({ currentRole }),
  themeMode: 'dark',
  setThemeMode: (themeMode) => set({ themeMode }),
  focusMode: false,
  setFocusMode: (focusMode) => set({ focusMode }),
  toggleFocusMode: () => set((state) => ({ focusMode: !state.focusMode })),
  videoGuideOpen: false,
  setVideoGuideOpen: (videoGuideOpen) => set({ videoGuideOpen }),
  apiStatus: 'demo',
  setApiStatus: (apiStatus) => set({ apiStatus }),
}));
