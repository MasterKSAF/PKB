import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Collapse,
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
  ChevronDown,
  ChevronRight,
  ChevronUp,
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
import { adminApi, draftsApi, documentsApi, tasksApi, type DraftMetadataOverrides } from '../utils/http';
import { downloadPreviewFile } from '../utils/downloadPreview';
import { MOCK_DOCUMENTS, MOCK_PROCESSING_LOGS, MOCK_PROCESSING_QUEUE, type ProcessingLogItem } from '../utils/mockData';

type DraftStatus = 'uploaded' | 'previewing' | 'ready_for_approve' | 'review_required' | 'validation' | 'approved' | 'discarded' | 'failed';

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

type DraftNotification = {
  code: string;
  severity: 'info' | 'warning' | 'error' | 'critical' | string;
  category?: string;
  message: string;
  location?: string;
  suggestedAction?: string;
};

type DraftSort = 'updated_desc' | 'name_asc' | 'status';
type MetadataReviewStatus = 'manual' | 'extracted' | 'review' | 'empty';
type KnowledgeProcessingSection = 'upload' | 'drafts' | 'registry' | 'journal';

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
  validFrom?: string;
  validUntil?: string;
  status: DraftStatus;
  progress: number;
  confidence: number;
  preview: DraftPreview | null;
  duplicates: DraftDuplicate[];
  notifications?: DraftNotification[];
  createdAt: string;
  updatedAt: string;
  note?: string;
  gatewayTaskId?: string;
  gatewayVersionId?: string;
  gatewayDraftId?: string;
  gatewayDocumentKey?: string;
  gatewayFileHashSha256?: string;
  gatewayTitleHashSha256?: string;
  gatewayTitleKey?: string;
  gatewayPromotedDocumentId?: string | null;
  gatewayErrorCode?: string | null;
  gatewayErrorMessage?: string | null;
  gatewayRawData?: unknown;
  gatewayMetadataOverrides?: DraftMetadataOverrides;
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
  validFrom: string;
  validUntil: string;
};

type DraftMetadataValidationErrors = Partial<Record<keyof DraftForm, string>>;

const SOURCE_TYPE_OPTIONS = ['GOST', 'GOST_R', 'OST', 'RD', 'TU', 'ISO', 'DNV', 'ASTM', 'RMRS', 'OTHER'];
const ERA_OPTIONS = ['USSR', 'CIS', 'RF', 'CURRENT'];
const JURISDICTION_OPTIONS = ['RU', 'EU', 'US', 'NO', 'INTL'];
const DRAFT_DOCUMENT_KEYS_STORAGE = 'pkb_gateway_draft_document_keys_v1';
const TITLE_MAX_LENGTH = 180;
const DOC_CODE_MAX_LENGTH = 80;
const CLASSIFIER_CODE_MAX_LENGTH = 64;
const ISSUING_BODY_MAX_LENGTH = 120;

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
  validFrom: '',
  validUntil: '',
});

const trimLength = (value: string, maxLength: number) => value.slice(0, maxLength);
const sanitizeDocumentCode = (value: string) => trimLength(value.replace(/[^\p{L}\p{N}\s./_№()\-]/gu, ''), DOC_CODE_MAX_LENGTH);
const sanitizeClassifierCode = (value: string) => trimLength(value.replace(/[^\d.,;\s]/g, ''), CLASSIFIER_CODE_MAX_LENGTH);
const sanitizeOkstuCode = (value: string) => trimLength(value.replace(/[^\d,;\s]/g, ''), CLASSIFIER_CODE_MAX_LENGTH);

const validateDraftMetadata = (form: DraftForm): DraftMetadataValidationErrors => {
  const errors: DraftMetadataValidationErrors = {};
  const year = form.year.trim();
  const docCode = form.docCode.trim();
  const mksOksCode = form.mksOksCode.trim();
  const okstuCode = form.okstuCode.trim();
  const validFrom = form.validFrom.trim();
  const validUntil = form.validUntil.trim();

  if (form.title.trim().length > TITLE_MAX_LENGTH) {
    errors.title = `Не больше ${TITLE_MAX_LENGTH} символов.`;
  }

  if (docCode && !/^[\p{L}\p{N}\s./_№()\-]+$/u.test(docCode)) {
    errors.docCode = 'Только буквы, цифры, пробелы и символы . / _ - № ().';
  }

  if (year) {
    if (!/^\d{4}$/.test(year)) {
      errors.year = 'Год должен быть в формате YYYY.';
    } else {
      const numericYear = Number(year);
      if (numericYear < 1900 || numericYear > 2099) {
        errors.year = 'Год должен быть от 1900 до 2099.';
      }
    }
  }

  if (
    mksOksCode &&
    mksOksCode
      .split(/[,;]/)
      .map((code) => code.trim())
      .some((code) => !/^\d+(?:\.\d+)*$/.test(code) || code.replace(/\D/g, '').length < 1 || code.replace(/\D/g, '').length > 15)
  ) {
    errors.mksOksCode = 'От 1 до 15 цифр, можно с точками; несколько кодов через запятую.';
  }

  if (okstuCode && !/^\d{3,10}([,;]\s*\d{3,10})*$/.test(okstuCode)) {
    errors.okstuCode = 'Только цифры, 3-10 знаков; несколько кодов через запятую.';
  }

  if (form.issuingBody.trim().length > ISSUING_BODY_MAX_LENGTH) {
    errors.issuingBody = `Не больше ${ISSUING_BODY_MAX_LENGTH} символов.`;
  }

  if (validFrom && !/^\d{4}-\d{2}-\d{2}$/.test(validFrom)) {
    errors.validFrom = 'Дата должна быть в формате YYYY-MM-DD.';
  }

  if (validUntil && !/^\d{4}-\d{2}-\d{2}$/.test(validUntil)) {
    errors.validUntil = 'Дата должна быть в формате YYYY-MM-DD или пустой для бессрочного документа.';
  }

  if (!errors.validFrom && !errors.validUntil && validFrom && validUntil) {
    const fromTime = new Date(validFrom).getTime();
    const untilTime = new Date(validUntil).getTime();
    if (!Number.isNaN(fromTime) && !Number.isNaN(untilTime) && fromTime > untilTime) {
      errors.validUntil = 'Дата окончания не может быть раньше даты начала.';
    }
  }

  return errors;
};

const getFirstMetadataError = (errors: DraftMetadataValidationErrors) =>
  Object.values(errors).find((message): message is string => Boolean(message)) ?? '';

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
    validFrom: draft.validFrom ?? '',
    validUntil: draft.validUntil ?? '',
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
    validFrom: draft.validFrom ?? '',
    validUntil: draft.validUntil ?? '',
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
  validFrom: form.validFrom.trim(),
  validUntil: form.validUntil.trim(),
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
  borderRadius: 2,
  bgcolor: 'transparent',
  borderWidth: 0,
  borderColor: 'transparent',
  boxShadow: 'none',
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
    note: 'Проверка готова, можно принять в базу знаний.',
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
    note: 'Идёт первичная проверка.',
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
    note: 'Файл загружен, проверка еще не завершена.',
  },
];

