export type AppTab = 'chat' | 'search' | 'documents' | 'checks' | 'history' | 'qa' | 'admin';

export type UserRole = 'user' | 'admin';

export const ROLE_LABELS: Record<UserRole, string> = {
  user: 'Пользователь',
  admin: 'Администратор',
};

export const USER_ROLE_BY_LABEL: Record<string, UserRole> = {
  Пользователь: 'user',
  Администратор: 'admin',
};

export const ROLE_DESCRIPTIONS: Record<UserRole, string> = {
  user: 'работа с чатами, поиском, проверкой и своей историей диалогов',
  admin: 'доступ ко всем рабочим разделам, пользователям, ролям, реестру, QA и журналам',
};

export const TAB_TITLES: Record<AppTab, string> = {
  chat: 'Чат инженера',
  search: 'Поиск',
  documents: 'Реестр',
  checks: 'Проверка на соответствие требований НСИ',
  history: 'История',
  qa: 'QA',
  admin: 'Администрирование',
};

export const TAB_DESCRIPTIONS: Record<AppTab, string> = {
  chat: '',
  search: '',
  documents: '',
  checks: '',
  history: '',
  qa: '',
  admin: '',
};

export const ROLE_TAB_ACCESS: Record<UserRole, AppTab[]> = {
  user: ['chat', 'search', 'checks', 'history'],
  admin: ['chat', 'search', 'documents', 'checks', 'history', 'qa', 'admin'],
};

export const ADMIN_SECTIONS_ACCESS: Record<UserRole, string[]> = {
  user: [],
  admin: ['users', 'documents', 'processingLogs', 'permissions', 'systemSettings'],
};

export function canAccessTab(role: UserRole, tab: AppTab) {
  return ROLE_TAB_ACCESS[role].includes(tab);
}

export function getFallbackTab(role: UserRole): AppTab {
  return ROLE_TAB_ACCESS[role][0] ?? 'chat';
}
