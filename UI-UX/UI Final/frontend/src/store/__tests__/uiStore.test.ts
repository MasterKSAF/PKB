import { beforeEach, describe, expect, it } from 'vitest';
import { useUIStore } from '../uiStore';
import type { AdminUser } from '../../utils/mockData';

const productionUser: AdminUser = {
  id: '42',
  name: 'Production Admin',
  position: 'Системный администратор',
  login: 'admin@example.com',
  role: 'Системный администратор',
  access: 'chat, search, history, admin',
  status: 'Активен',
  lastSeen: '',
  availableTabs: ['chat', 'search', 'history', 'admin'],
  permissions: { can_manage_users: true },
};

describe('uiStore work mode', () => {
  beforeEach(() => {
    useUIStore.setState(useUIStore.getInitialState(), true);
  });

  it('restores the production identity after a temporary demo session', () => {
    const store = useUIStore.getState();
    store.setAdminUsers([productionUser]);
    store.login(productionUser.id);
    store.setWorkMode('demo');

    expect(useUIStore.getState().workMode).toBe('demo');
    expect(useUIStore.getState().currentUserId).not.toBe(productionUser.id);

    useUIStore.getState().setWorkMode('prod');

    expect(useUIStore.getState().isAuthenticated).toBe(true);
    expect(useUIStore.getState().currentUserId).toBe(productionUser.id);
    expect(useUIStore.getState().adminUsers).toEqual([productionUser]);
  });

  it('clears production snapshots on production logout', () => {
    const store = useUIStore.getState();
    store.setAdminUsers([productionUser]);
    store.login(productionUser.id);
    useUIStore.getState().logout();

    expect(useUIStore.getState().isAuthenticated).toBe(false);
    expect(useUIStore.getState().prodCurrentUserIdSnapshot).toBe('');
    expect(useUIStore.getState().prodAdminUsersSnapshot).toEqual([]);
  });

  it('preserves the current session access when the admin user list omits it', () => {
    const store = useUIStore.getState();
    store.setAdminUsers([productionUser]);
    store.login(productionUser.id);

    useUIStore.getState().setAdminUsers([
      {
        ...productionUser,
        position: 'Должность не указана',
        availableTabs: undefined,
        permissions: {},
      },
    ]);

    const currentUser = useUIStore.getState().adminUsers.find((user) => user.id === productionUser.id);
    expect(currentUser?.availableTabs).toEqual(productionUser.availableTabs);
    expect(currentUser?.permissions).toEqual(productionUser.permissions);
    expect(useUIStore.getState().isAuthenticated).toBe(true);
  });

  it('keeps the current session profile when it is outside the admin list page', () => {
    const store = useUIStore.getState();
    store.setAdminUsers([productionUser]);
    store.login(productionUser.id);

    useUIStore.getState().setAdminUsers([
      {
        ...productionUser,
        id: '84',
        login: 'other@example.com',
      },
    ]);

    expect(useUIStore.getState().adminUsers.some((user) => user.id === productionUser.id)).toBe(true);
  });
});
