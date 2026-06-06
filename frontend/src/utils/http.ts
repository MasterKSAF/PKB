import axios from 'axios';
import {
  MOCK_CHATS,
  MOCK_CITATIONS,
  MOCK_DOCUMENTS,
  MOCK_ENGINEER_RATINGS,
  MOCK_HISTORY,
  MOCK_KNOWLEDGE_SECTIONS,
  MOCK_METRICS,
  type AdminUser,
  type ChatMessage,
  type Citation,
  type Document,
  type EngineerRatingMetrics,
  type KnowledgeSection,
  type ProcessingLogItem,
  type ProcessingQueueItem,
  type QueryHistoryItem,
  type SystemMetrics,
} from './mockData';
import { useUIStore } from '../store/uiStore';

const DEFAULT_GATEWAY_URL = 'http://127.0.0.1:8081/api/v1';
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_GATEWAY_URL;
const GATEWAY_AUTO_LOGIN = import.meta.env.VITE_GATEWAY_AUTO_LOGIN !== 'false';
const GATEWAY_USERNAME = import.meta.env.VITE_GATEWAY_USERNAME ?? 'admin@example.com';
const GATEWAY_PASSWORD = import.meta.env.VITE_GATEWAY_PASSWORD ?? 'admin123';
const ACCESS_TOKEN_KEY = 'pkb_gateway_access_token_v2';
const REFRESH_TOKEN_KEY = 'pkb_gateway_refresh_token_v2';
const LEGACY_ACCESS_TOKEN_KEY = 'pkb_gateway_access_token';
const LEGACY_REFRESH_TOKEN_KEY = 'pkb_gateway_refresh_token';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 6500,
});

export type MonitorLogRow = {
  time: string;
  text: string;
  level?: 'INFO' | 'WARN' | 'ERROR' | string;
};

export type MetricsDashboard = {
  control: SystemMetrics;
  answers: EngineerRatingMetrics;
  logs: MonitorLogRow[];
};

export type GatewayChatProject = {
  id: string;
  name: string;
  chats: Array<{
    id: string;
    title: string;
    preview?: string;
    updatedAt?: string;
  }>;
};

export type GatewayHealth = {
  status: string;
  service?: string;
  version?: string;
  timestamp?: string;
  raw?: unknown;
};

function isDemoMode() {
  return useUIStore.getState().workMode === 'demo';
}

