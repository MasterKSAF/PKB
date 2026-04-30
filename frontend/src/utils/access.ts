export type AppTab = 'chat' | 'search' | 'documents' | 'checks' | 'history' | 'qa' | 'admin';

export type UserRole = 'engineer' | 'knowledge_admin' | 'system_admin';

export const ROLE_LABELS: Record<UserRole, string> = {
  engineer: 'Инженер',
  knowledge_admin: 'Администратор знаний',
  system_admin: 'Администратор системы',
};

export const USER_ROLE_BY_LABEL: Record<string, UserRole> = {
  Инженер: 'engineer',
  'Администратор знаний': 'knowledge_admin',
  'Администратор системы': 'system_admin',
};

export const ROLE_DESCRIPTIONS: Record<UserRole, string> = {
  engineer: 'работа с вопросами, поиском, проверкой и своей историей',
  knowledge_admin: 'управление базой НСИ, обработкой документов и качеством данных',
  system_admin: 'пользователи, роли, права доступа, настройки и полный журнал',
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
  engineer: ['chat', 'search', 'checks', 'history'],
  knowledge_admin: ['chat', 'search', 'documents', 'checks', 'history', 'qa', 'admin'],
  system_admin: ['chat', 'search', 'documents', 'checks', 'history', 'qa', 'admin'],
};

export const ADMIN_SECTIONS_ACCESS: Record<UserRole, string[]> = {
  engineer: [],
  knowledge_admin: ['documents', 'processingLogs'],
  system_admin: ['users', 'documents', 'processingLogs', 'permissions', 'systemSettings'],
};

export function canAccessTab(role: UserRole, tab: AppTab) {
  return ROLE_TAB_ACCESS[role].includes(tab);
}

export function getFallbackTab(role: UserRole): AppTab {
  return ROLE_TAB_ACCESS[role][0] ?? 'chat';
}
