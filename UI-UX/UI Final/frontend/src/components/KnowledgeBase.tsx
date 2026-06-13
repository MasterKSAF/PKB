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
  ChevronLeft,
  ChevronRight,
  Download,
  FileText,
  Maximize2,
  Search,
  X,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useUIStore } from '../store/uiStore';
import { MOCK_DOCUMENTS, MOCK_KNOWLEDGE_SECTIONS, type Citation, type Document, type KnowledgeSection } from '../utils/mockData';
import { documentsApi, registryApi, searchApi, sourceApi } from '../utils/http';
import { downloadPreviewFile } from '../utils/downloadPreview';

type SectionDocument = Document & {
  sectionId?: string;
  classifierCode?: string;
  mksOksCode?: string;
  okstuCode?: string;
};
type DocumentSort = 'updated_desc' | 'name_asc' | 'type_asc';
type SearchScope = 'all' | 'current' | `section:${string}`;
type PreviewPage = { title: string; lines: string[] };

const PANEL_SX = {
  bgcolor: 'rgba(22, 23, 27, 0.72)',
  borderColor: 'rgba(198, 216, 240, 0.34)',
  borderWidth: 1.5,
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
} as const;

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

const contentValueToText = (value: unknown): string => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return value.map(contentValueToText).filter(Boolean).join('\n');
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    if (typeof record.text === 'string') return record.text;
    if (typeof record.content === 'string') return record.content;
    return Object.values(record).map(contentValueToText).filter(Boolean).join('\n');
  }

  return '';
};

const extractRegistrySectionLines = (payload?: any): string[] => {
  const sections = payload?.sections ?? payload?.data?.sections ?? payload?.document?.sections ?? [];
  if (!Array.isArray(sections)) return [];

  return sections
    .map((section: any, index: number) => {
      const heading = [section.clause, section.title].filter(Boolean).join(' ') || `Раздел ${index + 1}`;
      const page = section.page ? `стр. ${section.page}` : '';
      const body = contentValueToText(section.content ?? section.text).trim();

      return [heading, page, body].filter(Boolean).join('\n');
    })
    .filter(Boolean);
};

const buildDocumentPreviewText = (doc: Document, citation?: Citation | null, registrySectionLines: string[] = []) =>
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
    registrySectionLines.length ? `Секции Registry:\n${registrySectionLines.join('\n\n')}` : '',
    registrySectionLines.length ? '' : '',
    citation?.text ?? 'Карточка документа отображается из UI, пока источник предпросмотра не получен.',
  ]
    .filter(Boolean)
    .join('\n');

const buildPreviewPages = (doc: Document, citation?: Citation | null, registrySectionLines: string[] = []): PreviewPage[] => {
  const pages: PreviewPage[] = [
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
  ];

  if (registrySectionLines.length) {
    pages.push({
      title: 'Секции Registry',
      lines: registrySectionLines,
    });
  }

  pages.push({
    title: 'Текст предпросмотра',
    lines: buildDocumentPreviewText(doc, citation, registrySectionLines).split('\n'),
  });

  return pages;
};

const sortDocuments = (documents: SectionDocument[], sort: DocumentSort) => {
  const compareDate = (left: SectionDocument, right: SectionDocument) =>
    new Date(right.updatedAt || 0).getTime() - new Date(left.updatedAt || 0).getTime();

  const compareName = (left: SectionDocument, right: SectionDocument) => left.name.localeCompare(right.name, 'ru');

  const compareType = (left: SectionDocument, right: SectionDocument) =>
    left.type.localeCompare(right.type, 'ru') || compareName(left, right);

  return [...documents].sort((left, right) => {
    if (sort === 'name_asc') return compareName(left, right);
    if (sort === 'type_asc') return compareType(left, right);
    return compareDate(left, right);
  });
};

const normalizeClassifierToken = (value?: string | null) => String(value ?? '').trim().toLowerCase();