function toUiTimestamp(value?: string) {
  if (!value) return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getAccessToken() {
  if (typeof window === 'undefined') return null;
  window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(LEGACY_REFRESH_TOKEN_KEY);
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken() {
  if (typeof window === 'undefined') return null;
  window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(LEGACY_REFRESH_TOKEN_KEY);
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setGatewayTokens(payload: { access_token?: string; refresh_token?: string }) {
  if (typeof window === 'undefined') return;

  if (payload.access_token) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, payload.access_token);
  }

  if (payload.refresh_token) {
    window.localStorage.setItem(REFRESH_TOKEN_KEY, payload.refresh_token);
  }
}

async function syncGatewayCurrentUser(accessToken?: string) {
  const response = await apiClient.get('/auth/me', {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
  });
  const profile = mapGatewayProfileToAdminUser(response.data);
  const store = useUIStore.getState();

  store.upsertAdminUser(profile);
  store.setCurrentUserId(profile.id);

  return profile;
}

export function clearGatewayTokens() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

async function ensureGatewayToken() {
  if (isDemoMode() || !GATEWAY_AUTO_LOGIN) return;

  let token = getAccessToken();

  if (!token) {
    const response = await apiClient.post('/auth/token', {
      username: GATEWAY_USERNAME,
      password: GATEWAY_PASSWORD,
    });
    setGatewayTokens(response.data);
    token = response.data?.access_token;
  }

  const currentUserId = useUIStore.getState().currentUserId;
  if (!currentUserId.includes('-')) {
    await syncGatewayCurrentUser(token ?? undefined);
  }
}

async function gatewayRequest<T>(request: () => Promise<{ data: T }>) {
  await ensureGatewayToken();

  try {
    return await request();
  } catch (error: any) {
    if (error?.response?.status === 401) {
      clearGatewayTokens();
      await ensureGatewayToken();
      return await request();
    }
    throw error;
  }
}

function needsClarification(query: string) {
  const normalized = query.toLowerCase();
  const broadWords = ['толщина', 'материал', 'соответствует', 'проверить', 'норма'];
  const hasBroadIntent = broadWords.some((word) => normalized.includes(word));
  const hasContext =
    normalized.includes('проект') ||
    normalized.includes('21900') ||
    normalized.includes('версия') ||
    normalized.includes('раздел') ||
    normalized.includes('чертеж');

  return hasBroadIntent && !hasContext;
}

function shouldShowNoKnowledgeResult(query: string) {
  const normalized = query.toLowerCase();
  const markers = ['ничего не найдено', 'нет данных', 'не найден', 'несуществ'];

  return markers.some((marker) => normalized.includes(marker));
}

function shouldShowOutOfScopeResult(query: string) {
  const normalized = query.toLowerCase();
  const markers = ['погода', 'температура на улице', 'курс валют', 'который час', 'сколько времени', 'текущее время'];

  return markers.some((marker) => normalized.includes(marker));
}

function mapGatewayStatus(status?: string, scenario?: string): ChatMessage['status'] {
  const normalized = String(status ?? '').toLowerCase();

  if (scenario === 'needs_clarification' || normalized === 'needs_clarification') return 'needs_clarification';
  if (scenario === 'conflict' || normalized === 'source_conflict') return 'source_conflict';
  if (scenario === 'out_of_scope' || normalized === 'out_of_scope') return 'out_of_scope';
  if (normalized === 'not_found') return 'not_found';
  if (scenario === 'failed' || normalized === 'failed' || normalized === 'error') return 'backend_error';
  if (normalized === 'insufficient_data') return 'insufficient_data';

  return 'answered';
}

function mapGatewaySource(source: any, index = 0): Citation {
  return {
    id: source.section_id ?? source.source_id ?? source.document_id ?? `gateway-source-${index}`,
    documentId: source.document_id ?? source.doc_id,
    document: source.document_title ?? source.document ?? source.document_id ?? 'Документ базы знаний',
    section: source.clause ?? source.section ?? source.section_id ?? 'Фрагмент источника',
    page: Number(source.page ?? source.page_num ?? 1),
    text: source.excerpt ?? source.content ?? source.text ?? '',
    version: source.version ?? 'Актуальная версия',
    confidence: typeof source.score === 'number' ? source.score : undefined,
    pagePreviewUrl: source.page_preview_url ?? source.preview_url,
    documentUrl: source.document_url ?? source.file_url,
    contentType: source.content_type,
  };
}

function mapGatewayChatResponse(payload: any, query: string): ChatMessage {
  const answerItems = Array.isArray(payload.answer_items) ? payload.answer_items : [];
  const directSources = Array.isArray(payload.sources) ? payload.sources : [];
  const itemSources = answerItems.flatMap((item: any) =>
    Array.isArray(item.sources) ? item.sources.map((source: any, index: number) => mapGatewaySource(source, index)) : [],
  );
  const citations = itemSources.length ? itemSources : directSources.map((source: any, index: number) => mapGatewaySource(source, index));

  if (payload.scenario === 'needs_clarification') {
    return {
      id: payload.answer_id ?? payload.message_id ?? Math.random().toString(36).slice(2),
      role: 'assistant',
      content: `Система просит уточнить запрос: ${(payload.missing_fields ?? []).join(', ') || 'недостаточно контекста'}.`,
      status: 'needs_clarification',
      timestamp: toUiTimestamp(payload.timestamp),
    };
  }

  if (payload.scenario === 'conflict') {
    return {
      id: payload.answer_id ?? payload.message_id ?? Math.random().toString(36).slice(2),
      role: 'assistant',
      content: payload.message ?? 'Система обнаружила конфликт источников.',
      status: 'source_conflict',
      timestamp: toUiTimestamp(payload.timestamp),
    };
  }

  const content =
    answerItems.length > 0
      ? answerItems.map((item: any, index: number) => `${item.number ?? index + 1}. ${item.text ?? ''}`.trim()).join('\n')
      : payload.content ?? payload.answer ?? payload.message ?? `Система приняла запрос: ${query}`;

  return {
    id: payload.answer_id ?? payload.message_id ?? Math.random().toString(36).slice(2),
    role: 'assistant',
    content,
    status: mapGatewayStatus(payload.status, payload.scenario),
    citations: citations.length ? citations : undefined,
    timestamp: toUiTimestamp(payload.timestamp),
  };
}

function mapGatewaySessionMessages(session: any): ChatMessage[] {
  const messages = Array.isArray(session.messages) ? session.messages : [];

  return messages.map((message: any, index: number) => ({
    id: message.message_id ?? `${session.session_id ?? 'session'}-${index}`,
    role: message.role === 'assistant' ? 'assistant' : 'user',
    content: message.content ?? message.text ?? message.answer ?? '',
    timestamp: toUiTimestamp(message.timestamp ?? message.created_at),
    status: message.role === 'assistant' ? mapGatewayStatus(message.status, message.scenario) : undefined,
    citations: Array.isArray(message.sources)
      ? message.sources.map((source: any, sourceIndex: number) => mapGatewaySource(source, sourceIndex))
      : undefined,
  }));
}

function mapGatewaySearchResponse(payload: any) {
  const items = Array.isArray(payload) ? payload : payload.results ?? payload.items ?? [];

  return items.map((item: any, index: number) => ({
    id: item.document_id ?? item.section_id ?? `gateway-search-${index}`,
    documentId: item.document_id ?? item.doc_id,
    name: item.document_title ?? item.title ?? item.document_id ?? 'Документ базы знаний',
    type: (item.document_type ?? item.source_type ?? item.type ?? 'PDF').toUpperCase(),
    version: item.version ?? 'Актуальная версия',
    source: item.document_type ?? item.source ?? 'База знаний',
    relevance: typeof item.score === 'number' ? item.score : 0,
    fragment: item.content ?? item.excerpt ?? item.text ?? '',
    page: Number(item.page ?? 1),
    section: item.clause ?? item.section ?? item.section_id ?? 'Фрагмент',
    pagePreviewUrl: item.page_preview_url ?? item.preview_url,
    documentUrl: item.document_url ?? item.file_url,
  }));
}

function mapGatewayDocumentsResponse(payload: any): Document[] {
  const documents = Array.isArray(payload) ? payload : payload.documents ?? payload.items ?? [];

  return documents.map((doc: any, index: number) => ({
    id: doc.document_id ?? doc.id ?? `gateway-document-${index}`,
    name: doc.title ?? doc.filename ?? doc.name ?? 'Документ базы знаний',
    type: (doc.document_type ?? doc.source_type ?? doc.type ?? 'PDF').toUpperCase(),
    version: `v${doc.latest_version ?? doc.version ?? 1}`,
    source: doc.source ?? doc.uploaded_by ?? 'База знаний',
    ocrStatus: doc.status === 'failed' ? 'Ошибка' : doc.status === 'uploaded' || doc.status === 'parsing' ? 'В обработке' : 'Завершено',
    indexStatus: doc.status === 'completed' || doc.status === 'approved' || doc.status === 'ready_for_promotion' ? 'Индексировано' : 'Ожидание',
    updatedAt: doc.updated_at ?? doc.created_at ?? '',
  }));
}

function mapGatewayHistoryResponse(payload: any): QueryHistoryItem[] {
  const items = Array.isArray(payload) ? payload : payload.items ?? payload.history ?? [];

  return items.map((item: any, index: number) => {
    const query = item.question ?? item.query ?? '';
    const answer = item.answer_preview ?? item.answer ?? '';
    const status = mapGatewayStatus(item.status);

    return {
      id: item.history_id ?? item.id ?? `gateway-history-${index}`,
      user: item.user_name ?? item.user_id ?? 'Пользователь системы',
      project: item.project ?? item.project_name ?? 'Проект не указан',
      topic: item.topic ?? item.title ?? 'Рабочий чат',
      session: item.session_id ?? item.session ?? '',
      query,
      answer,
      sources: Number(item.source_count ?? item.sources_count ?? 0),
      status,
      createdAt: item.created_at ?? item.timestamp ?? '',
      messages: [
        { id: `${item.history_id ?? index}-q`, role: 'user', content: query, timestamp: toUiTimestamp(item.created_at) },
        {
          id: `${item.history_id ?? index}-a`,
          role: 'assistant',
          content: answer,
          status,
          citations: Array.isArray(item.sources) ? item.sources.map((source: any, sourceIndex: number) => mapGatewaySource(source, sourceIndex)) : undefined,
          timestamp: toUiTimestamp(item.created_at),
        },
      ].filter((message) => message.content),
    };
  });
}

function mapGatewaySessionsResponse(payload: any): QueryHistoryItem[] {
  const sessions = Array.isArray(payload) ? payload : payload.sessions ?? payload.items ?? [];

  return sessions.map((session: any, index: number) => {
    const messages = mapGatewaySessionMessages(session);
    const userMessage = messages.find((message) => message.role === 'user');
    const assistantMessage = [...messages].reverse().find((message) => message.role === 'assistant');
    const sourceCount = messages.reduce((sum, message) => sum + (message.citations?.length ?? 0), 0);

    return {
      id: session.session_id ?? session.id ?? `gateway-session-${index}`,
      user: session.user_name ?? session.user_id ?? 'Пользователь системы',
      project: session.project ?? session.project_name ?? 'Рабочие диалоги',
      topic: session.topic ?? session.title ?? 'Рабочий диалог',
      session: session.title ?? session.session_id ?? `Сессия ${index + 1}`,
      query: userMessage?.content ?? session.last_question ?? session.last_message_preview ?? '',
      answer: assistantMessage?.content ?? session.last_answer ?? session.last_message_preview ?? '',
      sources: Number(session.source_count ?? sourceCount),
      status: mapGatewayStatus(session.status),
      createdAt: session.created_at ?? session.updated_at ?? '',
      messages,
    };
  });
}

function mapGatewaySessionsToProjects(payload: any): GatewayChatProject[] {
  const sessions = Array.isArray(payload) ? payload : payload.sessions ?? payload.items ?? [];
  const groups = new Map<string, GatewayChatProject>();

  sessions.forEach((session: any, index: number) => {
    const projectName = session.project ?? session.project_name ?? session.workspace ?? 'Рабочие диалоги';
    const projectId = session.project_id ?? projectName;

    if (!groups.has(projectId)) {
      groups.set(projectId, { id: projectId, name: projectName, chats: [] });
    }

    groups.get(projectId)?.chats.push({
      id: session.session_id ?? session.id ?? `gateway-session-${index}`,
      title: session.title ?? session.session_id ?? `Сессия ${index + 1}`,
      preview: session.last_message_preview ?? session.last_question ?? '',
      updatedAt: session.updated_at ?? session.created_at ?? '',
    });
  });

  return [...groups.values()];
}

function mapGatewayMetricsResponse(payload: any): SystemMetrics {
  const control = payload.control_metrics ?? payload;
  const toPercent = (value: unknown, fallback: number) => {
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return fallback;
    return numeric <= 1 ? Math.round(numeric * 100) : Math.round(numeric);
  };

  return {
    ocrQuality: toPercent(control.ocr_quality, MOCK_METRICS.ocrQuality),
    retrievalQuality: toPercent(control.retrieval_quality, MOCK_METRICS.retrievalQuality),
    answersWithSources: toPercent(control.answers_with_sources, MOCK_METRICS.answersWithSources),
    manualReviewQueue: Number(control.manual_review_queue ?? MOCK_METRICS.manualReviewQueue),
    searchLatency: Number(control.avg_latency_ms ? control.avg_latency_ms / 1000 : MOCK_METRICS.searchLatency),
  };
}

function mapGatewayAnswerMetrics(payload: any): EngineerRatingMetrics {
  const answer = payload.answer_metrics ?? payload;
  const useful = Number(answer.useful_rate ?? MOCK_ENGINEER_RATINGS.usefulRate);

  return {
    ratedAnswers: Number(answer.rated_answers ?? MOCK_ENGINEER_RATINGS.ratedAnswers),
    usefulRate: useful <= 1 ? Math.round(useful * 100) : Math.round(useful),
    flaggedForReview: Number(answer.flagged_for_review ?? MOCK_ENGINEER_RATINGS.flaggedForReview),
    unresolvedAfterReview: Number(answer.open_questions ?? MOCK_ENGINEER_RATINGS.unresolvedAfterReview),
    commonSignals: MOCK_ENGINEER_RATINGS.commonSignals,
  };
}

function mapGatewayMonitorLogs(payload: any): MonitorLogRow[] {
  const logs = Array.isArray(payload.logs) ? payload.logs : [];

  if (!logs.length) {
    return [{ time: toUiTimestamp(), text: 'Журнал проверки пока не получен.', level: 'INFO' }];
  }

  return logs.map((row: any, index: number) => ({
    time: toUiTimestamp(row.time ?? row.timestamp),
    text: row.text ?? row.message ?? row.type ?? `Событие системы ${index + 1}`,
    level: row.level ?? row.type,
  }));
}

function mapGatewayQueueResponse(payload: any): ProcessingQueueItem[] {
  const queue = Array.isArray(payload) ? payload : payload.queue ?? payload.items ?? [];

  return queue.map((item: any, index: number) => ({
    id: item.document_id ?? item.id ?? `gateway-queue-${index}`,
    document: item.title ?? item.document_title ?? item.document_id ?? 'Документ базы знаний',
    stage: item.status === 'failed' ? 'Индексация' : item.status === 'parsing' ? 'Разбор таблиц' : 'OCR',
    progress: Number(item.progress ?? (item.status === 'completed' ? 100 : 45)),
    status: item.status === 'failed' ? 'ошибка' : item.status === 'queued' || item.status === 'uploaded' ? 'в очереди' : 'в работе',
  }));
}

function countClassifierChildren(node: any): number {
  const children = Array.isArray(node.children) ? node.children : [];
  return children.length + children.reduce((sum: number, child: any) => sum + countClassifierChildren(child), 0);
}

function mapGatewayKnowledgeSections(payload: any): KnowledgeSection[] {
  const nodes = Array.isArray(payload) ? payload : payload.data ?? payload.items ?? payload.children ?? [];
  if (!nodes.length) return MOCK_KNOWLEDGE_SECTIONS;

  return nodes.map((node: any, index: number) => ({
    id: node.code ?? node.id ?? `gateway-section-${index}`,
    title: node.full_name ?? node.name ?? node.code ?? 'Раздел НСИ',
    description: `${node.classifier_system ?? 'Классификатор'}${node.effective_date ? `, действует с ${node.effective_date}` : ''}`,
    documents: Math.max(1, Number(node.documents_count ?? countClassifierChildren(node))),
    updatedAt: node.effective_date ?? node.updated_at ?? '',
    status: node.status === 'active' || node.status === 'Готово' ? 'Готово' : 'Нужна проверка',
  }));
}

function mapGatewayRole(role?: string): AdminUser['role'] {
  if (role === 'system_admin' || role === 'admin') return 'Системный администратор';
  if (role === 'knowledge_admin') return 'Администратор знаний';
  return 'Пользователь';
}

function mapGatewayUserStatus(active?: boolean): AdminUser['status'] {
  return active === false ? 'Отключен' : 'Активен';
}

function mapGatewayUsersResponse(payload: any): AdminUser[] {
  const users = Array.isArray(payload) ? payload : payload.users ?? payload.items ?? [];

  return users.map((user: any, index: number) => {
    const role = Array.isArray(user.roles) ? user.roles[0] : user.role;

    return {
      id: user.user_id ?? user.id ?? `gateway-user-${index}`,
      name: user.full_name ?? user.name ?? 'Пользователь системы',
      position: user.position ?? user.role_title ?? 'Должность не указана',
      login: user.email ?? user.username ?? user.login ?? '',
      role: mapGatewayRole(role),
      access: Array.isArray(user.available_tabs)
        ? user.available_tabs.join(', ')
        : Array.isArray(user.roles)
          ? user.roles.join(', ')
          : role ?? '',
      status: mapGatewayUserStatus(user.is_active),
      lastSeen: user.last_login_at ?? user.updated_at ?? '',
    };
  });
}

function mapGatewayProfileToAdminUser(profile: any): AdminUser {
  const role = profile.role ?? (Array.isArray(profile.roles) ? profile.roles[0] : undefined);

  return {
    id: profile.user_id ?? profile.id ?? 'gateway-current-user',
    name: profile.full_name ?? profile.name ?? profile.email ?? 'Пользователь системы',
    position: profile.position ?? profile.role_title ?? 'Пользователь',
    login: profile.email ?? profile.username ?? profile.login ?? profile.user_id ?? '',
    role: mapGatewayRole(role),
    access: Array.isArray(profile.available_tabs)
      ? profile.available_tabs.join(', ')
      : Array.isArray(profile.permissions)
        ? profile.permissions.join(', ')
        : JSON.stringify(profile.permissions ?? {}),
    status: mapGatewayUserStatus(profile.is_active),
    lastSeen: profile.last_login_at ?? '',
  };
}

function mapGatewayAuditResponse(payload: any): ProcessingLogItem[] {
  const events = Array.isArray(payload) ? payload : payload.events ?? payload.items ?? payload.audit ?? [];

  return events.slice(0, 20).map((event: any, index: number) => ({
    id: event.event_id ?? event.id ?? `gateway-audit-${index}`,
    time: toUiTimestamp(event.timestamp ?? event.created_at),
    document: event.resource_id || event.resource_type || 'Система',
    stage: 'Answer generation',
    event: `${event.action ?? 'event'}${event.ip_address ? `, ${event.ip_address}` : ''}`,
    retryStatus: event.action?.includes('error') || event.action?.includes('delete') ? 'Запланирована' : 'Не требуется',
    visibility: event.action?.includes('admin') ? 'Администратор' : 'Инженер',
  }));
}

function backendUnavailableMessage(): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: 'Серверная часть недоступна. Повторите запрос позже или переключитесь в демонстрационный режим.',
    status: 'backend_error',
    timestamp: toUiTimestamp(),
  };
}

