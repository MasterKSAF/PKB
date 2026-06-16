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
  Divider,
  MenuItem,
  IconButton,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Download,
  FileDown,
  FilePlus2,
  FileSearch,
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
import { DocumentRegistryPanel } from './DocumentRegistryPanel';
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
  year?: string;
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
  year: string;
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

const createDefaultDraftForm = (): DraftForm => ({
  title: '',
  sourceType: 'GOST',
  docCode: '',
  year: '',
  mksOksCode: '',
  okstuCode: '',
  era: 'CURRENT',
  jurisdiction: 'RU',
  issuingBody: '',
});

const buildDraftFormFromDraft = (draft: DraftItem | null): DraftForm => {
  if (!draft) return createDefaultDraftForm();

  return {
    title: draft.title ?? '',
    sourceType: draft.sourceType ?? 'GOST',
    docCode: draft.docCode ?? '',
    year: draft.year ?? draft.preview?.year ?? '',
    mksOksCode: draft.mksOksCode ?? '',
    okstuCode: draft.okstuCode ?? '',
    era: draft.era ?? 'CURRENT',
    jurisdiction: draft.jurisdiction ?? 'RU',
    issuingBody: draft.issuingBody ?? '',
  };
};

const buildDraftFormFromExtracted = (draft: DraftItem | null): DraftForm => {
  if (!draft) return createDefaultDraftForm();

  return {
    title: draft.preview?.title ?? draft.title ?? '',
    sourceType: draft.preview?.documentType ? draft.sourceType : draft.sourceType,
    docCode: draft.preview?.docCode ?? draft.docCode ?? '',
    year: draft.preview?.year ?? draft.year ?? '',
    mksOksCode: draft.mksOksCode ?? '',
    okstuCode: draft.okstuCode ?? '',
    era: draft.era ?? 'CURRENT',
    jurisdiction: draft.jurisdiction ?? 'RU',
    issuingBody: draft.issuingBody ?? '',
  };
};

const buildWorkspaceDraft = (form: DraftForm, fileName: string): DraftItem => ({
  id: 'workspace-draft',
  fileName: fileName || 'Новый файл',
  title: form.title.trim() || fileName || 'Новый черновик',
  sourceType: form.sourceType,
  docCode: form.docCode.trim(),
  year: form.year.trim(),
  mksOksCode: form.mksOksCode.trim(),
  okstuCode: form.okstuCode.trim(),
  era: form.era,
  jurisdiction: form.jurisdiction,
  issuingBody: form.issuingBody.trim(),
  status: 'uploaded',
  progress: 0,
  confidence: 0,
  preview:
    form.title.trim() || form.docCode.trim() || form.year.trim()
      ? {
          docCode: form.docCode.trim() || form.title.trim() || fileName || 'не указан',
          title: form.title.trim() || fileName || 'Новый черновик',
          documentType: form.sourceType.toLowerCase(),
          year: form.year.trim() || '',
          revision: null,
        }
      : null,
  duplicates: [],
  createdAt: '',
  updatedAt: '',
  note: '',
});

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
        `Год: ${draft.year || draft.preview?.year || 'не указан'}`,
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
    `Год: ${draft.year || draft.preview?.year || 'не указан'}`,
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
  if (status === 'review') return 'изменено';
  if (status === 'extracted') return 'совпадает';
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

