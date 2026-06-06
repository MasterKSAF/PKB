import React, { useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Paper,
  Snackbar,
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
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  Database,
  Download,
  Edit3,
  ExternalLink,
  Eye,
  FileText,
  FolderInput,
  History as HistoryIcon,
  Link2,
  MoreVertical,
  RefreshCw,
  Save,
  ScanText,
  Upload,
  X,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { MOCK_DOCUMENTS, MOCK_KNOWLEDGE_SECTIONS, type Citation, type Document } from '../utils/mockData';
import { useUIStore } from '../store/uiStore';
import { apiClient, documentsApi, sourceApi } from '../utils/http';
import { downloadPreviewFile } from '../utils/downloadPreview';

const TABLE_SX = {
  borderRadius: 3,
  bgcolor: 'rgba(7, 14, 22, 0.94)',
  borderWidth: 1.5,
  borderColor: 'rgba(198, 216, 240, 0.52)',
  boxShadow:
    '0 0 0 1px rgba(198, 216, 240, 0.32), 0 0 0 3px rgba(102, 142, 198, 0.14), inset 0 1px 0 rgba(255,255,255,0.03)',
} as const;

const PANEL_SX = {
  bgcolor: 'rgba(22, 23, 27, 0.72)',
  borderColor: 'rgba(198, 216, 240, 0.34)',
  borderWidth: 1.5,
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
} as const;

const DOCUMENT_MENU_ACTIONS = [
  { label: 'Открыть предпросмотр', icon: <Eye size={15} /> },
  { label: 'Скачать документ', icon: <Download size={15} /> },
  { label: 'Перезапустить OCR', icon: <RefreshCw size={15} /> },
  { label: 'Изменить метаданные', icon: <Edit3 size={15} /> },
  { label: 'История версий', icon: <HistoryIcon size={15} /> },
  { label: 'Назначить раздел', icon: <FolderInput size={15} /> },
  { label: 'Архивировать', icon: <Archive size={15} /> },
] as const;

type DocumentMenuAction = (typeof DOCUMENT_MENU_ACTIONS)[number]['label'];
type DocumentVersion = {
  version_id?: string;
  version_number?: number;
  title?: string;
  created_at?: string;
  file_size?: number;
  status?: string;
  content_hash_sha256?: string;
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

const resolveGatewayFileUrl = (value?: string) => {
  if (!value) return '';
  if (/^https?:\/\//i.test(value)) return value;

  const baseUrl = String(apiClient.defaults.baseURL ?? 'http://127.0.0.1:8081/api/v1');
  return new URL(value, baseUrl).toString();
};

const buildDocumentFallbackContent = (doc: Document, citation?: Citation | null) =>
  [
    doc.name,
    `ID: ${doc.id}`,
    `Тип: ${doc.type}`,
    `Версия: ${doc.version}`,
    `Источник: ${doc.source}`,
    `OCR статус: ${doc.ocrStatus}`,
    `Индекс статус: ${doc.indexStatus}`,
    `Обновлен: ${doc.updatedAt || 'не указано'}`,
    citation?.documentUrl ? `Ссылка Gateway: ${resolveGatewayFileUrl(citation.documentUrl)}` : '',
    '',
    citation?.text ?? 'Оригинальный файл будет скачан после того, как Gateway начнет отдавать бинарное содержимое по file_url.',
  ]
    .filter(Boolean)
    .join('\n');

const safeDownloadName = (value: string, extension: string) => {
  const normalized = value.replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, ' ').trim().slice(0, 90) || 'document';
  return `${normalized}.${extension.replace(/^\./, '').toLowerCase() || 'pdf'}`;
};

export const DocumentRegistry: React.FC = () => {
  const { themeMode, workMode } = useUIStore();
  const isLight = themeMode === 'light';
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFileName, setSelectedFileName] = useState('');
  const [notice, setNotice] = useState('');
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<HTMLElement | null>(null);
  const [menuDocument, setMenuDocument] = useState<Document | null>(null);
  const [documentOverrides, setDocumentOverrides] = useState<Record<string, Partial<Document>>>({});
  const [documentSections, setDocumentSections] = useState<Record<string, string>>({});
  const [archivedDocumentIds, setArchivedDocumentIds] = useState<string[]>([]);
  const [previewDocument, setPreviewDocument] = useState<Document | null>(null);
  const [previewCitation, setPreviewCitation] = useState<Citation | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [metadataDocument, setMetadataDocument] = useState<Document | null>(null);
  const [metadataForm, setMetadataForm] = useState({ name: '', type: '', version: '', source: '' });
  const [versionsDocument, setVersionsDocument] = useState<Document | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [sectionDocument, setSectionDocument] = useState<Document | null>(null);
  const [archiveDocument, setArchiveDocument] = useState<Document | null>(null);

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

  const rawDocuments = documentsQuery.data ?? MOCK_DOCUMENTS;
  const knowledgeSections = knowledgeSectionsQuery.data ?? MOCK_KNOWLEDGE_SECTIONS;
  const documents = rawDocuments
    .map((doc) => ({ ...doc, ...documentOverrides[doc.id] }))
    .filter((doc) => !archivedDocumentIds.includes(doc.id));
  const completedOcrCount = documents.filter((doc) => doc.ocrStatus === 'Завершено').length;
  const indexedCount = documents.filter((doc) => doc.indexStatus === 'Индексировано').length;
  const problemCount = documents.filter((doc) => doc.ocrStatus !== 'Завершено' || doc.indexStatus !== 'Индексировано').length;

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

  const stats = [
    {
      label: 'Документов в реестре',
      value: `${documents.length}`,
      note: 'всего записей',
      icon: <FileText size={20} />,
      color: '#d9b783',
    },
    {
      label: 'OCR завершен',
      value: `${completedOcrCount}`,
      note: `из ${documents.length} документов`,
      icon: <CheckCircle2 size={20} />,
      color: '#79c58b',
    },
    {
      label: 'Индексировано',
      value: `${indexedCount}`,
      note: 'готово к поиску',
      icon: <RefreshCw size={20} />,
      color: '#9fb6d8',
    },
    {
      label: 'Требуют внимания',
      value: `${problemCount}`,
      note: 'нужна проверка',
      icon: <AlertTriangle size={20} />,
      color: '#e08c74',
    },
  ];

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFileName(file.name);
    event.target.value = '';

    if (workMode === 'prod') {
      setNotice(`Файл «${file.name}» отправляется в обработку`);
      void documentsApi
        .upload(file)
        .then(() => {
          setNotice(`Файл «${file.name}» передан в серверную обработку`);
          void documentsQuery.refetch();
        })
        .catch(() => {
          setNotice(`Файл «${file.name}» не принят серверной частью. Проверьте доступность системы`);
        });
    }
  };

  const showGatewayNotice = (message: string) => {
    setNotice(`${message}. В рабочем режиме действие будет выполняться серверной частью.`);
  };

  const handleReprocess = (targetDocument?: Document) => {
    const firstDocument = targetDocument ?? documents[0];

    if (workMode !== 'prod' || !firstDocument) {
      showGatewayNotice('Повторный запуск OCR');
      return;
    }

    setNotice(`Повторная обработка документа «${firstDocument.name}» отправляется в систему`);
    void documentsApi
      .reprocess(firstDocument.id)
      .then(() => {
        setNotice(`Задача повторной обработки принята: ${firstDocument.name}`);
        void documentsQuery.refetch();
      })
      .catch(() => setNotice('Задача повторной обработки не принята. Проверьте доступность системы'));
  };

  const handleDocumentMenuOpen = (event: React.MouseEvent<HTMLElement>, document: Document) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
    setMenuDocument(document);
  };

  const handleDocumentMenuClose = () => {
    setMenuAnchorEl(null);
    setMenuDocument(null);
  };

  const handleOpenPreview = async (document: Document) => {
    const baseCitation = createDocumentCitation(document);

    setPreviewDocument(document);
    setPreviewCitation(baseCitation);
    setPreviewError('');
    setPreviewLoading(workMode === 'prod');

    if (workMode !== 'prod') return;

    try {
      const citation = await sourceApi.preview(baseCitation, 'document');
      setPreviewCitation(citation);

      if (!citation.documentUrl) {
        setPreviewError('Gateway не вернул ссылку на оригинальный файл. Показываем карточку документа из UI.');
      }
    } catch {
      setPreviewError('Не удалось получить данные файла от Gateway. Показываем карточку документа из UI.');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDownloadDocument = async (document: Document, citationFromPreview?: Citation | null) => {
    setNotice(`Подготовка документа «${document.name}» к скачиванию`);

    const baseCitation = citationFromPreview ?? createDocumentCitation(document);
    const citation = workMode === 'prod' ? await sourceApi.preview(baseCitation, 'document') : baseCitation;
    const fileUrl = resolveGatewayFileUrl(citation.documentUrl);

    if (fileUrl) {
      try {
        const response = await apiClient.get(fileUrl, { responseType: 'blob' });
        const blobUrl = URL.createObjectURL(response.data);
        const link = window.document.createElement('a');

        link.href = blobUrl;
        link.download = safeDownloadName(document.name, document.type || 'pdf');
        link.click();
        URL.revokeObjectURL(blobUrl);
        setNotice(`Документ «${document.name}» скачан`);
        return;
      } catch {
        downloadPreviewFile(document.name, buildDocumentFallbackContent(document, citation), 'txt');
        setNotice(`Gateway вернул ссылку, но файл пока недоступен. Скачана карточка документа «${document.name}»`);
        return;
      }
    }

    downloadPreviewFile(document.name, buildDocumentFallbackContent(document, citation), 'txt');
    setNotice(`Для «${document.name}» пока нет file_url. Скачана карточка документа`);
  };

  const handleOpenMetadata = (document: Document) => {
    setMetadataDocument(document);
    setMetadataForm({
      name: document.name,
      type: document.type,
      version: document.version,
      source: document.source,
    });
  };

  const handleSaveMetadata = () => {
    if (!metadataDocument) return;

    setDocumentOverrides((current) => ({
      ...current,
      [metadataDocument.id]: {
        name: metadataForm.name.trim() || metadataDocument.name,
        type: metadataForm.type.trim() || metadataDocument.type,
        version: metadataForm.version.trim() || metadataDocument.version,
        source: metadataForm.source.trim() || metadataDocument.source,
      },
    }));
    setNotice(`Метаданные документа «${metadataForm.name || metadataDocument.name}» обновлены в интерфейсе`);
    setMetadataDocument(null);
  };

  const handleOpenVersions = async (document: Document) => {
    setVersionsDocument(document);
    setVersions([
      {
        version_id: `${document.id}-${document.version}`,
        version_number: Number(document.version.replace(/[^\d]/g, '')) || 1,
        title: document.name,
        created_at: document.updatedAt,
        status: document.indexStatus,
      },
    ]);
    setVersionsLoading(workMode === 'prod');

    if (workMode !== 'prod') return;

    try {
      const gatewayVersions = await documentsApi.versions(document.id);
      setVersions(gatewayVersions.length ? gatewayVersions : []);
    } catch {
      setNotice(`История версий для «${document.name}» пока недоступна в Gateway`);
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleAssignSection = (sectionId: string) => {
    if (!sectionDocument) return;

    const section = knowledgeSections.find((item) => item.id === sectionId);
    setDocumentSections((current) => ({ ...current, [sectionDocument.id]: sectionId }));
    setNotice(`Документ «${sectionDocument.name}» назначен в раздел «${section?.title ?? sectionId}»`);
    setSectionDocument(null);
  };

  const handleConfirmArchive = () => {
    if (!archiveDocument) return;
    const document = archiveDocument;

    const archiveLocally = () => {
      setArchivedDocumentIds((current) => [...new Set([...current, document.id])]);
      setArchiveDocument(null);
    };

    if (workMode !== 'prod') {
      archiveLocally();
      setNotice(`Документ «${document.name}» скрыт из реестра`);
      return;
    }

    setNotice(`Архивирование документа «${document.name}» отправлено в Gateway`);
    void documentsApi
      .archive(document.id)
      .then(() => {
        archiveLocally();
        setNotice(`Документ «${document.name}» архивирован`);
        void documentsQuery.refetch();
      })
      .catch(() => setNotice(`Gateway не принял архивирование документа «${document.name}»`));
  };

  const handleDocumentMenuAction = (action: DocumentMenuAction, document: Document) => {
    switch (action) {
      case 'Открыть предпросмотр':
        void handleOpenPreview(document);
        break;
      case 'Скачать документ':
        void handleDownloadDocument(document);
        break;
      case 'Перезапустить OCR':
        handleReprocess(document);
        break;
      case 'Изменить метаданные':
        handleOpenMetadata(document);
        break;
      case 'История версий':
        void handleOpenVersions(document);
        break;
      case 'Назначить раздел':
        setSectionDocument(document);
        break;
      case 'Архивировать':
        setArchiveDocument(document);
        break;
      default:
        break;
    }
  };

  const getAssignedSection = (documentId: string) => {
    const sectionId = documentSections[documentId];
    return knowledgeSections.find((section) => section.id === sectionId);
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
      <Stack spacing={3}>
        <Paper
          variant="outlined"
          sx={{
            p: 1.4,
            borderRadius: 2.6,
            ...panelSx,
          }}
        >
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            sx={{ justifyContent: 'flex-end', alignItems: { xs: 'flex-start', md: 'center' } }}
          >
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
              <Button className="app-action-button" variant="contained" startIcon={<Upload size={16} />} onClick={handleUploadClick}>
                Загрузить документ
              </Button>
              <Button
                className="app-action-button"
                variant="contained"
                startIcon={<Link2 size={16} />}
                onClick={() => showGatewayNotice('Загрузка документа по ссылке')}
              >
                Загрузить по ссылке
              </Button>
              <Button
                className="app-action-button"
                variant="contained"
                startIcon={<ScanText size={16} />}
                onClick={() => handleReprocess()}
              >
                Повторить OCR
              </Button>
              <input ref={fileInputRef} type="file" hidden onChange={handleFileSelect} />
            </Stack>
          </Stack>
          {selectedFileName && (
            <Alert severity="info" variant="outlined" sx={{ mt: 1.4, borderRadius: 2 }}>
              Выбран файл: {selectedFileName}. В рабочем режиме он будет отправлен в хранилище, OCR и индекс.
            </Alert>
          )}
        </Paper>

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

        <Paper
          variant="outlined"
          sx={{
            p: 1.8,
            borderRadius: 3,
            ...panelSx,
          }}
        >
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' }, mb: 1.4 }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flex: 1 }}>
              <Database size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
              <Box>
                <Typography sx={{ fontWeight: 560, color: isLight ? '#0f172a' : 'rgba(233, 237, 243, 0.92)' }}>
                  База знаний по разделам
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Тематические области нормативно-справочных документов для судостроительных проектов.
                </Typography>
              </Box>
            </Stack>
            <Chip size="small" label={`${knowledgeSections.length} разделов`} variant="outlined" />
          </Stack>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)', xl: 'repeat(6, 1fr)' }, gap: 1 }}>
            {knowledgeSections.map((section) => (
              <Paper
                key={section.id}
                variant="outlined"
                onClick={() => {
                  setSelectedSectionId((current) => (current === section.id ? null : section.id));
                  setNotice(`Выбран раздел базы знаний: ${section.title}`);
                }}
                sx={{
                  p: 1.15,
                  minHeight: 112,
                  borderRadius: 2.1,
                  cursor: 'pointer',
                  bgcolor: isLight ? 'rgba(248, 250, 252, 0.76)' : 'rgba(255,255,255,0.028)',
                  borderColor:
                    selectedSectionId === section.id
                      ? isLight
                        ? 'rgba(2, 132, 199, 0.62)'
                        : 'rgba(152, 217, 216, 0.62)'
                      : isLight
                        ? 'rgba(14,116,144,0.18)'
                        : 'rgba(198,216,240,0.22)',
                  boxShadow:
                    selectedSectionId === section.id
                      ? isLight
                        ? '0 0 0 2px rgba(2,132,199,0.10)'
                        : '0 0 0 2px rgba(152,217,216,0.10)'
                      : 'none',
                  transition: 'border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease',
                  '&:hover': {
                    transform: 'translateY(-1px)',
                    borderColor: isLight ? 'rgba(2,132,199,0.42)' : 'rgba(152,217,216,0.42)',
                  },
                }}
              >
                <Stack spacing={0.7} sx={{ height: '100%' }}>
                  <Stack direction="row" spacing={0.7} sx={{ alignItems: 'center' }}>
                    <FileText size={15} color="#d9b783" />
                    <Typography sx={{ fontSize: '0.8rem', fontWeight: 560, lineHeight: 1.2 }}>{section.title}</Typography>
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
            ))}
          </Box>
        </Paper>

        <TableContainer component={Paper} variant="outlined" sx={tableSx}>
          <Table
            size="small"
              sx={{
                '& .MuiTableCell-root': {
                  borderBottomColor: 'rgba(198, 214, 236, 0.24)',
                  borderBottomWidth: '1px',
                  borderBottomStyle: 'solid',
                  verticalAlign: 'top',
                  py: 1.3,
                  px: 1.6,
                },
                '& .MuiTableHead-root .MuiTableCell-root': {
                  color: isLight ? '#0f172a' : 'rgba(230, 236, 244, 0.90)',
                  borderBottom: isLight ? '1px solid rgba(14,116,144,0.22)' : '1px solid rgba(181, 198, 220, 0.36)',
                  boxShadow: isLight
                    ? 'inset 0 -1px 0 rgba(14,116,144,0.12)'
                    : 'inset 0 -1px 0 rgba(181, 198, 220, 0.16), inset 0 1px 0 rgba(255,255,255,0.04)',
                fontWeight: 600,
                letterSpacing: '0.01em',
                textAlign: 'center',
              },
                '& .MuiTableHead-root .MuiTableCell-root:not(:last-child)': {
                  borderRight: '1px solid rgba(188, 207, 232, 0.26)',
                },
                '& .MuiTableBody-root .MuiTableRow-root:nth-of-type(odd)': {
                  bgcolor: 'rgba(255,255,255,0.016)',
                },
                '& .MuiTableBody-root .MuiTableRow-root': {
                  boxShadow: 'inset 0 -1px 0 rgba(198, 214, 236, 0.12)',
                },
                '& .MuiTableBody-root .MuiTableRow-root:hover': {
                  bgcolor: 'rgba(123, 166, 227, 0.05)',
                  boxShadow: 'inset 0 -1px 0 rgba(198, 214, 236, 0.24), inset 0 1px 0 rgba(198, 214, 236, 0.10)',
                },
                '& .MuiTableBody-root .MuiTableCell-root': {
                  fontSize: '0.83rem',
                  lineHeight: 1.55,
                  color: isLight ? '#1e293b' : 'rgba(222, 230, 241, 0.84)',
                },
              }}
            >
            <TableHead>
              <TableRow sx={{ bgcolor: isLight ? 'rgba(14,116,144,0.055)' : 'rgba(156, 176, 204, 0.075)' }}>
                <TableCell>Документ</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell>Версия</TableCell>
                <TableCell>Источник</TableCell>
                <TableCell>OCR статус</TableCell>
                <TableCell>Индекс статус</TableCell>
                <TableCell>Обновлен</TableCell>
                <TableCell align="center"></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => {
                const assignedSection = getAssignedSection(doc.id);

                return (
                  <TableRow
                    key={doc.id}
                    hover
                    onClick={() => void handleOpenPreview(doc)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell sx={{ fontWeight: 500 }}>
                      <Stack spacing={0.6}>
                        <Typography sx={{ fontSize: '0.83rem', fontWeight: 560, lineHeight: 1.35 }}>{doc.name}</Typography>
                        {assignedSection && (
                          <Chip
                            label={`Раздел: ${assignedSection.title}`}
                            size="small"
                            variant="outlined"
                            sx={{ alignSelf: 'flex-start', height: 20, fontSize: '0.68rem' }}
                          />
                        )}
                      </Stack>
                    </TableCell>
                  <TableCell>{doc.type}</TableCell>
                  <TableCell>
                    <Chip label={doc.version} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.7rem' }} />
                  </TableCell>
                  <TableCell sx={{ color: 'text.secondary' }}>{doc.source}</TableCell>
                  <TableCell>
                    <Chip
                      label={doc.ocrStatus}
                      size="small"
                      color={getOcrStatusColor(doc.ocrStatus) as 'success' | 'warning' | 'error' | 'default'}
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={doc.indexStatus}
                      size="small"
                      color={getIndexStatusColor(doc.indexStatus) as 'success' | 'warning'}
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </TableCell>
                  <TableCell>{doc.updatedAt}</TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={(event) => handleDocumentMenuOpen(event, doc)}>
                      <MoreVertical size={16} />
                    </IconButton>
                  </TableCell>
                </TableRow>
                );
              })}
              {documents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>
                    В реестре нет документов для отображения.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Stack>
      <Menu anchorEl={menuAnchorEl} open={Boolean(menuAnchorEl)} onClose={handleDocumentMenuClose}>
        {DOCUMENT_MENU_ACTIONS.map((action) => (
          <MenuItem
            key={action.label}
            onClick={() => {
              const selectedDocument = menuDocument;
              handleDocumentMenuClose();
              if (selectedDocument) handleDocumentMenuAction(action.label, selectedDocument);
            }}
          >
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
              {action.icon}
              <Typography variant="body2">{action.label}</Typography>
            </Stack>
          </MenuItem>
        ))}
      </Menu>

      <Dialog open={Boolean(previewDocument)} onClose={() => setPreviewDocument(null)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
            <FileText size={20} />
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {previewDocument?.name ?? 'Предпросмотр документа'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Предпросмотр из базы знаний
              </Typography>
            </Box>
          </Stack>
          <IconButton size="small" onClick={() => setPreviewDocument(null)}>
            <X size={18} />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {previewLoading ? (
            <Stack spacing={2} sx={{ py: 6, alignItems: 'center' }}>
              <CircularProgress size={28} />
              <Typography color="text.secondary">Получаем данные файла от Gateway...</Typography>
            </Stack>
          ) : (
            <Stack spacing={2}>
              {previewError && (
                <Alert severity="warning" variant="outlined">
                  {previewError}
                </Alert>
              )}
              {previewCitation?.documentUrl && (
                <Alert severity="info" variant="outlined">
                  Gateway вернул ссылку на файл: {resolveGatewayFileUrl(previewCitation.documentUrl)}
                </Alert>
              )}
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
                <Chip label={`ID: ${previewDocument?.id ?? ''}`} variant="outlined" />
                <Chip label={`Тип: ${previewDocument?.type ?? ''}`} variant="outlined" />
                <Chip label={`Версия: ${previewDocument?.version ?? ''}`} variant="outlined" />
                <Chip label={`OCR: ${previewDocument?.ocrStatus ?? ''}`} variant="outlined" />
                <Chip label={`Индекс: ${previewDocument?.indexStatus ?? ''}`} variant="outlined" />
              </Stack>

              <Paper
                variant="outlined"
                sx={{
                  minHeight: 360,
                  p: 3,
                  borderRadius: 2.4,
                  bgcolor: '#f4f1e8',
                  color: '#202020',
                  fontFamily: 'Georgia, serif',
                }}
              >
                <Typography variant="caption" sx={{ color: '#777' }}>
                  Карточка документа
                </Typography>
                <Typography variant="h6" sx={{ mt: 1, mb: 2, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                  {previewDocument?.name}
                </Typography>
                <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', lineHeight: 1.75, fontFamily: 'inherit' }}>
                  {previewDocument ? buildDocumentFallbackContent(previewDocument, previewCitation) : ''}
                </Typography>
              </Paper>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDocument(null)}>Закрыть</Button>
          {previewCitation?.documentUrl && (
            <Button
              startIcon={<ExternalLink size={16} />}
              onClick={() => window.open(resolveGatewayFileUrl(previewCitation.documentUrl), '_blank', 'noopener,noreferrer')}
            >
              Открыть ссылку
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<Download size={16} />}
            disabled={!previewDocument}
            onClick={() => previewDocument && void handleDownloadDocument(previewDocument, previewCitation)}
          >
            Скачать
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(metadataDocument)} onClose={() => setMetadataDocument(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Изменить метаданные</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} sx={{ pt: 1 }}>
            <TextField label="Название документа" value={metadataForm.name} onChange={(event) => setMetadataForm((form) => ({ ...form, name: event.target.value }))} />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField label="Тип" value={metadataForm.type} onChange={(event) => setMetadataForm((form) => ({ ...form, type: event.target.value }))} sx={{ flex: 1 }} />
              <TextField
                label="Версия"
                value={metadataForm.version}
                onChange={(event) => setMetadataForm((form) => ({ ...form, version: event.target.value }))}
                sx={{ flex: 1 }}
              />
            </Stack>
            <TextField label="Источник" value={metadataForm.source} onChange={(event) => setMetadataForm((form) => ({ ...form, source: event.target.value }))} />
            <Alert severity="info" variant="outlined">
              Сейчас Gateway не даёт отдельный write-контракт на редактирование метаданных, поэтому изменение фиксируется в интерфейсе.
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMetadataDocument(null)}>Отмена</Button>
          <Button variant="contained" startIcon={<Save size={16} />} onClick={handleSaveMetadata}>
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(versionsDocument)} onClose={() => setVersionsDocument(null)} maxWidth="sm" fullWidth>
        <DialogTitle>История версий</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.5}>
            <Typography sx={{ fontWeight: 600 }}>{versionsDocument?.name}</Typography>
            {versionsLoading ? (
              <Stack direction="row" spacing={1.2} sx={{ alignItems: 'center' }}>
                <CircularProgress size={18} />
                <Typography color="text.secondary">Получаем версии от Gateway...</Typography>
              </Stack>
            ) : versions.length > 0 ? (
              versions.map((version, index) => (
                <Paper key={version.version_id ?? index} variant="outlined" sx={{ p: 1.4, borderRadius: 2 }}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography sx={{ fontWeight: 560 }}>
                        Версия {version.version_number ?? index + 1}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {version.version_id ?? 'ID версии не указан'}
                      </Typography>
                    </Box>
                    {version.status && <Chip label={version.status} size="small" variant="outlined" />}
                  </Stack>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    {version.title ?? versionsDocument?.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Создана: {version.created_at ?? 'дата не указана'}
                    {version.file_size ? `, размер: ${version.file_size} байт` : ''}
                  </Typography>
                </Paper>
              ))
            ) : (
              <Alert severity="info" variant="outlined">
                Gateway не вернул список версий для этого документа.
              </Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVersionsDocument(null)}>Закрыть</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(sectionDocument)} onClose={() => setSectionDocument(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Назначить раздел</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.2}>
            <Typography color="text.secondary">Выберите раздел базы знаний для документа «{sectionDocument?.name}».</Typography>
            {knowledgeSections.map((section) => (
              <Button key={section.id} variant="outlined" onClick={() => handleAssignSection(section.id)} sx={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <Stack spacing={0.2} sx={{ alignItems: 'flex-start' }}>
                  <Typography sx={{ fontWeight: 560 }}>{section.title}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {section.description}
                  </Typography>
                </Stack>
              </Button>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSectionDocument(null)}>Отмена</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(archiveDocument)} onClose={() => setArchiveDocument(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Архивировать документ?</DialogTitle>
        <DialogContent dividers>
          <Typography>
            Документ «{archiveDocument?.name}» будет скрыт из таблицы. В рабочем режиме запрос отправляется в Gateway.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setArchiveDocument(null)}>Отмена</Button>
          <Button color="error" variant="contained" startIcon={<Archive size={16} />} onClick={handleConfirmArchive}>
            Архивировать
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={Boolean(notice)} autoHideDuration={4200} onClose={() => setNotice('')} message={notice} />
    </Container>
  );
};
