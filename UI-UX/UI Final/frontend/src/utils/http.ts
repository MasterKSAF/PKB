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

const DEFAULT_GATEWAY_URL = 'http://127.0.0.1:8080/api/v1';
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_GATEWAY_URL;
const GATEWAY_AUTO_LOGIN = import.meta.env.VITE_GATEWAY_AUTO_LOGIN === 'true';
const GATEWAY_USERNAME = import.meta.env.VITE_GATEWAY_USERNAME ?? 'admin@example.com';
const GATEWAY_PASSWORD = import.meta.env.VITE_GATEWAY_PASSWORD ?? 'Admin1234!';
const ACCESS_TOKEN_KEY = 'pkb_gateway_access_token_v2';
const REFRESH_TOKEN_KEY = 'pkb_gateway_refresh_token_v2';
const LEGACY_ACCESS_TOKEN_KEY = 'pkb_gateway_access_token';
const LEGACY_REFRESH_TOKEN_KEY = 'pkb_gateway_refresh_token';
const SKIP_AUTH_HEADER = 'X-PKB-Skip-Auth';
let refreshGatewayTokenPromise: Promise<string | null> | null = null;

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

export const pipelineClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,
});

const FILE_UPLOAD_TIMEOUT_MS = 120_000;

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
  documentKey?: string;
  sourceType?: string;
  title?: string;
  docCode?: string;
  mksOksCode?: string;
  okstuCode?: string;
  era?: string;
  jurisdiction?: string;
  issuingBody?: string;
  validFrom?: string | null;
  validUntil?: string | null;
  metadata?: Record<string, unknown> | string;
  idempotencyKey?: string;
};

type DraftPreviewMetadata = {
  doc_code?: string;
  title?: string;
  document_type?: string;
  year?: string | number | null;
  revision?: string | number | null;
  source_type?: string | null;
  mks_oks_code?: string | null;
  okstu_code?: string | null;
  era?: string | null;
  jurisdiction?: string | null;
  issuing_body?: string | null;
  validity_status?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  title_key?: string | null;
  title_hash_sha256?: string | null;
};

export type DraftMetadataOverrides = {
  title?: string | null;
  source_type?: string | null;
  doc_code?: string | null;
  year?: string | number | null;
  mks_oks_code?: string | null;
  okstu_code?: string | null;
  era?: string | null;
  jurisdiction?: string | null;
  issuing_body?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
};

type DraftDecisionAction = 'approve' | 'reject' | 'confirm';

type DraftDecisionInput = {
  action: DraftDecisionAction;
  comment?: string;
  metadataOverrides?: DraftMetadataOverrides;
};

