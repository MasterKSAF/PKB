import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Checkbox,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Download, FileText, History, Layers3, Maximize2, MoreVertical, Save, Search, Trash2, X } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useUIStore } from '../store/uiStore';
import { downloadPreviewFile } from '../utils/downloadPreview';
import { type Document } from '../utils/mockData';
import { apiClient, documentsApi } from '../utils/http';

type DocumentVersionSummary = {
  id: string;
  label: string;
  createdAt: string;
  author: string;
  size: string;
  status: string;
  note: string;
  raw: Record<string, unknown>;
};

type DocumentPreviewPage = {
  title: string;
  lines: string[];
  pageNumber: number;
  imageUrl?: string;
};

const PANEL_SX = {
  bgcolor: 'rgba(22, 23, 27, 0.72)',
  borderColor: 'rgba(198, 216, 240, 0.34)',
  borderWidth: 1.5,
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
} as const;

const TABLE_SX = {
  borderRadius: 2,
  bgcolor: 'transparent',
  borderWidth: 0,
  borderColor: 'transparent',
  boxShadow: 'none',
} as const;

const normalizeText = (value: unknown) => String(value ?? '').trim();
const GATEWAY_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8080/api/v1';

const displayValue = (value: unknown) => {
  const text = normalizeText(value);
  return text || 'не передано';
};

const REGISTRY_STATUS_LABELS: Record<string, string> = {
  active: 'действует',
  pending: 'ожидает',
  expired: 'истек срок',
  uploaded: 'загружен',
  created: 'создан',
  completed: 'завершен',
  failed: 'ошибка',
  processing: 'в обработке',
  published: 'опубликован',
  validating: 'проверяется',
  pending_index: 'ожидает индексации',
  indexing: 'индексируется',
  indexed: 'индексирован',
  approved: 'подтвержден',
  discarded: 'отклонен',
  current: 'текущая',
  archive: 'архив',
};

const REGISTRY_STATUS_FILTER_OPTIONS = [
  { value: 'active', label: 'Действует' },
  { value: 'pending', label: 'Ожидает' },
  { value: 'expired', label: 'Истек срок' },
  { value: 'uploaded', label: 'Загружен' },
  { value: 'created', label: 'Создан' },
  { value: 'completed', label: 'Завершен' },
  { value: 'failed', label: 'Ошибка' },
] as const;

const formatRegistryStatus = (value: unknown) => {
  const text = normalizeText(value);
  if (!text) return 'не передано';
  return REGISTRY_STATUS_LABELS[text.toLowerCase()] ?? text;
};

const normalizeValidUntil = (value: unknown) => {
  const text = normalizeText(value);
  if (!text) return '';
  if (text === '9999-12-31') return 'бессрочно';
  return text;
};

const resolveGatewayAssetUrl = (url: unknown) => {
  const text = normalizeText(url);
  if (!text) return '';
  if (/^https?:\/\//i.test(text)) {
    try {
      const parsed = new URL(text);
      if (['minio', 'registry', 'orchestrator', 'gateway'].includes(parsed.hostname.toLowerCase())) {
        return '';
      }
    } catch {
      return '';
    }
    return text;
  }

  const apiBase = GATEWAY_API_BASE_URL.replace(/\/+$/, '');
  const originBase = apiBase.replace(/\/api\/v\d+$/i, '');
  return `${originBase}${text.startsWith('/') ? text : `/${text}`}`;
};

