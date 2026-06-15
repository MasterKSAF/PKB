import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Collapse,
  Divider,
  LinearProgress,
  MenuItem,
  IconButton,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  CheckCircle2,
  Download,
  FileDown,
  FilePlus2,
  FileSearch,
  FileText,
  FolderInput,
  Maximize2,
  PlayCircle,
  RotateCw,
  ShieldCheck,
  XCircle,
  X,
} from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useUIStore } from '../store/uiStore';
import { adminApi, draftsApi, documentsApi } from '../utils/http';
import { downloadPreviewFile } from '../utils/downloadPreview';
import { MOCK_DOCUMENTS, MOCK_PROCESSING_LOGS, MOCK_PROCESSING_QUEUE } from '../utils/mockData';

type DraftStatus = 'uploaded' | 'previewing' | 'ready_for_approve' | 'approved' | 'discarded' | 'failed';

type DraftPreview = {
  docCode: string;
  title: string;
  documentType: string;
  year: string;
  revision: string | null;
};

type PreviewPage = {
  title: string;
  lines: string[];
};

type DraftDuplicate = {
  title: string;
  reason: string;
  similarity: number;
};

type DraftSort = 'updated_desc' | 'name_asc' | 'status';
type MetadataReviewStatus = 'manual' | 'extracted' | 'review' | 'empty';

type DraftItem = {
  id: string;
  fileName: string;
  title: string;
  sourceType: string;
  docCode: string;
  mksOksCode: string;
  okstuCode: string;
  era: string;
  jurisdiction: string;
  issuingBody: string;
  status: DraftStatus;
  progress: number;
  confidence: number;
  preview: DraftPreview | null;
  duplicates: DraftDuplicate[];
  createdAt: string;
  updatedAt: string;
  note?: string;
  gatewayTaskId?: string;
  gatewayVersionId?: string;
  gatewayDraftId?: string;
  gatewayDocumentKey?: string;
  gatewayFileHashSha256?: string;
  gatewayTitleHashSha256?: string;
  gatewayPromotedDocumentId?: string | null;
  gatewayErrorCode?: string | null;
  gatewayErrorMessage?: string | null;
  gatewayRawData?: unknown;
};

type DraftForm = {
  title: string;
  sourceType: string;
  docCode: string;
  mksOksCode: string;
  okstuCode: string;
  era: string;
  jurisdiction: string;
  issuingBody: string;
};

const SOURCE_TYPE_OPTIONS = ['GOST', 'GOST_R', 'OST', 'RD', 'TU', 'ISO', 'DNV', 'ASTM', 'OTHER'];
const ERA_OPTIONS = ['USSR', 'CIS', 'RF', 'CURRENT'];
const JURISDICTION_OPTIONS = ['RU', 'EU', 'US', 'NO', 'INTL'];
const DRAFT_DOCUMENT_KEYS_STORAGE = 'pkb_gateway_draft_document_keys_v1';

const PANEL_SX = {
  bgcolor: 'rgba(22, 23, 27, 0.72)',
  borderColor: 'rgba(198, 216, 240, 0.34)',
  borderWidth: 1.5,
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
} as const;

const TABLE_SX = {
  borderRadius: 3,
  bgcolor: 'rgba(7, 14, 22, 0.94)',
  borderWidth: 1.5,
  borderColor: 'rgba(198, 216, 240, 0.52)',
  boxShadow:
    '0 0 0 1px rgba(198, 216, 240, 0.32), 0 0 0 3px rgba(102, 142, 198, 0.14), inset 0 1px 0 rgba(255,255,255,0.03)',
} as const;

const createDemoDrafts = (): DraftItem[] => [
  {
    id: 'draft-demo-1',
    fileName: 'gost_2_103_2013.pdf',
    title: 'ГОСТ 2.103-2013',
    sourceType: 'GOST',
    docCode: '2.103-2013',
    mksOksCode: '47.020',
    okstuCode: '750000',
    era: 'CURRENT',
    jurisdiction: 'RU',
    issuingBody: 'Росстандарт',
    status: 'ready_for_approve',
    progress: 72,
    confidence: 0.94,
    preview: {
      docCode: 'ГОСТ 2.103-2013',
      title: 'ЕСКД. Стадии разработки',
      documentType: 'normative',
      year: '2013',
      revision: '1',
    },
    duplicates: [
      {
        title: 'ГОСТ 2.103-2011',
        reason: 'похожее наименование и совпадающий код',
        similarity: 0.82,
      },
    ],
    createdAt: '12:04',
    updatedAt: '12:11',
    note: 'Предпросмотр готов, можно принять в базу знаний.',
  },
  {
    id: 'draft-demo-2',
    fileName: 'spec_21900m2_362135_0903.pdf',
    title: 'Спецификация 21900M2.362135.0903',
    sourceType: 'RD',
    docCode: '21900M2.362135.0903',
    mksOksCode: '47.060',
    okstuCode: '775000',
    era: 'RF',
    jurisdiction: 'RU',
    issuingBody: 'КБ проекта 21900М2',
    status: 'previewing',
    progress: 46,
    confidence: 0.76,
    preview: null,
    duplicates: [],
    createdAt: '12:18',
    updatedAt: '12:19',
    note: 'Идёт первичный предпросмотр.',
  },
  {
    id: 'draft-demo-3',
    fileName: 'archive_scan_rko.tiff',
    title: 'Архивный скан РКО',
    sourceType: 'OTHER',
    docCode: 'RKO-ARCHIVE',
    mksOksCode: '',
    okstuCode: '',
    era: 'CIS',
    jurisdiction: 'RU',
    issuingBody: 'Архив',
    status: 'uploaded',
    progress: 18,
    confidence: 0.0,
    preview: null,
    duplicates: [],
    createdAt: '12:35',
    updatedAt: '12:35',
    note: 'Файл загружен, предпросмотр еще не запускался.',
  },
];

const getStatusLabel = (status: DraftStatus) => {
  switch (status) {
    case 'uploaded':
      return 'Загружен';
    case 'previewing':
      return 'Предпросмотр';
    case 'ready_for_approve':
      return 'Нужна проверка';
    case 'approved':
      return 'Принят';
    case 'discarded':
      return 'Отклонён';
    case 'failed':
      return 'Ошибка';
    default:
      return status;
  }
};