function notFoundMessage(query: string): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: `В базе знаний не найдено подтвержденных фрагментов по запросу «${query}». Попробуйте уточнить формулировку, проект, раздел или документ.`,
    status: 'not_found',
    timestamp: toUiTimestamp(),
  };
}

function outOfScopeMessage(query: string): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: `Запрос «${query}» не относится к инженерным документам, НСИ или проектной проверке. Задайте вопрос в рамках базы знаний проекта.`,
    status: 'out_of_scope',
    timestamp: toUiTimestamp(),
  };
}

async function demoChatMessage(query: string): Promise<ChatMessage> {
  await new Promise((resolve) => setTimeout(resolve, 900));

  if (needsClarification(query)) {
    return {
      id: Math.random().toString(36).slice(2),
      role: 'assistant',
      content:
        'Нужно уточнить контекст, чтобы не дать слишком общий ответ. Укажите проект, тип конструкции, версию НСИ или конкретный документ.',
      status: 'needs_clarification',
      limitation: 'По ТЗ ассистент не должен угадывать недостающие параметры.',
      timestamp: toUiTimestamp(),
    };
  }

  if (shouldShowOutOfScopeResult(query)) return outOfScopeMessage(query);
  if (shouldShowNoKnowledgeResult(query)) return notFoundMessage(query);

  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content:
      `1. По запросу "${query}" найдены релевантные фрагменты в базе знаний.\n` +
      '2. Ответ сформирован только по документам, которые попали в подборку источников.\n' +
      '3. Перед применением результата нужно открыть источник и сверить страницу, раздел и редакцию документа.',
    status: 'answered',
    citations: MOCK_CITATIONS,
    timestamp: toUiTimestamp(),
  };
}

