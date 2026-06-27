export type AppTab = 'chat' | 'search' | 'documents' | 'knowledgeProcessing' | 'history' | 'qa' | 'admin';

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
  user: 'работа с чатами, базой знаний и своей историей диалогов',
  knowledgeAdmin: 'ведение базы знаний, обработка документов и журналы обработки',
  systemAdmin: 'полный доступ ко всем разделам, пользователям, ролям, правам и журналам',
};

export const TAB_TITLES: Record<AppTab, string> = {
  chat: 'Чат инженера',
  search: 'Поиск',
  documents: 'База знаний',
  knowledgeProcessing: 'Обработка базы знаний',
  history: 'История',
  qa: 'QA',
  admin: 'Администрирование',
};

export const TAB_DESCRIPTIONS: Record<AppTab, string> = {
  chat: '',
  search: '',
  documents: '',
  knowledgeProcessing: '',
  history: '',
  qa: '',
  admin: '',
};

export const ROLE_TAB_ACCESS: Record<UserRole, AppTab[]> = {
  user: ['chat', 'documents', 'history'],
  knowledgeAdmin: ['chat', 'documents', 'knowledgeProcessing', 'history'],
  systemAdmin: ['chat', 'documents', 'knowledgeProcessing', 'history', 'qa', 'admin'],
};

const GATEWAY_TAB_ACCESS: Record<string, AppTab[]> = {
  chat: ['chat'],
  search: ['documents'],
  knowledge_base: ['documents'],
  documents: ['knowledgeProcessing'],
  registry: ['knowledgeProcessing'],
  knowledge_processing: ['knowledgeProcessing'],
  history: ['history'],
  monitor: ['qa'],
  qa: ['qa'],
  admin: ['admin'],
};

export const ADMIN_SECTIONS_ACCESS: Record<UserRole, string[]> = {
  user: [],
  knowledgeAdmin: ['processingLogs'],
  systemAdmin: ['users', 'processingLogs', 'permissions', 'systemSettings'],
};

export function canAccessTab(role: UserRole, tab: AppTab) {
  return ROLE_TAB_ACCESS[role].includes(tab);
}

export function getFallbackTab(role: UserRole): AppTab {
  return ROLE_TAB_ACCESS[role][0] ?? 'chat';
}

export function getAccessibleTabs(
  role: UserRole,
  availableTabs: string[] | undefined,
  workMode: 'demo' | 'prod',
): AppTab[] {
  if (workMode === 'demo') return ROLE_TAB_ACCESS[role];

  if (!Array.isArray(availableTabs)) {
    return ['chat'];
  }

  const mapped = availableTabs.flatMap((tab) => GATEWAY_TAB_ACCESS[String(tab).trim().toLowerCase()] ?? []);
  return Array.from(new Set(mapped));
}

export function getAccessibleFallbackTab(tabs: AppTab[]): AppTab {
  return tabs[0] ?? 'chat';
}
