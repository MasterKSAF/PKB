import React, { useCallback, useEffect, useMemo, useState } from 'react';
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
  IconButton,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Database,
  Download,
  FileText,
  Maximize2,
  RefreshCw,
  X,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useUIStore } from '../store/uiStore';
import { MOCK_DOCUMENTS, MOCK_KNOWLEDGE_SECTIONS, type Citation, type Document, type KnowledgeSection } from '../utils/mockData';
import { documentsApi, sourceApi } from '../utils/http';
import { downloadPreviewFile } from '../utils/downloadPreview';

type SectionDocument = Document & { sectionId?: string };
type DocumentSort = 'updated_desc' | 'name_asc' | 'status';
type PreviewPage = { title: string; lines: string[] };

const PANEL_SX = {
  bgcolor: 'rgba(22, 23, 27, 0.72)',
  borderColor: 'rgba(198, 216, 240, 0.34)',
  borderWidth: 1.5,
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
} as const;

const SECTION_DOCUMENT_ASSIGNMENTS: Record<string, string[]> = {
  'kb-hull': ['d1'],
  'kb-machinery': ['d2'],
  'kb-electrical': ['d4'],
  'kb-materials': ['d4'],
  'kb-piping': ['d2'],
  'kb-environment': ['d3'],
  'kb-fire': ['d3'],
  'kb-welding': ['d1'],
};

const createDocumentCitation = (doc: Document): Citation => ({
  id: `registry-${doc.id}`,
  documentId: doc.id,
  document: doc.name,
  section: 'Полный документ из базы знаний',
  page: 1,
  text:
    `Документ: ${doc.name}\n` +
    `Тип: ${doc.type}\n` +
    `Версия: ${doc.version}\n` +
    `Источник: ${doc.source}\n` +
    `OCR: ${doc.ocrStatus}\n` +
    `Индекс: ${doc.indexStatus}`,
  version: doc.version,
});

const buildDocumentPreviewText = (doc: Document, citation?: Citation | null) =>
  [
    doc.name,
    `ID: ${doc.id}`,
    `Тип: ${doc.type}`,
    `Версия: ${doc.version}`,
    `Источник: ${doc.source}`,
    `OCR статус: ${doc.ocrStatus}`,
    `Индекс статус: ${doc.indexStatus}`,
    `Обновлен: ${doc.updatedAt || 'не указано'}`,
    citation?.documentUrl ? `Ссылка на файл: ${citation.documentUrl}` : '',
    '',
    citation?.text ?? 'Карточка документа отображается из UI, пока источник предпросмотра не получен.',
  ]
    .filter(Boolean)
    .join('\n');

const buildPreviewPages = (doc: Document, citation?: Citation | null): PreviewPage[] => [
  {
    title: 'Краткий срез',
    lines: [
      doc.name,
      `Тип: ${doc.type}`,
      `Версия: ${doc.version}`,
      `Источник: ${doc.source}`,
      `OCR: ${doc.ocrStatus}`,
      `Индекс: ${doc.indexStatus}`,
    ],
  },
  {
    title: 'Служебные данные',
    lines: [
      `ID: ${doc.id}`,
      `Обновлен: ${doc.updatedAt || 'не указано'}`,
      `Тип источника: ${doc.type}`,
      `Версия: ${doc.version}`,
      citation?.documentUrl ? `URL файла: ${citation.documentUrl}` : 'URL файла не передан.',
    ],
  },
  {
    title: 'Текст предпросмотра',
    lines: buildDocumentPreviewText(doc, citation).split('\n'),
  },
];

const getOcrStatusColor = (status: string) => {
  switch (status) {
    case 'Завершено':
      return 'success';
    case 'В обработке':
      return 'warning';
    case 'Ошибка':
      return 'error';
    default:
      return 'default';
  }
};

const getIndexStatusColor = (status: string) => (status === 'Индексировано' ? 'success' : 'warning');