function demoSearchResults(q: string) {
  if (shouldShowNoKnowledgeResult(q) || shouldShowOutOfScopeResult(q)) return [];

  return MOCK_DOCUMENTS.map((doc, index) => ({
    ...doc,
    section: MOCK_KNOWLEDGE_SECTIONS[index % MOCK_KNOWLEDGE_SECTIONS.length].title,
    relevance: 0.92,
    fragment: 'Найденный фрагмент в документе: описание технических требований и связанных параметров проекта.',
  }));
}

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/token', { username, password });
    setGatewayTokens(response.data);
    const profile = await syncGatewayCurrentUser(response.data?.access_token);
    useUIStore.getState().setApiStatus('online');
    return profile;
  },
  me: async (): Promise<AdminUser> => {
    const response = await gatewayRequest<any>(() => apiClient.get('/auth/me'));
    return mapGatewayProfileToAdminUser(response.data);
  },
  refresh: async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) throw new Error('Refresh token is empty');

    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    setGatewayTokens(response.data);
    return response.data;
  },
  logout: async () => {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) {
        await apiClient.post('/auth/revoke', { refresh_token: refreshToken });
      }
    } finally {
      clearGatewayTokens();
      useUIStore.getState().setCurrentGatewaySessionId(null);
      useUIStore.getState().setApiStatus(useUIStore.getState().workMode === 'demo' ? 'demo' : 'offline');
    }
  },
};