type GatewayDocumentDetail = {
  document_id?: string;
  id?: string;
  title?: string;
  doc_code?: string;
  source_type?: string;
  title_key?: string;
  title_hash_sha256?: string;
  status?: string;
  era?: string;
  validity_status?: string;
  valid_from?: string;
  valid_until?: string | null;
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

export interface RegistryListResponse<T> {
  data: T[];
  meta?: Record<string, unknown>;
}

export interface RegistryClassifierNode {
  classifier_system: string;
  code: string;
  parent_code?: string | null;
  full_name: string;
  status: string;
  effective_date?: string | null;
  replaced_by?: string | null;
  created_at?: string | null;
  documents_count?: number;
  children?: RegistryClassifierNode[];
}

export interface RegistryClassifierPending {
  id: string;
  system: string;
  code: string;
  found_in_document_id?: string | null;
  found_in_document_title?: string;
  status: string;
  suggested_parent_code?: string | null;
  suggested_parent_name?: string;
  admin_comment?: string | null;
  created_at?: string | null;
}

export interface RegistryTerminologyEntry {
  id: string;
  raw_term: string;
  standard_term: string;
  normalized_value: string;
  term_type: string;
  is_case_sensitive?: boolean;
  definition?: string | null;
  synonyms?: string[];
  related_docs?: string[];
  scope?: string[];
  is_blocked?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

function appendFormValue(form: FormData, key: string, value: unknown) {
  if (value === undefined || value === null || value === '') return;
  form.append(key, typeof value === 'string' ? value : String(value));
}

async function calculateFileSha256(file: File) {
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
    return Array.from(new Uint8Array(digest))
      .map((byte) => byte.toString(16).padStart(2, '0'))
      .join('');
  }
  // crypto.subtle недоступен в небезопасном контексте (HTTP).
  // Сервер сам вычисляет хеш файла, нам хеш нужен только для documentKey.
  // Генерируем случайную строку как fallback.
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return Array.from(bytes)
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}

function toGatewayStringId(value: unknown, fallback = '') {
  return value === undefined || value === null || value === '' ? fallback : String(value);
}

function deriveDocumentKey(fileHashSha256?: string) {
  if (!fileHashSha256) return '';
  return `sha256:${fileHashSha256.slice(0, 16)}`;
}

function normalizeDraftStatus(status?: string) {
  const normalized = String(status ?? '').toLowerCase();
  if (['preview_ready', 'ready_for_approve', 'previewing', 'uploaded', 'new', 'review_required', 'validation'].includes(normalized)) {
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
    source_type: payload.source_type ?? null,
    mks_oks_code: payload.mks_oks_code ?? null,
    okstu_code: payload.okstu_code ?? null,
    era: payload.era ?? null,
    jurisdiction: payload.jurisdiction ?? null,
    issuing_body: payload.issuing_body ?? null,
    validity_status: payload.validity_status ?? null,
    valid_from: payload.valid_from ?? null,
    valid_until: payload.valid_until ?? null,
    title_key: payload.title_key ?? null,
    title_hash_sha256: payload.title_hash_sha256 ?? null,
  };
}

function isDemoMode() {
  return useUIStore.getState().workMode === 'demo';
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
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
  store.setCurrentPermissions(profile.permissions ?? {});

  return profile;
}

export function clearGatewayTokens() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function clearGatewaySession() {
  clearGatewayTokens();
  const store = useUIStore.getState();
  store.logout();
  store.setApiStatus(store.workMode === 'demo' ? 'demo' : 'offline');
}

apiClient.interceptors.request.use((config) => {
  const headers = config.headers as any;
  if (headers?.[SKIP_AUTH_HEADER]) {
    delete headers[SKIP_AUTH_HEADER];
    delete headers.Authorization;
    return config;
  }

  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

async function refreshGatewayAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  const response = await apiClient.post(
    '/auth/refresh',
    { refresh_token: refreshToken },
    { headers: { [SKIP_AUTH_HEADER]: 'true' } },
  );
  setGatewayTokens(response.data);
  return response.data?.access_token ?? null;
}

async function refreshGatewayTokenOnce() {
  if (!refreshGatewayTokenPromise) {
    refreshGatewayTokenPromise = refreshGatewayAccessToken().finally(() => {
      refreshGatewayTokenPromise = null;
    });
  }

  return refreshGatewayTokenPromise;
}

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

  const currentUserId = String(useUIStore.getState().currentUserId ?? '');
  if (!currentUserId || currentUserId.startsWith('u')) {
    await syncGatewayCurrentUser(token ?? undefined);
  }
}

async function gatewayRequest<T>(request: () => Promise<{ data: T }>) {
  await ensureGatewayToken();

  try {
    return await request();
  } catch (error: any) {
    if (error?.response?.status === 401) {
      let refreshedToken: string | null = null;

      try {
        refreshedToken = await refreshGatewayTokenOnce();
      } catch {
        refreshedToken = null;
      }

      if (refreshedToken) {
        try {
          return await request();
        } catch (retryError: any) {
          if (retryError?.response?.status === 401) {
            clearGatewaySession();
          }
          throw retryError;
        }
      }

      clearGatewaySession();
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

function mapGatewayStatus(
  status?: string,
  scenario?: string,
): ChatMessage['status'] {
  const normalized = String(status ?? '').toLowerCase();

  if (normalized === 'pending') return 'pending';
  if (normalized === 'enriching') return 'enriching';
  if (normalized === 'searching') return 'searching';
  if (normalized === 'generating') return 'generating';
  if (normalized === 'enriching_citations') return 'enriching_citations';
  if (normalized === 'completed' || normalized === 'answered') return 'answered';
  if (scenario === 'failed' || normalized === 'failed' || normalized === 'error') return 'failed';

  return 'failed';
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
  const rawCitationIndex = source.index ?? source.citation_index;
  const citationIndex = rawCitationIndex === undefined || rawCitationIndex === null ? undefined : Number(rawCitationIndex);

  return {
    id: toGatewayStringId(
      source.source_id ?? source.id ?? `${source.document_id ?? 'doc'}-${source.section_id ?? 'section'}-${index}`,
      `gateway-source-${index}`,
    ),
    index: Number.isFinite(citationIndex) ? citationIndex : undefined,
    documentId: toGatewayStringId(source.document_id ?? source.doc_id),
    sectionId: toGatewayStringId(source.section_id ?? source.chunk_id),
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

  const answerItemsContent = answerItems
    .map((item: any, index: number) => `${item.number ?? index + 1}. ${item.text ?? ''}`.trim())
    .filter(Boolean)
    .join('\n');
  const content = answerItemsContent || messagePayload.content || messagePayload.answer || messagePayload.message;

  if (!String(content ?? '').trim()) {
    throw new Error(
      `Gateway response does not contain final answer content for query "${query}". message_id=${
        messagePayload.message_id ?? 'missing'
      }, status=${messagePayload.status ?? 'missing'}`,
    );
  }
  const status = mapGatewayStatus(messagePayload.status, messagePayload.scenario);

  return {
    id: messagePayload.message_id ?? messagePayload.answer_id ?? Math.random().toString(36).slice(2),
    role: 'assistant',
    content,
    status,
    citations: citations.length ? citations : undefined,
    timestamp: toUiTimestamp(messagePayload.timestamp),
  };
}

function isFinalChatStatus(status?: string) {
  const normalized = String(status ?? '').toLowerCase();
  return normalized === 'answered' || normalized === 'completed' || normalized === 'failed';
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
  throw new Error(`Gateway chat longpoll did not reach final status. session_id=${sessionId}, message_id=${messageId}, status=${lastStatus}`);
}

function mapGatewaySessionMessages(session: any): ChatMessage[] {
  const messages = Array.isArray(session.messages) ? session.messages : [];

  return messages.map((message: any, index: number) => ({
    id: toGatewayStringId(message.message_id, `${session.session_id ?? 'session'}-${index}`),
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
  const items = Array.isArray(payload) ? payload : payload.results ?? payload.items ?? payload.data ?? [];

  return items.map((item: any, index: number) => ({
    id: toGatewayStringId(item.document_id ?? item.section_id, `gateway-search-${index}`),
    documentId: toGatewayStringId(item.document_id ?? item.doc_id),
    name: item.document_title ?? item.title ?? item.document_id ?? 'Документ базы знаний',
    type: (item.document_type ?? item.source_type ?? item.type ?? 'PDF').toUpperCase(),
    version: item.version ?? 'Актуальная версия',
    source: item.document_type ?? item.source ?? 'База знаний',
    relevance: typeof item.score === 'number' ? item.score : 0,
    fragment: item.content ?? item.excerpt ?? item.text ?? '',
    page: Number(item.page ?? 1),
    section: item.clause ?? item.section ?? item.section_id ?? 'Фрагмент',
    sectionId: item.section_id ?? item.group ?? item.classifier_code ?? item.mks_oks_code ?? item.okstu_code ?? '',
    group: item.group ?? item.classification_group ?? item.classifier_group ?? '',
    classifierCode: item.classifier_code ?? item.section_code ?? item.group ?? item.section_id ?? '',
    classifierSystem: item.classifier_system ?? (item.mks_oks_code ? 'MKS' : item.okstu_code ? 'OKSTU' : ''),
    mksOksCode: item.mks_oks_code ?? item.mks_oks ?? item.oks_code ?? '',
    okstuCode: item.okstu_code ?? '',
    pagePreviewUrl: item.page_preview_url ?? item.preview_url,
    documentUrl: item.document_url ?? item.file_url,
  }));
}

function mapGatewayDocumentsResponse(payload: any): Document[] {
  const documents = Array.isArray(payload) ? payload : payload.documents ?? payload.items ?? payload.data ?? [];

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
      id: toGatewayStringId(doc.document_id ?? doc.id, `gateway-document-${index}`),
      name: doc.title ?? doc.filename ?? doc.name ?? 'Документ базы знаний',
      type: (doc.document_type ?? doc.source_type ?? doc.type ?? 'PDF').toUpperCase(),
      version: `v${doc.latest_version ?? doc.version ?? 1}`,
      source: doc.source ?? doc.uploaded_by ?? 'База знаний',
      ocrStatus: mapGatewayDocumentOcrStatus(normalizedStatus),
      indexStatus: mapGatewayDocumentIndexStatus(normalizedStatus),
      updatedAt: doc.updated_at ?? doc.created_at ?? '',
      sectionId: toGatewayStringId(doc.section_id ?? group),
      group,
      docCode: doc.doc_code ?? '',
      status: doc.status ?? '',
      validityStatus: doc.validity_status ?? '',
      sourceType: doc.source_type ?? doc.document_type ?? doc.type ?? '',
      documentKey: doc.document_key ?? doc.file_hash_sha256 ?? '',
      titleKey: doc.title_key ?? '',
      titleHashSha256: doc.title_hash_sha256 ?? '',
      validFrom: doc.valid_from ?? '',
      validUntil: doc.valid_until ?? '',
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
    document_id: toGatewayStringId(data.document_id ?? data.id),
    id: toGatewayStringId(data.document_id ?? data.id),
    title: data.title ?? '',
    doc_code: data.doc_code ?? '',
    source_type: data.source_type ?? '',
    title_key: data.title_key ?? '',
    title_hash_sha256: data.title_hash_sha256 ?? '',
    status: data.status ?? '',
    era: data.era ?? '',
    validity_status: data.validity_status ?? '',
    valid_from: data.valid_from ?? '',
    valid_until: data.valid_until ?? null,
    jurisdiction: data.jurisdiction ?? '',
    issuing_body: data.issuing_body ?? '',
    mks_oks_code: data.mks_oks_code ?? null,
    okstu_code: data.okstu_code ?? null,
    classification_status: data.classification_status ?? {},
    successor_doc_id: data.successor_doc_id === undefined || data.successor_doc_id === null ? null : String(data.successor_doc_id),
    predecessor_doc_id: data.predecessor_doc_id === undefined || data.predecessor_doc_id === null ? null : String(data.predecessor_doc_id),
    chunk_container_id: data.chunk_container_id === undefined || data.chunk_container_id === null ? null : String(data.chunk_container_id),
    metadata: data.metadata ?? {},
    latest_version: data.latest_version ?? null,
    total_versions: Number(data.total_versions ?? 0),
    user_id: toGatewayStringId(data.user_id),
    uploaded_by: data.uploaded_by ?? '',
    created_by: data.created_by ?? '',
    updated_by: data.updated_by ?? '',
    created_at: data.created_at ?? '',
    updated_at: data.updated_at ?? '',
  };
}

function mapGatewaySessionsResponse(payload: any): QueryHistoryItem[] {
  const sessions = Array.isArray(payload) ? payload : payload.sessions ?? payload.items ?? [];

  return sessions.map((session: any, index: number) => {
    const messages = mapGatewaySessionMessages(session);
    const userMessage = messages.find((message) => message.role === 'user');
    const assistantMessage = [...messages].reverse().find((message) => message.role === 'assistant');
    const sourceCount = messages.reduce((sum, message) => sum + (message.citations?.length ?? 0), 0);

    return {
      id: toGatewayStringId(session.session_id ?? session.id, `gateway-session-${index}`),
      user: session.user_name ?? session.user_id ?? 'Пользователь системы',
      project: session.project ?? session.project_name ?? 'Рабочие диалоги',
      topic: session.topic ?? session.title ?? 'Рабочий диалог',
      session: toGatewayStringId(session.title ?? session.session_id, `Сессия ${index + 1}`),
      query: userMessage?.content ?? session.last_question ?? session.last_message_preview ?? '',
      answer: assistantMessage?.content ?? session.last_answer ?? session.last_message_preview ?? '',
      sources: Number(session.source_count ?? sourceCount),
      status: assistantMessage?.status ?? mapGatewayStatus(session.status, session.scenario),
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
    const projectId = toGatewayStringId(session.project_id ?? projectName, 'gateway-dialogs');

    if (!groups.has(projectId)) {
      groups.set(projectId, { id: projectId, name: projectName, chats: [] });
    }

    groups.get(projectId)?.chats.push({
      id: toGatewayStringId(session.session_id ?? session.id, `gateway-session-${index}`),
      title: toGatewayStringId(session.title ?? session.session_id, `Сессия ${index + 1}`),
      preview: session.last_message_preview ?? session.last_question ?? '',
      updatedAt: session.updated_at ?? session.created_at ?? '',
    });
  });

  return [...groups.values()];
}

function mapGatewayProject(project: any, index = 0): GatewayChatProject {
  const projectId = String(project.project_id ?? project.id ?? project.code ?? `gateway-project-${index}`);
  const chats = Array.isArray(project.chats)
    ? project.chats
    : Array.isArray(project.sessions)
      ? project.sessions
      : [];

  return {
    id: projectId,
    name: project.name ?? project.title ?? project.code ?? `Проект ${index + 1}`,
    code: project.code,
    description: project.description,
    status: project.status,
    chats: chats.map((chat: any, chatIndex: number) => ({
      id: toGatewayStringId(chat.session_id ?? chat.id, `${projectId}-session-${chatIndex}`),
      title: toGatewayStringId(chat.title ?? chat.name ?? chat.session_id, `Сессия ${chatIndex + 1}`),
      preview: chat.last_message_preview ?? chat.last_question ?? chat.preview,
      updatedAt: chat.updated_at ?? chat.created_at,
    })),
  };
}

function mapGatewayProjectsResponse(payload: any): GatewayChatProject[] {
  const items = Array.isArray(payload) ? payload : payload.items ?? payload.projects ?? payload.data ?? [];
  return items.map((project: any, index: number) => mapGatewayProject(project, index));
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
          : 'Распознавание текста';

    return {
      id: toGatewayStringId(item.document_id ?? item.draft_id ?? item.id, `gateway-queue-${index}`),
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

function mapGatewayPermissions(permissions: any): Record<string, boolean> {
  if (!permissions) return {};

  if (Array.isArray(permissions)) {
    return permissions.reduce<Record<string, boolean>>((acc, permission) => {
      if (typeof permission === 'string' && permission.trim()) {
        acc[permission.trim()] = true;
      }
      return acc;
    }, {});
  }

  if (typeof permissions === 'object') {
    return Object.entries(permissions).reduce<Record<string, boolean>>((acc, [key, value]) => {
      acc[key] = Boolean(value);
      return acc;
    }, {});
  }

  return {};
}

function mapGatewayUsersResponse(payload: any): AdminUser[] {
  const users = Array.isArray(payload) ? payload : payload.users ?? payload.items ?? [];

  return users.map((user: any, index: number) => {
    const role = Array.isArray(user.roles) ? user.roles[0] : user.role;

    return {
      id: toGatewayStringId(user.user_id ?? user.id, `gateway-user-${index}`),
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
      availableTabs: Array.isArray(user.available_tabs) ? user.available_tabs : undefined,
      permissions: mapGatewayPermissions(user.permissions),
    };
  });
}

function mapGatewayProfileToAdminUser(profile: any): AdminUser {
  const role = profile.role ?? (Array.isArray(profile.roles) ? profile.roles[0] : undefined);

  return {
    id: toGatewayStringId(profile.user_id ?? profile.id, 'gateway-current-user'),
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
    availableTabs: Array.isArray(profile.available_tabs) ? profile.available_tabs : undefined,
    permissions: mapGatewayPermissions(profile.permissions),
  };
}

function mapGatewayAuditResponse(payload: any): ProcessingLogItem[] {
  const events = Array.isArray(payload) ? payload : payload.events ?? payload.items ?? payload.audit ?? [];

  return events.slice(0, 20).map((event: any, index: number) => {
    const action = String(event?.action ?? 'event');
    const resource = event?.resource_id ?? event?.resource_type ?? 'Система';

    return {
      id: toGatewayStringId(event?.event_id ?? event?.id, `gateway-audit-${index}`),
      time: toUiTimestamp(event?.timestamp ?? event?.created_at),
      document: String(resource),
      stage: mapGatewayTaskStage(event?.resource_type, 'audit'),
      event: formatAuditEvent(action, event?.ip_address),
      retryStatus: action.includes('error') || action.includes('delete') ? 'Запланирована' : 'Не требуется',
      visibility: action.includes('admin') || action.includes('user') || action.includes('role') ? 'Администратор' : 'Инженер',
    };
  });
}

function normalizeGatewayCode(value?: unknown) {
  return String(value ?? '').trim().toLowerCase();
}

function mapGatewayTaskStage(stage?: unknown, serviceName?: unknown): ProcessingLogItem['stage'] {
  const value = `${normalizeGatewayCode(stage)} ${normalizeGatewayCode(serviceName)}`;
  if (value.includes('ocr') || value.includes('recogn')) return 'Распознавание текста';
  if (value.includes('parse') || value.includes('parser') || value.includes('table') || value.includes('extract')) return 'Разбор документа';
  if (value.includes('index') || value.includes('rag') || value.includes('embedding') || value.includes('vector')) return 'Индексация';
  if (value.includes('upload') || value.includes('import') || value.includes('draft') || value.includes('create')) return 'Загрузка';
  if (value.includes('classif') || value.includes('registry') || value.includes('metadata')) return 'Сверка метаданных';
  if (value.includes('answer') || value.includes('generat') || value.includes('llm') || value.includes('chat')) return 'Генерация ответа';
  if (value.includes('audit') || value.includes('auth') || value.includes('admin') || value.includes('role') || value.includes('user')) {
    return 'Аудит системы';
  }
  return 'Обработка';
}

function mapGatewayTaskStatusLabel(status?: unknown) {
  const value = normalizeGatewayCode(status);
  if (!value || value === 'unknown') return 'Неизвестно';
  if (['queued', 'queue', 'pending', 'waiting'].includes(value)) return 'В очереди';
  if (['uploaded', 'created', 'new'].includes(value)) return 'Создано';
  if (['running', 'processing', 'in_progress', 'started', 'active'].includes(value)) return 'В обработке';
  if (['retry', 'retrying'].includes(value)) return 'Повторная попытка';
  if (['completed', 'done', 'success', 'succeeded', 'answered', 'approved', 'indexed'].includes(value)) return 'Завершено';
  if (['failed', 'error', 'failure'].includes(value)) return 'Ошибка';
  if (['cancelled', 'canceled', 'discarded', 'rejected'].includes(value)) return 'Отменено';
  return 'Неизвестно';
}

function mapGatewayServiceLabel(serviceName?: unknown) {
  const value = normalizeGatewayCode(serviceName);
  if (!value || value === 'pipeline') return 'Конвейер обработки';
  if (value.includes('ocr')) return 'Распознавание текста';
  if (value.includes('parse') || value.includes('parser')) return 'Разбор документа';
  if (value.includes('index') || value.includes('rag')) return 'Индексация';
  if (value.includes('registry')) return 'Реестр';
  if (value.includes('gateway') || value.includes('query')) return 'Контур запросов';
  if (value.includes('audit')) return 'Аудит';
  return 'Сервис обработки';
}

function formatAuditEvent(action?: unknown, ipAddress?: unknown) {
  const value = normalizeGatewayCode(action);
  const label =
    value.includes('login') || value.includes('auth') || value.includes('token')
      ? 'Авторизация пользователя'
      : value.includes('logout')
        ? 'Выход пользователя'
        : value.includes('role') || value.includes('permission') || value.includes('access')
          ? 'Изменение прав доступа'
          : value.includes('user') || value.includes('admin')
            ? 'Административное действие'
            : value.includes('delete') || value.includes('remove') || value.includes('archive')
              ? 'Удаление записи'
              : value.includes('create') || value.includes('add') || value.includes('post') || value.includes('upload') || value.includes('import')
                ? 'Создание записи'
                : value.includes('update') || value.includes('edit') || value.includes('change') || value.includes('patch') || value.includes('put')
                  ? 'Изменение записи'
                  : value.includes('error') || value.includes('fail')
                    ? 'Ошибка операции'
                    : 'Системное событие';
  const ip = String(ipAddress ?? '').trim();
  return ip ? `${label}. IP: ${ip}` : label;
}

function formatTaskEvent(taskId: string, stage?: unknown, status?: unknown, progress?: unknown) {
  return `Задача ${taskId}: ${mapGatewayTaskStage(stage)}; статус: ${mapGatewayTaskStatusLabel(status)}; прогресс: ${Number(progress ?? 0)}%.`;
}

function formatTaskStepEvent(step: any, index: number) {
  return `${mapGatewayServiceLabel(step?.service_name)}: ${mapGatewayTaskStage(step?.step_name, step?.service_name)}; статус: ${mapGatewayTaskStatusLabel(
    step?.status,
  )}; шаг ${index + 1}.`;
}

function mapGatewayTaskRetryStatus(status?: string): ProcessingLogItem['retryStatus'] {
  const value = String(status ?? '').toLowerCase();
  if (value === 'failed' || value === 'error') return 'Ошибка';
  if (value === 'retry' || value === 'retrying') return 'Запланирована';
  if (value === 'completed' || value === 'done' || value === 'success') return 'Выполнена';
  return 'Не требуется';
}

function mapGatewayTaskStatusResponse(payload: any): ProcessingLogItem[] {
  const data = payload?.data ?? payload ?? {};
  const taskId = toGatewayStringId(data.task_id ?? data.id, 'task');
  const draftLabel = data.draft_id ? `draft ${data.draft_id}` : data.document_id ? `document ${data.document_id}` : `task ${taskId}`;
  const logs: ProcessingLogItem[] = [
    {
      id: `gateway-task-${taskId}`,
      time: toUiTimestamp(data.updated_at ?? data.created_at),
      document: draftLabel,
      stage: mapGatewayTaskStage(data.pipeline_stage),
      event: formatTaskEvent(taskId, data.pipeline_stage, data.status, data.progress_percent),
      retryStatus: mapGatewayTaskRetryStatus(data.status),
      visibility: 'Администратор',
    },
  ];

  const steps = Array.isArray(data.steps) ? data.steps : [];
  steps.forEach((step: any, index: number) => {
    logs.push({
      id: `gateway-task-${taskId}-step-${step.step_name ?? index}`,
      time: toUiTimestamp(step.completed_at ?? step.started_at ?? data.updated_at ?? data.created_at),
      document: draftLabel,
      stage: mapGatewayTaskStage(step.step_name, step.service_name),
      event: formatTaskStepEvent(step, index),
      retryStatus: mapGatewayTaskRetryStatus(step.status),
      visibility: 'Администратор',
    });
  });

  return logs;
}

function mapGatewayDraftRecord(payload: any) {
  const data = payload?.data ?? payload ?? {};
  const previewMetadata = normalizePreviewMetadata(data.preview_metadata ?? data.preview ?? null);
  const rawData = data.raw_data ?? data.raw ?? data;
  const metadataOverrides = data.metadata_overrides ?? data.metadataOverrides ?? {};
  const notifications = Array.isArray(data.notifications)
    ? data.notifications
    : Array.isArray(data.quality?.notifications)
      ? data.quality.notifications
      : [];

  return {
    ...data,
    draft_id: data.draft_id,
    task_id: data.task_id ?? data.taskId,
    version_id: data.version_id ?? data.versionId,
    file_key: data.file_key ?? data.fileKey,
    document_key: data.document_key ?? data.documentKey ?? deriveDocumentKey(data.file_hash_sha256 ?? data.fileHashSha256),
    file_hash_sha256: data.file_hash_sha256 ?? data.fileHashSha256,
    title_hash_sha256: data.title_hash_sha256 ?? data.titleHashSha256 ?? previewMetadata?.title_hash_sha256,
    title_key: data.title_key ?? data.titleKey ?? previewMetadata?.title_key,
    status: normalizeDraftStatus(data.status),
    confidence: data.confidence ?? null,
    preview_metadata: previewMetadata,
    metadata_overrides: metadataOverrides,
    notifications,
    has_notifications: Boolean(data.has_notifications ?? notifications.length),
    critical_count:
      data.critical_count ??
      notifications.filter((item: any) => String(item?.severity ?? '').toLowerCase() === 'critical').length,
    valid_from: data.valid_from ?? metadataOverrides.valid_from ?? previewMetadata?.valid_from ?? null,
    valid_until: data.valid_until ?? metadataOverrides.valid_until ?? previewMetadata?.valid_until ?? null,
    document_id: data.document_id ?? data.promoted_document_id ?? data.approved_document_id ?? null,
    promoted_document_id: data.document_id ?? data.promoted_document_id ?? data.approved_document_id ?? null,
    approved_document_id: data.document_id ?? data.approved_document_id ?? data.promoted_document_id ?? null,
    error_code: data.error_code ?? null,
    error_message: data.error_message ?? null,
    raw_data: rawData,
    created_at: data.created_at ?? data.createdAt ?? '',
    updated_at: data.updated_at ?? data.updatedAt ?? '',
  };
}

function unwrapRegistryObject<T>(payload: any): T {
  return (payload?.data ?? payload) as T;
}

function mapRegistryListResponse<T>(payload: any, mapper: (item: any, index: number) => T): RegistryListResponse<T> {
  const items = Array.isArray(payload) ? payload : payload?.data ?? payload?.items ?? [];

  return {
    data: items.map(mapper),
    meta: payload?.meta ?? payload?.pagination ?? payload?.page ?? {},
  };
}

function mapRegistryClassifierNode(node: any): RegistryClassifierNode {
  const children = Array.isArray(node.children) ? node.children.map((child: any) => mapRegistryClassifierNode(child)) : [];

  return {
    classifier_system: String(node.classifier_system ?? node.system ?? ''),
    code: String(node.code ?? ''),
    parent_code: node.parent_code ?? null,
    full_name: node.full_name ?? node.name ?? node.code ?? '',
    status: node.status ?? 'active',
    effective_date: node.effective_date ?? null,
    replaced_by: node.replaced_by ?? null,
    created_at: node.created_at ?? null,
    documents_count: Number(node.documents_count ?? node.document_count ?? node.linked_documents_count ?? 0),
    children,
  };
}

function mapRegistryPendingNode(node: any): RegistryClassifierPending {
  return {
    id: toGatewayStringId(node.id),
    system: node.system ?? node.classifier_system ?? '',
    code: node.code ?? '',
    found_in_document_id: node.found_in_document_id === undefined || node.found_in_document_id === null ? null : String(node.found_in_document_id),
    found_in_document_title: node.found_in_document_title ?? '',
    status: node.status ?? '',
    suggested_parent_code: node.suggested_parent_code ?? null,
    suggested_parent_name: node.suggested_parent_name ?? '',
    admin_comment: node.admin_comment ?? null,
    created_at: node.created_at ?? null,
  };
}

function mapRegistryTerminologyNode(node: any): RegistryTerminologyEntry {
  const scope = Array.isArray(node.scope) ? node.scope : node.scope ? [node.scope] : [];

  return {
    id: toGatewayStringId(node.id),
    raw_term: node.raw_term ?? '',
    standard_term: node.standard_term ?? '',
    normalized_value: node.normalized_value ?? '',
    term_type: node.term_type ?? '',
    is_case_sensitive: Boolean(node.is_case_sensitive),
    definition: node.definition ?? null,
    synonyms: Array.isArray(node.synonyms) ? node.synonyms.map((item: any) => String(item)) : [],
    related_docs: Array.isArray(node.related_docs) ? node.related_docs.map((item: any) => String(item)) : [],
    scope: scope.map((item: any) => String(item)),
    is_blocked: Boolean(node.is_blocked),
    created_at: node.created_at ?? null,
    updated_at: node.updated_at ?? null,
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
    const response = await apiClient.post('/auth/token', { username, password }, { headers: { [SKIP_AUTH_HEADER]: 'true' } });
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
    store.setCurrentPermissions(profile.permissions ?? {});

    return profile;
  },
  refresh: async () => {
    const accessToken = await refreshGatewayTokenOnce();
    if (!accessToken) throw new Error('Refresh token is empty');
    return { access_token: accessToken };
  },
  restore: async (): Promise<AdminUser | null> => {
    if (isDemoMode()) return null;
    if (!getAccessToken() && !getRefreshToken()) return null;

    try {
      const profile = await authApi.me();
      useUIStore.getState().setApiStatus('online');
      return profile;
    } catch {
      clearGatewaySession();
      return null;
    }
  },
  logout: async () => {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) {
        await apiClient.post(
          '/auth/revoke',
          { refresh_token: refreshToken },
          { headers: { [SKIP_AUTH_HEADER]: 'true' } },
        );
      }
    } finally {
      clearGatewaySession();
      useUIStore.getState().setCurrentGatewaySessionId(null);
    }
  },
};

export const systemApi = {
  health: async (): Promise<GatewayHealth> => {
    const response = await apiClient.get('/system/health');
    return {
      status: response.data?.status ?? 'unknown',
      service: response.data?.service,
      version: response.data?.version,
      timestamp: response.data?.timestamp,
      raw: response.data,
    };
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
      const resolveGatewayProjectId = async () => {
        const currentProjectId = useUIStore.getState().activeProjectId;
        if (currentProjectId && /^\d+$/.test(currentProjectId)) {
          return currentProjectId;
        }

        const projects = await projectsApi.list();
        const resolvedProjectId = projects.find((project) => /^\d+$/.test(project.id))?.id ?? projects[0]?.id;

        if (resolvedProjectId) {
          useUIStore.getState().setActiveProjectId(resolvedProjectId);
          return resolvedProjectId;
        }

        return currentProjectId || undefined;
      };

      const createAndSelectSession = async () => {
        const projectId = await resolveGatewayProjectId();
        const created = await chatApi.createSession(query.slice(0, 70) || 'Новый чат', projectId);
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
        throw new Error('Gateway accepted chat request but did not return message_id or answer_id.');
      }

      let finalResponse;
      try {
        finalResponse = await waitForGatewayChatMessage(activeSessionId, String(messageId), 15, 4);
      } catch (error) {
        useUIStore.getState().setApiStatus('offline');
        throw error;
      }

      useUIStore.getState().setApiStatus('online');
      return mapGatewayChatResponse(finalResponse ?? { ...response.data, session_id: activeSessionId }, query);
    } catch (error) {
      useUIStore.getState().setApiStatus('offline');
      throw error;
    }
  },
};

export const projectsApi = {
  list: async (): Promise<GatewayChatProject[]> => {
    const response = await gatewayRequest<any>(() => apiClient.get('/chat/projects', { params: { page_size: 100 } }));
    return mapGatewayProjectsResponse(response.data);
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
    const response = await gatewayRequest<any>(() => apiClient.delete(`/chat/projects/${projectId}`));
    return response.data;
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
      const response = await gatewayRequest<any>(() =>
        apiClient.post('/text/search', { text: q, top_k: 10, valid_at: todayIsoDate() }),
      );
      useUIStore.getState().setApiStatus('online');
      return mapGatewaySearchResponse(response.data);
    } catch {
      useUIStore.getState().setApiStatus('offline');
      throw new Error('Серверная часть недоступна');
    }
  },
};

const isNumericDraftId = (draftId: string): boolean => /^\d+$/.test(draftId);

/** @internal Кидает ошибку, если draftId нечисловой */
function requireNumericDraftId(draftId: string, method: string): asserts draftId is string {
  if (!isNumericDraftId(draftId)) {
    throw new Error(`draftsApi.${method}: draft_id «${draftId}» не является числом — запрос не отправлен.`);
  }
}

export const draftsApi = {
  create: async (file: File, input: DraftCreateInput = {}) => {
    const form = new FormData();
    const fileHashSha256 = await calculateFileSha256(file);
    const documentKey = input.documentKey?.trim() || deriveDocumentKey(fileHashSha256);

    form.append('file', file);
    form.append('document_key', documentKey);
    form.append('source_type', input.sourceType?.trim() || 'OTHER');
    appendFormValue(form, 'title', input.title?.trim());
    appendFormValue(form, 'doc_code', input.docCode?.trim());
    appendFormValue(form, 'mks_oks_code', input.mksOksCode?.trim());
    appendFormValue(form, 'okstu_code', input.okstuCode?.trim());
    appendFormValue(form, 'era', input.era?.trim());
    appendFormValue(form, 'jurisdiction', input.jurisdiction?.trim());
    appendFormValue(form, 'issuing_body', input.issuingBody?.trim());
    appendFormValue(form, 'valid_from', input.validFrom);
    appendFormValue(form, 'valid_until', input.validUntil);
    if (input.metadata !== undefined && input.metadata !== null && input.metadata !== '') {
      form.append('metadata', typeof input.metadata === 'string' ? input.metadata : JSON.stringify(input.metadata));
    }

    const response = await gatewayRequest<any>(() =>
      apiClient.post('/drafts', form, {
        timeout: FILE_UPLOAD_TIMEOUT_MS,
        headers: {
          ...(input.idempotencyKey ? { 'Idempotency-Key': input.idempotencyKey } : {}),
        },
      }),
    );

    return mapGatewayDraftRecord(response.data);
  },
  list: async (params: { documentKey?: string; status?: string; page?: number; pageSize?: number } = {}) => {
    const response = await gatewayRequest<any>(() =>
      apiClient.get('/drafts', {
        params: {
          ...(params.documentKey ? { document_key: params.documentKey } : {}),
          status: params.status,
          page: params.page ?? 1,
          page_size: params.pageSize ?? 50,
        },
      }),
    );

    const items = Array.isArray(response.data)
      ? response.data
      : response.data?.items ?? response.data?.drafts ?? response.data?.data ?? [];
    return items.map((item: any) => mapGatewayDraftRecord(item));
  },
  get: async (draftId: string) => {
    requireNumericDraftId(draftId, 'get');
    const response = await gatewayRequest<any>(() => apiClient.get(`/drafts/${draftId}`));
    return mapGatewayDraftRecord(response.data);
  },
  getPreview: async (draftId: string) => {
    requireNumericDraftId(draftId, 'getPreview');
    const response = await gatewayRequest<any>(() => apiClient.get(`/drafts/${draftId}/preview`));
    return mapGatewayDraftRecord(response.data);
  },
  startPreview: async (draftId: string) => {
    requireNumericDraftId(draftId, 'startPreview');
    const response = await gatewayRequest<any>(() => pipelineClient.post(`/drafts/${draftId}/preview`));
    return response.data;
  },
  waitPreview: async (draftId: string, longpoll = 15) => {
    requireNumericDraftId(draftId, 'waitPreview');
    const response = await gatewayRequest<any>(() =>
      pipelineClient.get(`/drafts/${draftId}/preview/status`, {
        params: { longpoll },
      }),
    );
    return response.data;
  },
  updateMetadata: async (draftId: string, metadataOverrides: DraftMetadataOverrides) => {
    requireNumericDraftId(draftId, 'updateMetadata');
    const response = await gatewayRequest<any>(() => apiClient.patch(`/drafts/${draftId}/metadata`, metadataOverrides));
    return mapGatewayDraftRecord(response.data);
  },
  decide: async (draftId: string, actionOrInput: DraftDecisionAction | DraftDecisionInput, comment?: string) => {
    requireNumericDraftId(draftId, 'decide');
    const input: DraftDecisionInput =
      typeof actionOrInput === 'string'
        ? { action: actionOrInput, comment }
        : actionOrInput;
    const payload = {
      action: input.action,
      comment: input.comment,
      ...(input.metadataOverrides ? { metadata_overrides: input.metadataOverrides } : {}),
    };
    const response = await gatewayRequest<any>(() =>
      apiClient.patch(`/drafts/${draftId}/decide`, payload),
    );
    return response.data;
  },
  delete: async (draftId: string) => {
    requireNumericDraftId(draftId, 'delete');
    const response = await gatewayRequest<any>(() => apiClient.delete(`/drafts/${draftId}`));
    return response.data;
  },
};

export const tasksApi = {
  status: async (taskId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/tasks/${taskId}/status`));
    return mapGatewayTaskStatusResponse(response.data);
  },
  forDraft: async (draftId: string) => {
    // Только числовой draft_id имеет смысл — локальные id (draft-{timestamp}-{random}) не шлём
    if (!/^\d+$/.test(draftId)) return [];
    const response = await gatewayRequest<any>(() => apiClient.get(`/drafts/${draftId}/tasks`));
    const tasks = Array.isArray(response.data?.tasks)
      ? response.data.tasks
      : Array.isArray(response.data?.items)
        ? response.data.items
        : Array.isArray(response.data?.data)
          ? response.data.data
          : [];

    const taskLogs = await Promise.all(
      tasks
        .filter((task: any) => task?.task_id ?? task?.id)
        .slice(0, 8)
        .map(async (task: any) => {
          try {
            return await tasksApi.status(String(task.task_id ?? task.id));
          } catch {
            return mapGatewayTaskStatusResponse(task);
          }
        }),
    );

    return taskLogs.flat();
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
    const payload = response.data?.data ?? response.data;
    return Array.isArray(payload) ? payload : Array.isArray(payload?.history) ? payload.history : [];
  },
  errors: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/errors`));
    const payload = (response.data?.data ?? response.data) as GatewayDocumentErrors;
    return Array.isArray(payload?.errors) ? payload.errors : [];
  },
  parameters: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/parameters`));
    return (response.data?.data ?? response.data) as GatewayDocumentParameters;
  },
  pages: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/pages`));
    const payload = (response.data?.data ?? response.data) as GatewayDocumentPages;
    return Array.isArray(payload?.pages) ? payload.pages : [];
  },
  pagePreview: async (documentId: string, pageNumber: number) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/pages/${pageNumber}/preview`));
    return response.data?.data ?? response.data;
  },
  pageText: async (documentId: string, pageNumber: number) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/pages/${pageNumber}/text`));
    return response.data?.data ?? response.data;
  },
  file: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/file`));
    return response.data?.data ?? response.data;
  },
  updateValidity: async (documentId: string, payload: { valid_from?: string; valid_until?: string | null }) => {
    const response = await gatewayRequest<any>(() => apiClient.patch(`/registry/documents/${documentId}`, payload));
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
      apiClient.get('/registry/classifiers/tree', {
        params: {
          classifier_system: 'MKS',
          max_depth: 10,
        },
      }),
    );
    return mapGatewayKnowledgeSections(response.data);
  },
  upload: async (file: File) => {
    return draftsApi.create(file);
  },
  reprocess: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.post(`/documents/${documentId}/reprocess`, { mode: 'full' }));
    return response.data;
  },
  versions: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/documents/${documentId}/versions`));
    const payload = response.data?.data ?? response.data;
    return Array.isArray(payload) ? payload : Array.isArray(payload?.versions) ? payload.versions : [];
  },
  archive: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.delete(`/documents/${documentId}`));
    return response.data;
  },
};