const classifierTokenMatches = (documentToken: string, sectionToken: string) => {
  if (!documentToken || !sectionToken) return false;
  return documentToken === sectionToken || documentToken.startsWith(`${sectionToken}.`);
};

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const countTextMatches = (text: string, query: string) => {
  const normalized = query.trim();
  if (!normalized) return 0;
  return text.match(new RegExp(escapeRegExp(normalized), 'gi'))?.length ?? 0;
};

const renderHighlightedText = (text: string, query: string, isLight: boolean) => {
  const normalized = query.trim();
  if (!normalized) return text;

  const parts = text.split(new RegExp(`(${escapeRegExp(normalized)})`, 'gi'));
  return parts.map((part, index) =>
    part.toLowerCase() === normalized.toLowerCase() ? (
      <Box
        key={`${part}-${index}`}
        component="mark"
        sx={{
          px: 0.25,
          borderRadius: 0.4,
          bgcolor: isLight ? 'rgba(250, 204, 21, 0.45)' : 'rgba(250, 204, 21, 0.35)',
          color: 'inherit',
        }}
      >
        {part}
      </Box>
    ) : (
      part
    ),
  );
};

const matchSectionDocuments = (section: KnowledgeSection, documents: SectionDocument[]) => {
  const sectionTokens = [section.id, section.title].map(normalizeClassifierToken).filter(Boolean);

  return documents.filter((doc) => {
    const documentTokens = [doc.sectionId, doc.group, doc.classifierCode, doc.mksOksCode, doc.okstuCode]
      .map(normalizeClassifierToken)
      .filter(Boolean);

    return sectionTokens.some((sectionToken) =>
      documentTokens.some((documentToken) => classifierTokenMatches(documentToken, sectionToken)),
    );
  });
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
  const [knowledgeSearch, setKnowledgeSearch] = useState('');
  const [knowledgeSearchScope, setKnowledgeSearchScope] = useState<SearchScope>('all');
  const [previewDocumentSearch, setPreviewDocumentSearch] = useState('');

  const documentsQuery = useQuery({
    queryKey: ['gateway-documents', workMode],
    queryFn: registryApi.documents,
    staleTime: 30_000,
  });
  const knowledgeSectionsQuery = useQuery({
    queryKey: ['gateway-knowledge-sections', workMode],
    queryFn: registryApi.knowledgeSections,
    staleTime: 60_000,
  });
  const documentDetailQuery = useQuery({
    queryKey: ['gateway-document-detail', workMode, selectedDocument?.id],
    queryFn: () => registryApi.document(selectedDocument!.id),
    enabled: Boolean(selectedDocument) && workMode === 'prod',
    staleTime: 30_000,
  });
  const documentRegistrySectionsQuery = useQuery({
    queryKey: ['gateway-registry-document-sections', workMode, selectedDocument?.id],
    queryFn: () => registryApi.documentSections(selectedDocument!.id),
    enabled: Boolean(selectedDocument) && workMode === 'prod',
    staleTime: 30_000,
  });
  const documentStatusQuery = useQuery({
    queryKey: ['gateway-document-status', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.status(selectedDocument!.id),
    enabled: Boolean(selectedDocument) && workMode === 'prod',
    staleTime: 30_000,
  });
  const documentHistoryQuery = useQuery({
    queryKey: ['gateway-document-history', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.history(selectedDocument!.id),
    enabled: Boolean(selectedDocument) && workMode === 'prod',
    staleTime: 30_000,
  });
  const documentErrorsQuery = useQuery({
    queryKey: ['gateway-document-errors', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.errors(selectedDocument!.id),
    enabled: Boolean(selectedDocument) && workMode === 'prod',
    staleTime: 30_000,
  });
  const documentParametersQuery = useQuery({
    queryKey: ['gateway-document-parameters', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.parameters(selectedDocument!.id),
    enabled: Boolean(selectedDocument) && workMode === 'prod',
    staleTime: 30_000,
  });
  const documentPagesQuery = useQuery({
    queryKey: ['gateway-document-pages', workMode, selectedDocument?.id],
    queryFn: () => documentsApi.pages(selectedDocument!.id),
    enabled: Boolean(selectedDocument) && workMode === 'prod',
    staleTime: 30_000,
  });
  const normalizedKnowledgeSearch = knowledgeSearch.trim();
  const knowledgeSearchQuery = useQuery({
    queryKey: ['knowledge-base-search', workMode, normalizedKnowledgeSearch],
    queryFn: () => searchApi.query(normalizedKnowledgeSearch),
    enabled: normalizedKnowledgeSearch.length >= 3,
    staleTime: 15_000,
  });

  const rawDocuments =
    workMode === 'demo'
      ? ((documentsQuery.data ?? MOCK_DOCUMENTS) as SectionDocument[])
      : ((documentsQuery.data ?? []) as SectionDocument[]);
  const knowledgeSections = workMode === 'demo' ? knowledgeSectionsQuery.data ?? MOCK_KNOWLEDGE_SECTIONS : knowledgeSectionsQuery.data ?? [];

  useEffect(() => {
    if (selectedSectionId && !knowledgeSections.some((section) => section.id === selectedSectionId)) {
      setSelectedSectionId(null);
    }
  }, [knowledgeSections, selectedSectionId]);

  useEffect(() => {
    if (knowledgeSearchScope === 'current' && !selectedSectionId) {
      setKnowledgeSearchScope('all');
      return;
    }

    if (
      knowledgeSearchScope.startsWith('section:') &&
      !knowledgeSections.some((section) => `section:${section.id}` === knowledgeSearchScope)
    ) {
      setKnowledgeSearchScope('all');
    }
  }, [knowledgeSearchScope, knowledgeSections, selectedSectionId]);

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
  const searchScopeSectionId =
    knowledgeSearchScope === 'current'
      ? selectedSectionId
      : knowledgeSearchScope.startsWith('section:')
        ? knowledgeSearchScope.replace('section:', '')
        : null;
  const searchScopeSection =
    searchScopeSectionId ? knowledgeSections.find((section) => section.id === searchScopeSectionId) ?? null : null;

  const sectionDocuments = useMemo(() => {
    if (!selectedSection) return [];
    return sortDocuments(matchSectionDocuments(selectedSection, rawDocuments), documentSort);
  }, [documentSort, rawDocuments, selectedSection]);
  const visibleSectionDocuments = useMemo(() => {
    if (!normalizedKnowledgeSearch) return sectionDocuments;
    const normalized = normalizedKnowledgeSearch.toLowerCase();

    return sectionDocuments.filter((document) =>
      [
        document.name,
        document.type,
        document.source,
        document.version,
        document.group ?? '',
        document.sectionId ?? '',
        document.classifierCode ?? '',
        document.mksOksCode ?? '',
        document.okstuCode ?? '',
      ].some((value) => String(value).toLowerCase().includes(normalized)),
    );
  }, [normalizedKnowledgeSearch, sectionDocuments]);
  const displayedSectionDocuments = useMemo(() => {
    if (!selectedDocument || visibleSectionDocuments.some((doc) => doc.id === selectedDocument.id)) {
      return visibleSectionDocuments;
    }

    return [selectedDocument, ...visibleSectionDocuments];
  }, [selectedDocument, visibleSectionDocuments]);
  const knowledgeSearchResults = Array.isArray(knowledgeSearchQuery.data) ? knowledgeSearchQuery.data : [];
  const scopedKnowledgeSearchResults = useMemo(() => {
    if (!searchScopeSection) return knowledgeSearchResults;

    const scopedDocuments = matchSectionDocuments(searchScopeSection, rawDocuments);
    const scopedDocumentIds = new Set(scopedDocuments.map((document) => document.id));
    const sectionTokens = [searchScopeSection.id, searchScopeSection.title].map(normalizeClassifierToken).filter(Boolean);

    return knowledgeSearchResults.filter((item: any) => {
      const documentId = String(item.documentId ?? item.document_id ?? item.id ?? '');
      if (scopedDocumentIds.has(documentId)) return true;

      const itemTokens = [
        item.sectionId,
        item.section_id,
        item.group,
        item.classifierCode,
        item.classifier_code,
        item.mksOksCode,
        item.mks_oks_code,
        item.okstuCode,
        item.okstu_code,
      ]
        .map(normalizeClassifierToken)
        .filter(Boolean);

      return sectionTokens.some((sectionToken) =>
        itemTokens.some((itemToken) => classifierTokenMatches(itemToken, sectionToken)),
      );
    });
  }, [knowledgeSearchResults, rawDocuments, searchScopeSection]);

  const handleOpenSection = (sectionId: string, scope: SearchScope = 'current') => {
    setSelectedSectionId(sectionId);
    setKnowledgeSearchScope(scope);
    setSelectedDocument(null);
    setPreviewCitation(null);
    setPreviewError('');
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
    setPreviewDocumentSearch('');
  };

  const handleBackToSections = () => {
    setSelectedSectionId(null);
    setKnowledgeSearchScope('all');
    setSelectedDocument(null);
    setPreviewCitation(null);
    setPreviewError('');
    setPreviewDialogOpen(false);
    setPreviewPageIndex(0);
    setPreviewDocumentSearch('');
  };

  const handleSearchScopeChange = (scope: SearchScope) => {
    setKnowledgeSearchScope(scope);

    if (scope.startsWith('section:')) {
      const sectionId = scope.replace('section:', '');
      if (sectionId !== selectedSectionId) {
        handleOpenSection(sectionId, scope);
      }
    }
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

    if (selectedDocument && !displayedSectionDocuments.some((doc) => doc.id === selectedDocument.id)) {
      setSelectedDocument(null);
      setPreviewCitation(null);
      setPreviewError('');
      setPreviewDialogOpen(false);
      setPreviewPageIndex(0);
    }
  }, [displayedSectionDocuments, selectedDocument, selectedSection]);

  const handleOpenPreview = useCallback(async (document: SectionDocument, initialCitation?: Citation) => {
    const baseCitation = initialCitation ?? createDocumentCitation(document);

    setSelectedDocument(document);
    setPreviewCitation(baseCitation);
    setPreviewError('');
    setPreviewLoading(workMode === 'prod');
    setPreviewDocumentSearch('');

    if (workMode !== 'prod') return;

    try {
      const citation = await sourceApi.preview(baseCitation, 'document');
      setPreviewCitation({
        ...citation,
        text:
          initialCitation?.text && !citation.text.includes(initialCitation.text)
            ? `${initialCitation.text}\n\n${citation.text}`
            : citation.text,
      });

      if (!citation.documentUrl) {
        setPreviewError('Источник не вернул ссылку на файл. Показываем карточку документа из UI.');
      }
    } catch {
      setPreviewError('Не удалось получить данные файла. Показываем карточку документа из UI.');
    } finally {
      setPreviewLoading(false);
    }
  }, [workMode]);

  const handleOpenSearchResult = (item: any) => {
    const documentId = String(item.documentId ?? item.document_id ?? item.id ?? '');
    const document = rawDocuments.find((doc) => doc.id === documentId || doc.name === item.name);

    if (!document) return;

    const matchingSection =
      knowledgeSections.find((section) => matchSectionDocuments(section, [document]).some((doc) => doc.id === document.id)) ??
      searchScopeSection ??
      selectedSection ??
      knowledgeSections[0] ??
      null;

    if (matchingSection) {
      setSelectedSectionId(matchingSection.id);
      setKnowledgeSearchScope(`section:${matchingSection.id}`);
    }

    const resultText = item.fragment ?? item.content ?? item.excerpt ?? item.text;
    const resultCitation: Citation = {
      ...createDocumentCitation(document),
      id: `search-${document.id}`,
      section: item.section ?? item.clause ?? 'Найденный фрагмент',
      page: Number(item.page ?? 1),
      text: resultText ? String(resultText) : createDocumentCitation(document).text,
      pagePreviewUrl: item.pagePreviewUrl ?? item.page_preview_url,
      documentUrl: item.documentUrl ?? item.document_url,
    };

    void handleOpenPreview(document, resultCitation);
  };

  const registrySectionLines = useMemo(
    () => extractRegistrySectionLines(documentRegistrySectionsQuery.data),
    [documentRegistrySectionsQuery.data],
  );
  const previewPages = useMemo(
    () => (selectedDocument ? buildPreviewPages(selectedDocument, previewCitation, registrySectionLines) : []),
    [previewCitation, registrySectionLines, selectedDocument],
  );
  const currentPreviewPage = previewPages[Math.min(previewPageIndex, Math.max(previewPages.length - 1, 0))] ?? null;
  const selectedDocumentPreviewText = selectedDocument
    ? buildDocumentPreviewText(selectedDocument, previewCitation, registrySectionLines)
    : '';
  const previewSearchMatchCount = countTextMatches(selectedDocumentPreviewText, previewDocumentSearch);
  const gatewayDocumentDetail = documentDetailQuery.data;
  const gatewayDocumentStatus = documentStatusQuery.data;
  const gatewayDocumentHistory = documentHistoryQuery.data ?? [];
  const gatewayDocumentErrors = documentErrorsQuery.data ?? [];
  const gatewayDocumentParameters = documentParametersQuery.data;
  const gatewayDocumentPages = documentPagesQuery.data ?? [];

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
        <Paper variant="outlined" sx={{ p: 1.35, borderRadius: 2.4, ...panelSx }}>
          <Stack spacing={1.2}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' } }}>
              <TextField
                fullWidth
                size="small"
                label="Поиск по базе знаний"
                value={knowledgeSearch}
                onChange={(event) => setKnowledgeSearch(event.target.value)}
                placeholder="Название документа, код, раздел или фраза"
                slotProps={{
                  input: {
                    startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.72 }} />,
                  },
                }}
              />
              <TextField
                select
                size="small"
                label="Где искать"
                value={knowledgeSearchScope}
                onChange={(event) => handleSearchScopeChange(event.target.value as SearchScope)}
                sx={{ minWidth: { xs: '100%', md: 240 } }}
              >
                <MenuItem value="all">Везде</MenuItem>
                {selectedSection && <MenuItem value="current">Текущий раздел</MenuItem>}
                {knowledgeSections.map((section) => (
                  <MenuItem key={section.id} value={`section:${section.id}`}>
                    {section.title}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>

            {normalizedKnowledgeSearch.length > 0 && normalizedKnowledgeSearch.length < 3 && (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                Для поиска через Gateway нужно минимум 3 символа.
              </Alert>
            )}

            {knowledgeSearchQuery.isError && (
              <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                Gateway не вернул результаты поиска по базе знаний.
              </Alert>
            )}

            {normalizedKnowledgeSearch.length >= 3 && scopedKnowledgeSearchResults.length > 0 && (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', xl: 'repeat(3, 1fr)' },
                  gap: 0.9,
                }}
              >
                {scopedKnowledgeSearchResults.slice(0, 6).map((item: any, index: number) => {
                  const documentId = String(item.documentId ?? item.document_id ?? item.id ?? '');
                  const canOpen = rawDocuments.some((doc) => doc.id === documentId || doc.name === item.name);

                  return (
                    <Paper
                      key={item.id ?? `${documentId}-${index}`}
                      variant="outlined"
                      onClick={() => {
                        if (canOpen) handleOpenSearchResult(item);
                      }}
                      sx={{
                        p: 1,
                        borderRadius: 1.6,
                        cursor: canOpen ? 'pointer' : 'default',
                        bgcolor: isLight ? 'rgba(248,250,252,0.72)' : 'rgba(255,255,255,0.025)',
                        borderColor: isLight ? 'rgba(14,116,144,0.18)' : 'rgba(198,216,240,0.18)',
                      }}
                    >
                      <Typography sx={{ fontSize: '0.84rem', fontWeight: 560, lineHeight: 1.3 }}>
                        {item.name ?? item.document ?? item.document_title ?? 'Документ базы знаний'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.35, lineHeight: 1.35 }}>
                        {item.fragment ?? item.content ?? item.section ?? 'Фрагмент найден Gateway-поиском.'}
                      </Typography>
                    </Paper>
                  );
                })}
              </Box>
            )}
          </Stack>
        </Paper>

        {(documentsQuery.isError || knowledgeSectionsQuery.isError) && (
          <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
            {documentsQuery.isError && knowledgeSectionsQuery.isError
              ? 'Gateway не вернул список документов и дерево разделов.'
              : documentsQuery.isError
                ? 'Gateway не вернул список документов.'
                : 'Gateway не вернул дерево разделов.'}
          </Alert>
        )}

        {!selectedSection && (
        <Paper variant="outlined" sx={{ p: 1.6, borderRadius: 3, ...panelSx }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)', xl: 'repeat(6, 1fr)' },
              gap: 1.45,
            }}
          >
            {knowledgeSections.map((section) => {
              const isSelected = section.id === selectedSectionId;

              return (
                <Paper
                  key={section.id}
                  variant="outlined"
                  onClick={() => handleOpenSection(section.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      handleOpenSection(section.id);
                    }
                  }}
                  sx={{
                    p: 1.3,
                    minHeight: 104,
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
                        <FileText size={15} color={isLight ? '#0284c7' : '#98d9d8'} />
                        <Typography
                          sx={{
                            fontSize: '0.86rem',
                            fontWeight: 650,
                            lineHeight: 1.2,
                            minWidth: 0,
                            color: isLight ? '#075985' : '#98d9d8',
                          }}
                        >
                          {section.title}
                        </Typography>
                      </Stack>
                      {isSelected && <Chip size="small" label="Открыт" variant="outlined" />}
                    </Stack>
                    <Typography
                      variant="caption"
                      sx={{
                        lineHeight: 1.38,
                        color: isLight ? 'rgba(71, 85, 105, 0.68)' : 'rgba(203, 213, 225, 0.58)',
                      }}
                    >
                      {section.description}
                    </Typography>
                  </Stack>
                </Paper>
              );
            })}
          </Box>
        </Paper>
        )}

        {selectedSection && (
        <Paper variant="outlined" sx={{ p: 1.8, borderRadius: 3, ...panelSx }}>
          <Stack spacing={1.4}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
              <Button variant="outlined" startIcon={<ChevronLeft size={16} />} onClick={handleBackToSections}>
                К разделам
              </Button>
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' } }}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flex: 1, minWidth: 0 }}>
                <FileText size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontWeight: 650, color: isLight ? '#075985' : '#98d9d8' }}>
                    {selectedSection?.title ?? 'Раздел'}
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
                <MenuItem value="type_asc">По типу</MenuItem>
              </TextField>
            </Stack>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'minmax(260px, 360px) minmax(0, 1fr)' }, gap: 2 }}>
              <Paper variant="outlined" sx={{ p: 1, borderRadius: 2.2, ...documentListSx }}>
                <Stack spacing={1}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography sx={{ fontWeight: 560 }}>Документы</Typography>
                    <Chip size="small" label={`${displayedSectionDocuments.length}`} variant="outlined" />
                  </Stack>

                  <Stack
                    divider={<Divider flexItem sx={{ borderColor: 'rgba(198, 214, 236, 0.14)' }} />}
                    sx={{ maxHeight: { xs: 320, lg: 560 }, overflowY: 'auto', pr: 0.4 }}
                  >
                    {displayedSectionDocuments.map((document) => {
                      const isSelected = selectedDocument?.id === document.id;

                      return (
                        <Box
                          key={document.id}
                          onClick={() => void handleOpenPreview(document)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault();
                              void handleOpenPreview(document);
                            }
                          }}
                          sx={{
                            p: 0.8,
                            cursor: 'pointer',
                            borderRadius: 1.4,
                            bgcolor: isSelected ? 'rgba(123, 166, 227, 0.12)' : 'transparent',
                            transition: 'background-color 160ms ease, transform 160ms ease',
                            '&:hover': {
                              bgcolor: 'rgba(123, 166, 227, 0.08)',
                              transform: 'translateY(-1px)',
                            },
                          }}
                        >
                          <Typography sx={{ fontSize: '0.88rem', fontWeight: 560, lineHeight: 1.35 }}>
                            {document.name}
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{
                              display: 'block',
                              mt: 0.25,
                              color: isLight ? 'rgba(71, 85, 105, 0.58)' : 'rgba(203, 213, 225, 0.48)',
                              lineHeight: 1.25,
                            }}
                          >
                            {document.type || document.source || document.id}
                          </Typography>
                        </Box>
                      );
                    })}

                    {displayedSectionDocuments.length === 0 && (
                      <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                        {normalizedKnowledgeSearch ? 'По этому запросу в разделе ничего не найдено.' : 'Для этого раздела пока нет документов.'}
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
                        {selectedDocument ? 'Предпросмотр и быстрые действия.' : 'Выберите документ слева.'}
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
                                  selectedDocumentPreviewText,
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
                      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ alignItems: { md: 'center' } }}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Поиск по открытому документу"
                          value={previewDocumentSearch}
                          onChange={(event) => setPreviewDocumentSearch(event.target.value)}
                          placeholder="Слово или фраза"
                          slotProps={{
                            input: {
                              startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.72 }} />,
                            },
                          }}
                        />
                        {previewDocumentSearch.trim() && (
                          <Chip
                            size="small"
                            variant="outlined"
                            label={previewSearchMatchCount ? `${previewSearchMatchCount} совп.` : 'Нет совпадений'}
                            sx={{ minWidth: 120 }}
                          />
                        )}
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
                              {renderHighlightedText(selectedDocumentPreviewText, previewDocumentSearch, isLight)}
                            </Typography>

                            <Stack direction="row" sx={{ justifyContent: 'center', pt: 0.6 }}>
                              <Button variant="outlined" startIcon={<Maximize2 size={16} />} onClick={() => setPreviewDialogOpen(true)}>
                                Развернуть документ
                              </Button>
                            </Stack>
                          </Stack>
                        )}
                      </Paper>

                      <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2.2, ...documentListSx }}>
                        <Stack spacing={1.25}>
                          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                            <Typography sx={{ fontWeight: 560 }}>Сведения Gateway</Typography>
                            <Chip
                              size="small"
                              variant="outlined"
                              label={
                                workMode === 'prod'
                                  ? documentStatusQuery.isFetching
                                    ? 'Обновляем'
                                    : gatewayDocumentStatus?.status ?? gatewayDocumentDetail?.status ?? 'Статус не получен'
                                  : 'Демо-данные'
                              }
                            />
                          </Stack>

                          {workMode === 'prod' && documentDetailQuery.isLoading ? (
                            <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                              Получаем документ, его статус и историю из Gateway...
                            </Alert>
                          ) : workMode === 'prod' ? (
                            <Stack spacing={1.2}>
                              <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                                <Chip label={`Версий: ${gatewayDocumentDetail?.total_versions ?? 0}`} size="small" variant="outlined" />
                                <Chip
                                  label={`Страниц: ${gatewayDocumentPages.length || 0}`}
                                  size="small"
                                  variant="outlined"
                                />
                                <Chip
                                  label={`Секций: ${registrySectionLines.length || 0}`}
                                  size="small"
                                  variant="outlined"
                                />
                                <Chip
                                  label={`Ошибок: ${gatewayDocumentErrors.length || 0}`}
                                  size="small"
                                  variant="outlined"
                                />
                                <Chip
                                  label={`История: ${gatewayDocumentHistory.length || 0}`}
                                  size="small"
                                  variant="outlined"
                                />
                              </Stack>

                              <Box
                                sx={{
                                  display: 'grid',
                                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' },
                                  gap: 1,
                                }}
                              >
                                <Paper variant="outlined" sx={{ p: 1.1, borderRadius: 2 }}>
                                  <Typography variant="caption" color="text.secondary">
                                    Метаданные
                                  </Typography>
                                  <Typography sx={{ fontWeight: 560, mt: 0.35 }}>{gatewayDocumentDetail?.title ?? selectedDocument.name}</Typography>
                                  <Typography variant="body2" color="text.secondary">
                                    {[
                                      gatewayDocumentDetail?.doc_code ? `Код: ${gatewayDocumentDetail.doc_code}` : '',
                                      gatewayDocumentDetail?.source_type ? `Тип: ${gatewayDocumentDetail.source_type}` : '',
                                      gatewayDocumentDetail?.era ? `Эпоха: ${gatewayDocumentDetail.era}` : '',
                                      gatewayDocumentDetail?.validity_status ? `Статус: ${gatewayDocumentDetail.validity_status}` : '',
                                      gatewayDocumentDetail?.jurisdiction ? `Юрисдикция: ${gatewayDocumentDetail.jurisdiction}` : '',
                                    ]
                                      .filter(Boolean)
                                      .join(' · ') || 'Gateway не вернул метаданные документа.'}
                                  </Typography>
                                </Paper>

                                <Paper variant="outlined" sx={{ p: 1.1, borderRadius: 2 }}>
                                  <Typography variant="caption" color="text.secondary">
                                    Параметры и контроль
                                  </Typography>
                                  <Typography sx={{ fontWeight: 560, mt: 0.35 }}>
                                    {typeof gatewayDocumentParameters?.extraction_confidence === 'number'
                                      ? `Точность извлечения: ${Math.round(gatewayDocumentParameters.extraction_confidence * 100)}%`
                                      : 'Точность извлечения не указана'}
                                  </Typography>
                                  <Typography variant="body2" color="text.secondary">
                                    {gatewayDocumentParameters?.unconfirmed_fields?.length
                                      ? `Неподтвержденные поля: ${gatewayDocumentParameters.unconfirmed_fields.join(', ')}`
                                      : 'Неподтвержденные поля не переданы.'}
                                  </Typography>
                                </Paper>
                              </Box>

                              <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                                {(gatewayDocumentParameters?.parameters && Object.keys(gatewayDocumentParameters.parameters).length
                                  ? Object.entries(gatewayDocumentParameters.parameters)
                                  : []
                                )
                                  .slice(0, 6)
                                  .map(([key, value]) => (
                                    <Chip
                                      key={key}
                                      size="small"
                                      variant="outlined"
                                      label={`${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`}
                                    />
                                  ))}
                              </Stack>

                              {gatewayDocumentErrors.length > 0 && (
                                <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                                  Последняя ошибка: {(gatewayDocumentErrors[0] as any)?.error_message ?? 'Gateway вернул список ошибок'}.
                                </Alert>
                              )}
                            </Stack>
                          ) : (
                            <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                              В демо-режиме сведения о документе показываются из локальных карточек.
                            </Alert>
                          )}
                        </Stack>
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

              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ alignItems: { md: 'center' } }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Поиск по открытому документу"
                  value={previewDocumentSearch}
                  onChange={(event) => setPreviewDocumentSearch(event.target.value)}
                  placeholder="Слово или фраза"
                  slotProps={{
                    input: {
                      startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.72 }} />,
                    },
                  }}
                />
                {previewDocumentSearch.trim() && (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={previewSearchMatchCount ? `${previewSearchMatchCount} совп.` : 'Нет совпадений'}
                    sx={{ minWidth: 120 }}
                  />
                )}
              </Stack>

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
                      {renderHighlightedText(currentPreviewPage.lines.join('\n'), previewDocumentSearch, isLight)}
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
              onClick={() => downloadPreviewFile(selectedDocument.name, selectedDocumentPreviewText, 'txt')}
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