export const systemApi = {
  health: async (): Promise<GatewayHealth> => {
    try {
      const response = await apiClient.get('/system/health');
      return {
        status: response.data?.status ?? 'unknown',
        service: response.data?.service,
        version: response.data?.version,
        timestamp: response.data?.timestamp,
        raw: response.data,
      };
    } catch {
      const response = await apiClient.get('/monitor/health');
      return {
        status: response.data?.status ?? 'unknown',
        service: response.data?.service ?? 'monitor',
        version: response.data?.version,
        raw: response.data,
      };
    }
  },
};

export const chatApi = {
  sessions: async (): Promise<GatewayChatProject[]> => {
    const response = await gatewayRequest<any>(() => apiClient.get('/chat/sessions'));
    return mapGatewaySessionsToProjects(response.data);
  },
  getSession: async (sessionId: string): Promise<QueryHistoryItem> => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/chat/sessions/${sessionId}`));
    const [session] = mapGatewaySessionsResponse({ sessions: [response.data] });
    return session;
  },
  createSession: async (title: string) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.post('/chat/sessions', {
        title,
        document_ids: [],
      }),
    );
    return response.data;
  },
  updateSession: async (sessionId: string, patch: { title?: string; documentIds?: string[] }) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.put(`/chat/sessions/${sessionId}`, {
        title: patch.title,
        document_ids: patch.documentIds,
      }),
    );
    return response.data;
  },
  deleteSession: async (sessionId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.delete(`/chat/sessions/${sessionId}`));
    return response.data;
  },
  exportSession: async (sessionId: string, format = 'pdf') => {
    const response = await gatewayRequest<any>(() => apiClient.post(`/chat/sessions/${sessionId}/export`, { format }));
    return response.data;
  },
  send: async (query: string): Promise<ChatMessage> => {
    const demoMode = isDemoMode();

    if (demoMode) {
      useUIStore.getState().setApiStatus('demo');
      return demoChatMessage(query);
    }

    try {
      const createAndSelectSession = async () => {
        const created = await chatApi.createSession(query.slice(0, 70) || 'Новый чат');
        const sessionId = created.session_id ?? created.id ?? created.session?.session_id;

        if (sessionId) {
          useUIStore.getState().setCurrentGatewaySessionId(sessionId);
        }

        return sessionId;
      };
      const sendToSession = (sessionId: string) =>
        gatewayRequest<any>(() =>
          apiClient.post(`/chat/sessions/${sessionId}/messages`, {
            content: query,
          }),
        );
      const isStaleSessionError = (error: any) => {
        const status = error?.response?.status;
        return status === 400 || status === 404 || status === 410 || status === 422;
      };

      let activeSessionId = useUIStore.getState().currentGatewaySessionId;

      if (!activeSessionId) {
        activeSessionId = await createAndSelectSession();
      }

      if (!activeSessionId) throw new Error('Gateway session was not created');

      let response;

      try {
        response = await sendToSession(activeSessionId);
      } catch (sessionError) {
        if (!isStaleSessionError(sessionError)) throw sessionError;

        useUIStore.getState().setCurrentGatewaySessionId(null);
        activeSessionId = await createAndSelectSession();
        if (!activeSessionId) throw sessionError;
        response = await sendToSession(activeSessionId);
      }

      const session = await chatApi.getSession(activeSessionId);
      const latestAssistant = [...session.messages].reverse().find((message) => message.role === 'assistant');

      useUIStore.getState().setApiStatus('online');
      return latestAssistant ?? mapGatewayChatResponse({ ...response.data, session_id: activeSessionId }, query);
    } catch {
      useUIStore.getState().setApiStatus('offline');

      try {
        const response = await gatewayRequest<any>(() => apiClient.post('/chat', { question: query }));
        useUIStore.getState().setApiStatus('online');
        return mapGatewayChatResponse(response.data, query);
      } catch {
        return backendUnavailableMessage();
      }
    }
  },
};

export const searchApi = {
  query: async (q: string) => {
    const demoMode = isDemoMode();

    if (demoMode) {
      useUIStore.getState().setApiStatus('demo');
      return demoSearchResults(q);
    }

    try {
      const response = await gatewayRequest<any>(() => apiClient.post('/documents/search', { query: q, top_k: 10 }));
      useUIStore.getState().setApiStatus('online');
      return mapGatewaySearchResponse(response.data);
    } catch {
      useUIStore.getState().setApiStatus('offline');

      try {
        const response = await gatewayRequest<any>(() => apiClient.post('/text/search', { text: q, top_k: 10 }));
        useUIStore.getState().setApiStatus('online');
        return mapGatewaySearchResponse(response.data);
      } catch {
        throw new Error('Серверная часть недоступна');
      }
    }
  },
};

export const documentsApi = {
  list: async () => {
    if (isDemoMode()) return MOCK_DOCUMENTS;

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/documents'));
      return mapGatewayDocumentsResponse(response.data);
    } catch {
      return MOCK_DOCUMENTS;
    }
  },
  queue: async () => {
    if (isDemoMode()) return [];

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/documents/queue'));
      return mapGatewayQueueResponse(response.data);
    } catch {
      return [];
    }
  },
  knowledgeSections: async () => {
    if (isDemoMode()) return MOCK_KNOWLEDGE_SECTIONS;

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/classifiers/tree'));
      return mapGatewayKnowledgeSections(response.data);
    } catch {
      return MOCK_KNOWLEDGE_SECTIONS;
    }
  },
  upload: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const response = await gatewayRequest<any>(() =>
      apiClient.post('/documents', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    );
    return response.data;
  },
  reprocess: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.post(`/documents/${documentId}/reprocess`, { mode: 'full' }));
    return response.data;
  },
  versions: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/versions`));
    return Array.isArray(response.data?.versions) ? response.data.versions : [];
  },
  archive: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.delete(`/documents/${documentId}`));
    return response.data;
  },
};