const sortDocuments = (documents: SectionDocument[], sort: DocumentSort) => {
  const statusRank: Record<string, number> = {
    'Завершено': 0,
    'В обработке': 1,
    'Ошибка': 2,
    'Индексировано': 0,
    'Ожидание': 1,
  };

  const compareDate = (left: SectionDocument, right: SectionDocument) =>
    new Date(right.updatedAt || 0).getTime() - new Date(left.updatedAt || 0).getTime();

  const compareName = (left: SectionDocument, right: SectionDocument) => left.name.localeCompare(right.name, 'ru');

  const compareStatus = (left: SectionDocument, right: SectionDocument) =>
    (statusRank[left.ocrStatus] ?? 99) - (statusRank[right.ocrStatus] ?? 99) ||
    (statusRank[left.indexStatus] ?? 99) - (statusRank[right.indexStatus] ?? 99) ||
    compareName(left, right);

  return [...documents].sort((left, right) => {
    if (sort === 'name_asc') return compareName(left, right);
    if (sort === 'status') return compareStatus(left, right);
    return compareDate(left, right);
  });
};

const matchSectionDocuments = (sectionId: string, documents: SectionDocument[]) => {
  const assignedIds = SECTION_DOCUMENT_ASSIGNMENTS[sectionId] ?? [];
  const matched = documents.filter((doc) => doc.sectionId === sectionId || assignedIds.includes(doc.id));
  return matched.length > 0 ? matched : documents;
};

