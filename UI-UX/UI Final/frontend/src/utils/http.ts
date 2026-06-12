import axios from 'axios';
import {
  MOCK_ADMIN_USERS,
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
import { USER_ROLE_BY_LABEL } from './access';
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
  code?: string;
  description?: string;
  status?: string;
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

type DraftCreateInput = {
  sourceType?: string;
  title?: string;
  docCode?: string;
  mksOksCode?: string;
  okstuCode?: string;
  era?: string;
  jurisdiction?: string;
  issuingBody?: string;
  metadata?: Record<string, unknown> | string;
  idempotencyKey?: string;
};

type DraftPreviewMetadata = {
  doc_code?: string;
  title?: string;
  document_type?: string;
  year?: string | number | null;
  revision?: string | number | null;
};

type GatewayDocumentDetail = {
  document_id?: string;
  id?: string;
  title?: string;
  doc_code?: string;
  source_type?: string;
  status?: string;
  era?: string;
  validity_status?: string;
  jurisdiction?: string;
  issuing_body?: string;
  mks_oks_code?: string | null;
  okstu_code?: string | null;
  classification_status?: Record<string, unknown>;
  successor_doc_id?: string | null;
  predecessor_doc_id?: string | null;
  chunk_container_id?: string | null;
  metadata?: Record<string, unknown>;
  latest_version?: Record<string, unknown> | null;
  total_versions?: number;
  user_id?: string;
  uploaded_by?: string;
  created_by?: string;
  updated_by?: string;
  created_at?: string;
  updated_at?: string;
};

type GatewayDocumentStatus = {
  document_id?: string;
  status?: string;
  progress_percent?: number;
  pipeline?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string | null;
};

type GatewayDocumentErrors = {
  errors?: Array<Record<string, unknown>>;
  meta?: Record<string, unknown>;
};

type GatewayDocumentParameters = {
  document_id?: string;
  parameters?: Record<string, unknown>;
  extraction_confidence?: number;
  unconfirmed_fields?: string[];
  updated_at?: string;
};

type GatewayDocumentPages = {
  document_id?: string;
  pages_total?: number;
  pages?: Array<Record<string, unknown>>;
  meta?: Record<string, unknown>;
};

const EMPTY_SYSTEM_METRICS: SystemMetrics = {
  ocrQuality: 0,
  retrievalQuality: 0,
  answersWithSources: 0,
  manualReviewQueue: 0,
  searchLatency: 0,
};

const EMPTY_ENGINEER_RATINGS: EngineerRatingMetrics = {
  ratedAnswers: 0,
  usefulRate: 0,
  flaggedForReview: 0,
  unresolvedAfterReview: 0,
  commonSignals: [],
};

function appendFormValue(form: FormData, key: string, value: unknown) {
  if (value === undefined || value === null || value === '') return;
  form.append(key, typeof value === 'string' ? value : String(value));
}

function deriveDocumentKey(fileHashSha256?: string) {
  if (!fileHashSha256) return '';
  return `sha256:${fileHashSha256.slice(0, 16)}`;
}

function normalizeDraftStatus(status?: string) {
  const normalized = String(status ?? '').toLowerCase();
  if (['preview_ready', 'ready_for_approve', 'previewing', 'uploaded', 'new'].includes(normalized)) {
    return normalized === 'preview_ready' ? 'ready_for_approve' : normalized;
  }
  if (['promoted', 'approved'].includes(normalized)) return 'approved';
  if (normalized === 'discarded') return 'discarded';
  if (normalized === 'failed' || normalized === 'error') return 'failed';
  return normalized || 'uploaded';
}

function normalizePreviewMetadata(payload?: DraftPreviewMetadata | null) {
  if (!payload) return null;

  return {
    doc_code: payload.doc_code ?? '',
    title: payload.title ?? '',
    document_type: payload.document_type ?? 'normative',
    year: payload.year ?? null,
    revision: payload.revision ?? null,
  };
}

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
  store.setCurrentRole(USER_ROLE_BY_LABEL[profile.role] ?? 'user');

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

  if (normalized === 'pending') return 'pending';
  if (normalized === 'enriching') return 'enriching';
  if (normalized === 'searching') return 'searching';
  if (normalized === 'generating') return 'generating';
  if (normalized === 'enriching_citations') return 'enriching_citations';
  if (normalized === 'completed' || normalized === 'answered') return 'answered';
  if (scenario === 'failed' || normalized === 'failed' || normalized === 'error') return 'failed';

  return 'answered';
}