export const historyApi = {
  get: async () => {
    if (isDemoMode()) return MOCK_HISTORY;

    try {
      const sessionsResponse = await gatewayRequest<any>(() => apiClient.get('/chat/sessions'));
      const sessions = mapGatewaySessionsResponse(sessionsResponse.data);

      const hydrated = await Promise.all(
        sessions.map(async (session) => {
          try {
            return await chatApi.getSession(session.id);
          } catch {
            return session;
          }
        }),
      );
      useUIStore.getState().setApiStatus('online');
      return hydrated;
    } catch {
      try {
        const response = await gatewayRequest<any>(() => apiClient.get('/chat/history'));
        useUIStore.getState().setApiStatus('online');
        return mapGatewayHistoryResponse(response.data);
      } catch {
        useUIStore.getState().setApiStatus('offline');
        return MOCK_HISTORY;
      }
    }
  },
  export: async (format = 'csv') => {
    const response = await gatewayRequest<any>(() => apiClient.get('/chat/history/export', { params: { format } }));
    return response.data;
  },
};

export const metricsApi = {
  get: async (): Promise<SystemMetrics> => {
    if (isDemoMode()) return MOCK_METRICS;

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/monitor/metrics'));
      useUIStore.getState().setApiStatus('online');
      return mapGatewayMetricsResponse(response.data);
    } catch {
      useUIStore.getState().setApiStatus('offline');
      return MOCK_METRICS;
    }
  },
  dashboard: async (): Promise<MetricsDashboard> => {
    if (isDemoMode()) {
      return {
        control: MOCK_METRICS,
        answers: MOCK_ENGINEER_RATINGS,
        logs: [{ time: toUiTimestamp(), text: 'Журнал QA сформирован на демонстрационных данных.', level: 'INFO' }],
      };
    }

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/monitor/metrics'));
      useUIStore.getState().setApiStatus('online');
      return {
        control: mapGatewayMetricsResponse(response.data),
        answers: mapGatewayAnswerMetrics(response.data),
        logs: mapGatewayMonitorLogs(response.data),
      };
    } catch {
      useUIStore.getState().setApiStatus('offline');
      return {
        control: MOCK_METRICS,
        answers: MOCK_ENGINEER_RATINGS,
        logs: [{ time: toUiTimestamp(), text: 'Серверная часть недоступна, показаны демонстрационные метрики.', level: 'WARN' }],
      };
    }
  },
};