export const KnowledgeBase: React.FC = () => {
  const { themeMode, workMode, activeTab } = useUIStore();
  const isLight = themeMode === 'light';
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [documentSort, setDocumentSort] = useState<DocumentSort>('updated_desc');
  const [selectedDocument, setSelectedDocument] = useState<SectionDocument | null>(null);
  const [previewCitation, setPreviewCitation] = useState<Citation | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewPageIndex, setPreviewPageIndex] = useState(0);

  const documentsQuery = useQuery({
    queryKey: ['gateway-documents', workMode],
    queryFn: documentsApi.list,
    staleTime: 30_000,
  });
  const knowledgeSectionsQuery = useQuery({
    queryKey: ['gateway-knowledge-sections', workMode],
    queryFn: documentsApi.knowledgeSections,
    staleTime: 60_000,
  });

  const rawDocuments = (documentsQuery.data ?? MOCK_DOCUMENTS) as SectionDocument[];
  const knowledgeSections = knowledgeSectionsQuery.data ?? MOCK_KNOWLEDGE_SECTIONS;

  useEffect(() => {
    if (selectedSectionId && !knowledgeSections.some((section) => section.id === selectedSectionId)) {
      setSelectedSectionId(null);
    }
  }, [knowledgeSections, selectedSectionId]);

  useEffect(() => {
    if (activeTab === 'documents') return;

    setSelectedSectionId(null);
    setSelectedDocument(null);
    setPreviewCitation(null);
    setPreviewError('');
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
  }, [activeTab]);

  const selectedSection: KnowledgeSection | null =
    knowledgeSections.find((section) => section.id === selectedSectionId) ?? null;

  const sectionDocuments = useMemo(() => {
    if (!selectedSection) return [];
    return sortDocuments(matchSectionDocuments(selectedSection.id, rawDocuments), documentSort);
  }, [documentSort, rawDocuments, selectedSection]);

  const handleOpenSection = (sectionId: string) => {
    setSelectedSectionId(sectionId);
    setSelectedDocument(null);
    setPreviewCitation(null);
    setPreviewError('');
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
  };

  const handleBackToSections = () => {
    setSelectedSectionId(null);
    setSelectedDocument(null);
    setPreviewCitation(null);
    setPreviewError('');
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
  };

  useEffect(() => {
    if (!selectedSection) {
      setSelectedDocument(null);
      setPreviewCitation(null);
      setPreviewError('');
      setPreviewDialogOpen(false);
      setPreviewPageIndex(0);
      return;
    }

    if (selectedDocument && !sectionDocuments.some((doc) => doc.id === selectedDocument.id)) {
      setSelectedDocument(null);
      setPreviewCitation(null);
      setPreviewError('');
      setPreviewDialogOpen(false);
      setPreviewPageIndex(0);
    }
  }, [selectedDocument, sectionDocuments, selectedSection]);

  const handleOpenPreview = useCallback(async (document: SectionDocument) => {
    const baseCitation = createDocumentCitation(document);

    setSelectedDocument(document);
    setPreviewCitation(baseCitation);
    setPreviewError('');
    setPreviewLoading(workMode === 'prod');

    if (workMode !== 'prod') return;

    try {
      const citation = await sourceApi.preview(baseCitation, 'document');
      setPreviewCitation(citation);

      if (!citation.documentUrl) {
        setPreviewError('Источник не вернул ссылку на файл. Показываем карточку документа из UI.');
      }
    } catch {
      setPreviewError('Не удалось получить данные файла. Показываем карточку документа из UI.');
    } finally {
      setPreviewLoading(false);
    }
  }, [workMode]);

  const completedOcrCount = rawDocuments.filter((doc) => doc.ocrStatus === 'Завершено').length;
  const indexedCount = rawDocuments.filter((doc) => doc.indexStatus === 'Индексировано').length;
  const problemCount = rawDocuments.filter((doc) => doc.ocrStatus !== 'Завершено' || doc.indexStatus !== 'Индексировано').length;

  const stats = [
    {
      label: 'Документов',
      value: `${rawDocuments.length}`,
      note: 'в реестре',
      icon: <FileText size={18} />,
      color: '#d9b783',
    },
    {
      label: 'OCR завершен',
      value: `${completedOcrCount}`,
      note: 'готово к просмотру',
      icon: <CheckCircle2 size={18} />,
      color: '#79c58b',
    },
    {
      label: 'Индексировано',
      value: `${indexedCount}`,
      note: 'для поиска',
      icon: <RefreshCw size={18} />,
      color: '#9fb6d8',
    },
    {
      label: 'Требуют внимания',
      value: `${problemCount}`,
      note: 'нужна проверка',
      icon: <AlertTriangle size={18} />,
      color: '#e08c74',
    },
  ];

  const previewPages = useMemo(
    () => (selectedDocument ? buildPreviewPages(selectedDocument, previewCitation) : []),
    [previewCitation, selectedDocument],
  );
  const currentPreviewPage = previewPages[Math.min(previewPageIndex, Math.max(previewPages.length - 1, 0))] ?? null;

  const panelSx = {
    ...PANEL_SX,
    ...(isLight && {
      bgcolor: 'rgba(255, 255, 255, 0.82)',
      borderColor: 'rgba(14, 116, 144, 0.24)',
      boxShadow: '0 8px 22px rgba(15,23,42,0.05)',
    }),
  };

  const documentListSx = {
    borderRadius: 2.3,
    bgcolor: isLight ? 'rgba(248, 250, 252, 0.9)' : 'rgba(255,255,255,0.025)',
    border: '1px solid',
    borderColor: isLight ? 'rgba(14,116,144,0.18)' : 'rgba(198,216,240,0.22)',
  } as const;

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Stack spacing={2.4}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          {stats.map((stat) => (
            <Box key={stat.label} sx={{ flex: '1 1 180px' }}>
              <Paper
                variant="outlined"
                sx={{
                  p: 1.6,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.4,
                  minHeight: 92,
                  borderRadius: 2.2,
                  ...panelSx,
                }}
              >
                <Box
                  sx={{
                    p: 0.9,
                    borderRadius: 1.6,
                    bgcolor: 'rgba(255,255,255,0.03)',
                    color: stat.color,
                    border: '1.5px solid rgba(198, 216, 240, 0.22)',
                  }}
                >
                  {stat.icon}
                </Box>
                <Box sx={{ minWidth: 0 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.25 }}>
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

        <Paper variant="outlined" sx={{ p: 1.8, borderRadius: 3, ...panelSx }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' }, mb: 1.4 }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flex: 1 }}>
              <Database size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
              <Box>
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  База знаний по разделам
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Нажмите на раздел, чтобы открыть его документы и предпросмотр.
                </Typography>
              </Box>
            </Stack>
            <Chip size="small" label={`${knowledgeSections.length} разделов`} variant="outlined" />
          </Stack>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)', xl: 'repeat(6, 1fr)' },
              gap: 1,
            }}
          >
            {knowledgeSections.map((section) => {
              const isSelected = section.id === selectedSectionId;

              return (
                <Paper
                  key={section.id}
                  variant="outlined"
                  onClick={() => handleOpenSection(section.id)}
                  sx={{
                    p: 1.1,
                    minHeight: 92,
                    borderRadius: 2.1,
                    cursor: 'pointer',
                    bgcolor: isLight ? 'rgba(248, 250, 252, 0.76)' : 'rgba(255,255,255,0.028)',
                    borderColor: isSelected
                      ? isLight
                        ? 'rgba(2,132,199,0.42)'
                        : 'rgba(152,217,216,0.42)'
                      : isLight
                        ? 'rgba(14,116,144,0.18)'
                        : 'rgba(198,216,240,0.22)',
                    boxShadow: isSelected
                      ? isLight
                        ? '0 10px 20px rgba(15,23,42,0.08)'
                        : '0 10px 20px rgba(0,0,0,0.15)'
                      : 'none',
                    transition: 'transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease',
                    '&:hover': {
                      transform: 'translateY(-1px)',
                      borderColor: isLight ? 'rgba(2,132,199,0.38)' : 'rgba(152,217,216,0.38)',
                    },
                  }}
                >
                  <Stack spacing={0.7} sx={{ height: '100%' }}>
                    <Stack direction="row" spacing={0.7} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                      <Stack direction="row" spacing={0.7} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <FileText size={15} color="#d9b783" />
                        <Typography sx={{ fontSize: '0.8rem', fontWeight: 560, lineHeight: 1.2, minWidth: 0 }}>
                          {section.title}
                        </Typography>
                      </Stack>
                      {isSelected && <Chip size="small" label="Открыт" variant="outlined" />}
                    </Stack>
                    <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.32 }}>
                      {section.description}
                    </Typography>
                    <Chip
                      size="small"
                      label={`${section.documents} док.`}
                      variant="outlined"
                      sx={{ mt: 'auto', alignSelf: 'flex-start', height: 20, fontSize: '0.66rem' }}
                    />
                  </Stack>
                </Paper>
              );
            })}
          </Box>
        </Paper>

        {selectedSection && (
        <Paper variant="outlined" sx={{ p: 1.8, borderRadius: 3, ...panelSx }}>
          <Stack spacing={1.4}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <Button variant="outlined" startIcon={<ChevronLeft size={16} />} onClick={handleBackToSections}>
                К разделам
              </Button>
              <Chip size="small" label={`${selectedSection.documents} док.`} variant="outlined" />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' } }}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flex: 1, minWidth: 0 }}>
                <FileText size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                    {selectedSection?.title ?? 'Раздел'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Список документов раздела, отсортированный так, как удобно смотреть.
                  </Typography>
                </Box>
              </Stack>

              <TextField
                select
                size="small"
                label="Сортировка"
                value={documentSort}
                onChange={(event) => setDocumentSort(event.target.value as DocumentSort)}
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="updated_desc">По обновлению</MenuItem>
                <MenuItem value="name_asc">По названию</MenuItem>
                <MenuItem value="status">По статусу</MenuItem>
              </TextField>
            </Stack>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', xl: '0.9fr 1.1fr' }, gap: 2.4 }}>
              <Paper variant="outlined" sx={{ p: 1.25, borderRadius: 2.2, ...documentListSx }}>
                <Stack spacing={1}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography sx={{ fontWeight: 560 }}>Документы</Typography>
                    <Chip size="small" label={`${sectionDocuments.length}`} variant="outlined" />
                  </Stack>

                  <Stack divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.14)' }} />}>
                    {sectionDocuments.map((document) => {
                      const isSelected = selectedDocument?.id === document.id;

                      return (
                        <Box
                          key={document.id}
                          onClick={() => void handleOpenPreview(document)}
                          sx={{
                            p: 1.15,
                            cursor: 'pointer',
                            borderRadius: 1.8,
                            bgcolor: isSelected ? 'rgba(123, 166, 227, 0.12)' : 'transparent',
                            transition: 'background-color 160ms ease, transform 160ms ease',
                            '&:hover': {
                              bgcolor: 'rgba(123, 166, 227, 0.08)',
                              transform: 'translateY(-1px)',
                            },
                          }}
                        >
                          <Stack spacing={0.95}>
                            <Stack direction="row" spacing={1} sx={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <Box sx={{ minWidth: 0 }}>
                                <Typography sx={{ fontWeight: 560, lineHeight: 1.35 }}>{document.name}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {document.updatedAt || 'не указано'}
                                </Typography>
                              </Box>
                              <Chip label={document.version} size="small" variant="outlined" />
                            </Stack>

                            <Stack direction="row" spacing={0.6} useFlexGap sx={{ flexWrap: 'wrap' }}>
                              <Chip label={document.type} size="small" variant="outlined" />
                              <Chip
                                label={document.ocrStatus}
                                size="small"
                                color={getOcrStatusColor(document.ocrStatus) as 'success' | 'warning' | 'error' | 'default'}
                                variant="outlined"
                              />
                              <Chip
                                label={document.indexStatus}
                                size="small"
                                color={getIndexStatusColor(document.indexStatus) as 'success' | 'warning'}
                                variant="outlined"
                              />
                            </Stack>
                          </Stack>
                        </Box>
                      );
                    })}

                    {sectionDocuments.length === 0 && (
                      <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                        Для этого раздела пока нет документов.
                      </Alert>
                    )}
                  </Stack>
                </Stack>
              </Paper>

              <Paper variant="outlined" sx={{ p: 1.25, borderRadius: 2.2, ...documentListSx }}>
                <Stack spacing={1.25}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography sx={{ fontWeight: 560, lineHeight: 1.35 }}>
                        {selectedDocument?.name ?? 'Предпросмотр'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {selectedDocument ? 'Карточка документа и быстрые действия.' : 'Выберите документ слева.'}
                      </Typography>
                    </Box>
                    {selectedDocument && (
                      <Stack direction="row" spacing={0.8}>
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<Download size={15} />}
                          onClick={() =>
                            selectedDocument
                              ? downloadPreviewFile(
                                  selectedDocument.name,
                                  buildDocumentPreviewText(selectedDocument, previewCitation),
                                  'txt',
                                )
                              : undefined
                          }
                        >
                          Скачать
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<Maximize2 size={15} />}
                          onClick={() => setPreviewDialogOpen(true)}
                        >
                          Развернуть
                        </Button>
                      </Stack>
                    )}
                  </Stack>

                  {selectedDocument ? (
                    <>
                      <Stack direction="row" spacing={0.6} useFlexGap sx={{ flexWrap: 'wrap' }}>
                        <Chip label={`ID: ${selectedDocument.id}`} variant="outlined" />
                        <Chip label={`Версия: ${selectedDocument.version}`} variant="outlined" />
                        <Chip label={`OCR: ${selectedDocument.ocrStatus}`} variant="outlined" />
                        <Chip label={`Индекс: ${selectedDocument.indexStatus}`} variant="outlined" />
                      </Stack>

                      {previewError && (
                        <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                          {previewError}
                        </Alert>
                      )}

                      <Paper
                        variant="outlined"
                        sx={{
                          minHeight: 300,
                          p: 2.2,
                          borderRadius: 2.3,
                          bgcolor: '#f4f1e8',
                          color: '#202020',
                          fontFamily: 'Georgia, serif',
                        }}
                      >
                        {previewLoading ? (
                          <Stack spacing={1.4} sx={{ alignItems: 'center', py: 4 }}>
                            <Typography color="text.secondary">Получаем предпросмотр...</Typography>
                          </Stack>
                        ) : (
                          <Stack spacing={1.2}>
                            <Typography variant="caption" sx={{ color: '#777' }}>
                              {previewCitation?.documentUrl ? 'Источник получен' : 'Карточка документа'}
                            </Typography>
                            <Typography variant="h6" sx={{ color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                              {selectedDocument.name}
                            </Typography>

                            <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.75, fontFamily: 'inherit' }}>
                              {buildDocumentPreviewText(selectedDocument, previewCitation)}
                            </Typography>

                            <Stack direction="row" sx={{ justifyContent: 'center', pt: 0.6 }}>
                              <Button variant="outlined" startIcon={<Maximize2 size={16} />} onClick={() => setPreviewDialogOpen(true)}>
                                Развернуть документ
                              </Button>
                            </Stack>
                          </Stack>
                        )}
                      </Paper>
                    </>
                  ) : (
                    <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                      Сначала выберите документ в левом списке.
                    </Alert>
                  )}
                </Stack>
              </Paper>
            </Box>
          </Stack>
        </Paper>
        )}
      </Stack>

      <Dialog open={previewDialogOpen && Boolean(selectedDocument)} onClose={() => setPreviewDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ pb: 1.2 }}>
          <Stack direction="row" spacing={1.2} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontWeight: 600, lineHeight: 1.2 }}>Предпросмотр документа</Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedDocument?.name ?? 'Документ'} · лист {previewPageIndex + 1} из {previewPages.length}
              </Typography>
            </Box>
            <IconButton aria-label="Закрыть предпросмотр" onClick={() => setPreviewDialogOpen(false)} size="small">
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
                        {selectedDocument?.name}
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
          {selectedDocument && (
            <Button
              startIcon={<Download size={16} />}
              onClick={() => downloadPreviewFile(selectedDocument.name, buildDocumentPreviewText(selectedDocument, previewCitation), 'txt')}
            >
              Скачать
            </Button>
          )}
          <Button onClick={() => setPreviewDialogOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