function mapGatewayDocumentOcrStatus(status?: string): Document['ocrStatus'] {
  const normalized = String(status ?? '').toLowerCase();

  if (normalized === 'failed' || normalized === 'error') return 'Ошибка';
  if (['uploaded', 'queued', 'created', 'processing', 'parsing', 'previewing', 'indexing'].includes(normalized)) {
    return 'В обработке';
  }

  return 'Завершено';
}

function mapGatewayDocumentIndexStatus(status?: string): Document['indexStatus'] {
  const normalized = String(status ?? '').toLowerCase();

  if (['indexed', 'completed', 'approved', 'ready_for_promotion'].includes(normalized)) return 'Индексировано';
  return 'Ожидание';
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
  const messagePayload = payload?.message ?? payload;
  const answerItems = Array.isArray(messagePayload.answer_items) ? messagePayload.answer_items : [];
  const directSources = Array.isArray(messagePayload.sources) ? messagePayload.sources : [];
  const itemSources = answerItems.flatMap((item: any) =>
    Array.isArray(item.sources) ? item.sources.map((source: any, index: number) => mapGatewaySource(source, index)) : [],
  );
  const citations = itemSources.length ? itemSources : directSources.map((source: any, index: number) => mapGatewaySource(source, index));

  if (messagePayload.scenario === 'needs_clarification') {
    return {
      id: messagePayload.message_id ?? messagePayload.answer_id ?? Math.random().toString(36).slice(2),
      role: 'assistant',
      content: `Система просит уточнить запрос: ${(messagePayload.missing_fields ?? []).join(', ') || 'недостаточно контекста'}.`,
      status: 'answered',
      limitation: 'Gateway вернул сценарий needs_clarification; статус сообщения оставлен в документированной FSM.',
      timestamp: toUiTimestamp(messagePayload.timestamp),
    };
  }

  if (messagePayload.scenario === 'conflict') {
    return {
      id: messagePayload.message_id ?? messagePayload.answer_id ?? Math.random().toString(36).slice(2),
      role: 'assistant',
      content: messagePayload.message ?? 'Система обнаружила конфликт источников.',
      status: 'answered',
      limitation: 'Gateway вернул сценарий conflict; статус сообщения оставлен в документированной FSM.',
      timestamp: toUiTimestamp(messagePayload.timestamp),
    };
  }

  const content =
    answerItems.length > 0
      ? answerItems.map((item: any, index: number) => `${item.number ?? index + 1}. ${item.text ?? ''}`.trim()).join('\n')
      : messagePayload.content ?? messagePayload.answer ?? messagePayload.message ?? `Система приняла запрос: ${query}`;

  return {
    id: messagePayload.message_id ?? messagePayload.answer_id ?? Math.random().toString(36).slice(2),
    role: 'assistant',
    content,
    status: mapGatewayStatus(messagePayload.status, messagePayload.scenario),
    citations: citations.length ? citations : undefined,
    timestamp: toUiTimestamp(messagePayload.timestamp),
  };
}

function isFinalChatStatus(status?: string) {
  const normalized = String(status ?? '').toLowerCase();
  return normalized === 'answered' || normalized === 'completed' || normalized === 'failed';
}

function chatLongpollIncompleteMessage(messageId?: string): ChatMessage {
  return {
    id: messageId ?? Math.random().toString(36).slice(2),
    role: 'assistant',
    content:
      'Gateway принял сообщение, но не вернул финальный ответ за время ожидания. Повторите запрос позже или обновите историю чата.',
    status: 'failed',
    timestamp: toUiTimestamp(),
  };
}

