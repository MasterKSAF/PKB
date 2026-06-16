import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
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
import { Download, FileText, History, Layers3, Maximize2, Search, X } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useUIStore } from '../store/uiStore';
import { downloadPreviewFile } from '../utils/downloadPreview';
import { type Document } from '../utils/mockData';
import { documentsApi, registryApi } from '../utils/http';

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
};

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

const normalizeText = (value: unknown) => String(value ?? '').trim();

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
    status: status || 'не указан',
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
    const body = normalizeText(item?.text ?? item?.content ?? item?.body ?? item?.preview ?? item?.excerpt);

    return {
      title: `${title}${number ? ` · стр. ${number}` : ''}`,
      lines: body ? body.split(/\r?\n/).filter(Boolean) : ['Текст страницы не передан.'],
    };
  });
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
      lines: [
        `Код: ${detail?.doc_code ?? 'не указан'}`,
        `Юрисдикция: ${detail?.jurisdiction ?? 'не указана'}`,
        `Издатель: ${detail?.issuing_body ?? 'не указан'}`,
        `Классификация: ${detail?.mks_oks_code ?? detail?.okstu_code ?? 'не указана'}`,
      ],
    },
    {
      title: 'История и версии',
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
    detail?.jurisdiction ? `Юрисдикция: ${detail.jurisdiction}` : '',
    detail?.validity_status ? `Статус действия: ${detail.validity_status}` : '',
    detail?.issuing_body ? `Издатель: ${detail.issuing_body}` : '',
    detail?.latest_version?.version ? `Последняя версия: ${detail.latest_version.version}` : '',
    versions.length ? `Версии: ${versions.map((item) => item.label).join(', ')}` : '',
    history.length ? `История: ${history.map((item) => `${item.action ?? 'Событие'} ${item.at ?? ''}`.trim()).join(' · ')}` : '',
    errors.length ? `Последняя ошибка: ${(errors[0] as any)?.error_message ?? 'не указана'}` : '',
    parameters?.extraction_confidence ? `Точность извлечения: ${Math.round(parameters.extraction_confidence * 100)}%` : '',
  ];

  return previewLines.filter(Boolean).join('\n');
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
    bgcolor: 'rgba(255, 255, 255, 0.94)',
    borderColor: 'rgba(14, 116, 144, 0.28)',
    boxShadow: '0 0 0 1px rgba(14, 116, 144, 0.14), 0 14px 34px rgba(15,23,42,0.06)',
  }),
});