const buildMetadataReviewRows = (draft: DraftItem, form: DraftForm) => [
  {
    label: 'Название',
    manual: form.title,
    current: draft.title ?? '',
    status: resolveMetadataStatus(form.title, draft.title),
  },
  {
    label: 'Тип источника',
    manual: form.sourceType,
    current: draft.sourceType ?? '',
    status: resolveMetadataStatus(form.sourceType, draft.sourceType),
  },
  {
    label: 'Код документа',
    manual: form.docCode,
    current: draft.docCode ?? '',
    status: resolveMetadataStatus(form.docCode, draft.docCode),
  },
  {
    label: 'Год',
    manual: form.year,
    current: draft.year ?? draft.preview?.year ?? '',
    status: resolveMetadataStatus(form.year, draft.year ?? draft.preview?.year),
  },
  {
    label: 'МКС / ОКС',
    manual: form.mksOksCode,
    current: draft.mksOksCode ?? '',
    status: resolveMetadataStatus(form.mksOksCode, draft.mksOksCode),
  },
  {
    label: 'ОКСТУ',
    manual: form.okstuCode,
    current: draft.okstuCode ?? '',
    status: resolveMetadataStatus(form.okstuCode, draft.okstuCode),
  },
  {
    label: 'Эра',
    manual: form.era,
    current: draft.era ?? '',
    status: resolveMetadataStatus(form.era, draft.era),
  },
  {
    label: 'Юрисдикция',
    manual: form.jurisdiction,
    current: draft.jurisdiction ?? '',
    status: resolveMetadataStatus(form.jurisdiction, draft.jurisdiction),
  },
  {
    label: 'Издатель',
    manual: form.issuingBody,
    current: draft.issuingBody ?? '',
    status: resolveMetadataStatus(form.issuingBody, draft.issuingBody),
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
    year: fallback?.year ?? payload?.year ?? payload?.preview_metadata?.year ?? preview?.year ?? '',
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
    year: normalized.year,
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
  const [draftSort, setDraftSort] = useState<DraftSort>('updated_desc');
  const [drafts, setDrafts] = useState<DraftItem[]>(() => (workMode === 'demo' ? createDemoDrafts() : []));
  const [draftDocumentKeys, setDraftDocumentKeys] = useState<string[]>(() =>
    workMode === 'prod' ? readStoredDraftDocumentKeys() : [],
  );
  const [deletedGatewayDraftIds, setDeletedGatewayDraftIds] = useState<string[]>([]);
  const [draftForm, setDraftForm] = useState<DraftForm>(() => createDefaultDraftForm());

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
    setDraftSort('updated_desc');
    setDraftDocumentKeys(workMode === 'prod' ? readStoredDraftDocumentKeys() : []);
    setDeletedGatewayDraftIds([]);
    setDraftForm(createDefaultDraftForm());
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
  }, [activeTab]);

  useEffect(() => {
    if (!selectedDraftId) {
      setDraftForm(createDefaultDraftForm());
      return;
    }

    const draft = drafts.find((item) => item.id === selectedDraftId) ?? null;
    setDraftForm(draft ? buildDraftFormFromDraft(draft) : createDefaultDraftForm());
  }, [selectedDraftId]);

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
  const queueHasError = workMode === 'prod' && gatewayQueueQuery.isError;
  const journalHasError = workMode === 'prod' && processingAuditQuery.isError;

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
    const title = draftForm.title.trim() || sourceName.replace(/\.[^.]+$/, '');
    const newDraft: DraftItem = {
      id,
      fileName: sourceName,
      title,
      sourceType: draftForm.sourceType,
      docCode: draftForm.docCode.trim(),
      year: draftForm.year.trim(),
      mksOksCode: draftForm.mksOksCode.trim(),
      okstuCode: draftForm.okstuCode.trim(),
      era: draftForm.era,
      jurisdiction: draftForm.jurisdiction,
      issuingBody: draftForm.issuingBody.trim(),
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
      sourceType: draftForm.sourceType,
      title: draftForm.title.trim() || sourceLabel.replace(/\.[^.]+$/, ''),
      docCode: draftForm.docCode.trim() || undefined,
      mksOksCode: draftForm.mksOksCode.trim() || undefined,
      okstuCode: draftForm.okstuCode.trim() || undefined,
      era: draftForm.era,
      jurisdiction: draftForm.jurisdiction,
      issuingBody: draftForm.issuingBody.trim() || undefined,
      metadata: {
        manual: true,
        source_type: draftForm.sourceType,
        title: draftForm.title.trim() || undefined,
        doc_code: draftForm.docCode.trim() || undefined,
        year: draftForm.year.trim() || undefined,
        mks_oks_code: draftForm.mksOksCode.trim() || undefined,
        okstu_code: draftForm.okstuCode.trim() || undefined,
        era: draftForm.era,
        jurisdiction: draftForm.jurisdiction,
        issuing_body: draftForm.issuingBody.trim() || undefined,
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

  const handleSaveDraftMetadata = () => {
    if (!selectedDraft) {
      setNotice('Сначала выберите черновик слева или создайте новый из выбранного файла.');
      return;
    }

    updateDraft(selectedDraft.id, {
      title: draftForm.title.trim() || selectedDraft.title,
      sourceType: draftForm.sourceType,
      docCode: draftForm.docCode.trim(),
      year: draftForm.year.trim(),
      mksOksCode: draftForm.mksOksCode.trim(),
      okstuCode: draftForm.okstuCode.trim(),
      era: draftForm.era,
      jurisdiction: draftForm.jurisdiction,
      issuingBody: draftForm.issuingBody.trim(),
      note: 'Метаданные черновика сохранены вручную.',
    });
    setNotice(`Метаданные для «${selectedDraft.title}» сохранены.`);
  };

  const handleResetDraftMetadata = () => {
    if (selectedDraft) {
      setDraftForm(buildDraftFormFromExtracted(selectedDraft));
      setNotice(`Метаданные для «${selectedDraft.title}» сброшены к извлечённым значениям.`);
      return;
    }

    setDraftForm(createDefaultDraftForm());
    setNotice('Форма черновика очищена.');
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
          year: draftAfterPreview.year || (draftAfterPreview.era === 'CURRENT' ? String(new Date().getFullYear()) : '1981'),
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
              year: draftAfterPreview.year || (draftAfterPreview.era === 'CURRENT' ? String(new Date().getFullYear()) : '1981'),
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
      const response = await draftsApi.decide(gatewayDraftId, action, draftForm.title.trim() || undefined);
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
  const workspaceDraft = selectedDraft ?? buildWorkspaceDraft(draftForm, selectedFileName || '');
  const hasWorkspaceInput = Boolean(
    selectedDraft ||
      selectedFileName ||
      draftForm.title ||
      draftForm.docCode ||
      draftForm.year ||
      draftForm.mksOksCode ||
      draftForm.okstuCode ||
      draftForm.issuingBody,
  );
  const workspacePreviewPage = hasWorkspaceInput ? buildPreviewPages(workspaceDraft)[0] ?? null : null;
  const canStartPreview = Boolean(
    selectedDraft &&
      selectedDraft.status !== 'previewing' &&
      selectedDraft.status !== 'ready_for_approve' &&
      selectedDraft.status !== 'approved' &&
      selectedDraft.status !== 'discarded',
  );
  const canDecideDraft = selectedDraft?.status === 'ready_for_approve';
  const canOpenKnowledgeBase = selectedDraft?.status === 'approved';
  const renderMetadataFieldInput = (label: string) => {
    const commonSx = { minWidth: 0 };

    switch (label) {
      case 'Название':
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.title}
            onChange={(event) => setDraftForm((current) => ({ ...current, title: event.target.value }))}
            sx={commonSx}
          />
        );
      case 'Тип источника':
        return (
          <TextField
            size="small"
            fullWidth
            select
            value={draftForm.sourceType}
            onChange={(event) => setDraftForm((current) => ({ ...current, sourceType: event.target.value }))}
            sx={commonSx}
          >
            {SOURCE_TYPE_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
        );
      case 'Код документа':
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.docCode}
            onChange={(event) => setDraftForm((current) => ({ ...current, docCode: event.target.value }))}
            sx={commonSx}
          />
        );
      case 'Год':
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.year}
            onChange={(event) => setDraftForm((current) => ({ ...current, year: event.target.value }))}
            sx={commonSx}
          />
        );
      case 'МКС / ОКС':
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.mksOksCode}
            onChange={(event) => setDraftForm((current) => ({ ...current, mksOksCode: event.target.value }))}
            sx={commonSx}
          />
        );
      case 'ОКСТУ':
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.okstuCode}
            onChange={(event) => setDraftForm((current) => ({ ...current, okstuCode: event.target.value }))}
            sx={commonSx}
          />
        );
      case 'Эра':
        return (
          <TextField
            size="small"
            fullWidth
            select
            value={draftForm.era}
            onChange={(event) => setDraftForm((current) => ({ ...current, era: event.target.value }))}
            sx={commonSx}
          >
            {ERA_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
        );
      case 'Юрисдикция':
        return (
          <TextField
            size="small"
            fullWidth
            select
            value={draftForm.jurisdiction}
            onChange={(event) => setDraftForm((current) => ({ ...current, jurisdiction: event.target.value }))}
            sx={commonSx}
          >
            {JURISDICTION_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
        );
      case 'Издатель':
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.issuingBody}
            onChange={(event) => setDraftForm((current) => ({ ...current, issuingBody: event.target.value }))}
            sx={commonSx}
          />
        );
      default:
        return <TextField size="small" fullWidth value="" disabled sx={commonSx} />;
    }
  };
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
      <Stack spacing={2}>
        <Paper variant="outlined" sx={{ p: 1.45, borderRadius: 3, ...panelSx }}>
          <Stack spacing={1.1}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <FilePlus2 size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Box>
                  <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                    Загрузка и обработка документа
                  </Typography>
                </Box>
              </Stack>

            <Stack direction="row" spacing={1.2} sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              <Button
                className="app-action-button"
                variant="contained"
                startIcon={<FileDown size={16} />}
                onClick={() => fileInputRef.current?.click()}
              >
                Выбрать файл
              </Button>
              {selectedFileName && <Chip label={selectedFileName} size="small" variant="outlined" />}
              <input ref={fileInputRef} type="file" hidden accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff" onChange={handleFileSelect} />
            </Stack>

            <Divider sx={{ borderColor: 'rgba(198, 214, 236, 0.18)' }} />

            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              sx={{ flexWrap: 'wrap', alignItems: 'center', '& .app-action-button': { whiteSpace: 'nowrap' } }}
            >
              <Button
                className="app-action-button"
                variant="contained"
                startIcon={<PlayCircle size={16} />}
                onClick={() => void handleCreateDraft()}
                disabled={!selectedFile}
              >
                Создать черновик
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                startIcon={<CheckCircle2 size={16} />}
                onClick={handleSaveDraftMetadata}
                disabled={!selectedDraft}
              >
                Сохранить изменения
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                startIcon={<XCircle size={16} />}
                onClick={handleResetDraftMetadata}
                disabled={!hasWorkspaceInput}
              >
                Сбросить метаданные
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                startIcon={<PlayCircle size={16} />}
                onClick={() => selectedDraft && handleStartPreview(selectedDraft.id)}
                disabled={!canStartPreview}
              >
                Запустить предпросмотр
              </Button>
              <Button
                className="app-action-button"
                variant="contained"
                color="success"
                startIcon={<CheckCircle2 size={16} />}
                onClick={() => selectedDraft && void handleDecision(selectedDraft.id, 'approve')}
                disabled={!canDecideDraft}
              >
                Принять в базу знаний
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                color="error"
                startIcon={<XCircle size={16} />}
                onClick={() => selectedDraft && void handleDecision(selectedDraft.id, 'reject')}
                disabled={!canDecideDraft}
              >
                Отклонить черновик
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                color="error"
                startIcon={<XCircle size={16} />}
                onClick={() => selectedDraft && handleDeleteDraft(selectedDraft.id)}
                disabled={!selectedDraft}
              >
                Удалить черновик
              </Button>
              {canOpenKnowledgeBase && (
                <Button
                  className="app-action-button"
                  variant="outlined"
                  startIcon={<FolderInput size={16} />}
                  onClick={() => setActiveTab('documents')}
                >
                  Открыть базу знаний
                </Button>
              )}
            </Stack>
          </Stack>
        </Paper>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', xl: '320px minmax(0, 1fr)' }, gap: 2 }}>
          <Paper variant="outlined" sx={{ p: 1.45, borderRadius: 3, ...panelSx }}>
            <Stack spacing={1.05}>
              <Stack spacing={0.9}>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                    <RotateCw size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                    <Typography
                      sx={{
                        minWidth: 0,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontWeight: 560,
                        color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)',
                      }}
                    >
                      Черновики обработки
                    </Typography>
                  </Stack>
                  <Chip label={drafts.length} size="small" variant="outlined" sx={{ flexShrink: 0 }} />
                </Stack>

                <Divider
                  sx={{
                    mx: 0.75,
                    borderBottomWidth: 2,
                    borderColor: isLight ? 'rgba(14, 116, 144, 0.24)' : 'rgba(198, 214, 236, 0.26)',
                  }}
                />

                <Stack direction="row" sx={{ justifyContent: 'flex-end' }}>
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
              </Stack>

              {workMode === 'prod' && gatewayDraftsQuery.isError && (
                <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                  Не удалось загрузить черновики из Gateway по сохраненным `document_key`.
                </Alert>
              )}

              <Box sx={{ overflow: 'hidden' }}>
                <Stack divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.18)' }} />} sx={{ maxHeight: 460, overflow: 'auto' }}>
                  {sortedDrafts.map((draft, index) => {
                    const isSelected = selectedDraftId === draft.id;

                    return (
                      <Box
                        key={draft.id}
                        onClick={() => setSelectedDraftId(draft.id)}
                        sx={{
                          px: 1,
                          py: 0.65,
                          cursor: 'pointer',
                          bgcolor: isSelected ? 'rgba(123, 166, 227, 0.12)' : 'transparent',
                          transition: 'background-color 160ms ease',
                          '&:hover': { bgcolor: 'rgba(123, 166, 227, 0.08)' },
                        }}
                      >
                        <Box
                          sx={{
                            display: 'grid',
                            gridTemplateColumns: 'minmax(0, 1fr) auto',
                            gap: 1,
                            alignItems: 'center',
                          }}
                        >
                          <Typography
                            title={`${draft.title} · ${draft.fileName}`}
                            sx={{
                              minWidth: 0,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              fontWeight: isSelected ? 620 : 520,
                              lineHeight: 1.35,
                              fontSize: '0.88rem',
                            }}
                          >
                            {index + 1}. {draft.title}
                          </Typography>
                          <Chip
                            label={getStatusLabel(draft.status)}
                            size="small"
                            color={getStatusColor(draft.status)}
                            variant="outlined"
                            sx={{ height: 22, '& .MuiChip-label': { px: 0.8, fontSize: '0.68rem' } }}
                          />
                        </Box>
                      </Box>
                    );
                  })}
                  {sortedDrafts.length === 0 && (
                    <Box sx={{ p: 1 }}>
                      <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                        Черновиков пока нет.
                      </Alert>
                    </Box>
                  )}
                </Stack>
              </Box>
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ p: 1.45, borderRadius: 3, ...panelSx }}>
            <Stack spacing={1.15}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <FileSearch size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                    Рабочая область черновика
                  </Typography>
                </Box>
              </Stack>

              <Paper
                variant="outlined"
                sx={{
                  minHeight: 420,
                  p: 2.1,
                  borderRadius: 2.3,
                  bgcolor: '#f4f1e8',
                  color: '#202020',
                  fontFamily: 'Georgia, serif',
                }}
              >
                <Stack spacing={1.15}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography variant="caption" sx={{ color: '#777' }}>
                        Предпросмотр документа
                      </Typography>
                      <Typography variant="h6" sx={{ mt: 0.65, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                        {workspacePreviewPage?.title ?? 'Черновик не выбран'}
                      </Typography>
                    </Box>
                  </Stack>

                  {workspacePreviewPage ? (
                    <Paper
                      variant="outlined"
                      sx={{
                        minHeight: 310,
                        p: 2.2,
                        borderRadius: 2,
                        bgcolor: '#fbf7ef',
                        borderColor: 'rgba(99, 89, 68, 0.22)',
                        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.7), 0 8px 18px rgba(15,23,42,0.08)',
                        color: '#202020',
                      }}
                    >
                      <Stack spacing={1.4}>
                        <Box>
                          <Typography variant="caption" sx={{ color: '#7c6f57' }}>
                            Страница 1
                          </Typography>
                          <Typography variant="h6" sx={{ mt: 0.45, color: '#222', fontFamily: 'Georgia, serif' }}>
                            {workspacePreviewPage.title}
                          </Typography>
                        </Box>
                        <Typography
                          component="pre"
                          sx={{
                            m: 0,
                            whiteSpace: 'pre-wrap',
                            lineHeight: 1.7,
                            fontFamily: 'inherit',
                            fontSize: '0.98rem',
                            minHeight: 220,
                          }}
                        >
                          {workspacePreviewPage.lines.join('\n')}
                        </Typography>
                      </Stack>
                    </Paper>
                  ) : (
                    <Paper
                      variant="outlined"
                      sx={{
                        minHeight: 310,
                        p: 2.2,
                        borderRadius: 2,
                        bgcolor: '#fbf7ef',
                        borderColor: 'rgba(99, 89, 68, 0.22)',
                        color: '#6f6757',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Typography sx={{ fontFamily: 'Georgia, serif' }}>Нет предпросмотра</Typography>
                    </Paper>
                  )}

                  <Stack direction="row" sx={{ justifyContent: 'center', pt: 0.25 }}>
                    <Button
                      className="app-action-button"
                      variant="outlined"
                      startIcon={<Maximize2 size={16} />}
                      onClick={() => selectedDraft && handleOpenPreviewDialog(selectedDraft.id)}
                      disabled={!selectedDraft}
                    >
                      Развернуть
                    </Button>
                  </Stack>
                </Stack>
              </Paper>

              <Paper variant="outlined" sx={{ p: 1.25, borderRadius: 2.2, ...panelSx }}>
                <Stack spacing={1}>
                  <Typography sx={{ fontWeight: 560 }}>Сверка и правка метаданных</Typography>
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: '1fr', lg: '0.72fr 0.92fr 1.25fr auto' },
                      gap: 1,
                      alignItems: 'start',
                    }}
                  >
                    <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', lg: 'block' } }} />
                    <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', lg: 'block' }, fontWeight: 560 }}>
                      Текущее значение
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', lg: 'block' }, fontWeight: 560 }}>
                      Новое значение
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', lg: 'block' }, fontWeight: 560 }}>
                      Статус
                    </Typography>
                    {buildMetadataReviewRows(workspaceDraft, draftForm).map((row) => (
                      <React.Fragment key={row.label}>
                        <Typography variant="caption" color="text.secondary" sx={{ pt: 1 }}>
                          {row.label}
                        </Typography>
                        <Typography variant="caption" sx={{ overflowWrap: 'anywhere', pt: 1.05 }}>
                          {row.current || 'не заполнено'}
                        </Typography>
                        {renderMetadataFieldInput(row.label)}
                        <Chip
                          size="small"
                          label={getMetadataStatusLabel(row.status)}
                          color={getMetadataStatusColor(row.status) as 'default' | 'info' | 'success' | 'warning'}
                          variant="outlined"
                        />
                      </React.Fragment>
                    ))}
                  </Box>
                </Stack>
              </Paper>

              {selectedDraft ? (
                <>
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
              ) : null}
            </Stack>
          </Paper>
        </Box>

        <DocumentRegistryPanel documents={publishedDocuments} />

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
          <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.4 }}>
              <RotateCw size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
              <Box>
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  Очередь обработки
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
