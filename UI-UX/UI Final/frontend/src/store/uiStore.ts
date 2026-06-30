import { create } from 'zustand';
import type { AppTab, UserRole } from '../utils/access';
import { USER_ROLE_BY_LABEL, getDemoStartTab, getProdStartTab } from '../utils/access';
import { MOCK_ADMIN_USERS, MOCK_CHATS } from '../utils/mockData';
import type { AdminUser } from '../utils/mockData';
import type { ChatMessage } from '../utils/mockData';

export type { AppTab, UserRole };

export type KnowledgeProcessingSection = 'upload' | 'drafts' | 'registry' | 'journal';

const getInitialThemeMode = (): 'dark' | 'light' => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return 'dark';
  }

  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
};

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
  activeKnowledgeProcessingSection: KnowledgeProcessingSection;
  setActiveKnowledgeProcessingSection: (section: KnowledgeProcessingSection) => void;
  currentUserId: string;
  setCurrentUserId: (userId: string) => void;
  currentRole: UserRole;
  setCurrentRole: (role: UserRole) => void;
  currentPermissions: Record<string, boolean>;
  setCurrentPermissions: (permissions: Record<string, boolean>) => void;
  currentGatewaySessionId: string | null;
  setCurrentGatewaySessionId: (sessionId: string | null) => void;
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
  setAdminUsers: (users: AdminUser[]) => void;
  upsertAdminUser: (user: AdminUser) => void;
  updateAdminUser: (userId: string, patch: Partial<AdminUser>) => void;
  prodAdminUsersSnapshot: AdminUser[];
  prodCurrentUserIdSnapshot: string;
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
      if (!user) {
        return {
          isAuthenticated: false,
          currentUserId: '',
          currentRole: 'user',
          currentPermissions: {},
          activeTab: 'chat',
        };
      }

      const currentRole = USER_ROLE_BY_LABEL[user.role] ?? 'user';
      const activeTab =
        state.workMode === 'demo'
          ? getDemoStartTab(currentRole)
          : getProdStartTab(user.availableTabs, user.permissions) ?? state.activeTab;

      return {
        isAuthenticated: true,
        currentUserId: user.id,
        currentRole,
        currentPermissions: user.permissions ?? {},
        activeTab,
        ...(state.workMode === 'prod'
          ? {
              prodAdminUsersSnapshot: state.adminUsers,
              prodCurrentUserIdSnapshot: user.id,
            }
          : {}),
      };
    }),
  logout: () =>
    set((state) => ({
      isAuthenticated: false,
      activeTab: 'chat',
      focusMode: false,
      currentUserId: '',
      currentRole: 'user',
      currentPermissions: {},
      currentGatewaySessionId: null,
      chatMessages: [],
      ...(state.workMode === 'prod'
        ? {
            prodAdminUsersSnapshot: [],
            prodCurrentUserIdSnapshot: '',
          }
        : {}),
    })),
  activeTab: 'chat',
  setActiveTab: (activeTab) => set({ activeTab }),
  activeKnowledgeProcessingSection: 'upload',
  setActiveKnowledgeProcessingSection: (activeKnowledgeProcessingSection) => set({ activeKnowledgeProcessingSection }),
  currentUserId: 'u1',
  setCurrentUserId: (currentUserId) => set({ currentUserId }),
  currentRole: 'user',
  setCurrentRole: (currentRole) => set({ currentRole }),
  currentPermissions: {},
  setCurrentPermissions: (currentPermissions) => set({ currentPermissions }),
  currentGatewaySessionId: null,
  setCurrentGatewaySessionId: (currentGatewaySessionId) => set({ currentGatewaySessionId }),
  activeProjectId: '',
  setActiveProjectId: (activeProjectId) => set({ activeProjectId }),
  themeMode: getInitialThemeMode(),
  setThemeMode: (themeMode) => set({ themeMode }),
  workMode: 'prod',
  setWorkMode: (workMode) =>
    set((state) => {
      if (workMode === state.workMode) return state;

      const prodUsers = state.workMode === 'prod' ? state.adminUsers : state.prodAdminUsersSnapshot;
      const prodUserId = state.workMode === 'prod' ? state.currentUserId : state.prodCurrentUserIdSnapshot;
      const targetUsers = workMode === 'demo' ? MOCK_ADMIN_USERS : prodUsers;
      const targetUserId = workMode === 'demo' ? MOCK_ADMIN_USERS[0]?.id ?? '' : prodUserId;
      const targetUser = targetUsers.find((user) => user.id === targetUserId);
      const currentRole = USER_ROLE_BY_LABEL[targetUser?.role ?? ''] ?? 'user';
      const activeTab =
        workMode === 'demo'
          ? getDemoStartTab(currentRole)
          : getProdStartTab(targetUser?.availableTabs, targetUser?.permissions) ?? state.activeTab;

      return {
        workMode,
        apiStatus: workMode === 'demo' ? 'demo' : 'offline',
        currentGatewaySessionId: null,
        adminUsers: targetUsers,
        currentUserId: targetUserId,
        currentRole,
        currentPermissions: targetUser?.permissions ?? {},
        activeTab,
        chatMessages: workMode === 'demo' ? MOCK_CHATS : [],
        isAuthenticated: workMode === 'demo' ? state.isAuthenticated : Boolean(prodUserId && prodUsers.length),
        prodAdminUsersSnapshot: prodUsers,
        prodCurrentUserIdSnapshot: prodUserId,
      };
    }),
  toggleWorkMode: () =>
    set((state) => {
      const workMode = state.workMode === 'demo' ? 'prod' : 'demo';
      const prodUsers = state.workMode === 'prod' ? state.adminUsers : state.prodAdminUsersSnapshot;
      const prodUserId = state.workMode === 'prod' ? state.currentUserId : state.prodCurrentUserIdSnapshot;
      const targetUsers = workMode === 'demo' ? MOCK_ADMIN_USERS : prodUsers;
      const targetUserId = workMode === 'demo' ? MOCK_ADMIN_USERS[0]?.id ?? '' : prodUserId;
      const targetUser = targetUsers.find((user) => user.id === targetUserId);
      const currentRole = USER_ROLE_BY_LABEL[targetUser?.role ?? ''] ?? 'user';
      const activeTab =
        workMode === 'demo'
          ? getDemoStartTab(currentRole)
          : getProdStartTab(targetUser?.availableTabs, targetUser?.permissions) ?? state.activeTab;

      return {
        workMode,
        apiStatus: workMode === 'demo' ? 'demo' : 'offline',
        currentGatewaySessionId: null,
        adminUsers: targetUsers,
        currentUserId: targetUserId,
        currentRole,
        currentPermissions: targetUser?.permissions ?? {},
        activeTab,
        chatMessages: workMode === 'demo' ? MOCK_CHATS : [],
        isAuthenticated: workMode === 'demo' ? state.isAuthenticated : Boolean(prodUserId && prodUsers.length),
        prodAdminUsersSnapshot: prodUsers,
        prodCurrentUserIdSnapshot: prodUserId,
      };
    }),
  focusMode: false,
  setFocusMode: (focusMode) => set({ focusMode }),
  toggleFocusMode: () => set((state) => ({ focusMode: !state.focusMode })),
  videoGuideOpen: false,
  setVideoGuideOpen: (videoGuideOpen) => set({ videoGuideOpen }),
  apiStatus: 'offline',
  setApiStatus: (apiStatus) => set({ apiStatus }),
  adminUsers: [],
  setAdminUsers: (adminUsers) =>
    set((state) => {
      const currentSessionUser = state.adminUsers.find((user) => user.id === state.currentUserId);
      const mergedUsers = adminUsers.map((user) => {
        if (!currentSessionUser || user.id !== currentSessionUser.id) return user;

        return {
          ...currentSessionUser,
          ...user,
          availableTabs: user.availableTabs ?? currentSessionUser.availableTabs,
          permissions:
            user.permissions && Object.keys(user.permissions).length > 0
              ? user.permissions
              : currentSessionUser.permissions,
        };
      });
      const usersWithCurrentSession =
        currentSessionUser && !mergedUsers.some((user) => user.id === currentSessionUser.id)
          ? [currentSessionUser, ...mergedUsers]
          : mergedUsers;

      return {
        adminUsers: usersWithCurrentSession,
        ...(state.workMode === 'prod' ? { prodAdminUsersSnapshot: usersWithCurrentSession } : {}),
      };
    }),
  prodAdminUsersSnapshot: [],
  prodCurrentUserIdSnapshot: '',
  upsertAdminUser: (user) =>
    set((state) => {
      const exists = state.adminUsers.some((item) => item.id === user.id);
      const adminUsers = exists
        ? state.adminUsers.map((item) => (item.id === user.id ? { ...item, ...user } : item))
        : [user, ...state.adminUsers];

      return {
        adminUsers,
        ...(state.workMode === 'prod' ? { prodAdminUsersSnapshot: adminUsers } : {}),
      };
    }),
  updateAdminUser: (userId, patch) =>
    set((state) => {
      const adminUsers = state.adminUsers.map((user) => (user.id === userId ? { ...user, ...patch } : user));
      return {
        adminUsers,
        ...(state.workMode === 'prod' ? { prodAdminUsersSnapshot: adminUsers } : {}),
      };
    }),
  adminAuditLog: [],
  addAdminAuditLogItem: (item) =>
    set((state) => ({
      adminAuditLog: [item, ...state.adminAuditLog].slice(0, 20),
    })),
  chatMessages: [],
  setChatMessages: (chatMessages) => set({ chatMessages }),
  appendChatMessages: (messages) =>
    set((state) => ({
      chatMessages: [...state.chatMessages, ...messages],
    })),
}));
