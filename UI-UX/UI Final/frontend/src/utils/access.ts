export type AppTab = 'chat' | 'search' | 'documents' | 'checks' | 'history' | 'qa' | 'admin';

export type UserRole = 'user' | 'knowledgeAdmin' | 'systemAdmin';

export const ROLE_LABELS: Record<UserRole, string> = {
  user: 'Пользователь',
  knowledgeAdmin: 'Администратор знаний',
  systemAdmin: 'Системный администратор',
};

export const USER_ROLE_BY_LABEL: Record<string, UserRole> = {
  Пользователь: 'user',
  'Администратор знаний': 'knowledgeAdmin',
  'Системный администратор': 'systemAdmin',
};

export const ROLE_DESCRIPTIONS: Record<UserRole, string> = {
  user: 'работа с чатами, поиском и своей историей диалогов',
  knowledgeAdmin: 'ведение базы знаний, документов, OCR-артефактов и QA-метрик',
  systemAdmin: 'полный доступ ко всем разделам, пользователям, ролям, правам и журналам',
};

export const TAB_TITLES: Record<AppTab, string> = {
  chat: 'Чат инженера',
  search: 'Поиск',
  documents: 'База знаний',
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
  user: ['chat', 'search', 'history'],
  knowledgeAdmin: ['chat', 'search', 'documents', 'history', 'qa'],
  systemAdmin: ['chat', 'search', 'documents', 'checks', 'history', 'qa', 'admin'],
};

export const ADMIN_SECTIONS_ACCESS: Record<UserRole, string[]> = {
  user: [],
  knowledgeAdmin: ['documents', 'processingLogs'],
  systemAdmin: ['users', 'documents', 'processingLogs', 'permissions', 'systemSettings'],
};

export function canAccessTab(role: UserRole, tab: AppTab) {
  return ROLE_TAB_ACCESS[role].includes(tab);
}

export function getFallbackTab(role: UserRole): AppTab {
  return ROLE_TAB_ACCESS[role][0] ?? 'chat';
}