const getInternalServiceHost = (url: unknown) => {
  const text = normalizeText(url);
  if (!/^https?:\/\//i.test(text)) return '';
  try {
    const parsed = new URL(text);
    return ['minio', 'registry', 'orchestrator', 'gateway'].includes(parsed.hostname.toLowerCase()) ? parsed.hostname : '';
  } catch {
    return '';
  }
};

const extractServerErrorMessage = async (payload: unknown) => {
  if (!payload) return '';
  try {
    if (payload instanceof Blob) {
      const text = await payload.text();
      if (!text) return '';
      try {
        const parsed = JSON.parse(text);
        return normalizeText(parsed?.error?.message ?? parsed?.detail?.error?.message ?? parsed?.detail ?? text);
      } catch {
        return text;
      }
    }
    if (typeof payload === 'string') return payload;
    if (typeof payload === 'object') {
      const data = payload as Record<string, any>;
      return normalizeText(data.error?.message ?? data.detail?.error?.message ?? data.detail ?? data.message);
    }
  } catch {
    return '';
  }
  return '';
};

const openBlobInNewTab = (blob: Blob) => {
  const objectUrl = URL.createObjectURL(blob);
  window.open(objectUrl, '_blank', 'noopener,noreferrer');
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
};

const getLatestVersionId = (detail: any, versions: DocumentVersionSummary[]) => {
  const latest = detail?.latest_version ?? {};
  return normalizeText(latest.version_id ?? latest.versionId ?? detail?.version_id ?? detail?.current_version_id ?? versions[0]?.id);
};

const getTodayDateInput = () => {
  const date = new Date();
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return offsetDate.toISOString().slice(0, 10);
};

const openNativeDatePicker = (event: React.MouseEvent<HTMLInputElement> | React.FocusEvent<HTMLInputElement>) => {
  const input = event.currentTarget as HTMLInputElement & { showPicker?: () => void };
  input.showPicker?.();
};

const normalizeDocumentVersion = (item: any, index: number): DocumentVersionSummary => {
  const raw = item && typeof item === 'object' ? item : {};
  const id = normalizeText(
    raw.version_id ?? raw.versionId ?? raw.id ?? raw.revision_id ?? raw.revisionId ?? `version-${index + 1}`,
  );
  const label = normalizeText(raw.version ?? raw.version_number ?? raw.revision ?? raw.name ?? raw.title) || `Версия ${index + 1}`;
  const createdAt = normalizeText(raw.created_at ?? raw.createdAt ?? raw.uploaded_at ?? raw.uploadedAt ?? raw.updated_at ?? raw.updatedAt);
  const author = normalizeText(raw.author ?? raw.created_by ?? raw.createdBy ?? raw.uploaded_by ?? raw.uploadedBy ?? raw.user ?? raw.user_name);
  const size = normalizeText(raw.size ?? raw.file_size ?? raw.fileSize ?? raw.bytes ?? raw.length);
  const status = normalizeText(raw.status ?? raw.state ?? raw.pipeline_status ?? raw.lifecycle_status);
  const note = normalizeText(raw.comment ?? raw.note ?? raw.message ?? raw.reason);

  return {
    id,
    label,
    createdAt: createdAt || 'не указано',
    author: author || 'не указан',
    size: size || 'н/д',
    status: status ? formatRegistryStatus(status) : 'не указан',
    note: note || 'без комментария',
    raw,
  };
};

const extractVersionItems = (payload: any): DocumentVersionSummary[] => {
  const source = Array.isArray(payload) ? payload : payload?.versions ?? payload?.items ?? payload?.data ?? [];
  if (!Array.isArray(source)) return [];
  return source.map((item: any, index: number) => normalizeDocumentVersion(item, index));
};

const extractPageEntries = (payload: any): DocumentPreviewPage[] => {
  const source = Array.isArray(payload) ? payload : payload?.pages ?? payload?.items ?? payload?.data ?? [];
  if (!Array.isArray(source)) return [];

  return source.map((item: any, index: number) => {
    const title = normalizeText(item?.title ?? item?.page_title ?? item?.name ?? item?.clause ?? `Страница ${index + 1}`);
    const number = normalizeText(item?.page_number ?? item?.pageNumber ?? item?.number ?? item?.page ?? index + 1);
    const pageNumber = Number(number || index + 1);
    const body = normalizeText(item?.text ?? item?.content ?? item?.body ?? item?.preview ?? item?.excerpt);

    return {
      title: `${title}${number ? ` · стр. ${number}` : ''}`,
      pageNumber: Number.isFinite(pageNumber) ? pageNumber : index + 1,
      lines: body ? body.split(/\r?\n/).filter(Boolean) : [],
      imageUrl: resolveGatewayAssetUrl(item?.image_url ?? item?.preview_url),
    };
  });
};

const extractPageText = (payload: any) => {
  const direct = normalizeText(payload?.full_text ?? payload?.text ?? payload?.content);
  if (direct) return direct;

  const blocks = Array.isArray(payload?.blocks) ? payload.blocks : [];
  return blocks
    .map((block: any) => normalizeText(block?.text ?? block?.content ?? block?.value))
    .filter(Boolean)
    .join('\n');
};

const buildDemoDetail = (document: Document | null) => {
  if (!document) return null;

  return {
    document_id: document.id,
    id: document.id,
    title: document.name,
    doc_code: document.id.toUpperCase(),
    source_type: document.type,
    status: document.indexStatus === 'Индексировано' ? 'published' : 'processing',
    era: 'CURRENT',
    validity_status: document.indexStatus === 'Индексировано' ? 'active' : 'pending',
    jurisdiction: 'RU',
    issuing_body: document.source,
    mks_oks_code: document.group ?? document.sectionId ?? null,
    okstu_code: document.sectionId ?? null,
    classification_status: {
      current: document.group ?? document.sectionId ?? '—',
    },
    successor_doc_id: null,
    predecessor_doc_id: null,
    chunk_container_id: null,
    metadata: {
      title: document.name,
      source: document.source,
      updated_at: document.updatedAt,
    },
    latest_version: {
      version: document.version,
    },
    total_versions: 2,
    user_id: '',
    uploaded_by: document.source,
    created_by: document.source,
    updated_by: document.source,
    created_at: document.updatedAt,
    updated_at: document.updatedAt,
  };
};

const buildDemoVersions = (document: Document | null): DocumentVersionSummary[] => {
  if (!document) return [];

  return [
    normalizeDocumentVersion(
      {
        version_id: `${document.id}-current`,
        version: document.version,
        created_at: document.updatedAt,
        uploaded_by: document.source,
        status: 'current',
        size: '—',
        comment: 'Текущая актуальная версия',
      },
      0,
    ),
    normalizeDocumentVersion(
      {
        version_id: `${document.id}-previous`,
        version: `${document.version}-1`,
        created_at: document.updatedAt,
        uploaded_by: document.source,
        status: 'archive',
        size: '—',
        comment: 'Предыдущая версия для сравнения',
      },
      1,
    ),
  ];
};

const buildDemoHistory = (document: Document | null) => {
  if (!document) return [];

  return [
    { id: `${document.id}-created`, action: 'Загрузка', at: document.updatedAt, user: document.source, note: 'Документ добавлен в реестр.' },
    { id: `${document.id}-reviewed`, action: 'Проверка', at: document.updatedAt, user: 'Администратор знаний', note: 'Метаданные подтверждены вручную.' },
  ];
};

const buildDemoErrors = (document: Document | null) => {
  if (!document || document.ocrStatus !== 'Ошибка') return [];

  return [{ error_message: 'OCR не завершился для документа из демо-набора.' }];
};

const buildDemoParameters = (document: Document | null) => {
  if (!document) return null;

  return {
    extraction_confidence: document.indexStatus === 'Индексировано' ? 0.94 : 0.58,
    unconfirmed_fields: document.indexStatus === 'Индексировано' ? [] : ['classification_status'],
    parameters: {
      source: document.source,
      version: document.version,
      updated_at: document.updatedAt,
    },
  };
};

const buildDemoPages = (document: Document | null, detail: any): DocumentPreviewPage[] => {
  if (!document) return [];

  return [
    {
      title: 'Краткий срез',
      pageNumber: 1,
      lines: [
        document.name,
        `ID: ${document.id}`,
        `Тип: ${document.type}`,
        `Версия: ${document.version}`,
        `Источник: ${document.source}`,
        `OCR: ${document.ocrStatus}`,
        `Индекс: ${document.indexStatus}`,
      ],
    },
    {
      title: 'Метаданные',
      pageNumber: 2,
      lines: [
        `Код: ${detail?.doc_code ?? 'не указан'}`,
        `Юрисдикция: ${detail?.jurisdiction ?? 'не указана'}`,
        `Издатель: ${detail?.issuing_body ?? 'не указан'}`,
        `Классификация: ${detail?.mks_oks_code ?? detail?.okstu_code ?? 'не указана'}`,
      ],
    },
    {
      title: 'История и версии',
      pageNumber: 3,
      lines: [
        `Версий: ${detail?.total_versions ?? 0}`,
        `История: ${document.updatedAt}`,
        `Предыдущая версия: ${document.version}-1`,
      ],
    },
  ];
};

const buildPreviewText = (
  document: Document | null,
  detail: any,
  versions: DocumentVersionSummary[],
  history: Array<{ action?: string; at?: string; user?: string; note?: string }>,
  errors: Array<Record<string, unknown>>,
  parameters: any,
) => {
  if (!document) return 'Документ не выбран.';

  const previewLines = [
    document.name,
    `ID: ${document.id}`,
    `Тип: ${document.type}`,
    `Версия: ${document.version}`,
    `Источник: ${document.source}`,
    `OCR статус: ${document.ocrStatus}`,
    `Индекс статус: ${document.indexStatus}`,
    `Обновлен: ${document.updatedAt || 'не указано'}`,
    detail?.doc_code ? `Код: ${detail.doc_code}` : '',
    detail?.source_type ? `Тип источника: ${detail.source_type}` : '',
    detail?.title_key ? `title_key: ${detail.title_key}` : '',
    detail?.title_hash_sha256 ? `title_hash_sha256: ${detail.title_hash_sha256}` : '',
    detail?.valid_from ? `Действует с: ${detail.valid_from}` : '',
    detail?.valid_until ? `Действует до: ${normalizeValidUntil(detail.valid_until)}` : '',
    detail?.jurisdiction ? `Юрисдикция: ${detail.jurisdiction}` : '',
    detail?.validity_status ? `Статус действия: ${formatRegistryStatus(detail.validity_status)}` : '',
    detail?.issuing_body ? `Издатель: ${detail.issuing_body}` : '',
    detail?.latest_version?.version ? `Последняя версия: ${detail.latest_version.version}` : '',
    versions.length ? `Версии: ${versions.map((item) => item.label).join(', ')}` : '',
    history.length ? `История: ${history.map((item) => `${item.action ?? 'Событие'} ${item.at ?? ''}`.trim()).join(' · ')}` : '',
    errors.length ? `Последняя ошибка: ${(errors[0] as any)?.error_message ?? 'не указана'}` : '',
    parameters?.extraction_confidence ? `Точность извлечения: ${Math.round(parameters.extraction_confidence * 100)}%` : '',
  ];

  return previewLines.filter(Boolean).join('\n');
};

const renderHighlightedText = (text: string, query: string, isLight: boolean) => {
  if (!query) return text;

  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  let matchIndex = lowerText.indexOf(lowerQuery);

  while (matchIndex !== -1) {
    if (matchIndex > cursor) parts.push(text.slice(cursor, matchIndex));
    parts.push(
      <Box
        key={`${matchIndex}-${query}`}
        component="mark"
        sx={{
          px: 0.25,
          borderRadius: 0.4,
          bgcolor: isLight ? 'rgba(250, 204, 21, 0.42)' : 'rgba(250, 204, 21, 0.36)',
          color: 'inherit',
        }}
      >
        {text.slice(matchIndex, matchIndex + query.length)}
      </Box>,
    );
    cursor = matchIndex + query.length;
    matchIndex = lowerText.indexOf(lowerQuery, cursor);
  }

  if (cursor < text.length) parts.push(text.slice(cursor));
  return parts;
};

const panelSxFor = (isLight: boolean) => ({
  ...PANEL_SX,
  ...(isLight && {
    bgcolor: 'rgba(255, 255, 255, 0.82)',
    borderColor: 'rgba(14, 116, 144, 0.24)',
    boxShadow: '0 8px 22px rgba(15,23,42,0.05)',
  }),
});

const tableSxFor = (isLight: boolean) => ({
  ...TABLE_SX,
  ...(isLight && {
    bgcolor: 'transparent',
    borderColor: 'transparent',
    boxShadow: 'none',
  }),
});

const sectionHeaderSxFor = (isLight: boolean) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 1,
  pb: 0.8,
  borderBottom: `2px solid ${isLight ? 'rgba(14, 116, 144, 0.24)' : 'rgba(198, 214, 236, 0.26)'}`,
});

