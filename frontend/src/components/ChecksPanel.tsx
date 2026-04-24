import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Chip,
  Container,
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
import { AlertCircle, Download, ExternalLink, FileText, Play, Upload, X } from 'lucide-react';
import * as XLSX from 'xlsx';
import { MOCK_CHECKS, MOCK_DOCUMENTS, type ParameterCheck } from '../utils/mockData';

type CheckPreview = {
  previewId: string;
  previewKind: 'page' | 'document';
  scope: 'project' | 'nsi';
  document: string;
  section: string;
  page: number;
  text: string;
  version: string;
};

type UploadedDocument = {
  id: string;
  name: string;
  source: 'upload';
};

const TABLE_SX = {
  borderRadius: 3,
  bgcolor: 'rgba(7, 14, 22, 0.96)',
  borderWidth: 1.5,
  borderColor: 'rgba(194, 213, 238, 0.5)',
  boxShadow:
    '0 0 0 1px rgba(194, 213, 238, 0.28), 0 0 0 3px rgba(102, 142, 198, 0.12), inset 0 1px 0 rgba(255,255,255,0.02)',
} as const;

const linkButtonSx = {
  px: 0.9,
  py: 0.28,
  minWidth: 0,
  height: 'auto',
  fontSize: '0.74rem',
  color: '#b8c4d8',
  border: '1px solid rgba(184,196,216,0.20)',
  borderRadius: 999,
  bgcolor: 'rgba(184,196,216,0.06)',
  textTransform: 'none',
  justifyContent: 'flex-start',
  '&:hover': {
    bgcolor: 'rgba(184,196,216,0.10)',
    borderColor: 'rgba(184,196,216,0.28)',
  },
} as const;

const subtleActionButtonSx = {
  px: 0,
  minWidth: 0,
  justifyContent: 'flex-start',
  textTransform: 'none',
  color: 'rgba(210, 220, 232, 0.82)',
  '&:hover': {
    bgcolor: 'transparent',
    color: '#eef4ff',
  },
} as const;

function buildPagePreview(check: ParameterCheck, scope: 'project' | 'nsi'): CheckPreview {
  const isProject = scope === 'project';

  return {
    previewId: `page-${scope}-${check.id}`,
    previewKind: 'page',
    scope,
    document: isProject ? check.projectDocument : check.nsiDocument,
    section: isProject ? check.projectSection : check.nsiSection,
    page: isProject ? check.projectPage : check.nsiPage,
    text: isProject ? check.projectText : check.nsiText,
    version: isProject ? check.projectVersion : check.nsiVersion,
  };
}

function buildDocumentPreview(check: ParameterCheck, scope: 'project' | 'nsi'): CheckPreview {
  const isProject = scope === 'project';

  return {
    previewId: `document-${scope}-${check.id}`,
    previewKind: 'document',
    scope,
    document: isProject ? check.projectDocument : check.nsiDocument,
    section: 'Полный документ',
    page: 1,
    text: isProject
      ? 'Открыт полный проектный документ. В рабочем режиме здесь будет исходный PDF, DWG или другой файл проекта с прокруткой от первой страницы.'
      : 'Открыт полный документ НСИ. В рабочем режиме здесь будет оригинальный нормативный документ с прокруткой от первой страницы.',
    version: isProject ? check.projectVersion : check.nsiVersion,
  };
}

function getStatusColor(status: ParameterCheck['status']) {
  switch (status) {
    case 'OK':
      return 'success';
    case 'WARNING':
      return 'warning';
    case 'ERROR':
      return 'error';
    default:
      return 'default';
  }
}

function getStatusDescription(status: ParameterCheck['status']) {
  switch (status) {
    case 'OK':
      return 'Требование НСИ соблюдено';
    case 'WARNING':
      return 'Нужна инженерная проверка';
    case 'ERROR':
      return 'Есть явное расхождение';
    default:
      return '';
  }
}

function getModeLabel(documentCount: number) {
  if (documentCount <= 1) return 'Выборочная проверка';
  return 'Пакетная проверка';
}