export const registryApi = {
  classifiers: {
    list: async (params: {
      classifierSystem?: string;
      code?: string;
      fullName?: string;
      status?: string;
      parentCode?: string;
      page?: number;
      pageSize?: number;
    } = {}) => {
      if (isDemoMode()) {
        return { data: [], meta: { total: 0, page: params.page ?? 1, page_size: params.pageSize ?? 50 } };
      }

      const response = await gatewayRequest<any>(() =>
        apiClient.get('/registry/classifiers', {
          params: {
            classifier_system: params.classifierSystem,
            code: params.code,
            full_name: params.fullName,
            status: params.status,
            parent_code: params.parentCode,
            page: params.page ?? 1,
            page_size: params.pageSize ?? 50,
          },
        }),
      );

      return mapRegistryListResponse(response.data, mapRegistryClassifierNode);
    },
    tree: async (params: { classifierSystem: string; rootCode?: string; maxDepth?: number; search?: string; status?: string }) => {
      if (isDemoMode()) {
        return { data: [], meta: { total: 0, max_depth_reached: false } };
      }

      const response = await gatewayRequest<any>(() =>
        apiClient.get('/registry/classifiers/tree', {
          params: {
            classifier_system: params.classifierSystem,
            root_code: params.rootCode,
            max_depth: params.maxDepth ?? 10,
            search: params.search,
            status: params.status,
          },
        }),
      );

      return mapRegistryListResponse(response.data, mapRegistryClassifierNode);
    },
    get: async (code: string, classifierSystem: string) => {
      if (isDemoMode()) return null;

      const response = await gatewayRequest<any>(() =>
        apiClient.get(`/registry/classifiers/${encodeURIComponent(code)}`, {
          params: { classifier_system: classifierSystem },
        }),
      );

      return mapRegistryClassifierNode(unwrapRegistryObject(response.data));
    },
    create: async (payload: Partial<RegistryClassifierNode> & { effective_date?: string | null }) => {
      const response = await gatewayRequest<any>(() => apiClient.post('/registry/classifiers', payload));
      return mapRegistryClassifierNode(unwrapRegistryObject(response.data));
    },
    update: async (code: string, classifierSystem: string, payload: Partial<RegistryClassifierNode> & { effective_date?: string | null }) => {
      const response = await gatewayRequest<any>(() =>
        apiClient.put(`/registry/classifiers/${encodeURIComponent(code)}`, payload, {
          params: { classifier_system: classifierSystem },
        }),
      );
      return mapRegistryClassifierNode(unwrapRegistryObject(response.data));
    },
    patch: async (code: string, classifierSystem: string, payload: Partial<RegistryClassifierNode> & { effective_date?: string | null }) => {
      const response = await gatewayRequest<any>(() =>
        apiClient.patch(`/registry/classifiers/${encodeURIComponent(code)}`, payload, {
          params: { classifier_system: classifierSystem },
        }),
      );
      return mapRegistryClassifierNode(unwrapRegistryObject(response.data));
    },
    delete: async (code: string, classifierSystem: string) => {
      const response = await gatewayRequest<any>(() =>
        apiClient.delete(`/registry/classifiers/${encodeURIComponent(code)}`, {
          params: { classifier_system: classifierSystem },
        }),
      );
      return response.data ?? { ok: true };
    },
    import: async (file: File, classifierSystem: string, mapping: string | Record<string, unknown>) => {
      const form = new FormData();
      form.append('file', file);
      form.append('classifier_system', classifierSystem);
      form.append('mapping', typeof mapping === 'string' ? mapping : JSON.stringify(mapping));

      const response = await gatewayRequest<any>(() =>
        apiClient.post('/registry/classifiers/import', form),
      );
      return response.data;
    },
    pending: async (params: { system?: string; status?: string; page?: number; pageSize?: number } = {}) => {
      if (isDemoMode()) {
        return { data: [], meta: { total: 0, page: params.page ?? 1, page_size: params.pageSize ?? 50 } };
      }

      const response = await gatewayRequest<any>(() =>
        apiClient.get('/registry/classifiers/pending', {
          params: {
            system: params.system,
            status: params.status,
            page: params.page ?? 1,
            page_size: params.pageSize ?? 50,
          },
        }),
      );

      return mapRegistryListResponse(response.data, mapRegistryPendingNode);
    },
    acceptPending: async (pendingId: string, payload: { parentCode?: string; fullName?: string; adminComment?: string }) => {
      const response = await gatewayRequest<any>(() =>
        apiClient.post(`/registry/classifiers/pending/${encodeURIComponent(pendingId)}/accept`, {
          parent_code: payload.parentCode,
          full_name: payload.fullName,
          admin_comment: payload.adminComment,
        }),
      );
      return response.data;
    },
    rejectPending: async (pendingId: string, adminComment?: string) => {
      const response = await gatewayRequest<any>(() =>
        apiClient.post(`/registry/classifiers/pending/${encodeURIComponent(pendingId)}/reject`, {
          admin_comment: adminComment,
        }),
      );
      return response.data;
    },
    validate: async (classification: { mksOksCode?: string; okstuCode?: string; udkCode?: string }) => {
      if (isDemoMode()) {
        return {
          classification: {
            mks_status: 'UNASSIGNED',
            okstu_status: 'UNASSIGNED',
            udk_valid: false,
            overall_status: 'pending',
          },
        };
      }

      const response = await gatewayRequest<any>(() =>
        apiClient.post('/registry/classifiers/validate', {
          classification: {
            mks_oks_code: classification.mksOksCode,
            okstu_code: classification.okstuCode,
            udk_code: classification.udkCode,
          },
        }),
      );
      return unwrapRegistryObject(response.data);
    },
  },
  terminology: {
    list: async (params: {
      rawTerm?: string;
      standardTerm?: string;
      termType?: string;
      isBlocked?: boolean;
      scope?: string;
      page?: number;
      pageSize?: number;
    } = {}) => {
      if (isDemoMode()) {
        return { data: [], meta: { total: 0, page: params.page ?? 1, page_size: params.pageSize ?? 50 } };
      }

      const response = await gatewayRequest<any>(() =>
        apiClient.get('/registry/terminology', {
          params: {
            raw_term: params.rawTerm,
            standard_term: params.standardTerm,
            term_type: params.termType,
            is_blocked: params.isBlocked,
            scope: params.scope,
            page: params.page ?? 1,
            page_size: params.pageSize ?? 50,
          },
        }),
      );

      return mapRegistryListResponse(response.data, mapRegistryTerminologyNode);
    },
    get: async (termId: string) => {
      if (isDemoMode()) return null;

      const response = await gatewayRequest<any>(() => apiClient.get(`/registry/terminology/${encodeURIComponent(termId)}`));
      return mapRegistryTerminologyNode(unwrapRegistryObject(response.data));
    },
    create: async (payload: Partial<RegistryTerminologyEntry>) => {
      const response = await gatewayRequest<any>(() => apiClient.post('/registry/terminology', payload));
      return mapRegistryTerminologyNode(unwrapRegistryObject(response.data));
    },
    update: async (termId: string, payload: Partial<RegistryTerminologyEntry>) => {
      const response = await gatewayRequest<any>(() =>
        apiClient.put(`/registry/terminology/${encodeURIComponent(termId)}`, payload),
      );
      return mapRegistryTerminologyNode(unwrapRegistryObject(response.data));
    },
    delete: async (termId: string) => {
      const response = await gatewayRequest<any>(() => apiClient.delete(`/registry/terminology/${encodeURIComponent(termId)}`));
      return response.data ?? { ok: true };
    },
    normalize: async (term: string) => {
      if (isDemoMode()) {
        return {
          raw_term: term,
          standard_term: term,
          normalized_value: term.toLowerCase(),
          term_type: 'unknown',
          is_blocked: false,
        };
      }

      const response = await gatewayRequest<any>(() =>
        apiClient.get('/registry/terminology/normalize', {
          params: { term },
        }),
      );
      return unwrapRegistryObject(response.data);
    },
    import: async (file: File, mapping: string | Record<string, unknown>) => {
      const form = new FormData();
      form.append('file', file);
      form.append('mapping', typeof mapping === 'string' ? mapping : JSON.stringify(mapping));

      const response = await gatewayRequest<any>(() =>
        apiClient.post('/registry/terminology/import', form),
      );
      return response.data;
    },
  },
  documents: async () => {
    if (isDemoMode()) return MOCK_DOCUMENTS;

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
  },
  document: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/registry/documents/${documentId}`));
    return mapGatewayDocumentDetailResponse(response.data);
  },
  documentSections: async (documentId: string) => {
    const response = await gatewayRequest<any>(() => apiClient.get(`/registry/documents/${documentId}/sections`));
    return response.data;
  },
  knowledgeSections: async () => {
    if (isDemoMode()) return MOCK_KNOWLEDGE_SECTIONS;

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
  },
  stats: async () => {
    const response = await gatewayRequest<any>(() => apiClient.get('/registry/stats'));
    return response.data?.data ?? response.data;
  },
  enums: async () => {
    const response = await gatewayRequest<any>(() => apiClient.get('/registry/enums'));
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
    } catch (error) {
      useUIStore.getState().setApiStatus('offline');
      throw error;
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
      throw new Error('Не удалось загрузить реальные метрики системы');
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
      throw new Error('Не удалось загрузить реальные метрики системы');
    }
  },
};

export const adminApi = {
  roles: async (): Promise<AdminUser['role'][]> => {
    if (isDemoMode()) {
      return Array.from(new Set(MOCK_ADMIN_USERS.map((user) => user.role)));
    }

    const response = await gatewayRequest<any>(() => apiClient.get('/admin/roles'));
    useUIStore.getState().setApiStatus('online');
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
      useUIStore.getState().setApiStatus('online');
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
          rating_status: payload.useful ? 'positive' : 'negative',
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