async function waitForGatewayChatMessage(sessionId: string, messageId: string, longpoll = 15, maxAttempts = 4) {
  let lastResponse: any = null;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const response = await gatewayRequest<any>(() =>
      apiClient.get(`/chat/sessions/${sessionId}/messages/${messageId}`, {
        params: { longpoll },
      }),
    );

    lastResponse = response.data;
    const messagePayload = response.data?.message ?? response.data;

    if (isFinalChatStatus(messagePayload?.status)) {
      return response.data;
    }
  }

  const lastStatus = lastResponse?.message?.status ?? lastResponse?.status ?? 'unknown';
  throw new Error(`Longpoll did not reach final status: ${lastStatus}`);
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

  return documents.map((doc: any, index: number) => {
    const normalizedStatus = String(doc.status ?? '').toLowerCase();
    const classificationStatus = doc.classification_status ?? {};
    const mksOksCode =
      doc.mks_oks_code ??
      doc.mks_oks ??
      doc.oks_code ??
      (Array.isArray(classificationStatus.mks) ? classificationStatus.mks[0] : undefined) ??
      '';
    const okstuCode =
      doc.okstu_code ??
      (Array.isArray(classificationStatus.okstu) ? classificationStatus.okstu[0] : undefined) ??
      '';
    const classifierCode = doc.classifier_code ?? doc.section_code ?? mksOksCode ?? okstuCode ?? '';
    const group = doc.group ?? doc.classification_group ?? doc.classifier_group ?? classifierCode ?? '';

    return {
      id: doc.document_id ?? doc.id ?? `gateway-document-${index}`,
      name: doc.title ?? doc.filename ?? doc.name ?? 'Документ базы знаний',
      type: (doc.document_type ?? doc.source_type ?? doc.type ?? 'PDF').toUpperCase(),
      version: `v${doc.latest_version ?? doc.version ?? 1}`,
      source: doc.source ?? doc.uploaded_by ?? 'База знаний',
      ocrStatus: mapGatewayDocumentOcrStatus(normalizedStatus),
      indexStatus: mapGatewayDocumentIndexStatus(normalizedStatus),
      updatedAt: doc.updated_at ?? doc.created_at ?? '',
      sectionId: doc.section_id ?? group,
      group,
      sourceType: doc.source_type ?? doc.document_type ?? doc.type ?? '',
      documentKey: doc.document_key ?? doc.file_hash_sha256 ?? '',
      classifierCode,
      classifierSystem: doc.classifier_system ?? (mksOksCode ? 'MKS' : okstuCode ? 'OKSTU' : ''),
      mksOksCode,
      okstuCode,
    };
  });
}