export const adminApi = {
  users: async () => {
    if (isDemoMode()) return useUIStore.getState().adminUsers;

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/admin/users'));
      const users = mapGatewayUsersResponse(response.data);
      useUIStore.getState().setAdminUsers(users);
      useUIStore.getState().setApiStatus('online');
      return users;
    } catch {
      useUIStore.getState().setApiStatus('offline');
      return useUIStore.getState().adminUsers;
    }
  },
  audit: async () => {
    if (isDemoMode()) return [];

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/admin/audit'));
      return mapGatewayAuditResponse(response.data);
    } catch {
      return [];
    }
  },
  updateUser: async (userId: string, payload: { role?: string; roles?: string[]; email?: string; fullName?: string; position?: string }) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.patch(`/admin/users/${userId}`, {
        role: payload.role,
        roles: payload.roles,
        email: payload.email,
        full_name: payload.fullName,
        position: payload.position,
      }),
    );
    return response.data;
  },
};

export const sourceApi = {
  preview: async (citation: Citation, previewKind: 'source' | 'document') => {
    if (!citation.documentId) return citation;

    try {
      if (previewKind === 'document') {
        const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${citation.documentId}/file`));

        return {
          ...citation,
          text: response.data?.text ?? response.data?.content ?? citation.text,
          documentUrl: response.data?.file_url ?? response.data?.document_url ?? citation.documentUrl,
          contentType: response.data?.content_type ?? citation.contentType,
        };
      }

      const [previewResponse, textResponse] = await Promise.allSettled([
        gatewayRequest<any>(() => apiClient.get(`/documents/${citation.documentId}/pages/${citation.page}/preview`)),
        gatewayRequest<any>(() => apiClient.get(`/documents/${citation.documentId}/pages/${citation.page}/text`)),
      ]);

      const previewData = previewResponse.status === 'fulfilled' ? previewResponse.value.data : {};
      const textData = textResponse.status === 'fulfilled' ? textResponse.value.data : {};

      return {
        ...citation,
        text: textData?.full_text ?? textData?.text ?? previewData?.text ?? previewData?.content ?? citation.text,
        pagePreviewUrl: previewData?.preview_url ?? previewData?.image_url ?? citation.pagePreviewUrl,
        documentUrl: previewData?.file_url ?? previewData?.document_url ?? citation.documentUrl,
        contentType: previewData?.content_type ?? textData?.content_type ?? citation.contentType,
      };
    } catch {
      return citation;
    }
  },
};

export const feedbackApi = {
  send: async (payload: { useful: boolean; comment: string; sessionId?: string; messageId?: string }) => {
    try {
      await gatewayRequest<any>(() =>
        apiClient.post('/chat/feedback', {
          session_id: payload.sessionId ?? useUIStore.getState().currentGatewaySessionId ?? 'ui-final-session',
          message_id: payload.messageId ?? 'ui-final-message',
          rating: payload.useful ? 5 : 1,
          useful: payload.useful,
          comment: payload.comment,
        }),
      );
      return { ok: true };
    } catch {
      return { ok: true, demo: true };
    }
  },
};

export const initialChatMessages = MOCK_CHATS;