const compactHeadSx = {
  fontSize: '0.68rem',
  fontWeight: 620,
  letterSpacing: '0.02em',
  textTransform: 'uppercase',
  color: 'text.secondary',
} as const;

const detailLabelSx = {
  fontSize: '0.69rem',
  fontWeight: 620,
  letterSpacing: '0.025em',
  textTransform: 'uppercase',
  color: 'text.secondary',
} as const;

const detailValueSx = {
  fontSize: '0.8rem',
  fontWeight: 500,
  overflowWrap: 'anywhere',
} as const;

const formatCompactDateTime = (value?: string) => {
  if (!value) return 'без даты';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

const HISTORY_ACTION_LABELS: Record<string, string> = {
  created: 'Создание',
  create: 'Создание',
  uploaded: 'Загрузка',
  upload: 'Загрузка',
  updated: 'Обновление',
  update: 'Обновление',
  metadata_updated: 'Обновление метаданных',
  status_changed: 'Смена статуса',
  approved: 'Подтверждение',
  discarded: 'Отклонение',
  deleted: 'Удаление',
  failed: 'Ошибка',
};

const formatHistoryAction = (value: unknown) => {
  const text = normalizeText(value);
  if (!text) return '';
  return HISTORY_ACTION_LABELS[text.toLowerCase()] ?? text;
};

const normalizeHistoryRows = (items: any[]) => {
  if (!Array.isArray(items)) return [];

  return items
    .map((item, index) => {
      if (!item || typeof item !== 'object') return null;

      const at = normalizeText(item.at ?? item.created_at ?? item.updated_at ?? item.timestamp ?? item.event_at);
      const action = formatHistoryAction(item.action ?? item.event ?? item.event_type ?? item.type ?? item.status);
      const details = item.details && typeof item.details === 'object' ? JSON.stringify(item.details) : item.details;
      const note = normalizeText(item.note ?? item.message ?? item.description ?? item.comment ?? item.reason ?? details);
      const user = normalizeText(item.user ?? item.user_id ?? item.created_by ?? item.updated_by ?? item.actor);

      if (!at && !action && !note && !user) return null;

      return {
        id: normalizeText(item.id ?? item.event_id ?? item.history_id) || `history-${index}`,
        at,
        action: action || 'Событие',
        note: note || (user ? `Пользователь: ${user}` : 'Дополнительные сведения не переданы.'),
      };
    })
    .filter((item): item is { id: string; at: string; action: string; note: string } => Boolean(item));
};

export const DocumentRegistryPanel: React.FC<{ documents: Document[] }> = ({ documents }) => {
  const { themeMode, workMode } = useUIStore();
  const queryClient = useQueryClient();
  const isLight = themeMode === 'light';
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [validityFilter, setValidityFilter] = useState('all');
  const [validAt, setValidAt] = useState(() => getTodayDateInput());
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [versionsOpen, setVersionsOpen] = useState(false);
  const [previewPageIndex, setPreviewPageIndex] = useState(0);
  const [previewSearch, setPreviewSearch] = useState('');
  const [selectedVersionIds, setSelectedVersionIds] = useState<string[]>([]);
  const [versionSelectionTouched, setVersionSelectionTouched] = useState(false);
  const [downloadError, setDownloadError] = useState('');
  const [validFromDraft, setValidFromDraft] = useState('');
  const [validUntilDraft, setValidUntilDraft] = useState('');
  const [registryNotice, setRegistryNotice] = useState('');
  const [registryError, setRegistryError] = useState('');
  const [validityOpen, setValidityOpen] = useState(false);
  const [metadataOpen, setMetadataOpen] = useState(false);
  const [technicalOpen, setTechnicalOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actionsAnchorEl, setActionsAnchorEl] = useState<null | HTMLElement>(null);

  const sourceFilterOptions = useMemo(
    () =>
      Array.from(new Set(documents.map((document) => document.sourceType || document.type).filter(Boolean))).sort((left, right) =>
        left.localeCompare(right, 'ru'),
      ),
    [documents],
  );

  const filteredDocuments = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    const sorted = [...documents].sort((left, right) => {
      const rightTime = new Date(right.updatedAt || 0).getTime();
      const leftTime = new Date(left.updatedAt || 0).getTime();
      return rightTime - leftTime || left.name.localeCompare(right.name, 'ru');
    });

    return sorted.filter((document) => {
      const matchesSearch =
        !normalized ||
        [
          document.id,
          document.name,
          document.docCode,
          document.type,
          document.source,
          document.sourceType,
          document.version,
          document.sectionId,
          document.group,
          document.validityStatus,
          document.status,
          document.indexStatus,
        ]
        .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(normalized));
      const matchesSource = sourceFilter === 'all' || document.sourceType === sourceFilter || document.type === sourceFilter;
      const normalizedStatusFilter = validityFilter.toLowerCase();
      const matchesValidity =
        validityFilter === 'all' ||
        [document.validityStatus, document.status, document.indexStatus]
          .filter(Boolean)
          .some((status) => String(status).toLowerCase() === normalizedStatusFilter);
      const matchesValidAt =
        !validAt ||
        ((!document.validFrom || document.validFrom <= validAt) &&
          (!document.validUntil || document.validUntil === '9999-12-31' || document.validUntil >= validAt));

      return matchesSearch && matchesSource && matchesValidity && matchesValidAt;
    });
  }, [documents, search, sourceFilter, validAt, validityFilter]);

  useEffect(() => {
    if (!selectedDocumentId && filteredDocuments[0]) {
      setSelectedDocumentId(filteredDocuments[0].id);
      return;
    }

    if (selectedDocumentId && !filteredDocuments.some((document) => document.id === selectedDocumentId)) {
      setSelectedDocumentId(filteredDocuments[0]?.id ?? '');
    }
  }, [filteredDocuments, selectedDocumentId]);

  const selectedDocument = filteredDocuments.find((document) => document.id === selectedDocumentId) ?? null;

  const detailQuery = useQuery({
    queryKey: ['document-registry-detail', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.get(selectedDocument!.id),
    enabled: workMode === 'prod' && Boolean(selectedDocument),
    staleTime: 30_000,
  });
  const versionsQuery = useQuery({
    queryKey: ['document-registry-versions', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.versions(selectedDocument!.id),
    enabled: workMode === 'prod' && Boolean(selectedDocument),
    staleTime: 30_000,
  });
  const historyQuery = useQuery({
    queryKey: ['document-registry-history', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.history(selectedDocument!.id),
    enabled: workMode === 'prod' && Boolean(selectedDocument),
    staleTime: 30_000,
  });
  const errorsQuery = useQuery({
    queryKey: ['document-registry-errors', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.errors(selectedDocument!.id),
    enabled: workMode === 'prod' && Boolean(selectedDocument),
    staleTime: 30_000,
  });
  const parametersQuery = useQuery({
    queryKey: ['document-registry-parameters', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.parameters(selectedDocument!.id),
    enabled: workMode === 'prod' && Boolean(selectedDocument),
    staleTime: 30_000,
  });
  const pagesQuery = useQuery({
    queryKey: ['document-registry-pages', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.pages(selectedDocument!.id),
    enabled: workMode === 'prod' && Boolean(selectedDocument),
    staleTime: 30_000,
  });
  const gatewayPages = useMemo(() => extractPageEntries(pagesQuery.data), [pagesQuery.data]);
  const selectedGatewayPage = gatewayPages[Math.min(previewPageIndex, Math.max(gatewayPages.length - 1, 0))] ?? null;
  const pageContentQuery = useQuery({
    queryKey: ['document-registry-page-content', workMode, selectedDocument?.id, selectedGatewayPage?.pageNumber],
    queryFn: async () => {
      const [previewResult, textResult] = await Promise.allSettled([
        documentsApi.pagePreview(selectedDocument!.id, selectedGatewayPage!.pageNumber),
        documentsApi.pageText(selectedDocument!.id, selectedGatewayPage!.pageNumber),
      ]);

      if (previewResult.status === 'rejected' && textResult.status === 'rejected') {
        throw new Error('Сервер не вернул предпросмотр страницы.');
      }

      return {
        preview: previewResult.status === 'fulfilled' ? previewResult.value : null,
        text: textResult.status === 'fulfilled' ? textResult.value : null,
      };
    },
    enabled:
      workMode === 'prod' &&
      Boolean(selectedDocument) &&
      Boolean(selectedGatewayPage) &&
      Number.isFinite(selectedGatewayPage?.pageNumber),
    staleTime: 30_000,
  });

  const detail = workMode === 'prod' ? detailQuery.data : buildDemoDetail(selectedDocument);
  const detailRecord = (detail ?? {}) as Record<string, any>;
  const versions = workMode === 'prod' ? extractVersionItems(versionsQuery.data) : buildDemoVersions(selectedDocument);
  const history = workMode === 'prod' ? (historyQuery.data ?? []) : buildDemoHistory(selectedDocument);
  const errors = workMode === 'prod' ? (errorsQuery.data ?? []) : buildDemoErrors(selectedDocument);
  const historyRows = useMemo(() => normalizeHistoryRows(history), [history]);
  const parameters = workMode === 'prod' ? parametersQuery.data : buildDemoParameters(selectedDocument);
  const previewPages = useMemo(
    () => {
      if (workMode !== 'prod') return buildDemoPages(selectedDocument, detail);

      if (!selectedGatewayPage || !pageContentQuery.data) return gatewayPages;

      const pageText =
        extractPageText(pageContentQuery.data.text) ||
        extractPageText(pageContentQuery.data.preview);
      const imageUrl = resolveGatewayAssetUrl(
        pageContentQuery.data.preview?.image_url ??
          pageContentQuery.data.preview?.preview_url,
      );

      return gatewayPages.map((page) =>
        page.pageNumber === selectedGatewayPage.pageNumber
          ? {
              ...page,
              lines: pageText ? pageText.split(/\r?\n/).filter(Boolean) : page.lines,
              imageUrl: imageUrl || page.imageUrl,
            }
          : page,
      );
    },
    [detail, gatewayPages, pageContentQuery.data, selectedDocument, selectedGatewayPage, workMode],
  );
  const selectedPreviewPage = previewPages[Math.min(previewPageIndex, Math.max(previewPages.length - 1, 0))] ?? null;
  const previewText = buildPreviewText(selectedDocument, detail, versions, historyRows, errors, parameters);
  const currentPreviewText = selectedPreviewPage?.lines.join('\n') ?? '';
  const compareVersions = versions.filter((version) => selectedVersionIds.includes(version.id)).slice(0, 2);
  const totalVersions = Number(detail?.total_versions ?? versions.length ?? 0);
  const selectedVersionRows = useMemo(
    () => versions.filter((version) => selectedVersionIds.includes(version.id)).slice(0, 2),
    [selectedVersionIds, versions],
  );
  const previewSearchMatchCount = useMemo(() => {
    const normalized = previewSearch.trim().toLowerCase();
    if (!normalized || !selectedPreviewPage) return 0;

    return currentPreviewText.toLowerCase().split(normalized).length - 1;
  }, [currentPreviewText, previewSearch]);

  useEffect(() => {
    if (versionsOpen && !versionSelectionTouched && !selectedVersionIds.length && versions.length) {
      setSelectedVersionIds(versions.slice(0, 2).map((version) => version.id));
    }
  }, [selectedVersionIds.length, versionSelectionTouched, versions, versionsOpen]);

  useEffect(() => {
    setPreviewOpen(false);
    setVersionsOpen(false);
    setPreviewPageIndex(0);
    setPreviewSearch('');
    setDownloadError('');
    setRegistryNotice('');
    setRegistryError('');
    setSelectedVersionIds([]);
    setVersionSelectionTouched(false);
    setActionsAnchorEl(null);
  }, [selectedDocumentId]);

  useEffect(() => {
    setValidFromDraft(normalizeText(detailRecord.valid_from ?? selectedDocument?.validFrom) || getTodayDateInput());
    const validUntil = normalizeText(detailRecord.valid_until ?? selectedDocument?.validUntil);
    setValidUntilDraft(validUntil === '9999-12-31' ? '' : validUntil);
  }, [detailRecord.valid_from, detailRecord.valid_until, selectedDocument?.validFrom, selectedDocument?.validUntil]);

  useEffect(() => {
    if (previewOpen && previewPages.length === 0) {
      setPreviewPageIndex(0);
    }
  }, [previewOpen, previewPages.length]);

  const summaryChips = [
    { label: `Версий: ${totalVersions}`, value: totalVersions },
    { label: `История: ${historyRows.length}`, value: historyRows.length },
    { label: `Ошибки: ${errors.length}`, value: errors.length },
    { label: `Страниц: ${previewPages.length}`, value: previewPages.length },
  ];
  const latestVersionRecord = (detailRecord.latest_version ?? {}) as Record<string, unknown>;
  const latestVersionId = getLatestVersionId(detailRecord, versions);
  const latestVersionLabel =
    normalizeText(latestVersionRecord.version ?? latestVersionRecord.version_number ?? latestVersionRecord.version_id) ||
    versions[0]?.label ||
    selectedDocument?.version;
  const businessKeyRows: Array<[string, unknown]> = [
    ['document_id', detailRecord.document_id ?? selectedDocument?.id],
    ['version_id', latestVersionId],
    ['title_key', detailRecord.title_key ?? selectedDocument?.titleKey],
    ['title_hash_sha256', detailRecord.title_hash_sha256 ?? selectedDocument?.titleHashSha256],
  ];
  const validityRows: Array<[string, unknown]> = [
    ['valid_from', detailRecord.valid_from ?? selectedDocument?.validFrom],
    ['valid_until', normalizeValidUntil(detailRecord.valid_until ?? selectedDocument?.validUntil)],
    ['validity_status', formatRegistryStatus(detailRecord.validity_status ?? selectedDocument?.validityStatus)],
    ['status', formatRegistryStatus(detailRecord.status ?? selectedDocument?.status)],
  ];
  const handleDownloadOriginal = async () => {
    if (!selectedDocument) return;

    setDownloadError('');
    try {
      try {
        const binaryResponse = await apiClient.get(`/documents/${selectedDocument.id}/file`, {
          params: { format: 'binary' },
          responseType: 'blob',
        });
        const contentType = normalizeText(binaryResponse.headers?.['content-type']).toLowerCase();
        const blob = binaryResponse.data instanceof Blob ? binaryResponse.data : new Blob([binaryResponse.data]);

        if (!contentType.includes('application/json')) {
          openBlobInNewTab(blob);
          return;
        }
      } catch (binaryError) {
        const status = (binaryError as { response?: { status?: number } })?.response?.status;
        if (status && ![404, 410, 501].includes(status)) {
          throw binaryError;
        }
      }

      const fileInfo = await documentsApi.file(selectedDocument.id);
      const rawFileUrl = fileInfo?.file_url ?? fileInfo?.url ?? fileInfo?.download_url;
      const fileUrl = resolveGatewayAssetUrl(rawFileUrl);
      const internalHost = getInternalServiceHost(rawFileUrl);

      if (!fileUrl) {
        throw new Error(
          internalHost
            ? `Сервер вернул внутреннюю ссылку ${internalHost}, но публичный proxy скачивания файлов не настроен.`
            : 'Сервер не передал публичную ссылку на файл.',
        );
      }

      const response = await apiClient.get(fileUrl, { responseType: 'blob' });
      const blob = response.data instanceof Blob ? response.data : new Blob([response.data]);
      openBlobInNewTab(blob);
    } catch (error) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      const serverMessage = await extractServerErrorMessage((error as { response?: { data?: unknown } })?.response?.data);
      setDownloadError(
        status === 404
          ? 'Сервер передал ссылку на файл, но файл по ней не найден (404).'
          : status === 410
            ? `Серверный proxy скачивания файлов отключен${serverMessage ? `: ${serverMessage}` : '.'}`
          : error instanceof Error
            ? error.message
            : 'Не удалось получить файл через сервер.',
      );
    }
  };

  const handleSaveValidity = async () => {
    if (!selectedDocument) return;

    setRegistryError('');
    setRegistryNotice('');

    if (validFromDraft && validUntilDraft && new Date(validFromDraft).getTime() > new Date(validUntilDraft).getTime()) {
      setRegistryError('Дата окончания не может быть раньше даты начала.');
      return;
    }

    try {
      await documentsApi.updateValidity(selectedDocument.id, {
        valid_from: validFromDraft || undefined,
        valid_until: validUntilDraft || null,
      });
      await queryClient.invalidateQueries({ queryKey: ['gateway-documents', workMode] });
      await queryClient.invalidateQueries({ queryKey: ['document-registry-detail', workMode, selectedDocument.id] });
      setRegistryNotice('Срок действия отправлен на сервер.');
    } catch (error) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      setRegistryError(
        status === 404
          ? 'Сервер не нашел документ в registry endpoint. Срок действия не сохранен.'
          : error instanceof Error
            ? error.message
            : 'Не удалось сохранить срок действия через сервер.',
      );
    }
  };

  const handleDeleteDocument = async () => {
    if (!selectedDocument) return;

    setRegistryError('');
    setRegistryNotice('');

    try {
      await documentsApi.archive(selectedDocument.id);
      setDeleteDialogOpen(false);
      setSelectedDocumentId('');
      await queryClient.invalidateQueries({ queryKey: ['gateway-documents', workMode] });
      setRegistryNotice('Документ удален на сервере.');
    } catch (error) {
      setRegistryError(error instanceof Error ? error.message : 'Не удалось удалить документ через сервер.');
    }
  };

  return (
    <Stack spacing={2.2}>
      <Paper variant="outlined" sx={{ p: 1.45, borderRadius: 3, ...panelSxFor(isLight) }}>
        <Stack spacing={1.2}>
          <Box sx={sectionHeaderSxFor(isLight)}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
              <Layers3 size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
              <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                Реестр документов
              </Typography>
            </Stack>
            <Chip size="small" label={`${filteredDocuments.length}`} variant="outlined" />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1fr) 180px 180px 170px' }, gap: 1 }}>
            <TextField
              fullWidth
              size="small"
              label="Поиск по реестру"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              slotProps={{
                input: {
                  startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.72 }} />,
                },
              }}
            />
            <TextField size="small" select label="Источник" value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
              <MenuItem value="all">Все источники</MenuItem>
              {sourceFilterOptions.map((source) => (
                <MenuItem key={source} value={source}>
                  {source}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              size="small"
              select
              label="Статус"
              value={validityFilter}
              onChange={(event) => setValidityFilter(event.target.value)}
            >
              <MenuItem value="all">Все статусы</MenuItem>
              {REGISTRY_STATUS_FILTER_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              size="small"
              type="date"
              label="Действует на"
              value={validAt}
              onChange={(event) => setValidAt(event.target.value)}
              slotProps={{
                inputLabel: { shrink: true },
                htmlInput: {
                  onClick: openNativeDatePicker,
                  onFocus: openNativeDatePicker,
                },
              }}
            />
          </Box>

          {workMode === 'prod' && detailQuery.isError && (
            <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
              Сервер не вернул сведения по выбранному документу.
            </Alert>
          )}
          {workMode === 'prod' && (versionsQuery.isError || historyQuery.isError || errorsQuery.isError || parametersQuery.isError || pagesQuery.isError) && (
            <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
              Часть данных реестра недоступна через сервер:{' '}
              {[
                versionsQuery.isError ? 'версии' : '',
                historyQuery.isError ? 'история' : '',
                errorsQuery.isError ? 'ошибки' : '',
                parametersQuery.isError ? 'параметры' : '',
                pagesQuery.isError ? 'страницы/preview' : '',
              ]
                .filter(Boolean)
                .join(', ')}
              .
            </Alert>
          )}

          {(registryError || registryNotice || downloadError) && (
            <Alert severity={registryError || downloadError ? 'warning' : 'success'} variant="outlined" sx={{ borderRadius: 2 }}>
              {registryError || downloadError || registryNotice}
            </Alert>
          )}

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', lg: 'minmax(520px, 1.08fr) minmax(400px, 0.92fr)' },
              gap: 1.4,
              alignItems: 'start',
            }}
          >
            <Paper variant="outlined" sx={{ p: 1, borderRadius: 2.2, ...tableSxFor(isLight) }}>
              <Stack spacing={1}>
                <TableContainer sx={{ maxHeight: 'calc(100vh - 245px)', minHeight: 520, overflow: 'auto' }}>
                  <Table
                    size="small"
                    stickyHeader
                    sx={{
                      tableLayout: 'fixed',
                      width: '100%',
                      '& .MuiTableCell-root': {
                        borderBottomColor: 'rgba(198, 214, 236, 0.14)',
                        py: 0.72,
                      },
                      '& .MuiTableHead-root .MuiTableCell-root': {
                        ...compactHeadSx,
                        bgcolor: isLight ? 'rgba(15, 23, 42, 0.035)' : 'rgba(255,255,255,0.025)',
                        borderBottom: '1px solid rgba(198, 214, 236, 0.24)',
                      },
                      '& .MuiTableBody-root .MuiTableRow-root:nth-of-type(odd)': {
                        bgcolor: 'rgba(255,255,255,0.012)',
                      },
                      borderCollapse: 'separate',
                      borderSpacing: '0 2px',
                    }}
                  >
                    <TableHead>
                      <TableRow>
                        <TableCell>Документ</TableCell>
                        <TableCell sx={{ width: 104 }}>Источник</TableCell>
                        <TableCell sx={{ width: 82 }}>Статус</TableCell>
                        <TableCell sx={{ width: 42 }} />
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredDocuments.map((document, index) => {
                        const selected = selectedDocument?.id === document.id;
                        const hasSelection = Boolean(selectedDocument);
                        const selectedBg = isLight ? 'rgba(14, 116, 144, 0.08)' : 'rgba(152, 217, 216, 0.08)';
                        const hoverBg = isLight ? 'rgba(14, 116, 144, 0.06)' : 'rgba(152, 217, 216, 0.06)';
                        const rowBg = selected ? selectedBg : index % 2 === 0 ? 'rgba(255,255,255,0.012)' : 'transparent';
                        return (
                          <TableRow
                            key={document.id}
                            hover
                            onClick={() => setSelectedDocumentId(document.id)}
                            sx={{
                              cursor: 'pointer',
                              opacity: hasSelection && !selected ? 0.48 : 1,
                              transition: 'opacity 160ms ease, background-color 160ms ease, border-color 160ms ease',
                              '& > .MuiTableCell-root': {
                                bgcolor: rowBg,
                                transition: 'background-color 160ms ease, border-color 160ms ease',
                              },
                              '&:hover > .MuiTableCell-root': {
                                bgcolor: hoverBg,
                              },
                              '&:hover': {
                                opacity: 1,
                              },
                              '& > .MuiTableCell-root:first-of-type': {
                                borderLeft: `3px solid ${
                                  selected ? (isLight ? 'rgba(2, 132, 199, 0.72)' : 'rgba(152, 217, 216, 0.72)') : 'transparent'
                                }`,
                                borderTopLeftRadius: 10,
                                borderBottomLeftRadius: 10,
                              },
                              '& > .MuiTableCell-root:last-of-type': {
                                borderTopRightRadius: 10,
                                borderBottomRightRadius: 10,
                              },
                            }}
                          >
                            <TableCell>
                              <Typography
                                title={document.name}
                                sx={{
                                  fontWeight: selected ? 620 : 540,
                                  lineHeight: 1.25,
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  maxWidth: '100%',
                                }}
                              >
                                {document.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {[document.docCode || document.id, document.version, formatCompactDateTime(document.updatedAt)].filter(Boolean).join(' · ')}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontSize: '0.78rem', lineHeight: 1.25 }}>
                                {document.sourceType || document.type}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {document.group || document.sectionId || 'категория не передана'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                size="small"
                                variant="outlined"
                                label={formatRegistryStatus(document.validityStatus || document.status || document.indexStatus)}
                                sx={{
                                  maxWidth: 78,
                                  '& .MuiChip-label': { px: 0.7, overflow: 'hidden', textOverflow: 'ellipsis' },
                                }}
                              />
                            </TableCell>
                            <TableCell sx={{ px: 0.4 }}>
                              <IconButton
                                size="small"
                                aria-label={`Действия с документом ${document.name}`}
                                onClick={(event) => {
                                  event.stopPropagation();
                                  setSelectedDocumentId(document.id);
                                  setActionsAnchorEl(event.currentTarget);
                                }}
                                sx={{ width: 28, height: 28 }}
                              >
                                <MoreVertical size={16} />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        );
                      })}

                      {filteredDocuments.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4} sx={{ py: 3, textAlign: 'center' }}>
                            <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                              По фильтру ничего не найдено.
                            </Alert>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Stack>
            </Paper>

            <Paper variant="outlined" sx={{ p: 1.15, borderRadius: 2.2, ...panelSxFor(isLight) }}>
              {selectedDocument ? (
                <Stack spacing={1.05}>
                  <Paper variant="outlined" sx={{ p: 1.05, borderRadius: 2.2, ...panelSxFor(isLight) }}>
                    <Stack spacing={1}>
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="Поиск по открытому документу"
                        value={previewSearch}
                        onChange={(event) => setPreviewSearch(event.target.value)}
                        slotProps={{
                          input: {
                            startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.72 }} />,
                            endAdornment: (
                              <IconButton size="small" aria-label="Развернуть предпросмотр" onClick={() => setPreviewOpen(true)} sx={{ width: 28, height: 28 }}>
                                <Maximize2 size={15} />
                              </IconButton>
                            ),
                          },
                        }}
                      />
                      {previewSearch.trim() && (
                        <Chip
                          size="small"
                          variant="outlined"
                          label={previewSearchMatchCount ? `${previewSearchMatchCount} совп.` : 'Нет совпадений'}
                          sx={{ width: 'fit-content' }}
                        />
                      )}
                      <Paper
                        variant="outlined"
                        sx={{
                          minHeight: 500,
                          maxHeight: 'calc(100vh - 315px)',
                          overflow: 'auto',
                          p: 2,
                          borderRadius: 2,
                          bgcolor: '#f4f1e8',
                          color: '#202020',
                          fontFamily: 'Georgia, serif',
                        }}
                      >
                        {selectedPreviewPage ? (
                          <Stack spacing={1}>
                            {selectedPreviewPage.imageUrl && (
                              <Box
                                component="img"
                                src={selectedPreviewPage.imageUrl}
                                alt={`${selectedDocument.name}, страница ${selectedPreviewPage.pageNumber}`}
                                sx={{ width: '100%', height: 'auto', display: 'block' }}
                              />
                            )}
                            {currentPreviewText ? (
                              <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.7, fontFamily: 'inherit' }}>
                                {renderHighlightedText(currentPreviewText, previewSearch.trim(), isLight)}
                              </Typography>
                            ) : (
                              <Typography color="text.secondary">
                                Страница существует, но сервер не передал доступное изображение или текстовый слой.
                              </Typography>
                            )}
                          </Stack>
                        ) : (
                          <Typography color="text.secondary">
                            Сервер не передал список страниц документа.
                          </Typography>
                        )}
                      </Paper>
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<ChevronLeft size={16} />}
                          onClick={() => setPreviewPageIndex((current) => Math.max(current - 1, 0))}
                          disabled={previewPageIndex === 0 || previewPages.length === 0}
                        >
                          Назад
                        </Button>
                        <Typography variant="caption" color="text.secondary">
                          Страница {previewPages.length ? previewPageIndex + 1 : 0} из {previewPages.length}
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          endIcon={<ChevronRight size={16} />}
                          onClick={() => setPreviewPageIndex((current) => Math.min(current + 1, previewPages.length - 1))}
                          disabled={previewPages.length === 0 || previewPageIndex >= previewPages.length - 1}
                        >
                          Вперед
                        </Button>
                      </Stack>
                    </Stack>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSxFor(isLight) }}>
                    <Button
                      fullWidth
                      onClick={() => setValidityOpen((current) => !current)}
                      endIcon={validityOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      sx={{ justifyContent: 'space-between', px: 1.2, py: 0.9, color: 'text.primary', textTransform: 'none' }}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                        <Typography sx={{ fontWeight: 560 }}>Срок действия</Typography>
                        <Chip size="small" variant="outlined" label={normalizeValidUntil(validUntilDraft) || 'бессрочно'} />
                      </Stack>
                    </Button>
                    <Divider sx={{ borderColor: 'rgba(198,214,236,0.16)' }} />
                    <Collapse in={validityOpen}>
                      <Stack spacing={1} sx={{ p: 1.1 }}>
                        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 1 }}>
                          <TextField
                            size="small"
                            type="date"
                            label="Действует с"
                            value={validFromDraft}
                            onChange={(event) => setValidFromDraft(event.target.value)}
                            slotProps={{
                              inputLabel: { shrink: true },
                              htmlInput: {
                                onClick: openNativeDatePicker,
                                onFocus: openNativeDatePicker,
                              },
                            }}
                          />
                          <TextField
                            size="small"
                            type="date"
                            label="Действует до"
                            value={validUntilDraft}
                            onChange={(event) => setValidUntilDraft(event.target.value)}
                            slotProps={{
                              inputLabel: { shrink: true },
                              htmlInput: {
                                onClick: openNativeDatePicker,
                                onFocus: openNativeDatePicker,
                              },
                            }}
                            helperText="Пусто = бессрочно"
                          />
                        </Box>
                        <Box
                          sx={{
                            display: 'grid',
                            gridTemplateColumns: { xs: '1fr', sm: '0.55fr 1fr 0.55fr 1fr' },
                            gap: 0.8,
                            alignItems: 'baseline',
                          }}
                        >
                          {[
                            ['Статус', formatRegistryStatus(detailRecord.status ?? selectedDocument.status)],
                            ['Действие', formatRegistryStatus(detailRecord.validity_status ?? selectedDocument.validityStatus)],
                            ['Обновлен', formatCompactDateTime(selectedDocument.updatedAt)],
                          ].map(([label, value]) => (
                            <React.Fragment key={label}>
                              <Typography sx={detailLabelSx}>{label}</Typography>
                              <Typography sx={detailValueSx}>{displayValue(value)}</Typography>
                            </React.Fragment>
                          ))}
                        </Box>
                        <Box>
                          <Button size="small" variant="outlined" startIcon={<Save size={15} />} onClick={() => void handleSaveValidity()}>
                            Сохранить срок
                          </Button>
                        </Box>
                      </Stack>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSxFor(isLight) }}>
                    <Button
                      fullWidth
                      onClick={() => setMetadataOpen((current) => !current)}
                      endIcon={metadataOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      sx={{ justifyContent: 'space-between', px: 1.2, py: 0.9, color: 'text.primary', textTransform: 'none' }}
                    >
                      <Typography sx={{ fontWeight: 560 }}>Метаданные и статусы</Typography>
                    </Button>
                    <Divider sx={{ borderColor: 'rgba(198,214,236,0.16)' }} />
                    <Collapse in={metadataOpen}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '0.7fr 1fr 0.7fr 1fr' },
                          gap: 0.8,
                          p: 1.1,
                        }}
                      >
                        {[
                          ['Название', detailRecord.title ?? selectedDocument.name],
                          ['Код', detailRecord.doc_code ?? selectedDocument.docCode],
                          ['Тип источника', detailRecord.source_type ?? selectedDocument.sourceType ?? selectedDocument.type],
                          ['Юрисдикция', detailRecord.jurisdiction],
                          ['Издатель', detailRecord.issuing_body],
                          ['OCR', selectedDocument.ocrStatus],
                          ['Индекс', selectedDocument.indexStatus],
                          ['Точность', typeof parameters?.extraction_confidence === 'number' ? `${Math.round(parameters.extraction_confidence * 100)}%` : 'не передано'],
                        ].map(([label, value]) => (
                          <React.Fragment key={label}>
                            <Typography sx={detailLabelSx}>
                              {label}
                            </Typography>
                            <Typography sx={detailValueSx}>
                              {displayValue(value)}
                            </Typography>
                          </React.Fragment>
                        ))}
                      </Box>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSxFor(isLight) }}>
                    <Button
                      fullWidth
                      onClick={() => setTechnicalOpen((current) => !current)}
                      endIcon={technicalOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      sx={{ justifyContent: 'space-between', px: 1.2, py: 0.9, color: 'text.primary', textTransform: 'none' }}
                    >
                      <Typography sx={{ fontWeight: 560 }}>Технические сведения</Typography>
                    </Button>
                    <Divider sx={{ borderColor: 'rgba(198,214,236,0.16)' }} />
                    <Collapse in={technicalOpen}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '0.7fr 1fr 0.7fr 1fr' },
                          gap: 0.8,
                          p: 1.1,
                        }}
                      >
                        {[...businessKeyRows, ...validityRows, ['версий', totalVersions], ['страниц', previewPages.length], ['ошибок', errors.length]].map(
                          ([label, value]) => (
                            <React.Fragment key={label}>
                              <Typography sx={detailLabelSx}>
                                {label}
                              </Typography>
                              <Typography sx={detailValueSx}>
                                {displayValue(value)}
                              </Typography>
                            </React.Fragment>
                          ),
                        )}
                      </Box>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSxFor(isLight) }}>
                    <Button
                      fullWidth
                      onClick={() => setHistoryOpen((current) => !current)}
                      endIcon={historyOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      sx={{ justifyContent: 'space-between', px: 1.2, py: 0.9, color: 'text.primary', textTransform: 'none' }}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                        <History size={16} color={isLight ? '#0284c7' : '#98d9d8'} />
                        <Typography sx={{ fontWeight: 560 }}>История и ошибки</Typography>
                        <Chip size="small" variant="outlined" label={historyRows.length + errors.length} />
                      </Stack>
                    </Button>
                    <Divider sx={{ borderColor: 'rgba(198,214,236,0.16)' }} />
                    <Collapse in={historyOpen}>
                      <Stack spacing={0.5} sx={{ p: 1.1 }}>
                        {historyRows.slice(0, 6).map((item) => (
                          <Box
                            key={item.id}
                            sx={{
                              display: 'grid',
                              gridTemplateColumns: { xs: '1fr', md: '110px 1fr 1fr' },
                              gap: 1,
                              py: 0.55,
                              borderBottom: '1px solid rgba(198,214,236,0.1)',
                            }}
                          >
                            <Typography sx={detailLabelSx}>
                              {formatCompactDateTime(item.at)}
                            </Typography>
                            <Typography sx={detailValueSx}>
                              {item.action}
                            </Typography>
                            <Typography sx={{ ...detailValueSx, color: 'text.secondary' }}>
                              {item.note}
                            </Typography>
                          </Box>
                        ))}
                        {errors.length > 0 && (
                          <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                            Последняя ошибка: {(errors[0] as any)?.error_message ?? 'Сервер вернул список ошибок.'}
                          </Alert>
                        )}
                        {!historyRows.length && !errors.length && (
                          <Typography variant="body2" color="text.secondary">
                            История и ошибки по документу не переданы сервером.
                          </Typography>
                        )}
                      </Stack>
                    </Collapse>
                  </Paper>

                  <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                    {summaryChips.map((item) => (
                      <Chip key={item.label} label={item.label} size="small" variant="outlined" />
                    ))}
                  </Stack>
                </Stack>
              ) : (
                <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                  Выберите документ в списке слева.
                </Alert>
              )}
            </Paper>
          </Box>
          <Menu
            anchorEl={actionsAnchorEl}
            open={Boolean(actionsAnchorEl)}
            onClose={() => setActionsAnchorEl(null)}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          >
            <MenuItem
              onClick={() => {
                setActionsAnchorEl(null);
                void handleDownloadOriginal();
              }}
            >
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <Download size={15} />
                <span>Скачать</span>
              </Stack>
            </MenuItem>
            <MenuItem
              onClick={() => {
                setActionsAnchorEl(null);
                setVersionsOpen(true);
              }}
            >
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <FileText size={15} />
                <span>Версии</span>
              </Stack>
            </MenuItem>
            <MenuItem
              className="app-danger-menu-item"
              onClick={() => {
                setActionsAnchorEl(null);
                setDeleteDialogOpen(true);
              }}
              sx={{ color: 'error.main' }}
            >
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <Trash2 size={15} />
                <span>Удалить</span>
              </Stack>
            </MenuItem>
          </Menu>
        </Stack>
      </Paper>

      <Dialog open={previewOpen && Boolean(selectedDocument)} onClose={() => setPreviewOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ pb: 1.2 }}>
          <Stack direction="row" spacing={1.2} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontWeight: 600, lineHeight: 1.2 }}>Предпросмотр документа</Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedDocument?.name ?? 'Документ'} · лист {previewPages.length ? previewPageIndex + 1 : 0} из {previewPages.length}
              </Typography>
            </Box>
            <IconButton aria-label="Закрыть предпросмотр" onClick={() => setPreviewOpen(false)} size="small">
              <X size={18} />
            </IconButton>
          </Stack>
        </DialogTitle>
        <DialogContent dividers sx={{ bgcolor: isLight ? '#f6f7f8' : 'rgba(8, 12, 18, 0.34)' }}>
          <Stack spacing={2}>
            <TextField
              fullWidth
              size="small"
              label="Поиск по открытому документу"
              value={previewSearch}
              onChange={(event) => setPreviewSearch(event.target.value)}
              placeholder="Слово или фраза"
              slotProps={{
                input: {
                  startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.72 }} />,
                },
              }}
            />
            {previewSearch.trim() && (
              <Chip size="small" variant="outlined" label={previewSearchMatchCount ? `${previewSearchMatchCount} совп.` : 'Нет совпадений'} sx={{ width: 'fit-content' }} />
            )}

            <Paper
              variant="outlined"
              sx={{
                minHeight: '56vh',
                p: 3,
                borderRadius: 2.4,
                bgcolor: '#f4f1e8',
                color: '#202020',
                fontFamily: 'Georgia, serif',
              }}
            >
              {selectedPreviewPage ? (
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="caption" sx={{ color: '#777' }}>
                      {selectedPreviewPage.title}
                    </Typography>
                    <Typography variant="h5" sx={{ mt: 0.8, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                      {selectedDocument?.name}
                    </Typography>
                  </Box>
                  {selectedPreviewPage.imageUrl && (
                    <Box
                      component="img"
                      src={selectedPreviewPage.imageUrl}
                      alt={`${selectedDocument?.name ?? 'Документ'}, страница ${selectedPreviewPage.pageNumber}`}
                      sx={{ width: '100%', height: 'auto', display: 'block' }}
                    />
                  )}
                  {currentPreviewText ? (
                    <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.75, fontFamily: 'inherit' }}>
                      {renderHighlightedText(currentPreviewText, previewSearch.trim(), isLight)}
                    </Typography>
                  ) : (
                    <Typography color="text.secondary">
                      Страница существует, но сервер не передал доступное изображение или текстовый слой.
                    </Typography>
                  )}
                </Stack>
              ) : (
                <Typography color="text.secondary">Сервер не передал список страниц документа.</Typography>
              )}
            </Paper>

            <Stack direction="row" spacing={1} sx={{ justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  onClick={() => setPreviewPageIndex((current) => Math.max(current - 1, 0))}
                disabled={previewPageIndex === 0 || previewPages.length === 0}
                >
                Назад
              </Button>
              <Typography variant="caption" color="text.secondary">
                Страница {previewPages.length ? previewPageIndex + 1 : 0} из {previewPages.length}
              </Typography>
              <Button
                  variant="outlined"
                  onClick={() => setPreviewPageIndex((current) => Math.min(current + 1, previewPages.length - 1))}
                disabled={previewPages.length === 0 || previewPageIndex >= previewPages.length - 1}
                >
                Вперед
              </Button>
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          {selectedDocument && (
            <Button
              startIcon={<Download size={16} />}
              onClick={() => downloadPreviewFile(selectedDocument.name, previewText, 'txt')}
            >
              Скачать срез
            </Button>
          )}
          <Button onClick={() => setPreviewOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteDialogOpen && Boolean(selectedDocument)} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Удалить документ</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.2}>
            <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
              Удаление отправляется на сервер через DELETE /documents/{selectedDocument?.id}. Ожидается, что backend удалит документ и связанные данные.
            </Alert>
            <Typography variant="body2" color="text.secondary">
              Документ: {selectedDocument?.name}
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Отмена</Button>
          <Button color="error" variant="contained" startIcon={<Trash2 size={16} />} onClick={() => void handleDeleteDocument()}>
            Удалить документ
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={versionsOpen && Boolean(selectedDocument)} onClose={() => setVersionsOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ pb: 1.2 }}>
          <Stack direction="row" spacing={1.2} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontWeight: 600, lineHeight: 1.2 }}>Версии документа</Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedDocument?.name ?? 'Документ'} · выберите 2 версии для сравнения
              </Typography>
            </Box>
            <IconButton aria-label="Закрыть версии" onClick={() => setVersionsOpen(false)} size="small">
              <X size={18} />
            </IconButton>
          </Stack>
        </DialogTitle>
        <DialogContent dividers sx={{ bgcolor: isLight ? '#f6f7f8' : 'rgba(8, 12, 18, 0.34)' }}>
          <Stack spacing={2}>
            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2.2, ...tableSxFor(isLight) }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell />
                    <TableCell>Версия</TableCell>
                    <TableCell>Дата</TableCell>
                    <TableCell>Автор</TableCell>
                    <TableCell>Размер</TableCell>
                    <TableCell>Статус</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {versions.map((version) => {
                    const checked = selectedVersionIds.includes(version.id);
                    return (
                      <TableRow key={version.id} hover selected={checked}>
                        <TableCell padding="checkbox">
                          <Checkbox
                            size="small"
                            checked={checked}
                            onChange={(event) => {
                              const isChecked = event.target.checked;
                              setVersionSelectionTouched(true);
                              setSelectedVersionIds((current) => {
                                if (isChecked) {
                                  return Array.from(new Set([...current, version.id])).slice(0, 2);
                                }
                                return current.filter((item) => item !== version.id);
                              });
                            }}
                          />
                        </TableCell>
                        <TableCell>{version.label}</TableCell>
                        <TableCell>{version.createdAt}</TableCell>
                        <TableCell>{version.author}</TableCell>
                        <TableCell>{version.size}</TableCell>
                        <TableCell>{version.status}</TableCell>
                      </TableRow>
                    );
                  })}
                  {versions.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} sx={{ py: 3, textAlign: 'center' }}>
                        <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                          Версии не получены.
                        </Alert>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {compareVersions.length === 2 ? (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' },
                  gap: 1.5,
                }}
              >
                {compareVersions.map((version, index) => (
                  <Paper key={version.id} variant="outlined" sx={{ p: 1.25, borderRadius: 2.2, ...panelSxFor(isLight) }}>
                    <Typography variant="caption" color="text.secondary">
                      Версия {index + 1}
                    </Typography>
                    <Typography sx={{ fontWeight: 560, mt: 0.25 }}>{version.label}</Typography>
                    <Stack spacing={0.45} sx={{ mt: 0.8 }}>
                      <Typography variant="body2" color="text.secondary">
                        Дата: {version.createdAt}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Автор: {version.author}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Размер: {version.size}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Статус: {version.status}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Комментарий: {version.note}
                      </Typography>
                    </Stack>
                  </Paper>
                ))}
              </Box>
            ) : (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                Отметьте две версии, чтобы показать сравнение.
              </Alert>
            )}

            <Paper variant="outlined" sx={{ p: 1.25, borderRadius: 2.2, ...panelSxFor(isLight) }}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.8 }}>
                <Layers3 size={16} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Typography sx={{ fontWeight: 560 }}>Краткий срез</Typography>
              </Stack>
              <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.65, fontFamily: 'inherit' }}>
                {previewText}
              </Typography>
            </Paper>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVersionsOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};