function mapGatewayDocumentDetailResponse(payload: any): GatewayDocumentDetail {
  const data = payload?.data ?? payload ?? {};

  return {
    document_id: data.document_id ?? data.id ?? '',
    id: data.document_id ?? data.id ?? '',
    title: data.title ?? '',
    doc_code: data.doc_code ?? '',
    source_type: data.source_type ?? '',
    status: data.status ?? '',
    era: data.era ?? '',
    validity_status: data.validity_status ?? '',
    jurisdiction: data.jurisdiction ?? '',
    issuing_body: data.issuing_body ?? '',
    mks_oks_code: data.mks_oks_code ?? null,
    okstu_code: data.okstu_code ?? null,
    classification_status: data.classification_status ?? {},
    successor_doc_id: data.successor_doc_id ?? null,
    predecessor_doc_id: data.predecessor_doc_id ?? null,
    chunk_container_id: data.chunk_container_id ?? null,
    metadata: data.metadata ?? {},
    latest_version: data.latest_version ?? null,
    total_versions: Number(data.total_versions ?? 0),
    user_id: data.user_id ?? '',
    uploaded_by: data.uploaded_by ?? '',
    created_by: data.created_by ?? '',
    updated_by: data.updated_by ?? '',
    created_at: data.created_at ?? '',
    updated_at: data.updated_at ?? '',
  };
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

function mapGatewayProject(project: any, index = 0): GatewayChatProject {
  const projectId = String(project.project_id ?? project.id ?? project.code ?? `gateway-project-${index}`);

  return {
    id: projectId,
    name: project.name ?? project.title ?? project.code ?? `Проект ${index + 1}`,
    code: project.code,
    description: project.description,
    status: project.status,
    chats: [],
  };
}

function mapGatewayProjectsResponse(payload: any): GatewayChatProject[] {
  const items = Array.isArray(payload) ? payload : payload.items ?? payload.projects ?? payload.data ?? [];
  return items.map((project: any, index: number) => mapGatewayProject(project, index));
}

function mergeGatewayProjectsWithSessions(projects: GatewayChatProject[], sessionProjects: GatewayChatProject[]) {
  if (!projects.length) return sessionProjects;

  const merged = new Map<string, GatewayChatProject>();
  projects.forEach((project) => {
    merged.set(project.id, { ...project, chats: [...project.chats] });
  });

  sessionProjects.forEach((sessionProject) => {
    const matchingProject =
      merged.get(sessionProject.id) ??
      [...merged.values()].find(
        (project) =>
          (project.code && project.code === sessionProject.code) ||
          project.name.trim().toLowerCase() === sessionProject.name.trim().toLowerCase(),
      );

    if (matchingProject) {
      matchingProject.chats = [...matchingProject.chats, ...sessionProject.chats];
      return;
    }

    merged.set(sessionProject.id, sessionProject);
  });

  return [...merged.values()];
}

function normalizeGatewayProjectId(projectId?: string) {
  if (!projectId || projectId === 'gateway-dialogs') return undefined;
  return projectId;
}

function createGatewayProjectCode(name: string) {
  const normalized = name
    .trim()
    .toUpperCase()
    .replace(/[^A-ZА-Я0-9]+/gi, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 20);

  return `${normalized || 'UI'}-${Date.now().toString(36).toUpperCase()}`;
}

function mapGatewayMetricsResponse(payload: any): SystemMetrics {
  const control = payload.control_metrics ?? payload;
  const toPercent = (value: unknown, fallback: number) => {
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return fallback;
    return numeric <= 1 ? Math.round(numeric * 100) : Math.round(numeric);
  };

  return {
    ocrQuality: toPercent(control.ocr_quality, 0),
    retrievalQuality: toPercent(control.retrieval_quality, 0),
    answersWithSources: toPercent(control.answers_with_sources, 0),
    manualReviewQueue: Number(control.manual_review_queue ?? 0),
    searchLatency: Number(control.avg_latency_ms ? control.avg_latency_ms / 1000 : 0),
  };
}

function mapGatewayAnswerMetrics(payload: any): EngineerRatingMetrics {
  const answer = payload.answer_metrics ?? payload;
  const useful = Number(answer.useful_rate ?? 0);

  return {
    ratedAnswers: Number(answer.rated_answers ?? 0),
    usefulRate: useful <= 1 ? Math.round(useful * 100) : Math.round(useful),
    flaggedForReview: Number(answer.flagged_for_review ?? 0),
    unresolvedAfterReview: Number(answer.open_questions ?? 0),
    commonSignals: Array.isArray(answer.common_signals)
      ? answer.common_signals.map((item: any, index: number) => ({
          label: item.label ?? item.name ?? `Сигнал ${index + 1}`,
          count: Number(item.count ?? item.value ?? 0),
        }))
      : [],
  };
}

function mapGatewayMonitorLogs(payload: any): MonitorLogRow[] {
  const logs = Array.isArray(payload.logs) ? payload.logs : [];

  if (!logs.length) {
    return [];
  }

  return logs.map((row: any, index: number) => ({
    time: toUiTimestamp(row.time ?? row.timestamp),
    text: row.text ?? row.message ?? row.type ?? `Событие системы ${index + 1}`,
    level: row.level ?? row.type,
  }));
}

function mapGatewayQueueResponse(payload: any): ProcessingQueueItem[] {
  const queue = Array.isArray(payload) ? payload : payload.queue ?? payload.items ?? [];

  return queue.map((item: any, index: number) => {
    const status = String(item.status ?? '').toLowerCase();
    const progressByStatus: Record<string, number> = {
      queued: 10,
      uploaded: 18,
      created: 24,
      parsing: 38,
      processing: 45,
      previewing: 58,
      ready_for_approve: 76,
      indexing: 82,
      completed: 100,
      indexed: 100,
      approved: 100,
      failed: 100,
    };
    const stage =
      status === 'parsing'
        ? 'Разбор таблиц'
        : ['indexing', 'indexed', 'completed', 'approved', 'failed'].includes(status)
          ? 'Индексация'
          : 'OCR';

    return {
      id: item.document_id ?? item.draft_id ?? item.id ?? `gateway-queue-${index}`,
      document: item.title ?? item.document_title ?? item.filename ?? item.document_id ?? 'Документ базы знаний',
      stage,
      progress: Number(item.progress ?? item.progress_percent ?? progressByStatus[status] ?? 45),
      status:
        status === 'failed' || status === 'error'
          ? 'ошибка'
          : ['queued', 'uploaded', 'created'].includes(status)
            ? 'в очереди'
            : 'в работе',
    };
  });
}

function countClassifierChildren(node: any): number {
  const children = Array.isArray(node.children) ? node.children : [];
  return children.length + children.reduce((sum: number, child: any) => sum + countClassifierChildren(child), 0);
}

function flattenClassifierNodes(nodes: any[], depth = 0): any[] {
  return nodes.flatMap((node) => {
    const children = Array.isArray(node.children) ? node.children : [];
    return [
      { ...node, depth, childrenCount: children.length },
      ...flattenClassifierNodes(children, depth + 1),
    ];
  });
}

function mapGatewayKnowledgeSections(payload: any): KnowledgeSection[] {
  const rootNodes = Array.isArray(payload) ? payload : payload.data ?? payload.items ?? payload.children ?? [];
  const nodes = flattenClassifierNodes(rootNodes);
  if (!nodes.length) return [];

  return nodes.map((node: any, index: number) => ({
    id: node.code ?? node.id ?? `gateway-section-${index}`,
    title: node.full_name ?? node.name ?? node.code ?? 'Раздел НСИ',
    description:
      `${node.classifier_system ?? 'Классификатор'}${node.parent_code ? ` · родитель ${node.parent_code}` : ''}` +
      `${node.childrenCount ? ` · ${node.childrenCount} подразделов` : ''}`,
    documents: Number(node.documents_count ?? node.document_count ?? node.linked_documents_count ?? 0),
    updatedAt: node.effective_date ?? node.updated_at ?? '',
    status: node.status === 'active' || node.status === 'Готово' ? 'Готово' : 'Нужна проверка',
  }));
}

function mapGatewayRole(role?: string): AdminUser['role'] {
  const normalized = String(role ?? '').trim().toLowerCase();

  if (normalized === 'system_admin' || normalized === 'admin' || normalized === 'системный администратор') {
    return 'Системный администратор';
  }
  if (
    normalized === 'knowledge_admin' ||
    normalized === 'knowledge admin' ||
    normalized === 'администратор знаний' ||
    normalized === 'администратор нси'
  ) {
    return 'Администратор знаний';
  }
  return 'Пользователь';
}

function mapGatewayRolesResponse(payload: any): AdminUser['role'][] {
  const roles = Array.isArray(payload) ? payload : payload.roles ?? payload.items ?? [];
  const mapped = roles.map((role: any) => mapGatewayRole(role?.name ?? role?.role ?? role?.title ?? role?.role_id ?? role));

  return Array.from(new Set(mapped));
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

function mapGatewayDraftRecord(payload: any) {
  const previewMetadata = normalizePreviewMetadata(payload.preview_metadata ?? payload.preview ?? null);

  return {
    ...payload,
    draft_id: payload.draft_id ?? payload.id,
    task_id: payload.task_id ?? payload.taskId,
    version_id: payload.version_id ?? payload.versionId,
    file_key: payload.file_key ?? payload.fileKey,
    document_key: payload.document_key ?? payload.documentKey ?? deriveDocumentKey(payload.file_hash_sha256 ?? payload.fileHashSha256),
    file_hash_sha256: payload.file_hash_sha256 ?? payload.fileHashSha256,
    title_hash_sha256: payload.title_hash_sha256 ?? payload.titleHashSha256,
    status: normalizeDraftStatus(payload.status),
    confidence: payload.confidence ?? null,
    preview_metadata: previewMetadata,
    promoted_document_id: payload.promoted_document_id ?? payload.approved_document_id ?? payload.document_id ?? null,
    approved_document_id: payload.approved_document_id ?? payload.promoted_document_id ?? payload.document_id ?? null,
    error_code: payload.error_code ?? null,
    error_message: payload.error_message ?? null,
    raw_data: payload.raw_data ?? null,
    created_at: payload.created_at ?? payload.createdAt ?? '',
    updated_at: payload.updated_at ?? payload.updatedAt ?? '',
  };
}

function backendUnavailableMessage(): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: 'Серверная часть недоступна. Повторите запрос позже или переключитесь в демонстрационный режим.',
    status: 'failed',
    timestamp: toUiTimestamp(),
  };
}

