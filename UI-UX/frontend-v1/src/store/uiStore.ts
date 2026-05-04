import { create } from 'zustand';
import type { AppTab, UserRole } from '../utils/access';
import { MOCK_ADMIN_USERS } from '../utils/mockData';
import type { AdminUser } from '../utils/mockData';

export type { AppTab, UserRole };

export interface AdminAuditLogItem {
  id: string;
  time: string;
  actor: string;
  target: string;
  action: string;
  details: string;
}

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
  adminUsers: AdminUser[];
  updateAdminUser: (userId: string, patch: Partial<AdminUser>) => void;
  adminAuditLog: AdminAuditLogItem[];
  addAdminAuditLogItem: (item: AdminAuditLogItem) => void;
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
  adminUsers: MOCK_ADMIN_USERS,
  updateAdminUser: (userId, patch) =>
    set((state) => ({
      adminUsers: state.adminUsers.map((user) => (user.id === userId ? { ...user, ...patch } : user)),
    })),
  adminAuditLog: [
    {
      id: 'audit-1',
      time: '2026-04-30 12:40',
      actor: 'Система',
      target: 'Права доступа',
      action: 'Инициализация',
      details: 'Загружена демонстрационная матрица ролей и прав доступа.',
    },
  ],
  addAdminAuditLogItem: (item) =>
    set((state) => ({
      adminAuditLog: [item, ...state.adminAuditLog].slice(0, 20),
    })),
}));