export const DocumentRegistryPanel: React.FC<{ documents: Document[] }> = ({ documents }) => {
  const { themeMode, workMode } = useUIStore();
  const isLight = themeMode === 'light';
  const [search, setSearch] = useState('');
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [versionsOpen, setVersionsOpen] = useState(false);
  const [previewPageIndex, setPreviewPageIndex] = useState(0);
  const [previewSearch, setPreviewSearch] = useState('');
  const [selectedVersionIds, setSelectedVersionIds] = useState<string[]>([]);

  const filteredDocuments = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    const sorted = [...documents].sort((left, right) => {
      const rightTime = new Date(right.updatedAt || 0).getTime();
      const leftTime = new Date(left.updatedAt || 0).getTime();
      return rightTime - leftTime || left.name.localeCompare(right.name, 'ru');
    });

    if (!normalized) return sorted;

    return sorted.filter((document) =>
      [document.id, document.name, document.type, document.source, document.version, document.sectionId, document.group]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalized)),
    );
  }, [documents, search]);

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
    queryFn: () => registryApi.document(selectedDocument!.id),
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

  const detail = workMode === 'prod' ? detailQuery.data : buildDemoDetail(selectedDocument);
  const versions = workMode === 'prod' ? extractVersionItems(versionsQuery.data) : buildDemoVersions(selectedDocument);
  const history = workMode === 'prod' ? (historyQuery.data ?? []) : buildDemoHistory(selectedDocument);
  const errors = workMode === 'prod' ? (errorsQuery.data ?? []) : buildDemoErrors(selectedDocument);
  const parameters = workMode === 'prod' ? parametersQuery.data : buildDemoParameters(selectedDocument);
  const previewPages = useMemo(
    () => {
      if (workMode !== 'prod') return buildDemoPages(selectedDocument, detail);

      const pages = extractPageEntries(pagesQuery.data);
      return pages.length ? pages : buildDemoPages(selectedDocument, detail);
    },
    [detail, pagesQuery.data, selectedDocument, workMode],
  );
  const selectedPreviewPage = previewPages[Math.min(previewPageIndex, Math.max(previewPages.length - 1, 0))] ?? null;
  const previewText = buildPreviewText(selectedDocument, detail, versions, history, errors, parameters);
  const compareVersions = versions.filter((version) => selectedVersionIds.includes(version.id)).slice(0, 2);
  const totalVersions = Number(detail?.total_versions ?? versions.length ?? 0);
  const selectedVersionRows = useMemo(() => {
    if (selectedVersionIds.length) return versions.filter((version) => selectedVersionIds.includes(version.id)).slice(0, 2);
    return versions.slice(0, 2);
  }, [selectedVersionIds, versions]);
  const previewSearchMatchCount = useMemo(() => {
    const normalized = previewSearch.trim().toLowerCase();
    if (!normalized || !selectedPreviewPage) return 0;

    return selectedPreviewPage.lines.join('\n').toLowerCase().split(normalized).length - 1;
  }, [previewSearch, selectedPreviewPage]);

  useEffect(() => {
    if (versionsOpen && !selectedVersionIds.length && selectedVersionRows.length) {
      setSelectedVersionIds(selectedVersionRows.map((version) => version.id));
    }
  }, [selectedVersionIds.length, selectedVersionRows, versionsOpen]);

  useEffect(() => {
    setPreviewOpen(false);
    setVersionsOpen(false);
    setPreviewPageIndex(0);
    setPreviewSearch('');
    setSelectedVersionIds([]);
  }, [selectedDocumentId]);

  useEffect(() => {
    if (previewOpen && previewPages.length === 0) {
      setPreviewPageIndex(0);
    }
  }, [previewOpen, previewPages.length]);

  const summaryChips = [
    { label: `Версий: ${totalVersions}`, value: totalVersions },
    { label: `История: ${history.length}`, value: history.length },
    { label: `Ошибки: ${errors.length}`, value: errors.length },
    { label: `Страниц: ${previewPages.length}`, value: previewPages.length },
  ];

  return (
    <Stack spacing={2.2}>
      <Paper variant="outlined" sx={{ p: 1.9, borderRadius: 3, ...panelSxFor(isLight) }}>
        <Stack spacing={1.4}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Layers3 size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
            <Box>
              <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                Реестр документов
              </Typography>
            </Box>
          </Stack>

          <TextField
            fullWidth
            size="small"
            label="Поиск по реестру"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Название, код, источник, версия, раздел"
            slotProps={{
              input: {
                startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.72 }} />,
              },
            }}
          />

          {workMode === 'prod' && detailQuery.isError && (
            <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
              Gateway не вернул сведения по выбранному документу.
            </Alert>
          )}

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'minmax(280px, 360px) minmax(0, 1fr)' }, gap: 2 }}>
            <Paper variant="outlined" sx={{ p: 1, borderRadius: 2.2, ...tableSxFor(isLight) }}>
              <Stack spacing={1}>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography sx={{ fontWeight: 560 }}>Документы</Typography>
                  <Chip size="small" label={`${filteredDocuments.length}`} variant="outlined" />
                </Stack>

                <TableContainer sx={{ maxHeight: 560, overflow: 'auto' }}>
                  <Table size="small" stickyHeader sx={{ '& .MuiTableCell-root': { borderBottomColor: 'rgba(198, 214, 236, 0.12)' } }}>
                    <TableHead>
                      <TableRow>
                        <TableCell>Документ</TableCell>
                        <TableCell>Версия</TableCell>
                        <TableCell>Источник</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredDocuments.map((document) => {
                        const selected = selectedDocument?.id === document.id;
                        return (
                          <TableRow
                            key={document.id}
                            hover
                            selected={selected}
                            onClick={() => setSelectedDocumentId(document.id)}
                            sx={{ cursor: 'pointer' }}
                          >
                            <TableCell>
                              <Typography sx={{ fontWeight: 560, lineHeight: 1.3 }}>{document.name}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {document.type} · {document.updatedAt || 'без даты'}
                              </Typography>
                            </TableCell>
                            <TableCell>{document.version}</TableCell>
                            <TableCell>{document.source}</TableCell>
                          </TableRow>
                        );
                      })}

                      {filteredDocuments.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={3} sx={{ py: 3, textAlign: 'center' }}>
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

            <Paper variant="outlined" sx={{ p: 1.35, borderRadius: 2.2, ...panelSxFor(isLight) }}>
              {selectedDocument ? (
                <Stack spacing={1.3}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between', gap: 1 }}>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography sx={{ fontWeight: 560, lineHeight: 1.3 }}>{selectedDocument.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {selectedDocument.id} · {selectedDocument.type} · {selectedDocument.source}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                      <Button variant="outlined" size="small" startIcon={<Maximize2 size={15} />} onClick={() => setPreviewOpen(true)}>
                        Preview
                      </Button>
                      <Button variant="outlined" size="small" startIcon={<FileText size={15} />} onClick={() => setVersionsOpen(true)}>
                        Версии
                      </Button>
                    </Stack>
                  </Stack>

                  <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                    <Chip label={selectedDocument.version} size="small" variant="outlined" />
                    <Chip label={selectedDocument.ocrStatus} size="small" variant="outlined" />
                    <Chip label={selectedDocument.indexStatus} size="small" variant="outlined" />
                    <Chip label={`Обновлен: ${selectedDocument.updatedAt || 'не указано'}`} size="small" variant="outlined" />
                  </Stack>

                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
                      gap: 1,
                    }}
                  >
                    {summaryChips.map((item) => (
                      <Paper key={item.label} variant="outlined" sx={{ p: 1, borderRadius: 2, ...panelSxFor(isLight) }}>
                        <Typography variant="caption" color="text.secondary">
                          {item.label}
                        </Typography>
                        <Typography sx={{ fontWeight: 560, mt: 0.25 }}>{item.value}</Typography>
                      </Paper>
                    ))}
                  </Box>

                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' },
                      gap: 1,
                    }}
                  >
                    <Paper variant="outlined" sx={{ p: 1.1, borderRadius: 2, ...panelSxFor(isLight) }}>
                      <Typography variant="caption" color="text.secondary">
                        Метаданные
                      </Typography>
                      <Stack spacing={0.35} sx={{ mt: 0.5 }}>
                        <Typography sx={{ fontWeight: 560 }}>{detail?.title ?? selectedDocument.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {detail?.doc_code ? `Код: ${detail.doc_code}` : 'Код не передан'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {detail?.source_type ? `Тип источника: ${detail.source_type}` : 'Тип источника не передан'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {detail?.jurisdiction ? `Юрисдикция: ${detail.jurisdiction}` : 'Юрисдикция не передана'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {detail?.issuing_body ? `Издатель: ${detail.issuing_body}` : 'Издатель не передан'}
                        </Typography>
                      </Stack>
                    </Paper>

                    <Paper variant="outlined" sx={{ p: 1.1, borderRadius: 2, ...panelSxFor(isLight) }}>
                      <Typography variant="caption" color="text.secondary">
                        Контроль и статусы
                      </Typography>
                      <Stack spacing={0.35} sx={{ mt: 0.5 }}>
                        <Typography sx={{ fontWeight: 560 }}>
                          {typeof parameters?.extraction_confidence === 'number'
                            ? `Точность извлечения: ${Math.round(parameters.extraction_confidence * 100)}%`
                            : 'Точность извлечения не указана'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {parameters?.unconfirmed_fields?.length
                            ? `Неподтвержденные поля: ${parameters.unconfirmed_fields.join(', ')}`
                            : 'Неподтвержденные поля не переданы.'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {detail?.validity_status ? `Статус действия: ${detail.validity_status}` : 'Статус действия не передан'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {detail?.classification_status
                            ? `Классификация: ${JSON.stringify(detail.classification_status)}`
                            : 'Статус классификации не передан'}
                        </Typography>
                      </Stack>
                    </Paper>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.8 }}>
                      Последние версии
                    </Typography>
                    <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                      {versions.slice(0, 4).map((version) => (
                        <Chip key={version.id} label={version.label} variant="outlined" size="small" />
                      ))}
                    </Stack>
                  </Box>

                  {history.length > 0 && (
                    <Paper variant="outlined" sx={{ p: 1.1, borderRadius: 2, ...panelSxFor(isLight) }}>
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.9 }}>
                        <History size={16} color={isLight ? '#0284c7' : '#98d9d8'} />
                        <Typography sx={{ fontWeight: 560 }}>История</Typography>
                      </Stack>
                      <Stack spacing={0.7}>
                        {history.slice(0, 4).map((item: any, index: number) => (
                          <Box key={item.id ?? index} sx={{ borderBottom: index < 3 ? '1px solid rgba(198,214,236,0.12)' : 'none', pb: 0.7 }}>
                            <Typography sx={{ fontWeight: 560, lineHeight: 1.3 }}>{item.action ?? item.event ?? 'Событие'}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {[item.at ?? item.created_at ?? '', item.user ?? item.user_name ?? ''].filter(Boolean).join(' · ')}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.35 }}>
                              {item.note ?? item.message ?? item.description ?? 'Комментарий не передан.'}
                            </Typography>
                          </Box>
                        ))}
                      </Stack>
                    </Paper>
                  )}

                  {errors.length > 0 && (
                    <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                      Последняя ошибка: {(errors[0] as any)?.error_message ?? 'Gateway вернул список ошибок.'}
                    </Alert>
                  )}
                </Stack>
              ) : (
                <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                  Выберите документ в списке слева.
                </Alert>
              )}
            </Paper>
          </Box>
        </Stack>
      </Paper>

      <Dialog open={previewOpen && Boolean(selectedDocument)} onClose={() => setPreviewOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ pb: 1.2 }}>
          <Stack direction="row" spacing={1.2} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontWeight: 600, lineHeight: 1.2 }}>Preview документа</Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedDocument?.name ?? 'Документ'} · лист {previewPageIndex + 1} из {previewPages.length}
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
                  <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.75, fontFamily: 'inherit' }}>
                    {selectedPreviewPage.lines.join('\n')}
                  </Typography>
                </Stack>
              ) : (
                <Typography color="text.secondary">Текст предпросмотра не получен.</Typography>
              )}
            </Paper>

            <Stack direction="row" spacing={1} sx={{ justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
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
                onClick={() => setPreviewPageIndex((current) => Math.min(current + 1, previewPages.length - 1))}
                disabled={previewPageIndex >= previewPages.length - 1}
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