function notFoundMessage(query: string): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: `В базе знаний не найдено подтвержденных фрагментов по запросу «${query}». Попробуйте уточнить формулировку, проект, раздел или документ.`,
    status: 'answered',
    limitation: 'По запросу не найдено подтвержденных источников в базе знаний.',
    timestamp: toUiTimestamp(),
  };
}

function outOfScopeMessage(query: string): ChatMessage {
  return {
    id: Math.random().toString(36).slice(2),
    role: 'assistant',
    content: `Запрос «${query}» не относится к инженерным документам, НСИ или проектной проверке. Задайте вопрос в рамках базы знаний проекта.`,
    status: 'answered',
    limitation: 'Запрос вне области инженерной базы знаний.',
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
      status: 'answered',
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
    const profile = mapGatewayProfileToAdminUser(response.data);
    const store = useUIStore.getState();

    store.upsertAdminUser(profile);
    store.setCurrentUserId(profile.id);
    store.setCurrentRole(USER_ROLE_BY_LABEL[profile.role] ?? 'user');

    return profile;
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
  createSession: async (title: string, projectId?: string) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.post('/chat/sessions', {
        title,
        project_id: normalizeGatewayProjectId(projectId),
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

      const messageId = response.data?.message_id ?? response.data?.answer_id;
      if (!messageId) {
        useUIStore.getState().setApiStatus('offline');
        return chatLongpollIncompleteMessage();
      }

      let finalResponse;
      try {
        finalResponse = await waitForGatewayChatMessage(activeSessionId, String(messageId), 15, 4);
      } catch {
        useUIStore.getState().setApiStatus('offline');
        return chatLongpollIncompleteMessage(String(messageId));
      }

      useUIStore.getState().setApiStatus('online');
      return mapGatewayChatResponse(finalResponse ?? { ...response.data, session_id: activeSessionId }, query);
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

export const projectsApi = {
  list: async (): Promise<GatewayChatProject[]> => {
    const [projectsResult, sessionsResult] = await Promise.allSettled([
      gatewayRequest<any>(() => apiClient.get('/chat/projects', { params: { page_size: 100 } })),
      gatewayRequest<any>(() => apiClient.get('/chat/sessions', { params: { page_size: 100 } })),
    ]);

    const projects =
      projectsResult.status === 'fulfilled' ? mapGatewayProjectsResponse(projectsResult.value.data) : [];
    const sessionProjects =
      sessionsResult.status === 'fulfilled' ? mapGatewaySessionsToProjects(sessionsResult.value.data) : [];

    if (!projects.length && !sessionProjects.length && projectsResult.status === 'rejected') {
      throw projectsResult.reason;
    }

    return mergeGatewayProjectsWithSessions(projects, sessionProjects);
  },
  create: async (name: string) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.post('/chat/projects', {
        code: createGatewayProjectCode(name),
        name,
        status: 'active',
      }),
    );

    return mapGatewayProject(response.data);
  },
  update: async (projectId: string, patch: { name?: string; status?: string }) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.put(`/chat/projects/${projectId}`, {
        name: patch.name,
        status: patch.status,
      }),
    );

    return mapGatewayProject(response.data);
  },
  delete: async (projectId: string) => {
    await gatewayRequest<any>(() => apiClient.delete(`/chat/projects/${projectId}`));
    return { ok: true };
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

export const draftsApi = {
  create: async (file: File, input: DraftCreateInput = {}) => {
    const form = new FormData();
    form.append('file', file);
    form.append('source_type', input.sourceType?.trim() || 'OTHER');
    appendFormValue(form, 'title', input.title?.trim());
    appendFormValue(form, 'doc_code', input.docCode?.trim());
    appendFormValue(form, 'mks_oks_code', input.mksOksCode?.trim());
    appendFormValue(form, 'okstu_code', input.okstuCode?.trim());
    appendFormValue(form, 'era', input.era?.trim());
    appendFormValue(form, 'jurisdiction', input.jurisdiction?.trim());
    appendFormValue(form, 'issuing_body', input.issuingBody?.trim());
    if (input.metadata !== undefined && input.metadata !== null && input.metadata !== '') {
      form.append('metadata', typeof input.metadata === 'string' ? input.metadata : JSON.stringify(input.metadata));
    }

    const response = await gatewayRequest<any>(() =>
      apiClient.post('/drafts', form, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(input.idempotencyKey ? { 'Idempotency-Key': input.idempotencyKey } : {}),
        },
      }),
    );

    return mapGatewayDraftRecord(response.data);
  },
  list: async (params: { documentKey?: string; status?: string; page?: number; pageSize?: number } = {}) => {
    if (!params.documentKey) return [];

    const response = await gatewayRequest<any>(() =>
      apiClient.get('/drafts', {
        params: {
          document_key: params.documentKey,
          status: params.status,
          page: params.page ?? 1,
          page_size: params.pageSize ?? 50,
        },
      }),
    );

    const items = Array.isArray(response.data?.items) ? response.data.items : [];
    return items.map((item: any) => mapGatewayDraftRecord(item));
  },
  get: async (draftId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/drafts/${draftId}`));
    return mapGatewayDraftRecord(response.data);
  },
  getPreview: async (draftId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/drafts/${draftId}/preview`));
    return mapGatewayDraftRecord(response.data);
  },
  startPreview: async (draftId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.post(`/drafts/${draftId}/preview`));
    return response.data;
  },
  waitPreview: async (draftId: string, longpoll = 15) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.get(`/drafts/${draftId}/preview/status`, {
        params: { longpoll },
      }),
    );
    return response.data;
  },
  decide: async (draftId: string, action: 'approve' | 'reject', comment?: string) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.patch(`/drafts/${draftId}/decide`, {
        action,
        comment,
      }),
    );
    return response.data;
  },
  delete: async (draftId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.delete(`/drafts/${draftId}`));
    return response.data;
  },
};