function exportChecksToExcel(checks: ParameterCheck[]) {
  const rows = checks.map((check) => ({
    Проект: check.projectDocument,
    Раздел: check.projectSection,
    Параметр: check.parameter,
    'Значение в проекте': check.projectValue,
    'Требование НСИ': check.nsiRequirement,
    'Документ НСИ': check.nsiDocument,
    Статус: check.status,
    Комментарий: check.comment,
    'Страница проекта': check.projectPage,
    'Страница НСИ': check.nsiPage,
  }));

  const worksheet = XLSX.utils.json_to_sheet(rows);
  worksheet['!cols'] = [
    { wch: 36 },
    { wch: 28 },
    { wch: 28 },
    { wch: 18 },
    { wch: 30 },
    { wch: 30 },
    { wch: 12 },
    { wch: 50 },
    { wch: 16 },
    { wch: 14 },
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Проверка');
  XLSX.writeFile(workbook, 'pkb-check-results.xlsx');
}

export const ChecksPanel: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [openedPreviews, setOpenedPreviews] = useState<CheckPreview[]>([]);
  const [activePreviewId, setActivePreviewId] = useState<string | null>(null);
  const [previewWidth, setPreviewWidth] = useState(420);
  const [isResizing, setIsResizing] = useState(false);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);

  const projectDocuments = useMemo(() => {
    const names = Array.from(new Set([...MOCK_CHECKS.map((check) => check.projectDocument), ...MOCK_DOCUMENTS.map((doc) => doc.name)]));
    return names.map((name, index) => ({
      id: `project-${index}`,
      name,
      source: 'registry' as const,
    }));
  }, []);

  const availableDocuments = useMemo(
    () => [...projectDocuments, ...uploadedDocuments],
    [projectDocuments, uploadedDocuments],
  );

  const defaultDocumentSelection = useMemo(
    () => Array.from(new Set(MOCK_CHECKS.map((check) => check.projectDocument))),
    [],
  );
  const [draftSelectedDocuments, setDraftSelectedDocuments] = useState<string[]>(defaultDocumentSelection);
  const [activeSelectedDocuments, setActiveSelectedDocuments] = useState<string[]>(defaultDocumentSelection);

  const activePreview = useMemo(
    () => openedPreviews.find((item) => item.previewId === activePreviewId) ?? openedPreviews[0],
    [activePreviewId, openedPreviews],
  );

  const filteredChecks = useMemo(
    () => MOCK_CHECKS.filter((check) => activeSelectedDocuments.includes(check.projectDocument)),
    [activeSelectedDocuments],
  );

  const issueCount = filteredChecks.filter((check) => check.status !== 'OK').length;

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (event: MouseEvent) => {
      const nextWidth = window.innerWidth - event.clientX - 24;
      setPreviewWidth(Math.min(720, Math.max(320, nextWidth)));
    };

    const handleMouseUp = () => setIsResizing(false);

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const openPreview = (preview: CheckPreview) => {
    setOpenedPreviews((prev) => {
      if (prev.some((item) => item.previewId === preview.previewId)) return prev;
      return [...prev, preview];
    });
    setActivePreviewId(preview.previewId);
  };

  const closePreview = (previewId: string) => {
    setOpenedPreviews((prev) => {
      const next = prev.filter((item) => item.previewId !== previewId);
      if (activePreviewId === previewId) {
        setActivePreviewId(next[0]?.previewId ?? null);
      }
      return next;
    });
  };

  const handleApplySelection = () => {
    setActiveSelectedDocuments(draftSelectedDocuments);
  };

  const handleResetSelection = () => {
    setDraftSelectedDocuments(defaultDocumentSelection);
    setActiveSelectedDocuments(defaultDocumentSelection);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;

    const nextUploaded = files.map((file, index) => ({
      id: `upload-${file.name}-${Date.now()}-${index}`,
      name: file.name,
      source: 'upload' as const,
    }));

    setUploadedDocuments((prev) => [...prev, ...nextUploaded]);
    setDraftSelectedDocuments((prev) => Array.from(new Set([...prev, ...nextUploaded.map((file) => file.name)])));
    event.target.value = '';
  };

  const selectedDocumentCount = activeSelectedDocuments.length;
  const uploadedSelectedCount = activeSelectedDocuments.filter((name) =>
    uploadedDocuments.some((document) => document.name === name),
  ).length;

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 142px)', minHeight: 0 }}>
      <Box sx={{ flex: 1, minWidth: 0, overflowY: 'auto' }}>
        <Container maxWidth={false} sx={{ py: 4, maxWidth: '1440px' }}>
          <Stack spacing={3}>
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                borderRadius: 3,
                bgcolor: 'rgba(10, 14, 22, 0.88)',
                borderColor: 'rgba(134, 166, 214, 0.16)',
              }}
            >
              <Stack spacing={2}>
                <Stack
                  direction={{ xs: 'column', xl: 'row' }}
                  spacing={1.5}
                  sx={{ alignItems: { xs: 'stretch', xl: 'center' }, justifyContent: 'space-between' }}
                >
                  <Autocomplete
                    multiple
                    disableCloseOnSelect
                    options={availableDocuments}
                    value={availableDocuments.filter((document) => draftSelectedDocuments.includes(document.name))}
                    onChange={(_, value) => setDraftSelectedDocuments(value.map((item) => item.name))}
                    getOptionLabel={(option) => option.name}
                    isOptionEqualToValue={(option, value) => option.id === value.id}
                    renderOption={(props, option, { selected }) => (
                      <Box component="li" {...props} sx={{ '& + li': { borderTop: '1px solid rgba(255,255,255,0.04)' } }}>
                        <Checkbox checked={selected} sx={{ mr: 1 }} />
                        <Box>
                          <Typography sx={{ color: 'rgba(232, 238, 247, 0.92)' }}>{option.name}</Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(183, 195, 210, 0.74)' }}>
                            {option.source === 'upload' ? 'загружен вручную' : 'доступен в проекте'}
                          </Typography>
                        </Box>
                      </Box>
                    )}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Документы для проверки"
                        placeholder={draftSelectedDocuments.length > 0 ? '' : 'Выберите один или несколько документов'}
                      />
                    )}
                    renderValue={(value) => (
                      <Typography
                        sx={{
                          minWidth: 0,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          color: 'rgba(228, 235, 247, 0.92)',
                          fontSize: '0.88rem',
                        }}
                      >
                        {value.map((item) => item.name).join(', ')}
                      </Typography>
                    )}
                    slotProps={{
                      paper: {
                        sx: {
                          bgcolor: 'rgba(12, 16, 24, 0.98)',
                          border: '1px solid rgba(132, 160, 205, 0.18)',
                          backgroundImage: 'none',
                        },
                      },
                    }}
                    sx={{
                      minWidth: 320,
                      flex: 1,
                      '& .MuiInputBase-root': {
                        minHeight: 40,
                        flexWrap: 'nowrap',
                        alignItems: 'center',
                      },
                      '& .MuiAutocomplete-inputRoot': {
                        pr: '40px !important',
                      },
                      '& .MuiAutocomplete-tag': {
                        maxWidth: '100%',
                      },
                    }}
                  />

                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2}>
                    <Button
                      variant="contained"
                      startIcon={<Upload size={16} />}
                      onClick={handleUploadClick}
                      sx={{
                        bgcolor: 'rgba(207, 153, 88, 0.88)',
                        color: '#16110b',
                        '&:hover': { bgcolor: 'rgba(219, 166, 100, 0.96)' },
                      }}
                    >
                      Загрузить документ
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<Play size={16} />}
                      onClick={handleApplySelection}
                      sx={{
                        bgcolor: 'rgba(207, 153, 88, 0.88)',
                        color: '#16110b',
                        '&:hover': { bgcolor: 'rgba(219, 166, 100, 0.96)' },
                      }}
                    >
                      Проверить выбранные
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<Download size={16} />}
                      onClick={() => exportChecksToExcel(filteredChecks)}
                      disabled={filteredChecks.length === 0}
                      sx={{
                        bgcolor: 'rgba(207, 153, 88, 0.88)',
                        color: '#16110b',
                        '&:hover': { bgcolor: 'rgba(219, 166, 100, 0.96)' },
                        '&.Mui-disabled': {
                          bgcolor: 'rgba(207, 153, 88, 0.28)',
                          color: 'rgba(22, 17, 11, 0.45)',
                        },
                      }}
                    >
                      Выгрузить в Excel
                    </Button>
                  </Stack>
                </Stack>

                <input ref={fileInputRef} type="file" multiple hidden onChange={handleFileUpload} />

                <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
                  <Chip size="small" label={getModeLabel(selectedDocumentCount)} />
                  <Chip size="small" variant="outlined" label={`выбрано документов: ${selectedDocumentCount}`} />
                  <Chip size="small" variant="outlined" label={`найдено результатов: ${filteredChecks.length}`} />
                  {uploadedSelectedCount > 0 && (
                    <Chip size="small" color="warning" variant="outlined" label={`загружено вручную: ${uploadedSelectedCount}`} />
                  )}
                  <Button size="small" variant="text" onClick={handleResetSelection} sx={subtleActionButtonSx}>
                    Сбросить выбор
                  </Button>
                </Stack>
              </Stack>
            </Paper>

            <TableContainer component={Paper} variant="outlined" sx={TABLE_SX}>
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
                    color: 'rgba(236, 242, 249, 0.94)',
                    borderBottom: '1px solid rgba(194, 210, 232, 0.38)',
                    boxShadow: 'inset 0 -1px 0 rgba(181, 198, 220, 0.14), inset 0 1px 0 rgba(255,255,255,0.03)',
                    fontWeight: 600,
                    letterSpacing: '0.01em',
                    fontSize: '0.79rem',
                    textAlign: 'center',
                  },
                  '& .MuiTableHead-root .MuiTableCell-root:not(:last-child)': {
                    borderRight: '1px solid rgba(188, 207, 232, 0.28)',
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
                    color: 'rgba(222, 230, 241, 0.84)',
                  },
                }}
              >
                <TableHead>
                  <TableRow sx={{ bgcolor: 'rgba(156, 176, 204, 0.095)' }}>
                    <TableCell sx={{ minWidth: 225 }}>Проект</TableCell>
                    <TableCell sx={{ minWidth: 160 }}>Раздел</TableCell>
                    <TableCell sx={{ minWidth: 165 }}>Параметр</TableCell>
                    <TableCell sx={{ minWidth: 150 }}>Значение в проекте</TableCell>
                    <TableCell sx={{ minWidth: 165 }}>Требование НСИ</TableCell>
                    <TableCell sx={{ minWidth: 225 }}>Документ НСИ</TableCell>
                    <TableCell sx={{ minWidth: 120 }}>Статус</TableCell>
                    <TableCell sx={{ minWidth: 225 }}>Комментарий</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredChecks.map((check) => (
                    <TableRow key={check.id} hover>
                      <TableCell>
                        <Stack spacing={0.7}>
                          <Typography sx={{ color: 'rgba(223, 231, 242, 0.9)', fontWeight: 500, fontSize: '0.83rem' }}>
                            {check.projectDocument}
                          </Typography>
                          <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                            <Button
                              size="small"
                              variant="text"
                              startIcon={<ExternalLink size={14} />}
                              onClick={() => openPreview(buildPagePreview(check, 'project'))}
                              sx={linkButtonSx}
                            >
                              Страница
                            </Button>
                            <Button
                              size="small"
                              variant="text"
                              startIcon={<FileText size={14} />}
                              onClick={() => openPreview(buildDocumentPreview(check, 'project'))}
                              sx={linkButtonSx}
                            >
                              Документ
                            </Button>
                          </Stack>
                        </Stack>
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ color: 'rgba(192, 203, 219, 0.78)', lineHeight: 1.55, fontSize: '0.82rem' }}>
                          {check.projectSection}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <Typography sx={{ fontWeight: 500, color: 'rgba(232, 238, 246, 0.92)', fontSize: '0.83rem' }}>{check.parameter}</Typography>
                      </TableCell>

                      <TableCell>
                        <Typography
                          sx={{
                            color: check.status === 'ERROR' ? 'error.main' : 'rgba(237, 242, 248, 0.92)',
                            fontWeight: 500,
                            fontSize: '0.83rem',
                          }}
                        >
                          {check.projectValue}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <Typography
                          sx={{
                            color: check.status === 'ERROR' ? 'error.main' : 'rgba(237, 242, 248, 0.92)',
                            lineHeight: 1.55,
                            fontSize: '0.83rem',
                          }}
                        >
                          {check.nsiRequirement}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <Stack spacing={0.7}>
                          <Typography sx={{ color: 'rgba(223, 231, 242, 0.9)', fontWeight: 500, fontSize: '0.83rem' }}>
                            {check.nsiDocument}
                          </Typography>
                          <Typography variant="body2" sx={{ color: 'rgba(183, 195, 210, 0.74)', fontSize: '0.82rem' }}>
                            {check.nsiSection}
                          </Typography>
                          <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                            <Button
                              size="small"
                              variant="text"
                              startIcon={<ExternalLink size={14} />}
                              onClick={() => openPreview(buildPagePreview(check, 'nsi'))}
                              sx={linkButtonSx}
                            >
                              Страница
                            </Button>
                            <Button
                              size="small"
                              variant="text"
                              startIcon={<FileText size={14} />}
                              onClick={() => openPreview(buildDocumentPreview(check, 'nsi'))}
                              sx={linkButtonSx}
                            >
                              Документ
                            </Button>
                          </Stack>
                        </Stack>
                      </TableCell>

                      <TableCell>
                        <Stack spacing={0.9}>
                          <Chip
                            label={check.status}
                            size="small"
                            color={getStatusColor(check.status) as 'success' | 'warning' | 'error' | 'default'}
                            variant="outlined"
                            sx={{ height: 22, fontSize: '0.7rem', fontWeight: 600, width: 'fit-content' }}
                          />
                          <Typography variant="caption" sx={{ color: 'rgba(188, 198, 214, 0.74)', lineHeight: 1.5 }}>
                            {getStatusDescription(check.status)}
                          </Typography>
                        </Stack>
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ color: 'rgba(212, 220, 231, 0.8)', lineHeight: 1.55, fontSize: '0.82rem' }}>
                          {check.comment}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {filteredChecks.length === 0 && (
              <Paper
                variant="outlined"
                sx={{
                  p: 2.4,
                  borderRadius: 3,
                  bgcolor: 'rgba(11, 15, 22, 0.82)',
                  borderColor: 'rgba(150, 172, 204, 0.14)',
                }}
              >
                <Typography sx={{ color: 'rgba(230, 236, 244, 0.92)', fontWeight: 600 }}>
                  Для выбранных документов пока нет результатов сверки
                </Typography>
                <Typography variant="body2" sx={{ mt: 0.8, color: 'rgba(187, 198, 214, 0.76)', lineHeight: 1.6 }}>
                  Это нормально для недавно загруженных файлов: сначала backend должен извлечь параметры проекта, сопоставить их с
                  НСИ и только потом вернуть карточки проверки.
                </Typography>
              </Paper>
            )}

            <Alert
              severity="warning"
              icon={<AlertCircle size={20} />}
              sx={{
                borderRadius: 2,
                bgcolor: 'rgba(240, 195, 109, 0.08)',
                border: '1px solid rgba(240, 195, 109, 0.18)',
                color: 'rgba(230, 236, 244, 0.86)',
                '& .MuiAlert-icon': {
                  color: 'rgba(240, 195, 109, 0.82)',
                },
              }}
            >
              Найдено записей, требующих внимания: {issueCount}. Вкладка показывает, как данные проекта соотносятся с
              требованиями НСИ, но финальное инженерное решение принимает сотрудник.
            </Alert>
          </Stack>
        </Container>
      </Box>

      {openedPreviews.length > 0 && (
        <Box
          sx={{
            width: previewWidth,
            minWidth: 320,
            maxWidth: 720,
            position: 'relative',
            borderLeft: '1px solid rgba(255,255,255,0.10)',
            bgcolor: '#101116',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            onMouseDown={() => setIsResizing(true)}
            sx={{
              position: 'absolute',
              left: -5,
              top: 0,
              bottom: 0,
              width: 10,
              cursor: 'col-resize',
              '&:hover': { bgcolor: 'rgba(112,161,255,0.20)' },
            }}
          />

          <Box sx={{ p: 1.5, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              {openedPreviews.map((preview) => (
                <Chip
                  key={preview.previewId}
                  size="small"
                  label={`${preview.scope === 'project' ? 'проект' : 'НСИ'} · ${
                    preview.previewKind === 'page' ? `стр. ${preview.page}` : 'документ'
                  }`}
                  color={preview.previewId === activePreview?.previewId ? 'primary' : 'default'}
                  variant={preview.previewId === activePreview?.previewId ? 'filled' : 'outlined'}
                  onClick={() => setActivePreviewId(preview.previewId)}
                  onDelete={() => closePreview(preview.previewId)}
                  deleteIcon={<X size={14} />}
                />
              ))}
            </Stack>
          </Box>

          {activePreview && (
            <Box sx={{ overflow: activePreview.previewKind === 'document' ? 'auto' : 'hidden', flexGrow: 1 }}>
              <Box
                sx={{
                  position: 'sticky',
                  top: 0,
                  zIndex: 2,
                  p: 2,
                  pb: 1.5,
                  bgcolor: '#101116',
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                  <FileText size={18} />
                  <Typography variant="subtitle2">
                    {activePreview.previewKind === 'page'
                      ? activePreview.scope === 'project'
                        ? 'Страница проектного документа'
                        : 'Страница документа НСИ'
                      : activePreview.scope === 'project'
                        ? 'Проектный документ'
                        : 'Документ НСИ'}
                  </Typography>
                </Stack>

                <Box sx={{ mt: 1.5 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                    {activePreview.document}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {activePreview.previewKind === 'document'
                      ? `с первой страницы · ${activePreview.version}`
                      : `${activePreview.section} · стр. ${activePreview.page} · ${activePreview.version}`}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ p: 2 }}>
                <Stack spacing={1.5}>
                  <Paper
                    variant="outlined"
                    sx={{
                      minHeight: activePreview.previewKind === 'document' ? 980 : 520,
                      p: 2.4,
                      borderRadius: 2,
                      bgcolor: '#f4f1e8',
                      color: '#242424',
                      borderColor: 'rgba(255,255,255,0.12)',
                      transformOrigin: 'top left',
                    }}
                  >
                    <Typography variant="caption" sx={{ color: '#666', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      {activePreview.previewKind === 'page'
                        ? activePreview.scope === 'project'
                          ? 'Проект / одна страница'
                          : 'НСИ / одна страница'
                        : activePreview.scope === 'project'
                          ? 'Проект / полный документ'
                          : 'НСИ / полный документ'}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#777' }}>
                      Страница {activePreview.page}
                    </Typography>
                    <Typography variant="h6" sx={{ mt: 1, mb: 1, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                      {activePreview.previewKind === 'document' ? 'Титульная страница документа' : activePreview.section}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#555', mb: 2 }}>
                      {activePreview.previewKind === 'page'
                        ? 'Открыта только та страница, на которую ссылается строка проверки. Остальные страницы документа не показываются.'
                        : 'Открыт весь документ: страницы идут ниже друг за другом, область просмотра прокручивается вниз начиная с первой страницы.'}
                    </Typography>
                    <Box
                      sx={{
                        mt: 2,
                        p: 2,
                        border: '2px solid rgba(112,161,255,0.55)',
                        bgcolor: 'rgba(112,161,255,0.08)',
                        borderRadius: 1,
                      }}
                    >
                      <Typography variant="body2" sx={{ lineHeight: 1.8 }}>
                        {activePreview.text}
                      </Typography>
                    </Box>
                    {activePreview.previewKind === 'document' &&
                      [1, 2, 3, 4].map((pageOffset) => {
                        const pageNumber = activePreview.page + pageOffset;
                        return (
                          <Box
                            key={pageNumber}
                            sx={{
                              mt: 4,
                              pt: 3,
                              minHeight: 520,
                              borderTop: '1px solid #d2cec2',
                            }}
                          >
                            <Typography variant="caption" sx={{ color: '#777' }}>
                              Страница {pageNumber}
                            </Typography>
                            <Typography variant="subtitle2" sx={{ color: '#1f1f1f', fontWeight: 700, mt: 1, mb: 1 }}>
                              {activePreview.scope === 'project'
                                ? `Раздел проекта ${pageOffset + 1}`
                                : `Раздел НСИ ${pageOffset + 1}`}
                            </Typography>
                            <Typography variant="body2" sx={{ lineHeight: 1.85 }}>
                              {activePreview.scope === 'project'
                                ? 'На следующих страницах проектного документа могут располагаться расчетные таблицы, примечания, спецификация узла и связанные проектные решения. При реальном подключении здесь будет показан оригинальный файл проекта с сохранением нумерации и масштаба.'
                                : 'На следующих страницах документа НСИ могут находиться дополнительные нормы, исключения, таблицы применимости и ссылки на смежные требования. При реальном подключении здесь будет отображаться оригинальная страница нормативного документа.'}
                            </Typography>
                          </Box>
                        );
                      })}
                    <Box sx={{ mt: 4, pt: 2, borderTop: '1px solid #d2cec2', color: '#777' }}>
                      <Typography variant="caption">
                        {activePreview.previewKind === 'page'
                          ? `Страница ${activePreview.page}`
                          : 'Конец документа, страниц: 5'}
                      </Typography>
                    </Box>
                  </Paper>
                </Stack>
              </Box>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};
