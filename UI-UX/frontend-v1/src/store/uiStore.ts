import { create } from 'zustand';

export type AppTab = 'chat' | 'search' | 'documents' | 'checks' | 'history' | 'qa';

interface UIState {
  activeTab: AppTab;
  setActiveTab: (tab: AppTab) => void;
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
  focusMode: false,
  setFocusMode: (focusMode) => set({ focusMode }),
  toggleFocusMode: () => set((state) => ({ focusMode: !state.focusMode })),
  videoGuideOpen: false,
  setVideoGuideOpen: (videoGuideOpen) => set({ videoGuideOpen }),
  apiStatus: 'demo',
  setApiStatus: (apiStatus) => set({ apiStatus }),
}));
