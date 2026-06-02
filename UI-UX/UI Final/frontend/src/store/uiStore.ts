import { create } from 'zustand';
import type { AppTab, UserRole } from '../utils/access';
import { USER_ROLE_BY_LABEL, getFallbackTab } from '../utils/access';
import { MOCK_ADMIN_USERS, MOCK_CHATS } from '../utils/mockData';
import type { AdminUser } from '../utils/mockData';
import type { ChatMessage } from '../utils/mockData';

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
  isAuthenticated: boolean;
  login: (userId: string) => void;
  logout: () => void;
  activeTab: AppTab;
  setActiveTab: (tab: AppTab) => void;
  currentUserId: string;
  setCurrentUserId: (userId: string) => void;
  currentRole: UserRole;
  setCurrentRole: (role: UserRole) => void;
  activeProjectId: string;
  setActiveProjectId: (projectId: string) => void;
  themeMode: 'dark' | 'light';
  setThemeMode: (mode: 'dark' | 'light') => void;
  workMode: 'demo' | 'prod';
  setWorkMode: (mode: 'demo' | 'prod') => void;
  toggleWorkMode: () => void;
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
  chatMessages: ChatMessage[];
  setChatMessages: (messages: ChatMessage[]) => void;
  appendChatMessages: (messages: ChatMessage[]) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isAuthenticated: false,
  login: (currentUserId) =>
    set((state) => {
      const user = state.adminUsers.find((item) => item.id === currentUserId) ?? state.adminUsers[0];
      const currentRole = USER_ROLE_BY_LABEL[user.role] ?? 'user';

      return {
        isAuthenticated: true,
        currentUserId: user.id,
        currentRole,
        activeTab: getFallbackTab(currentRole),
      };
    }),
  logout: () => set({ isAuthenticated: false, activeTab: 'chat', focusMode: false }),
  activeTab: 'chat',
  setActiveTab: (activeTab) => set({ activeTab }),
  currentUserId: 'u1',
  setCurrentUserId: (currentUserId) => set({ currentUserId }),
  currentRole: 'user',
  setCurrentRole: (currentRole) => set({ currentRole }),
  activeProjectId: 'project-223m',
  setActiveProjectId: (activeProjectId) => set({ activeProjectId }),
  themeMode: 'dark',
  setThemeMode: (themeMode) => set({ themeMode }),
  workMode: 'demo',
  setWorkMode: (workMode) => set({ workMode, apiStatus: workMode === 'demo' ? 'demo' : 'offline' }),
  toggleWorkMode: () =>
    set((state) => {
      const workMode = state.workMode === 'demo' ? 'prod' : 'demo';
      return { workMode, apiStatus: workMode === 'demo' ? 'demo' : 'offline' };
    }),
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
  chatMessages: MOCK_CHATS,
  setChatMessages: (chatMessages) => set({ chatMessages }),
  appendChatMessages: (messages) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, ...messages],
    })),
}));
