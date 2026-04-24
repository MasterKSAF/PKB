import { create } from 'zustand';

export type AppTab = 'chat' | 'search' | 'documents' | 'checks' | 'history' | 'qa';

interface UIState {
  activeTab: AppTab;
  setActiveTab: (tab: AppTab) => void;
  videoGuideOpen: boolean;
  setVideoGuideOpen: (open: boolean) => void;
  apiStatus: 'online' | 'offline' | 'demo';
  setApiStatus: (status: 'online' | 'offline' | 'demo') => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'chat',
  setActiveTab: (activeTab) => set({ activeTab }),
  videoGuideOpen: false,
  setVideoGuideOpen: (videoGuideOpen) => set({ videoGuideOpen }),
  apiStatus: 'demo',
  setApiStatus: (apiStatus) => set({ apiStatus }),
}));