const getStatusColor = (status: DraftStatus) => {
  switch (status) {
    case 'approved':
      return 'success';
    case 'ready_for_approve':
      return 'info';
    case 'previewing':
      return 'warning';
    case 'discarded':
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

const getQueueColor = (status: string) => {
  if (status === 'в работе') return 'warning';
  if (status === 'в очереди') return 'default';
  if (status === 'ошибка') return 'error';
  return 'success';
};

const buildPreviewPages = (draft: DraftItem): PreviewPage[] => {
  const preview = draft.preview;
  const previewStatusLine = preview
    ? `Предпросмотр: готов`
    : draft.status === 'previewing'
      ? 'Предпросмотр: выполняется'
      : 'Предпросмотр: не запущен';

  return [
    {
      title: 'Краткий срез',
      lines: [
        draft.title,
        `Файл: ${draft.fileName}`,
        'Источник: локальный файл',
        `Статус: ${getStatusLabel(draft.status)}`,
        previewStatusLine,
      ],
    },
    {
      title: 'Метаданные',
      lines: [
        `Код: ${draft.docCode || 'не указан'}`,
        `Тип источника: ${draft.sourceType}`,
        `МКС / ОКС: ${draft.mksOksCode || 'не указан'}`,
        `ОКСТУ: ${draft.okstuCode || 'не указан'}`,
        `Юрисдикция: ${draft.jurisdiction}`,
        `Эра: ${draft.era}`,
        `Издатель: ${draft.issuingBody || 'не указан'}`,
      ],
    },
    {
      title: 'Проверка',
      lines: [
        preview ? `Предпросмотр готов: ${preview.title}` : 'Предпросмотр еще не создан.',
        preview ? `Год: ${preview.year}` : 'Сначала запустите предпросмотр черновика.',
        preview ? `Редакция: ${preview.revision ?? 'не указана'}` : 'После проверки здесь появится сводка.',
        draft.duplicates.length ? `Похожих документов: ${draft.duplicates.length}` : 'Похожих документов не найдено.',
        draft.note ? `Комментарий: ${draft.note}` : 'Комментарий по черновику отсутствует.',
      ],
    },
  ];
};

const buildDocumentPreviewText = (draft: DraftItem) =>
  [
    draft.title,
    `Файл: ${draft.fileName}`,
    'Источник: локальный файл',
    `Статус: ${getStatusLabel(draft.status)}`,
    `Тип источника: ${draft.sourceType}`,
    `Код: ${draft.docCode || 'не указан'}`,
    `МКС / ОКС: ${draft.mksOksCode || 'не указан'}`,
    `ОКСТУ: ${draft.okstuCode || 'не указан'}`,
    `Юрисдикция: ${draft.jurisdiction}`,
    `Эра: ${draft.era}`,
    `Издатель: ${draft.issuingBody || 'не указан'}`,
    draft.preview ? `Предпросмотр: ${draft.preview.title}` : 'Предпросмотр еще не создан.',
    draft.note ? `Комментарий: ${draft.note}` : '',
  ]
    .filter(Boolean)
    .join('\n');

const getMetadataStatusLabel = (status: MetadataReviewStatus) => {
  if (status === 'review') return 'требует проверки';
  if (status === 'extracted') return 'извлечено системой';
  if (status === 'manual') return 'указано вручную';
  return 'не заполнено';
};

const getMetadataStatusColor = (status: MetadataReviewStatus) => {
  if (status === 'review') return 'warning';
  if (status === 'extracted') return 'success';
  if (status === 'manual') return 'info';
  return 'default';
};

const resolveMetadataStatus = (manual?: string | null, extracted?: string | null): MetadataReviewStatus => {
  const manualValue = String(manual ?? '').trim();
  const extractedValue = String(extracted ?? '').trim();

  if (manualValue && extractedValue && manualValue.toLowerCase() !== extractedValue.toLowerCase()) return 'review';
  if (extractedValue) return 'extracted';
  if (manualValue) return 'manual';
  return 'empty';
};

const buildMetadataReviewRows = (draft: DraftItem) => [
  {
    label: 'Название',
    manual: draft.title,
    extracted: draft.preview?.title,
    status: resolveMetadataStatus(draft.title, draft.preview?.title),
  },
  {
    label: 'Код документа',
    manual: draft.docCode,
    extracted: draft.preview?.docCode,
    status: resolveMetadataStatus(draft.docCode, draft.preview?.docCode),
  },
  {
    label: 'Тип источника',
    manual: draft.sourceType,
    extracted: draft.preview?.documentType,
    status: resolveMetadataStatus(draft.sourceType, draft.preview?.documentType),
  },
  {
    label: 'Год',
    manual: draft.era,
    extracted: draft.preview?.year,
    status: resolveMetadataStatus(draft.era, draft.preview?.year),
  },
];

const sortDrafts = (items: DraftItem[], sort: DraftSort) => {
  const statusRank: Record<DraftStatus, number> = {
    ready_for_approve: 0,
    previewing: 1,
    uploaded: 2,
    approved: 3,
    discarded: 4,
    failed: 5,
  };

  const compareUpdated = (left: DraftItem, right: DraftItem) =>
    new Date(right.updatedAt || 0).getTime() - new Date(left.updatedAt || 0).getTime();

  const compareName = (left: DraftItem, right: DraftItem) => left.title.localeCompare(right.title, 'ru');

  const compareStatus = (left: DraftItem, right: DraftItem) =>
    (statusRank[left.status] ?? 99) - (statusRank[right.status] ?? 99) ||
    compareUpdated(left, right) ||
    compareName(left, right);

  return [...items].sort((left, right) => {
    if (sort === 'name_asc') return compareName(left, right);
    if (sort === 'status') return compareStatus(left, right);
    return compareUpdated(left, right);
  });
};

const nextClock = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const createIdempotencyKey = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `draft-${Date.now()}-${Math.random().toString(36).slice(2)}`;

const readStoredDraftDocumentKeys = () => {
  if (typeof window === 'undefined') return [];

  try {
    const parsed = JSON.parse(window.localStorage.getItem(DRAFT_DOCUMENT_KEYS_STORAGE) ?? '[]');
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string' && Boolean(item)) : [];
  } catch {
    return [];
  }
};

const writeStoredDraftDocumentKeys = (keys: string[]) => {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(DRAFT_DOCUMENT_KEYS_STORAGE, JSON.stringify(Array.from(new Set(keys)).slice(0, 80)));
};

const draftProgressByStatus: Record<DraftStatus, number> = {
  uploaded: 14,
  previewing: 38,
  ready_for_approve: 72,
  approved: 100,
  discarded: 100,
  failed: 100,
};

const normalizeDraftStatusFromGateway = (status?: string): DraftStatus => {
  const normalized = String(status ?? '').toLowerCase();
  if (normalized === 'preview_ready' || normalized === 'ready_for_approve') return 'ready_for_approve';
  if (normalized === 'previewing' || normalized === 'uploaded') return normalized as DraftStatus;
  if (normalized === 'new') return 'uploaded';
  if (normalized === 'promoted') return 'approved';
  if (normalized === 'approved') return 'approved';
  if (normalized === 'discarded') return 'discarded';
  if (normalized === 'failed' || normalized === 'error') return 'failed';
  return 'uploaded';
};

const mapGatewayPreviewMetadata = (payload: any): DraftPreview | null => {
  const preview = payload?.preview_metadata ?? payload?.preview ?? null;
  if (!preview) return null;

  return {
    docCode: String(preview.doc_code ?? preview.docCode ?? payload?.doc_code ?? payload?.docCode ?? ''),
    title: String(preview.title ?? payload?.title ?? ''),
    documentType: String(preview.document_type ?? preview.documentType ?? 'normative'),
    year: String(preview.year ?? payload?.year ?? ''),
    revision: preview.revision ?? payload?.revision ?? null,
  };
};

const mapGatewayDuplicates = (payload: any): DraftDuplicate[] => {
  const duplicates = Array.isArray(payload?.duplicates) ? payload.duplicates : [];
  return duplicates.map((duplicate: any) => ({
    title: String(duplicate.title ?? duplicate.document_title ?? duplicate.document_id ?? 'Похожий документ'),
    reason: String(duplicate.reason ?? duplicate.message ?? 'Похожее содержание'),
    similarity: typeof duplicate.similarity === 'number' ? duplicate.similarity : Number(duplicate.score ?? 0),
  }));
};

const mapGatewayDraftRecordToUi = (payload: any, fallback?: Partial<DraftItem>): DraftItem => {
  const status = normalizeDraftStatusFromGateway(payload?.status ?? fallback?.status);
  const preview = mapGatewayPreviewMetadata(payload) ?? fallback?.preview ?? null;
  const duplicates = mapGatewayDuplicates(payload);
  const progress = draftProgressByStatus[status] ?? fallback?.progress ?? 0;
  const confidence = payload?.confidence ?? fallback?.confidence ?? 0;
  const createdAt = payload?.created_at ?? payload?.createdAt ?? fallback?.createdAt ?? nextClock();
  const updatedAt = payload?.updated_at ?? payload?.updatedAt ?? fallback?.updatedAt ?? createdAt;

  return {
    id: String(fallback?.id ?? payload?.draft_id ?? payload?.id ?? `draft-${Date.now()}`),
    fileName: fallback?.fileName ?? payload?.filename ?? payload?.file_name ?? payload?.title ?? 'Документ',
    title: fallback?.title ?? payload?.title ?? payload?.preview_metadata?.title ?? payload?.filename ?? 'Документ',
    sourceType: fallback?.sourceType ?? payload?.source_type ?? 'OTHER',
    docCode: fallback?.docCode ?? payload?.doc_code ?? payload?.preview_metadata?.doc_code ?? '',
    mksOksCode: fallback?.mksOksCode ?? payload?.mks_oks_code ?? '',
    okstuCode: fallback?.okstuCode ?? payload?.okstu_code ?? '',
    era: fallback?.era ?? payload?.era ?? 'CURRENT',
    jurisdiction: fallback?.jurisdiction ?? payload?.jurisdiction ?? 'RU',
    issuingBody: fallback?.issuingBody ?? payload?.issuing_body ?? '',
    status,
    progress,
    confidence: Number(confidence ?? 0),
    preview,
    duplicates: duplicates.length ? duplicates : fallback?.duplicates ?? [],
    createdAt,
    updatedAt,
    note: fallback?.note ?? payload?.message ?? '',
    gatewayTaskId: String(payload?.task_id ?? payload?.taskId ?? fallback?.gatewayTaskId ?? ''),
    gatewayVersionId: String(payload?.version_id ?? payload?.versionId ?? fallback?.gatewayVersionId ?? ''),
    gatewayDraftId: String(payload?.draft_id ?? payload?.draftId ?? fallback?.gatewayDraftId ?? ''),
    gatewayDocumentKey: String(payload?.document_key ?? payload?.documentKey ?? fallback?.gatewayDocumentKey ?? ''),
    gatewayFileHashSha256: String(payload?.file_hash_sha256 ?? payload?.fileHashSha256 ?? fallback?.gatewayFileHashSha256 ?? ''),
    gatewayTitleHashSha256: String(payload?.title_hash_sha256 ?? payload?.titleHashSha256 ?? fallback?.gatewayTitleHashSha256 ?? ''),
    gatewayPromotedDocumentId:
      payload?.document_id ??
      payload?.promoted_document_id ??
      payload?.approved_document_id ??
      fallback?.gatewayPromotedDocumentId ??
      null,
    gatewayErrorCode: payload?.error_code ?? fallback?.gatewayErrorCode ?? null,
    gatewayErrorMessage: payload?.error_message ?? fallback?.gatewayErrorMessage ?? null,
    gatewayRawData: payload?.raw_data ?? fallback?.gatewayRawData ?? null,
  };
};

const draftPatchFromGateway = (payload: any, fallback?: Partial<DraftItem>): Partial<DraftItem> => {
  const normalized = mapGatewayDraftRecordToUi(payload, fallback);

  return {
    fileName: normalized.fileName,
    title: normalized.title,
    sourceType: normalized.sourceType,
    docCode: normalized.docCode,
    mksOksCode: normalized.mksOksCode,
    okstuCode: normalized.okstuCode,
    era: normalized.era,
    jurisdiction: normalized.jurisdiction,
    issuingBody: normalized.issuingBody,
    status: normalized.status,
    progress: normalized.progress,
    confidence: normalized.confidence,
    preview: normalized.preview,
    duplicates: normalized.duplicates,
    note: normalized.note,
    gatewayTaskId: normalized.gatewayTaskId,
    gatewayVersionId: normalized.gatewayVersionId,
    gatewayDraftId: normalized.gatewayDraftId,
    gatewayDocumentKey: normalized.gatewayDocumentKey,
    gatewayFileHashSha256: normalized.gatewayFileHashSha256,
    gatewayTitleHashSha256: normalized.gatewayTitleHashSha256,
    gatewayPromotedDocumentId: normalized.gatewayPromotedDocumentId,
    gatewayErrorCode: normalized.gatewayErrorCode,
    gatewayErrorMessage: normalized.gatewayErrorMessage,
    gatewayRawData: normalized.gatewayRawData,
  };
};

export const KnowledgeProcessing: React.FC = () => {
  const { themeMode, workMode, activeTab, setActiveTab } = useUIStore();
  const queryClient = useQueryClient();
  const isLight = themeMode === 'light';
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const previewTimersRef = useRef<number[]>([]);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFileName, setSelectedFileName] = useState('');
  const [notice, setNotice] = useState('');
  const [selectedDraftId, setSelectedDraftId] = useState<string>('');
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewPageIndex, setPreviewPageIndex] = useState(0);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [metadataOpen, setMetadataOpen] = useState(false);
  const [draftSort, setDraftSort] = useState<DraftSort>('updated_desc');
  const [drafts, setDrafts] = useState<DraftItem[]>(() => (workMode === 'demo' ? createDemoDrafts() : []));
  const [draftDocumentKeys, setDraftDocumentKeys] = useState<string[]>(() =>
    workMode === 'prod' ? readStoredDraftDocumentKeys() : [],
  );
  const [deletedGatewayDraftIds, setDeletedGatewayDraftIds] = useState<string[]>([]);
  const [form, setForm] = useState<DraftForm>({
    title: '',
    sourceType: 'GOST',
    docCode: '',
    mksOksCode: '',
    okstuCode: '',
    era: 'CURRENT',
    jurisdiction: 'RU',
    issuingBody: '',
  });

  const publishedDocumentsQuery = useQuery({
    queryKey: ['gateway-documents', workMode],
    queryFn: documentsApi.list,
    staleTime: 30_000,
  });
  const gatewayQueueQuery = useQuery({
    queryKey: ['gateway-documents-queue', workMode],
    queryFn: documentsApi.queue,
    staleTime: 20_000,
  });
  const processingAuditQuery = useQuery({
    queryKey: ['gateway-processing-audit', workMode],
    queryFn: adminApi.audit,
    staleTime: 20_000,
  });
  const gatewayDraftsQuery = useQuery({
    queryKey: ['gateway-drafts', workMode, draftDocumentKeys],
    queryFn: async () => {
      const batches = await Promise.all(draftDocumentKeys.map((documentKey) => draftsApi.list({ documentKey })));
      return batches.flat();
    },
    enabled: workMode === 'prod' && draftDocumentKeys.length > 0,
    staleTime: 20_000,
  });

  useEffect(() => {
    previewTimersRef.current.forEach((timer) => window.clearTimeout(timer));
    previewTimersRef.current = [];
    setDrafts(workMode === 'demo' ? createDemoDrafts() : []);
    setSelectedDraftId('');
    setSelectedFile(null);
    setSelectedFileName('');
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
    setPreviewLoading(false);
    setPreviewError('');
    setMetadataOpen(false);
    setDraftSort('updated_desc');
    setDraftDocumentKeys(workMode === 'prod' ? readStoredDraftDocumentKeys() : []);
    setDeletedGatewayDraftIds([]);
    setForm({
      title: '',
      sourceType: 'GOST',
      docCode: '',
      mksOksCode: '',
      okstuCode: '',
      era: 'CURRENT',
      jurisdiction: 'RU',
      issuingBody: '',
    });
  }, [workMode]);

  useEffect(() => {
    if (workMode !== 'prod' || !gatewayDraftsQuery.data) return;

    setDrafts((current) => {
      const deletedIds = new Set(deletedGatewayDraftIds);
      const mapped = gatewayDraftsQuery.data
        .filter((item: any) => !item?.deleted_at && !item?.deletedAt)
        .map((item: any) => mapGatewayDraftRecordToUi(item))
        .filter((draft) => !deletedIds.has(draft.gatewayDraftId || draft.id));
      const byId = new Map(current.map((draft) => [draft.gatewayDraftId || draft.id, draft]));

      mapped.forEach((draft) => {
        byId.set(draft.gatewayDraftId || draft.id, {
          ...byId.get(draft.gatewayDraftId || draft.id),
          ...draft,
        });
      });

      return Array.from(byId.values());
    });
  }, [deletedGatewayDraftIds, gatewayDraftsQuery.data, workMode]);

  useEffect(() => {
    if (selectedDraftId && !drafts.some((draft) => draft.id === selectedDraftId)) {
      setSelectedDraftId('');
    }
  }, [drafts, selectedDraftId]);

  useEffect(() => {
    if (activeTab === 'knowledgeProcessing') return;

    setSelectedDraftId('');
    setPreviewError('');
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
    setPreviewLoading(false);
    setMetadataOpen(false);
  }, [activeTab]);

  const publishedDocuments = workMode === 'demo' ? publishedDocumentsQuery.data ?? MOCK_DOCUMENTS : publishedDocumentsQuery.data ?? [];
  const gatewayQueue =
    workMode === 'demo'
      ? gatewayQueueQuery.data?.length
        ? gatewayQueueQuery.data
        : MOCK_PROCESSING_QUEUE
      : gatewayQueueQuery.data ?? [];
  const gatewayProcessingLogs =
    workMode === 'demo'
      ? processingAuditQuery.data?.length
        ? processingAuditQuery.data
        : MOCK_PROCESSING_LOGS
      : processingAuditQuery.data ?? [];
  const sortedDrafts = useMemo(() => sortDrafts(drafts, draftSort), [drafts, draftSort]);
  const selectedDraft = drafts.find((draft) => draft.id === selectedDraftId) ?? null;
  const readyCount = drafts.filter((draft) => draft.status === 'ready_for_approve').length;
  const queueAttentionCount = gatewayQueue.filter((item) => item.status === 'ошибка').length;
  const queueHasError = workMode === 'prod' && gatewayQueueQuery.isError;
  const journalHasError = workMode === 'prod' && processingAuditQuery.isError;

  const stats = [
    {
      label: 'Черновиков',
      value: `${drafts.length}`,
      note: 'в сессии',
      icon: <FilePlus2 size={20} />,
      color: '#d9b783',
    },
    {
      label: 'К решению',
      value: `${readyCount}`,
      note: 'после предпросмотра',
      icon: <ShieldCheck size={20} />,
      color: '#79c58b',
    },
    {
      label: 'В очереди',
      value: `${gatewayQueue.length}`,
      note: `${queueAttentionCount ? `${queueAttentionCount} с ошибкой` : 'без ошибок'}`,
      icon: <RotateCw size={20} />,
      color: '#9fb6d8',
    },
    {
      label: 'В базе',
      value: `${publishedDocuments.length}`,
      note: 'готовые карточки',
      icon: <CheckCircle2 size={20} />,
      color: '#8fd19a',
    },
  ];

  const getSelectedDraft = (id = selectedDraftId) => drafts.find((draft) => draft.id === id) ?? null;

  const updateDraft = (id: string, patch: Partial<DraftItem>) => {
    setDrafts((current) =>
      current.map((draft) =>
        draft.id === id
          ? {
              ...draft,
              ...patch,
              updatedAt: nextClock(),
            }
          : draft,
      ),
    );
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) return;

    setSelectedFile(file);
    setSelectedFileName(file.name);
  };

  const clearSourceInputs = () => {
    setSelectedFile(null);
    setSelectedFileName('');
  };

  const createLocalDraft = (sourceName: string) => {
    const id = `draft-${Date.now()}`;
    const now = nextClock();
    const title = form.title.trim() || sourceName.replace(/\.[^.]+$/, '');
    const newDraft: DraftItem = {
      id,
      fileName: sourceName,
      title,
      sourceType: form.sourceType,
      docCode: form.docCode.trim(),
      mksOksCode: form.mksOksCode.trim(),
      okstuCode: form.okstuCode.trim(),
      era: form.era,
      jurisdiction: form.jurisdiction,
      issuingBody: form.issuingBody.trim(),
      status: 'uploaded',
      progress: 14,
      confidence: 0,
      preview: null,
      duplicates: [],
      createdAt: now,
      updatedAt: now,
      note: 'Файл добавлен в очередь обработки.',
    };

    setDrafts((current) => [newDraft, ...current]);
    setSelectedDraftId(id);
    setNotice(`Черновик «${title}» создан.`);
    return { id, title };
  };

  const uploadDraftFile = async (draftId: string, file: File, sourceLabel: string) => {
    const response = await draftsApi.create(file, {
      sourceType: form.sourceType,
      title: form.title.trim() || sourceLabel.replace(/\.[^.]+$/, ''),
      docCode: form.docCode.trim() || undefined,
      mksOksCode: form.mksOksCode.trim() || undefined,
      okstuCode: form.okstuCode.trim() || undefined,
      era: form.era,
      jurisdiction: form.jurisdiction,
      issuingBody: form.issuingBody.trim() || undefined,
      metadata: {
        manual: true,
        source_type: form.sourceType,
        title: form.title.trim() || undefined,
        doc_code: form.docCode.trim() || undefined,
        mks_oks_code: form.mksOksCode.trim() || undefined,
        okstu_code: form.okstuCode.trim() || undefined,
        era: form.era,
        jurisdiction: form.jurisdiction,
        issuing_body: form.issuingBody.trim() || undefined,
      },
      idempotencyKey: createIdempotencyKey(),
    });

    updateDraft(draftId, draftPatchFromGateway(response, getSelectedDraft(draftId) ?? undefined));
    if (response.document_key) {
      setDraftDocumentKeys((current) => {
        const next = Array.from(new Set([response.document_key, ...current]));
        writeStoredDraftDocumentKeys(next);
        return next;
      });
      await queryClient.invalidateQueries({ queryKey: ['gateway-drafts', workMode] });
    }
    await queryClient.invalidateQueries({ queryKey: ['gateway-documents', workMode] });
    await queryClient.invalidateQueries({ queryKey: ['gateway-documents-queue', workMode] });
    return response;
  };

  const handleCreateDraftFromFile = async () => {
    if (!selectedFile) {
      setNotice('Сначала выберите файл для обработки.');
      return;
    }

    const { id, title } = createLocalDraft(selectedFile.name);

    if (workMode === 'prod') {
      try {
        await uploadDraftFile(id, selectedFile, selectedFile.name);
        setNotice(`Файл «${selectedFile.name}» отправлен в Gateway на обработку.`);
      } catch (error: any) {
        updateDraft(id, {
          status: 'failed',
          progress: 100,
          note: 'Gateway не принял файл. Черновик помечен как failed.',
          gatewayErrorMessage: error?.message ?? 'Не удалось отправить файл в Gateway.',
        });
        setNotice(`Черновик «${title}» не удалось отправить в Gateway.`);
      }
    }

    clearSourceInputs();
  };

  const handleCreateDraft = async () => {
    if (selectedFile) {
      await handleCreateDraftFromFile();
      return;
    }

    setNotice('Сначала выберите файл для обработки.');
  };

  const handleStartPreview = (draftId: string) => {
    const draft = getSelectedDraft(draftId);
    if (!draft || draft.status === 'previewing' || draft.status === 'approved' || draft.status === 'discarded') return;

    updateDraft(draftId, {
      status: 'previewing',
      progress: 38,
      note: 'Проверяем метаданные и ищем дубликаты.',
    });
    setNotice(`Предпросмотр для «${draft.title}» запущен.`);

    if (workMode === 'demo') {
      const timer = window.setTimeout(() => {
        const draftAfterPreview = getSelectedDraft(draftId);
        if (!draftAfterPreview) return;

        const preview: DraftPreview = {
          docCode: draftAfterPreview.docCode || draftAfterPreview.title,
          title: draftAfterPreview.title,
          documentType: draftAfterPreview.sourceType.toLowerCase(),
          year: draftAfterPreview.era === 'CURRENT' ? String(new Date().getFullYear()) : '1981',
          revision: draftAfterPreview.sourceType === 'GOST' ? '1' : null,
        };

        const duplicates: DraftDuplicate[] =
          draftAfterPreview.docCode || draftAfterPreview.title
            ? [
                {
                  title: draftAfterPreview.title,
                  reason: 'Похожее наименование и близкий код документа',
                  similarity: 0.84,
                },
              ]
            : [];

        updateDraft(draftId, {
          status: 'ready_for_approve',
          progress: 72,
          confidence: 0.92,
          preview,
          duplicates,
          note: duplicates.length
            ? 'Предпросмотр готов. Есть кандидаты на дубликаты.'
            : 'Предпросмотр готов. Можно принимать документ.',
        });
        setNotice(`Предпросмотр для «${draftAfterPreview.title}» завершён.`);
      }, 1100);

      previewTimersRef.current.push(timer);
      return;
    }

    const gatewayDraftId = draft.gatewayDraftId;
    if (!gatewayDraftId) {
      updateDraft(draftId, {
        status: 'failed',
        progress: 100,
        note: 'У черновика нет gateway id для запуска предпросмотра.',
      });
      setNotice(`Предпросмотр для «${draft.title}» не удалось запустить.`);
      return;
    }

    void (async () => {
      try {
        await draftsApi.startPreview(gatewayDraftId);
        const previewResponse = await draftsApi.waitPreview(gatewayDraftId, 15);
        const draftAfterPreview = getSelectedDraft(draftId);
        if (!draftAfterPreview) return;

        const duplicates: DraftDuplicate[] = Array.isArray(previewResponse?.duplicates)
          ? previewResponse.duplicates.map((duplicate: any) => ({
              title: String(duplicate.title ?? duplicate.document_title ?? duplicate.document_id ?? 'Похожий документ'),
              reason: String(duplicate.reason ?? duplicate.message ?? 'Похожее содержание'),
              similarity: typeof duplicate.similarity === 'number' ? duplicate.similarity : Number(duplicate.score ?? 0),
            }))
          : [];

        updateDraft(draftId, {
          ...draftPatchFromGateway(previewResponse, draftAfterPreview),
          status: normalizeDraftStatusFromGateway(previewResponse?.status) === 'previewing' ? 'previewing' : 'ready_for_approve',
          progress: normalizeDraftStatusFromGateway(previewResponse?.status) === 'previewing' ? 38 : 72,
          confidence: Number(previewResponse?.confidence ?? draftAfterPreview.confidence ?? 0),
          preview:
            mapGatewayPreviewMetadata(previewResponse) ??
            draftAfterPreview.preview ?? {
              docCode: draftAfterPreview.docCode || draftAfterPreview.title,
              title: draftAfterPreview.title,
              documentType: draftAfterPreview.sourceType.toLowerCase(),
              year: draftAfterPreview.era === 'CURRENT' ? String(new Date().getFullYear()) : '1981',
              revision: draftAfterPreview.sourceType === 'GOST' ? '1' : null,
            },
          duplicates,
          note: previewResponse?.decision_required
            ? 'Предпросмотр готов. Требуется решение.'
            : 'Предпросмотр готов. Можно принимать документ.',
        });
        setNotice(`Предпросмотр для «${draftAfterPreview.title}» завершён.`);
      } catch (error: any) {
        updateDraft(draftId, {
          status: 'failed',
          progress: 100,
          note: 'Gateway не завершил предпросмотр.',
          gatewayErrorMessage: error?.message ?? 'Не удалось получить статус предпросмотра.',
        });
        setNotice(`Предпросмотр для «${draft.title}» завершить не удалось.`);
      }
    })();
  };

  const handleDecision = async (draftId: string, action: 'approve' | 'reject') => {
    const draft = getSelectedDraft(draftId);
    if (!draft) return;

    if (action === 'approve' && draft.status !== 'ready_for_approve') {
      setNotice('Сначала нужно завершить предпросмотр и получить карточку черновика.');
      return;
    }

    if (action === 'reject' && draft.status === 'approved') {
      return;
    }

    if (workMode === 'demo') {
      updateDraft(draftId, {
        status: action === 'approve' ? 'approved' : 'discarded',
        progress: 100,
        note:
          action === 'approve'
            ? 'Черновик принят и готов перейти в базу знаний.'
            : 'Черновик отклонён и может быть загружен повторно.',
      });
      setNotice(
        action === 'approve'
          ? `Документ «${draft.title}» принят в базу знаний.`
          : `Документ «${draft.title}» отклонён.`,
      );
      return;
    }

    const gatewayDraftId = draft.gatewayDraftId;
    if (!gatewayDraftId) {
      updateDraft(draftId, {
        status: 'failed',
        progress: 100,
        note: 'У черновика нет gateway id для принятия решения.',
      });
      setNotice(`Решение по «${draft.title}» не удалось отправить в Gateway.`);
      return;
    }

    try {
      const response = await draftsApi.decide(gatewayDraftId, action, form.title.trim() || undefined);
      updateDraft(draftId, {
        ...draftPatchFromGateway(response, draft),
        status: action === 'approve' ? 'approved' : 'discarded',
        progress: 100,
        note:
          response?.message ??
          (action === 'approve'
            ? 'Черновик принят и готов перейти в базу знаний.'
            : 'Черновик отклонён и может быть загружен повторно.'),
      });
      setNotice(
        action === 'approve'
          ? `Документ «${draft.title}» принят в базу знаний.`
          : `Документ «${draft.title}» отклонён.`,
      );
      if (action === 'approve') {
        await queryClient.invalidateQueries({ queryKey: ['gateway-documents', workMode] });
        await queryClient.invalidateQueries({ queryKey: ['gateway-documents-queue', workMode] });
        await queryClient.invalidateQueries({ queryKey: ['gateway-knowledge-sections', workMode] });
        await queryClient.invalidateQueries({ queryKey: ['gateway-drafts', workMode] });
      }
    } catch (error: any) {
      updateDraft(draftId, {
        status: 'failed',
        progress: 100,
        note: 'Gateway не принял решение по черновику.',
        gatewayErrorMessage: error?.message ?? 'Не удалось отправить решение в Gateway.',
      });
      setNotice(`Не удалось отправить решение по «${draft.title}» в Gateway.`);
    }
  };

  const handleDeleteDraft = (draftId: string) => {
    const draft = getSelectedDraft(draftId);
    if (!draft) return;

    if (workMode === 'demo') {
      setDrafts((current) => current.filter((item) => item.id !== draftId));
      setNotice(`Черновик «${draft.title}» удалён из локальной очереди.`);
      return;
    }

    const gatewayDraftId = draft.gatewayDraftId;
    if (!gatewayDraftId) {
      setNotice(`Черновик «${draft.title}» не удалось удалить: нет gateway id.`);
      return;
    }

    void draftsApi
      .delete(gatewayDraftId)
      .then(async () => {
        setDeletedGatewayDraftIds((current) => Array.from(new Set([gatewayDraftId, ...current])));
        if (draft.gatewayDocumentKey) {
          setDraftDocumentKeys((current) => {
            const hasOtherDraftWithSameKey = drafts.some(
              (item) => item.id !== draftId && item.gatewayDocumentKey === draft.gatewayDocumentKey,
            );
            if (hasOtherDraftWithSameKey) return current;

            const next = current.filter((key) => key !== draft.gatewayDocumentKey);
            writeStoredDraftDocumentKeys(next);
            return next;
          });
        }
        setDrafts((current) => current.filter((item) => item.id !== draftId));
        await queryClient.invalidateQueries({ queryKey: ['gateway-drafts', workMode] });
        await queryClient.invalidateQueries({ queryKey: ['gateway-documents-queue', workMode] });
        setNotice(`Черновик «${draft.title}» удалён из Gateway.`);
      })
      .catch((error: any) => {
        updateDraft(draftId, {
          status: 'failed',
          progress: 100,
          note: 'Gateway не удалил черновик.',
          gatewayErrorMessage: error?.message ?? 'Не удалось удалить черновик в Gateway.',
        });
        setNotice(`Черновик «${draft.title}» не удалось удалить из Gateway.`);
      });
  };

  const handleOpenPreviewDialog = (draftId: string) => {
    const draft = getSelectedDraft(draftId);
    setSelectedDraftId(draftId);
    setPreviewPageIndex(0);
    setPreviewError('');
    setPreviewLoading(draft?.status === 'previewing');
    setPreviewDialogOpen(true);
  };

  const handleClosePreviewDialog = () => {
    setPreviewDialogOpen(false);
    setPreviewLoading(false);
    setPreviewError('');
  };

  const previewPages = selectedDraft ? buildPreviewPages(selectedDraft) : [];
  const currentPreviewPage = previewPages[Math.min(previewPageIndex, Math.max(previewPages.length - 1, 0))] ?? null;
  const panelSx = {
    ...PANEL_SX,
    ...(isLight && {
      bgcolor: 'rgba(255, 255, 255, 0.82)',
      borderColor: 'rgba(14, 116, 144, 0.24)',
      boxShadow: '0 8px 22px rgba(15,23,42,0.05)',
    }),
  };

  const tableSx = {
    ...TABLE_SX,
    ...(isLight && {
      bgcolor: 'rgba(255, 255, 255, 0.94)',
      borderColor: 'rgba(14, 116, 144, 0.28)',
      boxShadow: '0 0 0 1px rgba(14, 116, 144, 0.14), 0 14px 34px rgba(15,23,42,0.06)',
    }),
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Stack spacing={3}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {stats.map((stat) => (
            <Box key={stat.label} sx={{ flex: '1 1 200px' }}>
              <Paper
                variant="outlined"
                sx={{
                  p: 2.3,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.8,
                  borderRadius: 2.4,
                  ...panelSx,
                }}
              >
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 1.7,
                    bgcolor: 'rgba(255,255,255,0.03)',
                    color: stat.color,
                    border: '1.5px solid rgba(198, 216, 240, 0.24)',
                  }}
                >
                  {stat.icon}
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.4 }}>
                    {stat.label}
                  </Typography>
                  <Typography variant="h6" sx={{ lineHeight: 1.05, fontWeight: 600 }}>
                    {stat.value}
                  </Typography>
                  <Typography variant="caption" sx={{ color: isLight ? 'rgba(71, 85, 105, 0.80)' : 'rgba(171, 183, 201, 0.72)' }}>
                    {stat.note}
                  </Typography>
                </Box>
              </Paper>
            </Box>
          ))}
        </Box>

        <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
              <FilePlus2 size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
              <Box>
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  Загрузка документа
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Компактный блок для старта обработки и добавления черновика.
                </Typography>
              </Box>
            </Stack>

            <Stack direction="row" spacing={1.2} sx={{ flexWrap: 'wrap' }}>
              <Button
                className="app-action-button"
                variant="contained"
                startIcon={<FileDown size={16} />}
                onClick={() => fileInputRef.current?.click()}
              >
                Выбрать файл
              </Button>
              <Button
                className="app-action-button"
                variant="contained"
                startIcon={<PlayCircle size={16} />}
                onClick={() => void handleCreateDraft()}
              >
                Создать черновик
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                startIcon={<XCircle size={16} />}
                onClick={() => {
                  setSelectedFile(null);
                  setSelectedFileName('');
                  setForm({
                    title: '',
                    sourceType: 'GOST',
                    docCode: '',
                    mksOksCode: '',
                    okstuCode: '',
                    era: 'CURRENT',
                    jurisdiction: 'RU',
                    issuingBody: '',
                  });
                  setNotice('Форма очищена.');
                }}
              >
                Сбросить
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                startIcon={metadataOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                onClick={() => setMetadataOpen((current) => !current)}
              >
                {metadataOpen ? 'Скрыть метаданные' : 'Метаданные'}
              </Button>
              <input ref={fileInputRef} type="file" hidden accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff" onChange={handleFileSelect} />
            </Stack>

            {selectedFileName && (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                Выбран файл: {selectedFileName}
              </Alert>
            )}

            <Collapse in={metadataOpen} timeout="auto" unmountOnExit>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' },
                  gap: 1.4,
                }}
              >
                <TextField
                  label="Название документа"
                  value={form.title}
                  onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                />
                <TextField
                  label="Тип источника"
                  select
                  value={form.sourceType}
                  onChange={(event) => setForm((current) => ({ ...current, sourceType: event.target.value }))}
                >
                  {SOURCE_TYPE_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  label="Код документа"
                  value={form.docCode}
                  onChange={(event) => setForm((current) => ({ ...current, docCode: event.target.value }))}
                />
                <TextField
                  label="Организация-издатель"
                  value={form.issuingBody}
                  onChange={(event) => setForm((current) => ({ ...current, issuingBody: event.target.value }))}
                />
                <TextField
                  label="МКС / ОКС"
                  value={form.mksOksCode}
                  onChange={(event) => setForm((current) => ({ ...current, mksOksCode: event.target.value }))}
                />
                <TextField
                  label="ОКСТУ"
                  value={form.okstuCode}
                  onChange={(event) => setForm((current) => ({ ...current, okstuCode: event.target.value }))}
                />
                <TextField
                  label="Эра"
                  select
                  value={form.era}
                  onChange={(event) => setForm((current) => ({ ...current, era: event.target.value }))}
                >
                  {ERA_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  label="Юрисдикция"
                  select
                  value={form.jurisdiction}
                  onChange={(event) => setForm((current) => ({ ...current, jurisdiction: event.target.value }))}
                >
                  {JURISDICTION_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
              </Box>
            </Collapse>
          </Stack>
        </Paper>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', xl: '1fr 1.2fr' }, gap: 3 }}>
          <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
            <Stack spacing={1.4}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                    <RotateCw size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                  <Box sx={{ minWidth: 0 }}>
                    <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                      Черновики обработки
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Отсортируйте список и выберите черновик для просмотра.
                    </Typography>
                  </Box>
                </Stack>

                <TextField
                  select
                  size="small"
                  label="Сортировка"
                  value={draftSort}
                  onChange={(event) => setDraftSort(event.target.value as DraftSort)}
                  sx={{ minWidth: 168 }}
                >
                  <MenuItem value="updated_desc">По обновлению</MenuItem>
                  <MenuItem value="name_asc">По названию</MenuItem>
                  <MenuItem value="status">По статусу</MenuItem>
                </TextField>
              </Stack>

              {workMode === 'prod' && draftDocumentKeys.length === 0 && (
                <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                  Gateway возвращает список черновиков по `document_key`. После загрузки через этот экран здесь появятся черновики,
                  которые можно повторно запросить из Gateway.
                </Alert>
              )}

              {workMode === 'prod' && gatewayDraftsQuery.isError && (
                <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                  Не удалось загрузить черновики из Gateway по сохраненным `document_key`.
                </Alert>
              )}

              <Paper variant="outlined" sx={{ borderRadius: 2.4, overflow: 'hidden', ...tableSx }}>
                <Stack divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.18)' }} />} sx={{ maxHeight: 560, overflow: 'auto' }}>
                  {sortedDrafts.map((draft) => {
                    const isSelected = selectedDraftId === draft.id;

                    return (
                      <Box
                        key={draft.id}
                        onClick={() => setSelectedDraftId(draft.id)}
                        sx={{
                          p: 1.4,
                          cursor: 'pointer',
                          bgcolor: isSelected ? 'rgba(123, 166, 227, 0.12)' : 'transparent',
                          transition: 'background-color 160ms ease',
                          '&:hover': { bgcolor: 'rgba(123, 166, 227, 0.08)' },
                        }}
                      >
                        <Stack spacing={1}>
                          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ justifyContent: 'space-between' }}>
                            <Box sx={{ minWidth: 0 }}>
                              <Typography sx={{ fontWeight: 560, lineHeight: 1.35 }}>{draft.title}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {draft.fileName} · {draft.createdAt}
                              </Typography>
                            </Box>
                            <Stack direction="row" spacing={0.75} useFlexGap sx={{ flexWrap: 'wrap' }}>
                              <Chip label={getStatusLabel(draft.status)} size="small" color={getStatusColor(draft.status)} variant="outlined" />
                              <Chip label={`${draft.progress}%`} size="small" variant="outlined" />
                            </Stack>
                          </Stack>
                          <LinearProgress
                            variant="determinate"
                            value={draft.progress}
                            sx={{
                              height: 8,
                              borderRadius: 999,
                              bgcolor: isLight ? 'rgba(148, 163, 184, 0.18)' : 'rgba(148, 163, 184, 0.12)',
                            }}
                          />
                        </Stack>
                      </Box>
                    );
                  })}
                  {sortedDrafts.length === 0 && (
                    <Box sx={{ p: 2 }}>
                      <Alert severity="info" variant="outlined">
                        Пока нет черновиков. Создайте первый файл сверху.
                      </Alert>
                    </Box>
                  )}
                </Stack>
              </Paper>
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
            <Stack spacing={1.4}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <FileSearch size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                    Предпросмотр черновика
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Выберите черновик слева, чтобы увидеть его карточку и решение.
                  </Typography>
                </Box>
              </Stack>

              {selectedDraft ? (
                <>
                  <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
                    <Chip label={getStatusLabel(selectedDraft.status)} color={getStatusColor(selectedDraft.status)} variant="outlined" />
                    <Chip label={`${selectedDraft.progress}%`} variant="outlined" />
                    <Chip
                      label={selectedDraft.confidence ? `Уверенность ${Math.round(selectedDraft.confidence * 100)}%` : 'Уверенность: н/д'}
                      variant="outlined"
                    />
                  </Stack>

                  <Divider sx={{ my: 0.5 }} />

                  <Stack spacing={0.8}>
                    <Typography sx={{ fontWeight: 560, lineHeight: 1.35 }}>{selectedDraft.title}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedDraft.fileName}
                    </Typography>
                    {selectedDraft.note && (
                      <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                        {selectedDraft.note}
                      </Alert>
                    )}
                  </Stack>

                  <Paper
                    variant="outlined"
                    sx={{
                      minHeight: 250,
                      p: 2.1,
                      borderRadius: 2.3,
                      bgcolor: '#f4f1e8',
                      color: '#202020',
                      fontFamily: 'Georgia, serif',
                    }}
                  >
                    <Stack spacing={1.2}>
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
                        <Box sx={{ minWidth: 0 }}>
                          <Typography variant="caption" sx={{ color: '#777' }}>
                            Предпросмотр карточки
                          </Typography>
                          <Typography variant="h6" sx={{ mt: 0.7, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                            {selectedDraft.preview?.title ?? selectedDraft.title}
                          </Typography>
                        </Box>
                        <Chip label={`${selectedDraft.progress}%`} size="small" variant="outlined" />
                      </Stack>

                      {selectedDraft.preview ? (
                        <Stack spacing={0.65}>
                          <Typography component="div" sx={{ lineHeight: 1.6, fontFamily: 'inherit' }}>
                            Код: {selectedDraft.preview.docCode}
                          </Typography>
                          <Typography component="div" sx={{ lineHeight: 1.6, fontFamily: 'inherit' }}>
                            Тип: {selectedDraft.preview.documentType}
                          </Typography>
                          <Typography component="div" sx={{ lineHeight: 1.6, fontFamily: 'inherit' }}>
                            Год: {selectedDraft.preview.year}
                          </Typography>
                          <Typography component="div" sx={{ lineHeight: 1.6, fontFamily: 'inherit' }}>
                            Редакция: {selectedDraft.preview.revision ?? 'не указана'}
                          </Typography>
                        </Stack>
                      ) : (
                        <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                          Предпросмотр еще не запущен.
                        </Alert>
                      )}

                      <Stack direction="row" sx={{ justifyContent: 'center', pt: 0.5 }}>
                        <Button
                          className="app-action-button"
                          variant="outlined"
                          startIcon={<Maximize2 size={16} />}
                          onClick={() => handleOpenPreviewDialog(selectedDraft.id)}
                        >
                          Развернуть
                        </Button>
                      </Stack>
                    </Stack>
                  </Paper>

                  <Paper variant="outlined" sx={{ p: 1.25, borderRadius: 2.2, ...panelSx }}>
                    <Stack spacing={1}>
                      <Typography sx={{ fontWeight: 560 }}>Сверка метаданных</Typography>
                      <Stack spacing={0.8}>
                        {buildMetadataReviewRows(selectedDraft).map((row) => (
                          <Box
                            key={row.label}
                            sx={{
                              display: 'grid',
                              gridTemplateColumns: { xs: '1fr', md: '0.8fr 1fr 1fr auto' },
                              gap: 1,
                              alignItems: 'center',
                              p: 0.8,
                              borderRadius: 1.6,
                              bgcolor: isLight ? 'rgba(248,250,252,0.68)' : 'rgba(255,255,255,0.025)',
                              border: isLight ? '1px solid rgba(14,116,144,0.14)' : '1px solid rgba(198,216,240,0.14)',
                            }}
                          >
                            <Typography variant="caption" color="text.secondary">
                              {row.label}
                            </Typography>
                            <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>
                              Ручное: {row.manual || 'не указано'}
                            </Typography>
                            <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>
                              Gateway: {row.extracted || 'не извлечено'}
                            </Typography>
                            <Chip
                              size="small"
                              label={getMetadataStatusLabel(row.status)}
                              color={getMetadataStatusColor(row.status) as 'default' | 'info' | 'success' | 'warning'}
                              variant="outlined"
                            />
                          </Box>
                        ))}
                      </Stack>
                    </Stack>
                  </Paper>

                  <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
                    {selectedDraft.status !== 'previewing' &&
                      selectedDraft.status !== 'ready_for_approve' &&
                      selectedDraft.status !== 'approved' &&
                      selectedDraft.status !== 'discarded' && (
                      <Button
                        className="app-action-button"
                        variant="contained"
                        startIcon={<PlayCircle size={16} />}
                        onClick={() => handleStartPreview(selectedDraft.id)}
                      >
                        Запустить предпросмотр
                      </Button>
                    )}
                    {selectedDraft.status === 'ready_for_approve' && (
                      <>
                        <Button
                          className="app-action-button"
                          variant="contained"
                          color="success"
                          startIcon={<CheckCircle2 size={16} />}
                          onClick={() => void handleDecision(selectedDraft.id, 'approve')}
                        >
                          Принять в базу знаний
                        </Button>
                        <Button
                          className="app-action-button"
                          variant="outlined"
                          color="error"
                          startIcon={<XCircle size={16} />}
                          onClick={() => void handleDecision(selectedDraft.id, 'reject')}
                        >
                          Отклонить
                        </Button>
                      </>
                    )}
                    {selectedDraft.status === 'approved' && (
                      <Button
                        className="app-action-button"
                        variant="contained"
                        startIcon={<FolderInput size={16} />}
                        onClick={() => setActiveTab('documents')}
                      >
                        Открыть базу знаний
                      </Button>
                    )}
                    <Button
                      className="app-action-button"
                      variant="outlined"
                      startIcon={<XCircle size={16} />}
                      onClick={() => handleDeleteDraft(selectedDraft.id)}
                    >
                      Удалить
                    </Button>
                  </Stack>

                  {selectedDraft.duplicates.length > 0 && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.8 }}>
                        Кандидаты на дубликаты
                      </Typography>
                      <Stack spacing={1}>
                        {selectedDraft.duplicates.map((duplicate) => (
                          <Alert key={duplicate.title} severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                            <Typography sx={{ fontWeight: 560 }}>{duplicate.title}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {duplicate.reason} · похожесть {Math.round(duplicate.similarity * 100)}%
                            </Typography>
                          </Alert>
                        ))}
                      </Stack>
                    </Box>
                  )}
                </>
              ) : (
                <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                  Выберите черновик слева, чтобы увидеть предпросмотр и действия.
                </Alert>
              )}
            </Stack>
          </Paper>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
          <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.4 }}>
              <RotateCw size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
              <Box>
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  Очередь обработки
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Текущие элементы, которые уже в работе.
                </Typography>
              </Box>
            </Stack>

            {queueHasError && (
              <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2, mb: 1.2 }}>
                Не удалось загрузить очередь обработки из Gateway.
              </Alert>
            )}
            {!queueHasError && gatewayQueue.length === 0 && (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2, mb: 1.2 }}>
                Очередь обработки пуста.
              </Alert>
            )}
            {gatewayQueue.length > 0 && (
              <Paper variant="outlined" sx={{ overflow: 'hidden', borderRadius: 2.4, ...tableSx }}>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '1.6fr 0.9fr 0.6fr 0.7fr' },
                    gap: 0,
                    alignItems: 'center',
                    px: 1.4,
                    py: 1,
                    borderBottom: '1px solid rgba(198, 214, 236, 0.16)',
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    Документ
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Этап
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Прогресс
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'right' }}>
                    Статус
                  </Typography>
                </Box>
                <Stack divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.12)' }} />}>
                  {gatewayQueue.map((item) => (
                    <Box
                      key={item.id}
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1.6fr 0.9fr 0.6fr 0.7fr' },
                        gap: 0,
                        alignItems: 'center',
                        px: 1.4,
                        py: 1.05,
                      }}
                    >
                      <Typography sx={{ fontSize: '0.84rem', pr: 1 }}>{item.document}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {item.stage}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {item.progress}%
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <Chip label={item.status} size="small" color={getQueueColor(item.status)} variant="outlined" />
                      </Box>
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}
          </Paper>

          <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.4 }}>
              <ShieldCheck size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
              <Box sx={{ minWidth: 0 }}>
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  Журнал обработки
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Короткая лента последних событий для администраторов.
                </Typography>
              </Box>
            </Stack>

            {journalHasError && (
              <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                Не удалось загрузить журнал обработки из Gateway.
              </Alert>
            )}
            {!journalHasError && gatewayProcessingLogs.length === 0 && (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                Журнал обработки пуст.
              </Alert>
            )}
            {gatewayProcessingLogs.length > 0 && (
              <Stack spacing={1.1} sx={{ maxHeight: 320, overflow: 'auto', pr: 0.4 }}>
                {gatewayProcessingLogs.map((log) => (
                  <Paper key={log.id} variant="outlined" sx={{ p: 1.25, borderRadius: 2, ...panelSx }}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ minWidth: 0 }}>
                        <Typography sx={{ fontWeight: 560, lineHeight: 1.35 }}>{log.document}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {log.time} · {log.stage}
                        </Typography>
                      </Box>
                      <Chip label={log.retryStatus} size="small" variant="outlined" />
                    </Stack>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.6, lineHeight: 1.4 }}>
                      {log.event}
                    </Typography>
                  </Paper>
                ))}
              </Stack>
            )}
          </Paper>
        </Box>

        <Dialog open={previewDialogOpen && Boolean(selectedDraft)} onClose={handleClosePreviewDialog} maxWidth="lg" fullWidth>
          <DialogTitle sx={{ pb: 1.2 }}>
            <Stack direction="row" spacing={1.2} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
              <Box sx={{ minWidth: 0 }}>
                <Typography sx={{ fontWeight: 600, lineHeight: 1.2 }}>Предпросмотр документа</Typography>
                <Typography variant="caption" color="text.secondary">
                  {selectedDraft?.title ?? selectedDraft?.fileName ?? 'Документ'} · лист {previewPageIndex + 1} из {previewPages.length}
                </Typography>
              </Box>
              <IconButton aria-label="Закрыть предпросмотр" onClick={handleClosePreviewDialog} size="small">
                <X size={18} />
              </IconButton>
            </Stack>
          </DialogTitle>
          <DialogContent dividers sx={{ bgcolor: isLight ? '#f6f7f8' : 'rgba(8, 12, 18, 0.34)' }}>
            {previewLoading ? (
              <Stack spacing={2} sx={{ py: 6, alignItems: 'center' }}>
                <Typography color="text.secondary">Получаем данные файла...</Typography>
              </Stack>
            ) : (
              <Stack spacing={2}>
                {previewError && (
                  <Alert severity="warning" variant="outlined">
                    {previewError}
                  </Alert>
                )}

                <Paper
                  variant="outlined"
                  sx={{
                    minHeight: '62vh',
                    p: 3,
                    borderRadius: 2.4,
                    bgcolor: '#f4f1e8',
                    color: '#202020',
                    fontFamily: 'Georgia, serif',
                  }}
                >
                  {currentPreviewPage && (
                    <Stack spacing={2}>
                      <Box>
                        <Typography variant="caption" sx={{ color: '#777' }}>
                          {currentPreviewPage.title}
                        </Typography>
                        <Typography variant="h5" sx={{ mt: 0.8, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                          {selectedDraft?.preview?.title ?? selectedDraft?.title}
                        </Typography>
                      </Box>
                      <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.75, fontFamily: 'inherit' }}>
                        {currentPreviewPage.lines.join('\n')}
                      </Typography>
                    </Stack>
                  )}
                </Paper>

                <Stack
                  direction="row"
                  spacing={1}
                  sx={{ justifyContent: 'space-between', alignItems: 'center', mt: 2, flexWrap: 'wrap' }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<ChevronLeft size={16} />}
                    onClick={() => setPreviewPageIndex((current) => Math.max(current - 1, 0))}
                    disabled={previewPageIndex === 0}
                  >
                    Назад
                  </Button>
                  <Typography variant="caption" color="text.secondary">
                    Страница {previewPageIndex + 1} из {previewPages.length}
                  </Typography>
                  <Button
                    variant="outlined"
                    endIcon={<ChevronRight size={16} />}
                    onClick={() => setPreviewPageIndex((current) => Math.min(current + 1, previewPages.length - 1))}
                    disabled={previewPageIndex >= previewPages.length - 1}
                  >
                    Вперед
                  </Button>
                </Stack>
              </Stack>
            )}
          </DialogContent>
          <DialogActions>
            {selectedDraft && (
              <Button
                startIcon={<Download size={16} />}
                onClick={() => downloadPreviewFile(selectedDraft.title, buildDocumentPreviewText(selectedDraft), 'txt')}
              >
                Скачать
              </Button>
            )}
            <Button onClick={handleClosePreviewDialog}>Закрыть</Button>
          </DialogActions>
        </Dialog>

        {notice && (
          <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
            {notice}
          </Alert>
        )}
      </Stack>
    </Container>
  );
};