const getStatusLabel = (status: DraftStatus) => {
  switch (status) {
    case 'uploaded':
      return 'Загружен';
    case 'previewing':
      return 'Проверяется';
    case 'ready_for_approve':
      return 'Нужна проверка';
    case 'review_required':
      return 'Требуется проверка';
    case 'validation':
      return 'Повторная проверка';
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
    case 'review_required':
      return 'warning';
    case 'validation':
      return 'secondary';
    case 'previewing':
      return 'warning';
    case 'discarded':
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

const getStatusDotColor = (status: DraftStatus) => {
  switch (status) {
    case 'approved':
      return '#22c55e';
    case 'ready_for_approve':
      return '#eab308';
    case 'review_required':
      return '#f97316';
    case 'validation':
      return '#a78bfa';
    case 'previewing':
      return '#38bdf8';
    case 'discarded':
    case 'failed':
      return '#ef4444';
    case 'uploaded':
    default:
      return '#60a5fa';
  }
};

const getQueueColor = (status: string) => {
  if (status === 'в работе') return 'warning';
  if (status === 'в очереди') return 'default';
  if (status === 'ошибка') return 'error';
  return 'success';
};

const getLogDotColor = (retryStatus: ProcessingLogItem['retryStatus']) => {
  if (retryStatus === 'Ошибка') return '#ef4444';
  if (retryStatus === 'Запланирована') return '#f97316';
  if (retryStatus === 'Выполнена') return '#22c55e';
  return '#38bdf8';
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
        preview ? `Проверка готова: ${preview.title}` : 'Проверка еще не завершена.',
        preview ? `Год: ${preview.year}` : 'Данные появятся после обработки черновика.',
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
  {
    label: 'Дата начала действия',
    manual: form.validFrom,
    current: draft.validFrom ?? '',
    status: resolveMetadataStatus(form.validFrom, draft.validFrom),
  },
  {
    label: 'Дата окончания действия',
    manual: form.validUntil,
    current: draft.validUntil ?? '',
    status: resolveMetadataStatus(form.validUntil, draft.validUntil),
  },
];

const displayValue = (value: unknown) => {
  const text = String(value ?? '').trim();
  return text || 'не передано';
};

const getNotificationAlertSeverity = (severity?: string): 'info' | 'warning' | 'error' => {
  const normalized = String(severity ?? '').toLowerCase();
  if (normalized === 'critical' || normalized === 'error') return 'error';
  if (normalized === 'warning') return 'warning';
  return 'info';
};

const countTextMatches = (text: string, query: string) => {
  if (!query) return 0;

  let count = 0;
  let position = text.toLowerCase().indexOf(query);

  while (position !== -1) {
    count += 1;
    position = text.toLowerCase().indexOf(query, position + query.length);
  }

  return count;
};

const renderHighlightedText = (text: string, query: string, isLight: boolean) => {
  if (!query) return text;

  const lowerText = text.toLowerCase();
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  let position = lowerText.indexOf(query);
  let index = 0;

  while (position !== -1) {
    if (position > cursor) {
      parts.push(text.slice(cursor, position));
    }

    parts.push(
      <Box
        component="mark"
        key={`${position}-${index}`}
        sx={{
          px: 0.35,
          py: 0.05,
          borderRadius: 0.7,
          color: isLight ? '#111827' : '#f8fbff',
          bgcolor: isLight ? 'rgba(202, 138, 4, 0.28)' : 'rgba(216, 176, 122, 0.36)',
        }}
      >
        {text.slice(position, position + query.length)}
      </Box>,
    );

    cursor = position + query.length;
    position = lowerText.indexOf(query, cursor);
    index += 1;
  }

  if (cursor < text.length) {
    parts.push(text.slice(cursor));
  }

  return parts;
};

const buildDraftRawJson = (draft: DraftItem, form: DraftForm) => ({
  gateway_raw_response: draft.gatewayRawData ?? null,
  normalized_gateway: {
    draft_id: draft.gatewayDraftId || null,
    task_id: draft.gatewayTaskId || null,
    document_key: draft.gatewayDocumentKey || null,
    document_id: draft.gatewayPromotedDocumentId || null,
    version_id: draft.gatewayVersionId || null,
    title_key: draft.gatewayTitleKey || null,
    title_hash_sha256: draft.gatewayTitleHashSha256 || null,
    status: draft.status,
    confidence: draft.confidence || null,
    preview_metadata: draft.preview,
    notifications: draft.notifications ?? [],
    duplicates: draft.duplicates,
  },
  manual_metadata: {
    title: form.title || null,
    source_type: form.sourceType || null,
    doc_code: form.docCode || null,
    year: form.year || null,
    mks_oks_code: form.mksOksCode || null,
    okstu_code: form.okstuCode || null,
    era: form.era || null,
    jurisdiction: form.jurisdiction || null,
    issuing_body: form.issuingBody || null,
    valid_from: form.validFrom || null,
    valid_until: form.validUntil || null,
  },
  metadata_overrides: draft.gatewayMetadataOverrides ?? null,
  gateway_error: draft.gatewayErrorCode || draft.gatewayErrorMessage
    ? {
        code: draft.gatewayErrorCode,
        message: draft.gatewayErrorMessage,
      }
    : null,
});

const sortDrafts = (items: DraftItem[], sort: DraftSort) => {
  const statusRank: Record<DraftStatus, number> = {
    ready_for_approve: 0,
    review_required: 1,
    validation: 2,
    previewing: 3,
    uploaded: 4,
    approved: 5,
    discarded: 6,
    failed: 7,
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
  review_required: 72,
  validation: 88,
  approved: 100,
  discarded: 100,
  failed: 100,
};

const isActiveDraftStatus = (status: DraftStatus) => status !== 'approved' && status !== 'discarded';
const shouldPollDraftDetails = (status?: DraftStatus | null) => status === 'previewing' || status === 'validation';

const normalizeDraftStatusFromGateway = (status?: string): DraftStatus => {
  const normalized = String(status ?? '').toLowerCase();
  if (normalized === 'preview_ready' || normalized === 'ready_for_approve') return 'ready_for_approve';
  if (normalized === 'review_required') return 'review_required';
  if (normalized === 'validation') return 'validation';
  if (normalized === 'processing' || normalized === 'proceeding') return 'validation';
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
  const candidates = payload?.duplicates ?? payload?.duplicate_candidates ?? payload?.uniqueness?.candidates ?? [];
  const duplicates = Array.isArray(candidates) ? candidates : [];
  return duplicates.map((duplicate: any) => ({
    title: String(duplicate.title ?? duplicate.document_title ?? duplicate.document_id ?? 'Похожий документ'),
    reason: String(duplicate.reason ?? duplicate.message ?? 'Похожее содержание'),
    similarity: typeof duplicate.similarity === 'number' ? duplicate.similarity : Number(duplicate.score ?? 0),
  }));
};

const mapGatewayNotifications = (payload: any): DraftNotification[] => {
  const source = Array.isArray(payload?.notifications)
    ? payload.notifications
    : Array.isArray(payload?.quality?.notifications)
      ? payload.quality.notifications
      : [];

  return source.map((item: any) => ({
    code: String(item.code ?? item.id ?? 'notification'),
    severity: String(item.severity ?? 'info'),
    category: item.category ? String(item.category) : undefined,
    message: String(item.message ?? item.text ?? item.code ?? 'Уведомление обработки'),
    location: item.location ? String(item.location) : undefined,
    suggestedAction: item.suggested_action ?? item.suggestedAction ? String(item.suggested_action ?? item.suggestedAction) : undefined,
  }));
};

const pickMetadataSource = (payload: any) => payload?.metadata_overrides ?? payload?.metadataOverrides ?? {};

const firstNonEmptyText = (...values: unknown[]) => {
  const value = values.find((item) => String(item ?? '').trim().length > 0);
  return value === undefined ? '' : String(value).trim();
};

const firstDefinedText = (...values: unknown[]) => {
  const value = values.find((item) => item !== null && item !== undefined);
  return value === undefined ? '' : String(value);
};

const buildMetadataOverridesFromForm = (form: DraftForm): DraftMetadataOverrides => ({
  title: form.title.trim() || null,
  source_type: form.sourceType || null,
  doc_code: form.docCode.trim() || null,
  year: form.year.trim() || null,
  mks_oks_code: form.mksOksCode.trim() || null,
  okstu_code: form.okstuCode.trim() || null,
  era: form.era || null,
  jurisdiction: form.jurisdiction || null,
  issuing_body: form.issuingBody.trim() || null,
  valid_from: form.validFrom.trim() || null,
  valid_until: form.validUntil.trim() || null,
});

export const mapGatewayDraftRecordToUi = (payload: any, fallback?: Partial<DraftItem>): DraftItem => {
  const status = normalizeDraftStatusFromGateway(payload?.status ?? fallback?.status);
  const preview = mapGatewayPreviewMetadata(payload) ?? fallback?.preview ?? null;
  const duplicates = mapGatewayDuplicates(payload);
  const notifications = mapGatewayNotifications(payload);
  const metadataOverrides = pickMetadataSource(payload);
  const progress = draftProgressByStatus[status] ?? fallback?.progress ?? 0;
  const confidence = payload?.confidence ?? fallback?.confidence ?? 0;
  const createdAt = payload?.created_at ?? payload?.createdAt ?? fallback?.createdAt ?? nextClock();
  const updatedAt = payload?.updated_at ?? payload?.updatedAt ?? fallback?.updatedAt ?? createdAt;
  const draftId = String(fallback?.id ?? payload?.draft_id ?? payload?.id ?? `draft-${Date.now()}`);
  const documentKey = firstNonEmptyText(payload?.document_key, payload?.documentKey, fallback?.gatewayDocumentKey);
  const fileKey = firstNonEmptyText(payload?.file_key, payload?.fileKey);
  const fallbackLabel = documentKey || fileKey || `Черновик #${draftId}`;
  const fileName = firstNonEmptyText(
    payload?.filename,
    payload?.file_name,
    fallback?.fileName,
    payload?.title,
    fallbackLabel,
  );
  const title = firstNonEmptyText(
    payload?.title,
    metadataOverrides.title,
    payload?.preview_metadata?.title,
    fallback?.title,
    payload?.filename,
    payload?.file_name,
    documentKey,
    fileKey,
    fallbackLabel,
  );

  return {
    id: draftId,
    fileName,
    title,
    sourceType: firstDefinedText(payload?.source_type, metadataOverrides.source_type, payload?.preview_metadata?.source_type, fallback?.sourceType, 'OTHER'),
    docCode: firstDefinedText(payload?.doc_code, metadataOverrides.doc_code, payload?.preview_metadata?.doc_code, fallback?.docCode),
    year: firstDefinedText(payload?.year, metadataOverrides.year, payload?.preview_metadata?.year, preview?.year, fallback?.year),
    mksOksCode: firstDefinedText(payload?.mks_oks_code, metadataOverrides.mks_oks_code, payload?.preview_metadata?.mks_oks_code, fallback?.mksOksCode),
    okstuCode: firstDefinedText(payload?.okstu_code, metadataOverrides.okstu_code, payload?.preview_metadata?.okstu_code, fallback?.okstuCode),
    era: firstDefinedText(payload?.era, metadataOverrides.era, payload?.preview_metadata?.era, fallback?.era, 'CURRENT'),
    jurisdiction: firstDefinedText(payload?.jurisdiction, metadataOverrides.jurisdiction, payload?.preview_metadata?.jurisdiction, fallback?.jurisdiction, 'RU'),
    issuingBody: firstDefinedText(payload?.issuing_body, metadataOverrides.issuing_body, payload?.preview_metadata?.issuing_body, fallback?.issuingBody),
    validFrom: firstDefinedText(payload?.valid_from, metadataOverrides.valid_from, payload?.preview_metadata?.valid_from, fallback?.validFrom),
    validUntil: firstDefinedText(payload?.valid_until, metadataOverrides.valid_until, payload?.preview_metadata?.valid_until, fallback?.validUntil),
    status,
    progress,
    confidence: Number(confidence ?? 0),
    preview,
    duplicates: duplicates.length ? duplicates : fallback?.duplicates ?? [],
    notifications: notifications.length ? notifications : fallback?.notifications ?? [],
    createdAt,
    updatedAt,
    note: fallback?.note ?? payload?.message ?? '',
    gatewayTaskId: String(payload?.task_id ?? payload?.taskId ?? fallback?.gatewayTaskId ?? ''),
    gatewayVersionId: String(payload?.version_id ?? payload?.versionId ?? fallback?.gatewayVersionId ?? ''),
    gatewayDraftId: (() => {
      const raw = payload?.draft_id ?? payload?.draftId ?? payload?.id ?? fallback?.gatewayDraftId ?? '';
      const str = String(raw);
      return /^\d+$/.test(str) ? str : '';
    })(),
    gatewayDocumentKey: documentKey,
    gatewayFileHashSha256: String(payload?.file_hash_sha256 ?? payload?.fileHashSha256 ?? fallback?.gatewayFileHashSha256 ?? ''),
    gatewayTitleHashSha256: String(payload?.title_hash_sha256 ?? payload?.titleHashSha256 ?? fallback?.gatewayTitleHashSha256 ?? ''),
    gatewayTitleKey: String(payload?.title_key ?? payload?.titleKey ?? fallback?.gatewayTitleKey ?? ''),
    gatewayPromotedDocumentId:
      payload?.document_id ??
      payload?.promoted_document_id ??
      payload?.approved_document_id ??
      fallback?.gatewayPromotedDocumentId ??
      null,
    gatewayErrorCode: payload?.error_code ?? fallback?.gatewayErrorCode ?? null,
    gatewayErrorMessage: payload?.error_message ?? fallback?.gatewayErrorMessage ?? null,
    gatewayRawData: payload?.raw_data ?? fallback?.gatewayRawData ?? null,
    gatewayMetadataOverrides: Object.keys(metadataOverrides).length ? metadataOverrides : fallback?.gatewayMetadataOverrides,
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
    validFrom: normalized.validFrom,
    validUntil: normalized.validUntil,
    status: normalized.status,
    progress: normalized.progress,
    confidence: normalized.confidence,
    preview: normalized.preview,
    duplicates: normalized.duplicates,
    notifications: normalized.notifications,
    note: normalized.note,
    gatewayTaskId: normalized.gatewayTaskId,
    gatewayVersionId: normalized.gatewayVersionId,
    gatewayDraftId: normalized.gatewayDraftId,
    gatewayDocumentKey: normalized.gatewayDocumentKey,
    gatewayFileHashSha256: normalized.gatewayFileHashSha256,
    gatewayTitleHashSha256: normalized.gatewayTitleHashSha256,
    gatewayTitleKey: normalized.gatewayTitleKey,
    gatewayPromotedDocumentId: normalized.gatewayPromotedDocumentId,
    gatewayErrorCode: normalized.gatewayErrorCode,
    gatewayErrorMessage: normalized.gatewayErrorMessage,
    gatewayRawData: normalized.gatewayRawData,
    gatewayMetadataOverrides: normalized.gatewayMetadataOverrides,
  };
};

export const KnowledgeProcessing: React.FC = () => {
  const { activeKnowledgeProcessingSection, themeMode, workMode, activeTab, setActiveTab } = useUIStore();
  const queryClient = useQueryClient();
  const isLight = themeMode === 'light';
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const previewTimersRef = useRef<number[]>([]);
  const activeDraftDetailsRequestRef = useRef('');

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [notice, setNotice] = useState('');
  const [selectedDraftId, setSelectedDraftId] = useState<string>('');
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewPageIndex, setPreviewPageIndex] = useState(0);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [metadataOpen, setMetadataOpen] = useState(true);
  const [classificationOpen, setClassificationOpen] = useState(false);
  const [gatewayDetailsOpen, setGatewayDetailsOpen] = useState(false);
  const [rawJsonOpen, setRawJsonOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [duplicatesOpen, setDuplicatesOpen] = useState(false);
  const [processingStatusOpen, setProcessingStatusOpen] = useState(false);
  const [previewPanelOpen, setPreviewPanelOpen] = useState(false);
  const [previewSearch, setPreviewSearch] = useState('');
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectComment, setRejectComment] = useState('');
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
      const gatewayDrafts = await draftsApi.list();
      const byId = new Map<string, any>(
        gatewayDrafts.map((item: any) => [String(item.draft_id ?? item.id), item]),
      );

      if (draftDocumentKeys.length > 0) {
        const batches = await Promise.all(draftDocumentKeys.map((documentKey) => draftsApi.list({ documentKey })));
        batches.flat().forEach((item: any) => {
          byId.set(String(item.draft_id ?? item.id), item);
        });
      }

      return Array.from(byId.values());
    },
    enabled: workMode === 'prod',
    staleTime: 20_000,
    refetchInterval: workMode === 'prod' && activeTab === 'knowledgeProcessing' ? 5_000 : false,
  });

  useEffect(() => {
    previewTimersRef.current.forEach((timer) => window.clearTimeout(timer));
    previewTimersRef.current = [];
    setDrafts(workMode === 'demo' ? createDemoDrafts() : []);
    setSelectedDraftId('');
    setSelectedFiles([]);
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
    setPreviewLoading(false);
    setPreviewError('');
    setMetadataOpen(true);
    setClassificationOpen(false);
    setGatewayDetailsOpen(false);
    setRawJsonOpen(false);
    setNotificationsOpen(false);
    setDuplicatesOpen(false);
    setProcessingStatusOpen(false);
    setPreviewPanelOpen(false);
    setPreviewSearch('');
    setRejectDialogOpen(false);
    setRejectComment('');
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

      return Array.from(byId.values()).filter((draft) => isActiveDraftStatus(draft.status));
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
    setPreviewPanelOpen(false);
    setPreviewSearch('');
    setRejectDialogOpen(false);
    setRejectComment('');
  }, [activeTab]);

  useEffect(() => {
    if (!selectedDraftId) {
      setDraftForm(createDefaultDraftForm());
      setPreviewPanelOpen(false);
      setPreviewSearch('');
      setPreviewPageIndex(0);
      return;
    }

    const draft = drafts.find((item) => item.id === selectedDraftId) ?? null;
    setDraftForm(draft ? buildDraftFormFromDraft(draft) : createDefaultDraftForm());
  }, [selectedDraftId]);

  const sortedDrafts = useMemo(() => sortDrafts(drafts, draftSort), [drafts, draftSort]);
  const selectedDraft = drafts.find((draft) => draft.id === selectedDraftId) ?? null;
  const selectedGatewayDraftId = workMode === 'prod' ? (selectedDraft?.gatewayDraftId || '') : '';
  const draftTasksQuery = useQuery({
    queryKey: ['gateway-draft-tasks', workMode, selectedGatewayDraftId],
    queryFn: () => tasksApi.forDraft(selectedGatewayDraftId),
    enabled: workMode === 'prod' && activeTab === 'knowledgeProcessing' && /^\d+$/.test(selectedDraft?.gatewayDraftId ?? ''),
    staleTime: 10_000,
    refetchInterval:
      workMode === 'prod' &&
      activeTab === 'knowledgeProcessing' &&
      selectedDraft &&
      shouldPollDraftDetails(selectedDraft.status)
        ? 5_000
        : false,
  });

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
      : draftTasksQuery.data?.length
        ? draftTasksQuery.data
        : processingAuditQuery.data ?? [];
  const selectedFilesLabel =
    selectedFiles.length === 1 ? selectedFiles[0]?.name ?? '' : selectedFiles.length > 1 ? `Выбрано файлов: ${selectedFiles.length}` : '';
  const metadataValidationErrors = useMemo(() => validateDraftMetadata(draftForm), [draftForm]);
  const firstMetadataError = getFirstMetadataError(metadataValidationErrors);
  const hasMetadataValidationErrors = Boolean(firstMetadataError);
  const queueHasError = workMode === 'prod' && gatewayQueueQuery.isError;
  const journalHasError =
    workMode === 'prod' &&
    (selectedGatewayDraftId
      ? draftTasksQuery.isError && processingAuditQuery.isError
      : processingAuditQuery.isError);

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

  const getGatewayDraftId = (draft: DraftItem | null) =>
    workMode === 'prod' ? (draft?.gatewayDraftId || '') : '';

  const refreshGatewayDraftDetails = async (draftId: string, fallbackDraft?: DraftItem | null) => {
    const draft = fallbackDraft ?? getSelectedDraft(draftId);
    const gatewayDraftId = getGatewayDraftId(draft);
    if (!draft || !gatewayDraftId || !/^\d+$/.test(gatewayDraftId)) return;

    try {
      let details = await draftsApi.get(gatewayDraftId);
      if (
        !details.preview_metadata &&
        ['ready_for_approve', 'review_required', 'validation', 'approved'].includes(String(details.status ?? ''))
      ) {
        try {
          const previewDetails = await draftsApi.getPreview(gatewayDraftId);
          details = {
            ...details,
            ...previewDetails,
            preview_metadata: previewDetails.preview_metadata ?? details.preview_metadata,
            raw_data: details.raw_data ?? previewDetails.raw_data,
          };
        } catch {
          // Full draft detail is still usable; preview endpoint may be absent on older Gateway builds.
        }
      }
      const patch = draftPatchFromGateway(details, getSelectedDraft(draftId) ?? draft);
      const mergedDraft = { ...draft, ...patch };
      updateDraft(draftId, patch);

      if (activeDraftDetailsRequestRef.current === draftId) {
        setDraftForm(buildDraftFormFromDraft(mergedDraft));
      }
    } catch (error: any) {
      updateDraft(draftId, {
        gatewayErrorMessage: error?.message ?? 'Не удалось загрузить полную карточку черновика с сервера.',
      });
    }
  };

  const handleSelectDraft = (draftId: string) => {
    const draft = getSelectedDraft(draftId);
    activeDraftDetailsRequestRef.current = draftId;
    setSelectedDraftId(draftId);
    setDraftForm(draft ? buildDraftFormFromDraft(draft) : createDefaultDraftForm());

    if (workMode === 'prod') {
      void refreshGatewayDraftDetails(draftId, draft);
    }
  };

  useEffect(() => {
    if (
      workMode !== 'prod' ||
      activeTab !== 'knowledgeProcessing' ||
      !selectedDraft ||
      !shouldPollDraftDetails(selectedDraft.status)
    ) {
      return;
    }

    activeDraftDetailsRequestRef.current = selectedDraft.id;
    void refreshGatewayDraftDetails(selectedDraft.id, selectedDraft);

    const timer = window.setInterval(() => {
      void refreshGatewayDraftDetails(selectedDraft.id);
    }, 5_000);

    return () => window.clearInterval(timer);
  }, [activeTab, selectedDraft?.id, selectedDraft?.status, workMode]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    event.target.value = '';

    if (!files.length) return;

    setSelectedFiles(files);
  };

  const clearSourceInputs = () => {
    setSelectedFiles([]);
  };

  const createLocalDraft = (sourceName: string, useManualTitle = true) => {
    const id = createIdempotencyKey();
    const now = nextClock();
    const title = useManualTitle && draftForm.title.trim() ? draftForm.title.trim() : sourceName.replace(/\.[^.]+$/, '');
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
      validFrom: draftForm.validFrom.trim(),
      validUntil: draftForm.validUntil.trim(),
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
    return { id, title, draft: newDraft };
  };

  const uploadDraftFile = async (
    draftId: string,
    file: File,
    sourceLabel: string,
    fallbackDraft?: DraftItem,
    titleOverride?: string,
  ) => {
    const uploadTitle = titleOverride || draftForm.title.trim() || sourceLabel.replace(/\.[^.]+$/, '');
    const response = await draftsApi.create(file, {
      sourceType: draftForm.sourceType,
      title: uploadTitle,
      docCode: draftForm.docCode.trim() || undefined,
      mksOksCode: draftForm.mksOksCode.trim() || undefined,
      okstuCode: draftForm.okstuCode.trim() || undefined,
      era: draftForm.era,
      jurisdiction: draftForm.jurisdiction,
      issuingBody: draftForm.issuingBody.trim() || undefined,
      validFrom: draftForm.validFrom.trim() || undefined,
      validUntil: draftForm.validUntil.trim() || null,
      metadata: {
        manual: true,
        source_type: draftForm.sourceType,
        title: uploadTitle || undefined,
        doc_code: draftForm.docCode.trim() || undefined,
        year: draftForm.year.trim() || undefined,
        mks_oks_code: draftForm.mksOksCode.trim() || undefined,
        okstu_code: draftForm.okstuCode.trim() || undefined,
        era: draftForm.era,
        jurisdiction: draftForm.jurisdiction,
        issuing_body: draftForm.issuingBody.trim() || undefined,
        valid_from: draftForm.validFrom.trim() || undefined,
        valid_until: draftForm.validUntil.trim() || null,
      },
      idempotencyKey: createIdempotencyKey(),
    });

    const patch = draftPatchFromGateway(response, getSelectedDraft(draftId) ?? fallbackDraft ?? undefined);
    updateDraft(draftId, patch);
    if (response.document_key) {
      setDraftDocumentKeys((current) => {
        const next = Array.from(new Set([response.document_key, ...current]));
        writeStoredDraftDocumentKeys(next);
        return next;
      });
    }
    await queryClient.invalidateQueries({ queryKey: ['gateway-drafts', workMode] });
    await queryClient.invalidateQueries({ queryKey: ['gateway-documents', workMode] });
    await queryClient.invalidateQueries({ queryKey: ['gateway-documents-queue', workMode] });
    return { response, patch };
  };

  const handleCreateDraftFromFiles = async () => {
    if (!selectedFiles.length) {
      setNotice('Сначала выберите файлы для обработки.');
      return;
    }

    if (hasMetadataValidationErrors) {
      setNotice(`Черновики не созданы: ${firstMetadataError}`);
      return;
    }

    const filesToUpload = selectedFiles;
    const useManualTitle = filesToUpload.length === 1;
    let failedCount = 0;

    for (const file of filesToUpload) {
      const { id, title, draft } = createLocalDraft(file.name, useManualTitle);

      if (workMode === 'prod') {
        try {
          const { patch } = await uploadDraftFile(id, file, file.name, draft, title);
          handleRunDraftChecks(id, { ...draft, ...patch });
        } catch (error: any) {
          failedCount += 1;
          console.error('[handleCreateDraftFromFiles] upload failed:', error);
          updateDraft(id, {
            status: 'failed',
            progress: 100,
            note: 'Сервер не принял файл. Черновик помечен как failed.',
            gatewayErrorMessage: error?.message ?? String(error) ?? 'Не удалось отправить файл на сервер.',
          });
          setNotice(`Черновик «${title}» не удалось отправить на сервер.`);
        }
      } else {
        handleRunDraftChecks(id, draft);
      }
    }

    clearSourceInputs();
    setNotice(
      filesToUpload.length === 1
        ? failedCount
          ? 'Файл не удалось отправить на сервер.'
          : 'Черновик создан и отправлен на проверку.'
        : `Черновики созданы: ${filesToUpload.length - failedCount} из ${filesToUpload.length}.`,
    );
  };

  const handleCreateDraft = async () => {
    if (selectedFiles.length) {
      await handleCreateDraftFromFiles();
      return;
    }

    setNotice('Сначала выберите файлы для обработки.');
  };

  const handleSaveDraftMetadata = async () => {
    if (!selectedDraft) {
      setNotice('Сначала выберите черновик слева или создайте новый из выбранного файла.');
      return;
    }

    if (hasMetadataValidationErrors) {
      setNotice(`Метаданные не сохранены: ${firstMetadataError}`);
      return;
    }

    const metadataOverrides = buildMetadataOverridesFromForm(draftForm);

    if (workMode === 'prod') {
      const gatewayDraftId = selectedDraft.gatewayDraftId;
      if (!gatewayDraftId) {
        setNotice(`Метаданные для «${selectedDraft.title}» не сохранены: нет gateway id черновика.`);
        return;
      }

      try {
        await draftsApi.updateMetadata(gatewayDraftId, metadataOverrides);
        const refreshedDraft = await draftsApi.get(gatewayDraftId);
        const patch = draftPatchFromGateway(refreshedDraft, selectedDraft);
        updateDraft(selectedDraft.id, {
          ...patch,
          note: 'Метаданные сохранены на сервере и перечитаны из черновика.',
        });
        await queryClient.invalidateQueries({ queryKey: ['gateway-drafts', workMode] });
        setNotice(`Метаданные для «${selectedDraft.title}» сохранены на сервере.`);
      } catch (error: any) {
        updateDraft(selectedDraft.id, {
          note: 'Сервер пока не подтвердил сохранение метаданных.',
          gatewayErrorMessage:
            error?.message ??
            'PATCH /drafts/{id}/metadata не выполнен. Контракт описан в документации, но текущий backend мог еще не реализовать endpoint.',
        });
        setNotice(
          `Метаданные не сохранены на сервере: ${
            error?.message ?? 'endpoint сохранения метаданных пока недоступен в текущем backend.'
          }`,
        );
      }
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
      validFrom: draftForm.validFrom.trim(),
      validUntil: draftForm.validUntil.trim(),
      gatewayMetadataOverrides: metadataOverrides,
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

  const handleRunDraftChecks = (draftId: string, draftOverride?: DraftItem) => {
    const draft = draftOverride ?? getSelectedDraft(draftId);
    if (
      !draft ||
      draft.status === 'previewing' ||
      draft.status === 'ready_for_approve' ||
      draft.status === 'review_required' ||
      draft.status === 'validation' ||
      draft.status === 'approved' ||
      draft.status === 'discarded'
    ) {
      return;
    }

    updateDraft(draftId, {
      status: 'previewing',
      progress: 38,
      note: 'Проверяем метаданные и ищем дубликаты.',
    });
    setNotice(`Проверка черновика «${draft.title}» запущена.`);

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
            ? 'Проверка готова. Есть кандидаты на дубликаты.'
            : 'Проверка готова. Можно принимать документ.',
        });
        setNotice(`Проверка черновика «${draftAfterPreview.title}» завершена.`);
      }, 1100);

      previewTimersRef.current.push(timer);
      return;
    }

    const gatewayDraftId = draft.gatewayDraftId;
    if (!gatewayDraftId) {
      updateDraft(draftId, {
        status: 'failed',
        progress: 100,
        note: 'У черновика нет gateway id для запуска проверки.',
      });
      setNotice(`Проверку черновика «${draft.title}» не удалось запустить.`);
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

        const nextStatus = normalizeDraftStatusFromGateway(previewResponse?.status);
        updateDraft(draftId, {
          ...draftPatchFromGateway(previewResponse, draftAfterPreview),
          status: nextStatus === 'uploaded' ? 'ready_for_approve' : nextStatus,
          progress: nextStatus === 'previewing' ? 38 : draftProgressByStatus[nextStatus] ?? 72,
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
          note: nextStatus === 'review_required' || previewResponse?.decision_required
            ? 'Проверка готова. Требуется решение.'
            : 'Проверка готова. Можно принимать документ.',
        });
        setNotice(`Проверка черновика «${draftAfterPreview.title}» завершена.`);
      } catch (error: any) {
        updateDraft(draftId, {
          status: 'failed',
          progress: 100,
          note: 'Сервер не завершил проверку черновика.',
          gatewayErrorMessage: error?.message ?? 'Не удалось получить статус проверки черновика.',
        });
        setNotice(`Проверку черновика «${draft.title}» завершить не удалось.`);
      }
    })();
  };

  const handleDecision = async (draftId: string, action: 'approve' | 'reject' | 'confirm', comment?: string) => {
    const draft = getSelectedDraft(draftId);
    if (!draft) return;

    if (action === 'approve' && draft.status !== 'ready_for_approve') {
      setNotice('Сначала нужно дождаться завершения проверки черновика.');
      return;
    }

    if (action === 'confirm' && draft.status !== 'review_required') {
      setNotice('Подтверждение доступно только для черновиков со статусом «Требуется проверка».');
      return;
    }

    if (action === 'reject' && !['ready_for_approve', 'review_required'].includes(draft.status)) {
      return;
    }

    if (workMode === 'demo') {
      if (action === 'confirm') {
        updateDraft(draftId, {
          status: 'validation',
          progress: 88,
          gatewayMetadataOverrides: buildMetadataOverridesFromForm(draftForm),
          note: 'Черновик подтверждён. Запущена повторная проверка.',
        });
        setNotice(`Черновик «${draft.title}» подтверждён и отправлен на повторную проверку.`);
        return;
      }

      setDrafts((current) => current.filter((item) => item.id !== draftId));
      setSelectedDraftId('');
      setPreviewPanelOpen(false);
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
      setNotice(`Решение по «${draft.title}» не удалось отправить на сервер.`);
      return;
    }

    try {
      const metadataOverrides = action === 'reject' ? undefined : buildMetadataOverridesFromForm(draftForm);
      const response = await draftsApi.decide(gatewayDraftId, {
        action,
        comment:
          comment ||
          (action === 'approve'
            ? 'Метаданные проверены.'
            : action === 'confirm'
              ? 'Замечания просмотрены, черновик подтверждён.'
              : 'Черновик отклонён администратором.'),
        metadataOverrides,
      });
      const nextStatus = normalizeDraftStatusFromGateway(response?.status);
      const shouldRemoveDraft = action === 'reject' || nextStatus === 'approved' || nextStatus === 'discarded' || Boolean(response?.document_id);

      if (shouldRemoveDraft) {
        setDrafts((current) => current.filter((item) => item.id !== draftId));
        setSelectedDraftId('');
        setPreviewPanelOpen(false);
      } else {
        updateDraft(draftId, {
          ...draftPatchFromGateway(response, draft),
          status: nextStatus,
          progress: draftProgressByStatus[nextStatus] ?? draft.progress,
          gatewayMetadataOverrides: metadataOverrides,
          note:
            action === 'confirm'
              ? 'Черновик подтверждён. Запущена повторная проверка.'
              : response?.message ?? draft.note,
        });
      }

      const gatewayMessage = typeof response?.message === 'string' && response.message.trim() ? ` ${response.message}` : '';
      setNotice(
        action === 'approve'
          ? `Документ «${draft.title}» принят в базу знаний.${gatewayMessage}`
          : action === 'confirm'
            ? `Черновик «${draft.title}» подтверждён.${gatewayMessage}`
            : `Документ «${draft.title}» отклонён.${gatewayMessage}`,
      );
      await queryClient.invalidateQueries({ queryKey: ['gateway-drafts', workMode] });
      await queryClient.invalidateQueries({ queryKey: ['gateway-documents', workMode] });
      await queryClient.invalidateQueries({ queryKey: ['gateway-documents-queue', workMode] });
      await queryClient.invalidateQueries({ queryKey: ['gateway-knowledge-sections', workMode] });
    } catch (error: any) {
      updateDraft(draftId, {
        note:
          action === 'confirm'
            ? 'Сервер пока не принял подтверждение по черновику.'
            : 'Сервер не принял решение по черновику.',
        gatewayErrorMessage:
          error?.message ??
          (action === 'confirm'
            ? 'PATCH /drafts/{id}/decide action=confirm описан в документации, но текущий backend мог еще не реализовать этот сценарий.'
            : 'Не удалось отправить решение на сервер.'),
      });
      setNotice(`Не удалось отправить решение по «${draft.title}» на сервер: ${error?.message ?? 'контракт пока не реализован в коде backend.'}`);
    }
  };

  const handleOpenRejectDialog = () => {
    if (!selectedDraft || !canRejectDraft) return;
    setRejectComment('');
    setRejectDialogOpen(true);
  };

  const handleSubmitReject = () => {
    if (!selectedDraft) return;
    const comment = rejectComment.trim() || 'Черновик отклонён администратором.';
    setRejectDialogOpen(false);
    setRejectComment('');
    void handleDecision(selectedDraft.id, 'reject', comment);
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
        setNotice(`Черновик «${draft.title}» удалён на сервере.`);
      })
      .catch((error: any) => {
        updateDraft(draftId, {
          status: 'failed',
          progress: 100,
          note: 'Сервер не удалил черновик.',
          gatewayErrorMessage: error?.message ?? 'Не удалось удалить черновик на сервере.',
        });
        setNotice(`Черновик «${draft.title}» не удалось удалить на сервере.`);
      });
  };

  const handleOpenPreviewDialog = (draftId: string) => {
    const draft = getSelectedDraft(draftId);
    handleSelectDraft(draftId);
    setPreviewPageIndex(0);
    setPreviewError('');
    if (draft?.status === 'uploaded') {
      handleRunDraftChecks(draftId, draft);
    }
    setPreviewLoading(draft?.status === 'uploaded' || draft?.status === 'previewing');
    setPreviewDialogOpen(true);
  };

  const handleClosePreviewDialog = () => {
    setPreviewDialogOpen(false);
    setPreviewLoading(false);
    setPreviewError('');
  };

  const handleOpenPreviewPanel = (draftId = selectedDraftId) => {
    const draft = getSelectedDraft(draftId);
    if (!draft) return;

    handleSelectDraft(draftId);
    setPreviewPanelOpen(true);
    setPreviewPageIndex(0);
    setPreviewError('');
    if (draft.status === 'uploaded') {
      handleRunDraftChecks(draftId, draft);
    }
    setPreviewLoading(draft.status === 'uploaded' || draft.status === 'previewing');
  };

  const previewPages = selectedDraft ? buildPreviewPages(selectedDraft) : [];
  const currentPreviewPage = previewPages[Math.min(previewPageIndex, Math.max(previewPages.length - 1, 0))] ?? null;
  const currentPreviewText = currentPreviewPage?.lines.join('\n') ?? '';
  const normalizedPreviewSearch = previewSearch.trim().toLowerCase();
  const previewSearchMatchCount = countTextMatches(currentPreviewText, normalizedPreviewSearch);
  const workspaceDraft = selectedDraft ?? buildWorkspaceDraft(draftForm, selectedFilesLabel || '');
  const hasWorkspaceInput = Boolean(
    selectedDraft ||
      selectedFiles.length ||
      draftForm.title ||
      draftForm.docCode ||
      draftForm.year ||
      draftForm.mksOksCode ||
      draftForm.okstuCode ||
      draftForm.issuingBody,
  );
  const workspacePreviewPage = hasWorkspaceInput ? buildPreviewPages(workspaceDraft)[0] ?? null : null;
  const canApproveDraft = selectedDraft?.status === 'ready_for_approve';
  const canConfirmDraft = selectedDraft?.status === 'review_required';
  const canRejectDraft = selectedDraft?.status === 'ready_for_approve' || selectedDraft?.status === 'review_required';
  const canOpenKnowledgeBase = selectedDraft?.status === 'approved';
  const getFieldError = (field: keyof DraftForm) => metadataValidationErrors[field] ?? '';
  const renderMetadataFieldInput = (label: string) => {
    const commonSx = { minWidth: 0 };

    switch (label) {
      case 'Название':
        const titleError = getFieldError('title');
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.title}
            onChange={(event) => setDraftForm((current) => ({ ...current, title: trimLength(event.target.value, TITLE_MAX_LENGTH) }))}
            error={Boolean(titleError)}
            helperText={titleError}
            slotProps={{ htmlInput: { maxLength: TITLE_MAX_LENGTH } }}
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
        const docCodeError = getFieldError('docCode');
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.docCode}
            onChange={(event) => setDraftForm((current) => ({ ...current, docCode: sanitizeDocumentCode(event.target.value) }))}
            error={Boolean(docCodeError)}
            helperText={docCodeError}
            slotProps={{ htmlInput: { maxLength: DOC_CODE_MAX_LENGTH } }}
            sx={commonSx}
          />
        );
      case 'Год':
        const yearError = getFieldError('year');
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.year}
            onChange={(event) => setDraftForm((current) => ({ ...current, year: event.target.value.replace(/\D/g, '').slice(0, 4) }))}
            error={Boolean(yearError)}
            helperText={yearError}
            slotProps={{ htmlInput: { inputMode: 'numeric', pattern: '[0-9]*', maxLength: 4 } }}
            sx={commonSx}
          />
        );
      case 'МКС / ОКС':
        const mksOksError = getFieldError('mksOksCode');
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.mksOksCode}
            onChange={(event) => setDraftForm((current) => ({ ...current, mksOksCode: sanitizeClassifierCode(event.target.value) }))}
            error={Boolean(mksOksError)}
            helperText={mksOksError}
            slotProps={{ htmlInput: { maxLength: CLASSIFIER_CODE_MAX_LENGTH } }}
            sx={commonSx}
          />
        );
      case 'ОКСТУ':
        const okstuError = getFieldError('okstuCode');
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.okstuCode}
            onChange={(event) => setDraftForm((current) => ({ ...current, okstuCode: sanitizeOkstuCode(event.target.value) }))}
            error={Boolean(okstuError)}
            helperText={okstuError}
            slotProps={{ htmlInput: { maxLength: CLASSIFIER_CODE_MAX_LENGTH } }}
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
        const issuingBodyError = getFieldError('issuingBody');
        return (
          <TextField
            size="small"
            fullWidth
            value={draftForm.issuingBody}
            onChange={(event) =>
              setDraftForm((current) => ({ ...current, issuingBody: trimLength(event.target.value, ISSUING_BODY_MAX_LENGTH) }))
            }
            error={Boolean(issuingBodyError)}
            helperText={issuingBodyError}
            slotProps={{ htmlInput: { maxLength: ISSUING_BODY_MAX_LENGTH } }}
            sx={commonSx}
          />
        );
      case 'Дата начала действия':
        const validFromError = getFieldError('validFrom');
        return (
          <TextField
            size="small"
            fullWidth
            type="date"
            value={draftForm.validFrom}
            onChange={(event) => setDraftForm((current) => ({ ...current, validFrom: event.target.value }))}
            error={Boolean(validFromError)}
            helperText={validFromError}
            sx={commonSx}
          />
        );
      case 'Дата окончания действия':
        const validUntilError = getFieldError('validUntil');
        return (
          <TextField
            size="small"
            fullWidth
            type="date"
            value={draftForm.validUntil}
            onChange={(event) => setDraftForm((current) => ({ ...current, validUntil: event.target.value }))}
            error={Boolean(validUntilError)}
            helperText={validUntilError || 'Пусто = бессрочно'}
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
      bgcolor: 'transparent',
      borderColor: 'transparent',
      boxShadow: 'none',
    }),
  };
  const headerDividerSx = {
    mx: 0.75,
    borderBottomWidth: 2,
    borderColor: isLight ? 'rgba(14, 116, 144, 0.24)' : 'rgba(198, 214, 236, 0.26)',
  };
  const draftSectionButtonSx = {
    justifyContent: 'space-between',
    minHeight: 38,
    px: 1.2,
    py: 0.72,
    color: isLight ? 'rgba(15, 23, 42, 0.72)' : 'rgba(233, 237, 243, 0.74)',
    textTransform: 'none',
    '& .MuiButton-endIcon': {
      color: isLight ? 'rgba(15, 23, 42, 0.48)' : 'rgba(233, 237, 243, 0.5)',
    },
  };
  const draftSectionTitleSx = {
    fontSize: '0.82rem',
    fontWeight: 520,
    letterSpacing: '0.01em',
    color: isLight ? 'rgba(15, 23, 42, 0.72)' : 'rgba(233, 237, 243, 0.74)',
  };
  const metadataColumnTitleSx = {
    display: { xs: 'none', lg: 'block' },
    fontSize: '0.68rem',
    fontWeight: 620,
    letterSpacing: '0.045em',
    textTransform: 'uppercase',
    color: isLight ? 'rgba(15, 23, 42, 0.48)' : 'rgba(233, 237, 243, 0.5)',
  };
  const metadataRowTitleSx = {
    pt: 1,
    fontSize: '0.72rem',
    fontWeight: 610,
    letterSpacing: '0.012em',
    color: isLight ? 'rgba(15, 23, 42, 0.58)' : 'rgba(233, 237, 243, 0.58)',
  };
  const metadataValueSx = {
    overflowWrap: 'anywhere',
    pt: 1.05,
    fontSize: '0.82rem',
    fontWeight: 450,
    color: isLight ? 'rgba(15, 23, 42, 0.88)' : 'rgba(233, 237, 243, 0.88)',
  };
  const activeProcessingSection = activeKnowledgeProcessingSection as KnowledgeProcessingSection;
  const showUploadSection = activeProcessingSection === 'upload';
  const showDraftsSection = activeProcessingSection === 'drafts';
  const showRegistrySection = activeProcessingSection === 'registry';
  const showJournalSection = activeProcessingSection === 'journal';

  return (
    <Container maxWidth={false} disableGutters sx={{ py: 3, width: '100%' }}>
      <Stack spacing={2}>
        {showUploadSection && (
        <Paper variant="outlined" sx={{ p: 1.45, borderRadius: 3, ...panelSx }}>
          <Stack spacing={1.1}>
            <Stack spacing={0.85}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <FilePlus2 size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Box>
                  <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                    Загрузка и обработка документа
                  </Typography>
                </Box>
              </Stack>
              <Divider sx={headerDividerSx} />
            </Stack>

            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              sx={{ flexWrap: 'wrap', alignItems: 'center', '& .app-action-button': { whiteSpace: 'nowrap' } }}
            >
              <Button
                className="app-action-button"
                variant="contained"
                startIcon={<FileDown size={16} />}
                onClick={() => fileInputRef.current?.click()}
              >
                Выбрать файлы
              </Button>
              {selectedFilesLabel && <Chip label={selectedFilesLabel} size="small" variant="outlined" />}
              <input
                ref={fileInputRef}
                type="file"
                hidden
                multiple
                accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff"
                onChange={handleFileSelect}
              />
              <Button
                className="app-action-button"
                variant="outlined"
                startIcon={<PlayCircle size={16} />}
                onClick={() => void handleCreateDraft()}
                disabled={!selectedFiles.length || hasMetadataValidationErrors}
              >
                {selectedFiles.length > 1 ? 'Создать черновики' : 'Создать черновик'}
              </Button>
            </Stack>
          </Stack>
        </Paper>
        )}

        {showDraftsSection && (
        <Paper variant="outlined" sx={{ p: 1.45, borderRadius: 3, ...panelSx }}>
          <Stack spacing={1.1}>
            <Stack spacing={0.85}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <CheckCircle2 size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  Действия с черновиком
                </Typography>
              </Stack>
              <Divider sx={headerDividerSx} />
            </Stack>
            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              sx={{ flexWrap: 'wrap', alignItems: 'center', '& .app-action-button': { whiteSpace: 'nowrap' } }}
            >
              <Button
                className="app-action-button"
                variant="outlined"
                startIcon={<CheckCircle2 size={16} />}
                onClick={() => void handleSaveDraftMetadata()}
                disabled={!selectedDraft || hasMetadataValidationErrors}
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
                variant="contained"
                color="success"
                startIcon={<CheckCircle2 size={16} />}
                onClick={() => selectedDraft && void handleDecision(selectedDraft.id, 'approve')}
                disabled={!canApproveDraft || hasMetadataValidationErrors}
              >
                Принять в базу знаний
              </Button>
              <Button
                className="app-action-button"
                variant="contained"
                color="warning"
                startIcon={<CheckCircle2 size={16} />}
                onClick={() => selectedDraft && void handleDecision(selectedDraft.id, 'confirm')}
                disabled={!canConfirmDraft || hasMetadataValidationErrors}
              >
                Подтвердить проверку
              </Button>
              <Button
                className="app-action-button"
                variant="outlined"
                color="error"
                startIcon={<XCircle size={16} />}
                onClick={handleOpenRejectDialog}
                disabled={!canRejectDraft}
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
        )}

        {showDraftsSection && (
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

                <Divider sx={headerDividerSx} />

                <Stack direction="row" sx={{ justifyContent: 'flex-end' }}>
                  <TextField
                    select
                    size="small"
                    label="Сорт."
                    value={draftSort}
                    onChange={(event) => setDraftSort(event.target.value as DraftSort)}
                    sx={{
                      width: 104,
                      '& .MuiOutlinedInput-root': {
                        minHeight: 30,
                        height: 30,
                        borderRadius: 1.4,
                      },
                      '& .MuiInputBase-input': {
                        py: 0.25,
                        pr: '22px !important',
                        fontSize: '0.72rem',
                      },
                      '& .MuiInputLabel-root': {
                        fontSize: '0.68rem',
                        transform: 'translate(14px, 6px) scale(1)',
                      },
                      '& .MuiInputLabel-shrink': {
                        transform: 'translate(14px, -7px) scale(0.76)',
                      },
                      '& .MuiSelect-icon': {
                        right: 4,
                        fontSize: '1rem',
                      },
                    }}
                  >
                    <MenuItem value="updated_desc">Обновление</MenuItem>
                    <MenuItem value="name_asc">Название</MenuItem>
                    <MenuItem value="status">Статус</MenuItem>
                  </TextField>
                </Stack>
              </Stack>

              {workMode === 'prod' && gatewayDraftsQuery.isError && (
                <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                  Не удалось загрузить черновики с сервера.
                </Alert>
              )}

              <Box sx={{ overflow: 'hidden' }}>
                <Stack divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.16)' }} />} sx={{ maxHeight: 460, overflow: 'auto' }}>
                  {sortedDrafts.map((draft, index) => {
                    const isSelected = selectedDraftId === draft.id;
                    const hasSelection = Boolean(selectedDraftId);
                    const selectedBg = isLight ? 'rgba(14, 116, 144, 0.08)' : 'rgba(152, 217, 216, 0.08)';
                    const hoverBg = isLight ? 'rgba(14, 116, 144, 0.06)' : 'rgba(152, 217, 216, 0.06)';
                    const rowBg = isSelected ? selectedBg : index % 2 === 0 ? 'rgba(255,255,255,0.012)' : 'transparent';

                    return (
                      <Box
                        key={draft.id}
                        onClick={() => handleSelectDraft(draft.id)}
                        sx={{
                          px: 1,
                          py: 0.65,
                          cursor: 'pointer',
                          opacity: hasSelection && !isSelected ? 0.48 : 1,
                          bgcolor: rowBg,
                          borderLeft: `3px solid ${
                            isSelected ? (isLight ? 'rgba(2, 132, 199, 0.72)' : 'rgba(152, 217, 216, 0.72)') : 'transparent'
                          }`,
                          borderRadius: '10px',
                          transition: 'opacity 160ms ease, background-color 160ms ease, border-color 160ms ease',
                          '&:hover': {
                            opacity: 1,
                            bgcolor: hoverBg,
                          },
                        }}
                      >
                        <Box
                          sx={{
                            display: 'grid',
                            gridTemplateColumns: 'minmax(0, 1fr) auto auto auto',
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
                          <Box
                            title={getStatusLabel(draft.status)}
                            aria-label={getStatusLabel(draft.status)}
                            sx={{
                              width: 10,
                              height: 10,
                              borderRadius: '50%',
                              bgcolor: getStatusDotColor(draft.status),
                              boxShadow: `0 0 0 3px ${getStatusDotColor(draft.status)}24`,
                            }}
                          />
                          <Box
                            title={draft.notifications?.length ? `Уведомлений: ${draft.notifications.length}` : 'Уведомлений нет'}
                            aria-label={draft.notifications?.length ? `Уведомлений: ${draft.notifications.length}` : 'Уведомлений нет'}
                            sx={{
                              minWidth: 18,
                              height: 18,
                              px: 0.45,
                              borderRadius: 999,
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.68rem',
                              lineHeight: 1,
                              color: draft.notifications?.length ? '#fff' : 'transparent',
                              bgcolor: draft.notifications?.some((item) => String(item.severity).toLowerCase() === 'critical')
                                ? '#dc2626'
                                : draft.notifications?.length
                                  ? '#f97316'
                                  : 'transparent',
                            }}
                          >
                            {draft.notifications?.length || ''}
                          </Box>
                          <IconButton
                            aria-label={`Предпросмотр ${draft.title}`}
                            title="Предпросмотр документа"
                            size="small"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleOpenPreviewPanel(draft.id);
                            }}
                            sx={{
                              width: 26,
                              height: 26,
                              color: isLight ? '#0284c7' : '#98d9d8',
                              border: `1px solid ${isLight ? 'rgba(14, 116, 144, 0.22)' : 'rgba(152, 217, 216, 0.24)'}`,
                              '&:hover': {
                                bgcolor: isLight ? 'rgba(14, 116, 144, 0.08)' : 'rgba(152, 217, 216, 0.08)',
                              },
                            }}
                          >
                            <FileSearch size={14} />
                          </IconButton>
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
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={1}
                sx={{ alignItems: { xs: 'flex-start', sm: 'center' }, justifyContent: 'space-between' }}
              >
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                  <FileSearch size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                  <Box sx={{ minWidth: 0 }}>
                    <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                      Рабочая область черновика
                    </Typography>
                  </Box>
                </Stack>
                <Chip
                  label={
                    selectedDraft
                      ? workspaceDraft.gatewayDraftId
                        ? `draft_id ${workspaceDraft.gatewayDraftId}`
                        : 'draft_id не назначен'
                      : 'черновик не выбран'
                  }
                  size="small"
                  variant="outlined"
                  sx={{ flexShrink: 0 }}
                />
              </Stack>
              <Divider sx={headerDividerSx} />

              {!selectedDraft ? (
                <Box
                  sx={{
                    minHeight: 180,
                    display: 'grid',
                    placeItems: 'center',
                    borderRadius: 2.2,
                    bgcolor: isLight ? 'rgba(248, 250, 252, 0.55)' : 'rgba(255,255,255,0.022)',
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Черновик не выбран.
                  </Typography>
                </Box>
              ) : (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    lg: previewPanelOpen ? 'minmax(0, 1fr) minmax(360px, 0.86fr)' : '1fr',
                  },
                  gap: 1.25,
                  alignItems: 'start',
                }}
              >
                <Stack spacing={1}>
                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSx }}>
                    <Button
                      fullWidth
                      onClick={() => setMetadataOpen((current) => !current)}
                      endIcon={metadataOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      sx={draftSectionButtonSx}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <Typography sx={draftSectionTitleSx}>Сверка и правка метаданных</Typography>
                        <Chip label="первый шаг" size="small" variant="outlined" />
                      </Stack>
                    </Button>
                    <Divider sx={headerDividerSx} />
                    <Collapse in={metadataOpen}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', lg: '0.72fr 0.92fr 1.25fr auto' },
                          gap: 1,
                          alignItems: 'start',
                          p: 1.25,
                        }}
                      >
                        <Typography sx={metadataColumnTitleSx} />
                        <Typography sx={metadataColumnTitleSx}>
                          Текущее значение
                        </Typography>
                        <Typography sx={metadataColumnTitleSx}>
                          Новое значение
                        </Typography>
                        <Typography sx={metadataColumnTitleSx}>
                          Статус
                        </Typography>
                        {buildMetadataReviewRows(workspaceDraft, draftForm).map((row) => (
                          <React.Fragment key={row.label}>
                            <Typography sx={metadataRowTitleSx}>
                              {row.label}
                            </Typography>
                            <Typography sx={metadataValueSx}>
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
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSx }}>
                    <Button
                      fullWidth
                      onClick={() => setNotificationsOpen((current) => !current)}
                      endIcon={notificationsOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      disabled={!selectedDraft}
                      sx={draftSectionButtonSx}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <Typography sx={draftSectionTitleSx}>Уведомления обработки</Typography>
                        <Chip label={selectedDraft?.notifications?.length ?? 0} size="small" variant="outlined" />
                      </Stack>
                    </Button>
                    <Divider sx={headerDividerSx} />
                    <Collapse in={notificationsOpen}>
                      <Stack spacing={1} sx={{ p: 1.25 }}>
                        {selectedDraft?.notifications?.length ? (
                          selectedDraft.notifications.map((notification) => (
                            <Alert
                              key={`${notification.code}-${notification.message}`}
                              severity={getNotificationAlertSeverity(notification.severity)}
                              variant="outlined"
                              sx={{ borderRadius: 2 }}
                            >
                              <Typography sx={{ fontWeight: 560 }}>
                                {notification.code}
                                {notification.category ? ` · ${notification.category}` : ''}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {notification.message}
                              </Typography>
                              {(notification.location || notification.suggestedAction) && (
                                <Typography variant="caption" color="text.secondary">
                                  {[notification.location, notification.suggestedAction].filter(Boolean).join(' · ')}
                                </Typography>
                              )}
                            </Alert>
                          ))
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Уведомления по черновику не переданы.
                          </Typography>
                        )}
                      </Stack>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSx }}>
                    <Button
                      fullWidth
                      onClick={() => setRawJsonOpen((current) => !current)}
                      endIcon={rawJsonOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      disabled={!selectedDraft}
                      sx={draftSectionButtonSx}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <Typography sx={draftSectionTitleSx}>Raw JSON</Typography>
                        <Chip label={workspaceDraft.gatewayRawData ? 'исходный JSON' : 'нормализованный снимок'} size="small" variant="outlined" />
                      </Stack>
                    </Button>
                    <Divider sx={headerDividerSx} />
                    <Collapse in={rawJsonOpen}>
                      <Stack spacing={1} sx={{ p: 1.25 }}>
                        {!workspaceDraft.gatewayRawData && (
                          <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                            Исходный raw JSON не передан. Ниже показан нормализованный снимок черновика.
                          </Alert>
                        )}
                        <Box
                          component="pre"
                          sx={{
                            m: 0,
                            maxHeight: 320,
                            overflow: 'auto',
                            p: 1.25,
                            borderRadius: 2,
                            bgcolor: isLight ? 'rgba(15, 23, 42, 0.05)' : 'rgba(2, 6, 12, 0.62)',
                            color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)',
                            fontSize: '0.76rem',
                            lineHeight: 1.45,
                            whiteSpace: 'pre-wrap',
                            overflowWrap: 'anywhere',
                          }}
                        >
                          {JSON.stringify(buildDraftRawJson(workspaceDraft, draftForm), null, 2)}
                        </Box>
                      </Stack>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSx }}>
                    <Button
                      fullWidth
                      onClick={() => setGatewayDetailsOpen((current) => !current)}
                      endIcon={gatewayDetailsOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      disabled={!selectedDraft}
                      sx={draftSectionButtonSx}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <Typography sx={draftSectionTitleSx}>Данные обработки</Typography>
                        <Chip label={workspaceDraft.gatewayDraftId ? 'есть draft_id' : 'локальный черновик'} size="small" variant="outlined" />
                      </Stack>
                    </Button>
                    <Divider sx={headerDividerSx} />
                    <Collapse in={gatewayDetailsOpen}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '0.74fr 1fr 0.74fr 1fr' },
                          gap: 1,
                          p: 1.25,
                        }}
                      >
                        {[
                          ['draft_id', workspaceDraft.gatewayDraftId || 'не назначен'],
                          ['task_id', workspaceDraft.gatewayTaskId],
                          ['version_id', workspaceDraft.gatewayVersionId],
                          ['document_key', workspaceDraft.gatewayDocumentKey],
                          ['document_id', workspaceDraft.gatewayPromotedDocumentId],
                          ['file_hash_sha256', workspaceDraft.gatewayFileHashSha256],
                          ['title_key', workspaceDraft.gatewayTitleKey],
                          ['title_hash_sha256', workspaceDraft.gatewayTitleHashSha256],
                          ['ошибка обработки', workspaceDraft.gatewayErrorMessage || workspaceDraft.gatewayErrorCode],
                        ].map(([label, value]) => (
                          <React.Fragment key={label}>
                            <Typography variant="caption" color="text.secondary">
                              {label}
                            </Typography>
                            <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>
                              {displayValue(value)}
                            </Typography>
                          </React.Fragment>
                        ))}
                      </Box>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSx }}>
                    <Button
                      fullWidth
                      onClick={() => setClassificationOpen((current) => !current)}
                      endIcon={classificationOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      disabled={!selectedDraft}
                      sx={draftSectionButtonSx}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <Typography sx={draftSectionTitleSx}>Классификация</Typography>
                        <Chip label={workspaceDraft.mksOksCode || workspaceDraft.okstuCode ? 'заполнено частично' : 'не заполнено'} size="small" variant="outlined" />
                      </Stack>
                    </Button>
                    <Divider sx={headerDividerSx} />
                    <Collapse in={classificationOpen}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '0.8fr 1fr 0.8fr 1fr' },
                          gap: 1,
                          p: 1.25,
                        }}
                      >
                        {[
                          ['МКС / ОКС', workspaceDraft.mksOksCode],
                          ['ОКСТУ', workspaceDraft.okstuCode],
                          ['Тип источника', workspaceDraft.sourceType],
                          ['Эра', workspaceDraft.era],
                          ['Юрисдикция', workspaceDraft.jurisdiction],
                          ['Издатель', workspaceDraft.issuingBody],
                          ['Категории', 'не переданы'],
                          ['Confidence', workspaceDraft.confidence ? `${Math.round(workspaceDraft.confidence * 100)}%` : 'не передано'],
                        ].map(([label, value]) => (
                          <React.Fragment key={label}>
                            <Typography variant="caption" color="text.secondary">
                              {label}
                            </Typography>
                            <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>
                              {displayValue(value)}
                            </Typography>
                          </React.Fragment>
                        ))}
                      </Box>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSx }}>
                    <Button
                      fullWidth
                      onClick={() => setDuplicatesOpen((current) => !current)}
                      endIcon={duplicatesOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      disabled={!selectedDraft}
                      sx={draftSectionButtonSx}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <Typography sx={draftSectionTitleSx}>Дубликаты</Typography>
                        <Chip label={selectedDraft?.duplicates.length ?? 0} size="small" variant="outlined" />
                      </Stack>
                    </Button>
                    <Divider sx={headerDividerSx} />
                    <Collapse in={duplicatesOpen}>
                      <Stack spacing={1} sx={{ p: 1.25 }}>
                        {selectedDraft?.duplicates.length ? (
                          selectedDraft.duplicates.map((duplicate) => (
                            <Alert key={duplicate.title} severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                              <Typography sx={{ fontWeight: 560 }}>{duplicate.title}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {duplicate.reason} · похожесть {Math.round(duplicate.similarity * 100)}%
                              </Typography>
                            </Alert>
                          ))
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Кандидаты на дубликаты не переданы.
                          </Typography>
                        )}
                      </Stack>
                    </Collapse>
                  </Paper>

                  <Paper variant="outlined" sx={{ borderRadius: 2.2, overflow: 'hidden', ...panelSx }}>
                    <Button
                      fullWidth
                      onClick={() => setProcessingStatusOpen((current) => !current)}
                      endIcon={processingStatusOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      disabled={!selectedDraft}
                      sx={draftSectionButtonSx}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <Typography sx={draftSectionTitleSx}>Статус обработки</Typography>
                        <Chip label={getStatusLabel(workspaceDraft.status)} size="small" variant="outlined" />
                      </Stack>
                    </Button>
                    <Divider sx={headerDividerSx} />
                    <Collapse in={processingStatusOpen}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: '1fr', md: '0.75fr 1fr 0.75fr 1fr' },
                          gap: 1,
                          p: 1.25,
                        }}
                      >
                        {[
                          ['Статус', getStatusLabel(workspaceDraft.status)],
                          ['Прогресс', `${workspaceDraft.progress}%`],
                          ['Обновлен', workspaceDraft.updatedAt],
                          ['Комментарий', workspaceDraft.note],
                        ].map(([label, value]) => (
                          <React.Fragment key={label}>
                            <Typography variant="caption" color="text.secondary">
                              {label}
                            </Typography>
                            <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>
                              {displayValue(value)}
                            </Typography>
                          </React.Fragment>
                        ))}
                      </Box>
                    </Collapse>
                  </Paper>
                </Stack>

                {previewPanelOpen && selectedDraft && (
                  <Paper variant="outlined" sx={{ p: 1.2, borderRadius: 2.4, ...panelSx }}>
                    <Stack spacing={1.1}>
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
                        <Box sx={{ minWidth: 0 }}>
                          <Typography sx={{ fontWeight: 560 }}>Предпросмотр документа</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {selectedDraft.title} · страница {previewPageIndex + 1} из {previewPages.length || 1}
                          </Typography>
                        </Box>
                        <Stack direction="row" spacing={0.5}>
                          <IconButton size="small" onClick={() => handleOpenPreviewDialog(selectedDraft.id)}>
                            <Maximize2 size={16} />
                          </IconButton>
                          <IconButton size="small" onClick={() => setPreviewPanelOpen(false)}>
                            <X size={16} />
                          </IconButton>
                        </Stack>
                      </Stack>
                      <Divider sx={headerDividerSx} />

                      <TextField
                        size="small"
                        value={previewSearch}
                        onChange={(event) => setPreviewSearch(event.target.value)}
                        placeholder="Поиск по предпросмотру"
                        fullWidth
                      />
                      {normalizedPreviewSearch && (
                        <Chip
                          label={previewSearchMatchCount ? `${previewSearchMatchCount} совп.` : 'Нет совпадений'}
                          size="small"
                          variant="outlined"
                          sx={{ width: 'fit-content' }}
                        />
                      )}

                      <Paper
                        variant="outlined"
                        sx={{
                          minHeight: 520,
                          maxHeight: 'calc(100vh - 260px)',
                          overflow: 'auto',
                          p: 2,
                          borderRadius: 2,
                          bgcolor: '#fbf7ef',
                          borderColor: 'rgba(99, 89, 68, 0.22)',
                          color: '#202020',
                          fontFamily: 'Georgia, serif',
                        }}
                      >
                        {currentPreviewPage ? (
                          <Stack spacing={1.4}>
                            <Box>
                              <Typography variant="caption" sx={{ color: '#7c6f57' }}>
                                {currentPreviewPage.title}
                              </Typography>
                              <Typography variant="h6" sx={{ mt: 0.45, color: '#222', fontFamily: 'Georgia, serif' }}>
                                {selectedDraft.preview?.title ?? selectedDraft.title}
                              </Typography>
                            </Box>
                            <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.7, fontFamily: 'inherit' }}>
                              {renderHighlightedText(currentPreviewText, normalizedPreviewSearch, isLight)}
                            </Typography>
                          </Stack>
                        ) : (
                          <Typography sx={{ color: '#6f6757', fontFamily: 'Georgia, serif' }}>Нет предпросмотра</Typography>
                        )}
                      </Paper>

                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                        <Button
                          variant="outlined"
                          startIcon={<ChevronLeft size={16} />}
                          onClick={() => setPreviewPageIndex((current) => Math.max(current - 1, 0))}
                          disabled={previewPageIndex === 0}
                        >
                          Назад
                        </Button>
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
                  </Paper>
                )}
              </Box>
              )}
            </Stack>
          </Paper>
        </Box>
        )}

        {showRegistrySection && <DocumentRegistryPanel documents={publishedDocuments} />}

        {(showUploadSection || showJournalSection) && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: showUploadSection && showJournalSection ? '1fr 1fr' : '1fr' }, gap: 3 }}>
          {showUploadSection && (
          <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
            <Stack spacing={1.1} sx={{ mb: 1.4 }}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <RotateCw size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  Очередь обработки
                </Typography>
              </Stack>
              <Divider sx={headerDividerSx} />
            </Stack>

            {queueHasError && (
              <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2, mb: 1.2 }}>
                Не удалось загрузить очередь обработки с сервера.
              </Alert>
            )}
            {!queueHasError && gatewayQueue.length === 0 && (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2, mb: 1.2 }}>
                Очередь обработки пуста.
              </Alert>
            )}
            {gatewayQueue.length > 0 && (
              <Paper variant="outlined" sx={{ overflow: 'hidden', borderRadius: 1.8, ...tableSx }}>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '1.6fr 0.9fr 0.6fr 0.7fr' },
                    gap: 1,
                    alignItems: 'center',
                    px: 1.2,
                    py: 0.75,
                    borderBottom: '1px solid rgba(198, 214, 236, 0.24)',
                    bgcolor: isLight ? 'rgba(15, 23, 42, 0.035)' : 'rgba(255,255,255,0.025)',
                  }}
                >
                  {['Документ', 'Этап', 'Прогресс', 'Статус'].map((label, index) => (
                    <Typography
                      key={label}
                      variant="caption"
                      sx={{
                        fontSize: '0.68rem',
                        fontWeight: 620,
                        letterSpacing: '0.025em',
                        textTransform: 'uppercase',
                        color: isLight ? 'rgba(15, 23, 42, 0.56)' : 'rgba(230, 236, 244, 0.74)',
                        textAlign: index === 3 ? 'right' : 'left',
                      }}
                    >
                      {label}
                    </Typography>
                  ))}
                </Box>
                <Stack divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.12)' }} />}>
                  {gatewayQueue.map((item, index) => (
                    <Box
                      key={item.id}
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '1.6fr 0.9fr 0.6fr 0.7fr' },
                        gap: 1,
                        alignItems: 'center',
                        px: 1.2,
                        py: 0.85,
                        bgcolor: index % 2 === 0 ? 'rgba(255,255,255,0.012)' : 'transparent',
                        '&:hover': {
                          bgcolor: isLight ? 'rgba(14, 116, 144, 0.05)' : 'rgba(123, 166, 227, 0.055)',
                        },
                      }}
                    >
                      <Typography sx={{ fontSize: '0.84rem', fontWeight: 520, pr: 1 }}>{item.document}</Typography>
                      <Typography variant="caption" sx={{ color: isLight ? 'rgba(15, 23, 42, 0.64)' : 'rgba(222, 230, 241, 0.68)' }}>
                        {item.stage}
                      </Typography>
                      <Typography variant="caption" sx={{ color: isLight ? 'rgba(15, 23, 42, 0.64)' : 'rgba(222, 230, 241, 0.68)' }}>
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
          )}

          {showJournalSection && (
          <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSx }}>
            <Stack spacing={1.1} sx={{ mb: 1.4 }}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                  <ShieldCheck size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                  <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                    Журнал обработки
                  </Typography>
                </Stack>
                <Chip label={gatewayProcessingLogs.length} size="small" variant="outlined" />
              </Stack>
              <Divider sx={headerDividerSx} />
            </Stack>

            {journalHasError && (
              <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                Не удалось загрузить журнал обработки с сервера.
              </Alert>
            )}
            {!journalHasError && gatewayProcessingLogs.length === 0 && (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                Журнал обработки пуст.
              </Alert>
            )}
            {gatewayProcessingLogs.length > 0 && (
              <Paper variant="outlined" sx={{ overflow: 'hidden', borderRadius: 1.8, ...tableSx }}>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '28px 82px 1fr 110px 2.1fr 126px 104px' },
                    gap: 1,
                    alignItems: 'center',
                    px: 1.2,
                    py: 0.75,
                    borderBottom: '1px solid rgba(198, 214, 236, 0.24)',
                    bgcolor: isLight ? 'rgba(15, 23, 42, 0.035)' : 'rgba(255,255,255,0.025)',
                  }}
                >
                  <Box />
                  {['Время', 'Объект', 'Этап', 'Событие', 'Статус', 'Доступ'].map((label) => (
                    <Typography
                      key={label}
                      variant="caption"
                      sx={{
                        fontSize: '0.68rem',
                        fontWeight: 620,
                        letterSpacing: '0.025em',
                        textTransform: 'uppercase',
                        color: isLight ? 'rgba(15, 23, 42, 0.56)' : 'rgba(230, 236, 244, 0.74)',
                      }}
                    >
                      {label}
                    </Typography>
                  ))}
                </Box>
                <Stack divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.22)', borderBottomWidth: 1 }} />} sx={{ maxHeight: 'calc(100vh - 250px)', overflow: 'auto' }}>
                  {gatewayProcessingLogs.map((log, index) => (
                    <Box
                      key={log.id}
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: { xs: '28px 82px 1fr 110px 2.1fr 126px 104px' },
                        gap: 1,
                        alignItems: 'center',
                        px: 1.2,
                        py: 0.7,
                        bgcolor: index % 2 === 0 ? 'rgba(255,255,255,0.012)' : 'transparent',
                        '&:hover': {
                          bgcolor: isLight ? 'rgba(14, 116, 144, 0.05)' : 'rgba(123, 166, 227, 0.055)',
                        },
                      }}
                    >
                      <Box
                        title={log.retryStatus}
                        sx={{
                          width: 10,
                          height: 10,
                          borderRadius: '50%',
                          bgcolor: getLogDotColor(log.retryStatus),
                          boxShadow: `0 0 0 3px ${getLogDotColor(log.retryStatus)}24`,
                        }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {log.time || '—'}
                      </Typography>
                      <Typography variant="caption" title={log.document} sx={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 560 }}>
                        {log.document}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {log.stage}
                      </Typography>
                      <Typography variant="caption" title={log.event} sx={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {log.event}
                      </Typography>
                      <Chip label={log.retryStatus} size="small" variant="outlined" />
                      <Typography variant="caption" color="text.secondary">
                        {log.visibility}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}
          </Paper>
          )}
        </Box>
        )}

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

                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ alignItems: { xs: 'stretch', sm: 'center' } }}>
                  <TextField
                    size="small"
                    value={previewSearch}
                    onChange={(event) => setPreviewSearch(event.target.value)}
                    placeholder="Поиск по предпросмотру"
                    sx={{ minWidth: { xs: 0, sm: 320 } }}
                  />
                  {normalizedPreviewSearch && (
                    <Chip
                      label={previewSearchMatchCount ? `${previewSearchMatchCount} совп.` : 'Нет совпадений'}
                      size="small"
                      variant="outlined"
                      sx={{ width: 'fit-content' }}
                    />
                  )}
                </Stack>

                <Paper
                  variant="outlined"
                  sx={{
                    minHeight: '62vh',
                    maxHeight: '70vh',
                    overflow: 'auto',
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
                        {renderHighlightedText(currentPreviewText, normalizedPreviewSearch, isLight)}
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

        <Dialog open={rejectDialogOpen && Boolean(selectedDraft)} onClose={() => setRejectDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Отклонить черновик</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={1.2}>
              <Typography variant="body2" color="text.secondary">
                Причина попадёт в комментарий к решению и останется в карточке черновика.
              </Typography>
              <TextField
                label="Причина отклонения"
                value={rejectComment}
                onChange={(event) => setRejectComment(event.target.value)}
                multiline
                minRows={3}
                fullWidth
                autoFocus
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setRejectDialogOpen(false)}>Отмена</Button>
            <Button color="error" variant="contained" onClick={handleSubmitReject}>
              Отклонить черновик
            </Button>
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