export const documentsApi = {
  list: async () => {
    if (isDemoMode()) return MOCK_DOCUMENTS;

    const response = await gatewayRequest<any>(() => apiClient.get('/documents'));
    return mapGatewayDocumentsResponse(response.data);
  },
  get: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}`));
    return mapGatewayDocumentDetailResponse(response.data);
  },
  status: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/status`));
    return response.data as GatewayDocumentStatus;
  },
  history: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/history`));
    return Array.isArray(response.data?.history) ? response.data.history : [];
  },
  errors: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/errors`));
    const payload = response.data as GatewayDocumentErrors;
    return Array.isArray(payload?.errors) ? payload.errors : [];
  },
  parameters: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/parameters`));
    return response.data as GatewayDocumentParameters;
  },
  pages: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/pages`));
    const payload = response.data as GatewayDocumentPages;
    return Array.isArray(payload?.pages) ? payload.pages : [];
  },
  pagePreview: async (documentId: string, pageNumber: number) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/pages/${pageNumber}/preview`));
    return response.data;
  },
  file: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/file`));
    return response.data;
  },
  queue: async () => {
    if (isDemoMode()) return [];

    const response = await gatewayRequest<any>(() => apiClient.get('/documents/queue'));
    return mapGatewayQueueResponse(response.data);
  },
  knowledgeSections: async () => {
    if (isDemoMode()) return MOCK_KNOWLEDGE_SECTIONS;

    const response = await gatewayRequest<any>(() =>
      apiClient.get('/classifiers/tree', {
        params: {
          classifier_system: 'MKS',
          max_depth: 10,
        },
      }),
    );
    return mapGatewayKnowledgeSections(response.data);
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

export const registryApi = {
  documents: async () => {
    if (isDemoMode()) return MOCK_DOCUMENTS;

    try {
      const response = await gatewayRequest<any>(() =>
        apiClient.get('/registry/documents', {
          params: {
            page_size: 200,
            sort_by: 'updated_at',
            order: 'desc',
          },
        }),
      );
      useUIStore.getState().setApiStatus('online');
      return mapGatewayDocumentsResponse(response.data);
    } catch {
      return documentsApi.list();
    }
  },
  document: async (documentId: string) => {
    try {
      const response = await gatewayRequest<any>(() => apiClient.get(`/registry/documents/${documentId}`));
      return mapGatewayDocumentDetailResponse(response.data);
    } catch {
      return documentsApi.get(documentId);
    }
  },
  documentSections: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/registry/documents/${documentId}/sections`));
    return response.data;
  },
  knowledgeSections: async () => {
    if (isDemoMode()) return MOCK_KNOWLEDGE_SECTIONS;

    try {
      const response = await gatewayRequest<any>(() =>
        apiClient.get('/classifiers/tree', {
          params: {
            classifier_system: 'MKS',
            max_depth: 10,
          },
        }),
      );
      useUIStore.getState().setApiStatus('online');
      return mapGatewayKnowledgeSections(response.data);
    } catch {
      const response = await gatewayRequest<any>(() =>
        apiClient.get('/registry/classifiers/tree', {
          params: {
            classifier_system: 'MKS',
            max_depth: 10,
          },
        }),
      );
      useUIStore.getState().setApiStatus('online');
      return mapGatewayKnowledgeSections(response.data);
    }
  },
  stats: async () => {
    const response = await gatewayRequest<any>(() => apiClient.get('/common/stats'));
    return response.data?.data ?? response.data;
  },
  enums: async () => {
    const response = await gatewayRequest<any>(() => apiClient.get('/common/enums'));
    return response.data?.data ?? response.data;
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
        return [];
      }
    }
  },
  export: async (format = 'csv') => {
    const response = await gatewayRequest<any>(() =>
      apiClient.get('/chat/history/export', {
        params: { format },
      }),
    );
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
      return EMPTY_SYSTEM_METRICS;
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
        control: EMPTY_SYSTEM_METRICS,
        answers: EMPTY_ENGINEER_RATINGS,
        logs: [],
      };
    }
  },
};

export const adminApi = {
  roles: async (): Promise<AdminUser['role'][]> => {
    if (isDemoMode()) {
      return Array.from(new Set(MOCK_ADMIN_USERS.map((user) => user.role)));
    }

    const response = await gatewayRequest<any>(() => apiClient.get('/admin/roles'));
    return mapGatewayRolesResponse(response.data);
  },
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
      throw new Error('Не удалось загрузить пользователей из Gateway');
    }
  },
  audit: async () => {
    if (isDemoMode()) return [];

    try {
      const response = await gatewayRequest<any>(() => apiClient.get('/admin/audit'));
      return mapGatewayAuditResponse(response.data);
    } catch {
      throw new Error('Не удалось загрузить журнал аудита из Gateway');
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

    if (previewResponse.status !== 'fulfilled' && textResponse.status !== 'fulfilled') {
      throw new Error('Gateway preview is unavailable');
    }

    const previewData = previewResponse.status === 'fulfilled' ? previewResponse.value.data : {};
    const textData = textResponse.status === 'fulfilled' ? textResponse.value.data : {};

    return {
      ...citation,
      text: textData?.full_text ?? textData?.text ?? previewData?.text ?? previewData?.content ?? citation.text,
      pagePreviewUrl: previewData?.preview_url ?? previewData?.image_url ?? citation.pagePreviewUrl,
      documentUrl: previewData?.file_url ?? previewData?.document_url ?? citation.documentUrl,
      contentType: previewData?.content_type ?? textData?.content_type ?? citation.contentType,
    };
  },
};

export const feedbackApi = {
  send: async (payload: { useful: boolean; comment: string; sessionId?: string; messageId?: string }) => {
    if (isDemoMode()) return { ok: true, demo: true };

    const sessionId = payload.sessionId ?? useUIStore.getState().currentGatewaySessionId;
    const messageId = payload.messageId;

    if (!sessionId || !messageId) {
      throw new Error('Не удалось отправить отзыв: нет связки сессии и сообщения Gateway.');
    }

    try {
      await gatewayRequest<any>(() =>
        apiClient.post('/chat/feedback', {
          session_id: sessionId,
          message_id: messageId,
          rating: payload.useful ? 5 : 1,
          useful: payload.useful,
          comment: payload.comment,
        }),
      );
      useUIStore.getState().setApiStatus('online');
      return { ok: true };
    } catch {
      useUIStore.getState().setApiStatus('offline');
      throw new Error('Не удалось отправить отзыв в Gateway');
    }
  },
};

export const initialChatMessages = MOCK_CHATS;
