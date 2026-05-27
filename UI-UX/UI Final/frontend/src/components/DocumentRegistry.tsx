import React, { useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Container,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { AlertTriangle, CheckCircle2, Database, FileText, Link2, MoreVertical, RefreshCw, ScanText, Upload } from 'lucide-react';
import { MOCK_DOCUMENTS, MOCK_KNOWLEDGE_SECTIONS } from '../utils/mockData';

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

export const DocumentRegistry: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFileName, setSelectedFileName] = useState('');
  const completedOcrCount = MOCK_DOCUMENTS.filter((doc) => doc.ocrStatus === 'Завершено').length;
  const indexedCount = MOCK_DOCUMENTS.filter((doc) => doc.indexStatus === 'Индексировано').length;
  const problemCount = MOCK_DOCUMENTS.filter((doc) => doc.ocrStatus !== 'Завершено' || doc.indexStatus !== 'Индексировано').length;

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
      value: `${MOCK_DOCUMENTS.length}`,
      note: 'всего записей',
      icon: <FileText size={20} />,
      color: '#d9b783',
    },
    {
      label: 'OCR завершен',
      value: `${completedOcrCount}`,
      note: `из ${MOCK_DOCUMENTS.length} документов`,
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
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Stack spacing={3}>
        <Paper
          variant="outlined"
          sx={{
            p: 1.4,
            borderRadius: 2.6,
            ...PANEL_SX,
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
              <Button className="app-action-button" variant="contained" startIcon={<Link2 size={16} />}>
                Загрузить по ссылке
              </Button>
              <Button className="app-action-button" variant="contained" startIcon={<ScanText size={16} />}>
                Повторить OCR
              </Button>
              <input ref={fileInputRef} type="file" hidden onChange={handleFileSelect} />
            </Stack>
          </Stack>
          {selectedFileName && (
            <Alert severity="info" variant="outlined" sx={{ mt: 1.4, borderRadius: 2 }}>
              Выбран файл: {selectedFileName}. После подключения backend он будет отправлен в хранилище, OCR и индекс.
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
                  ...PANEL_SX,
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
                  <Typography variant="caption" sx={{ color: 'rgba(171, 183, 201, 0.72)' }}>
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
            ...PANEL_SX,
          }}
        >
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' }, mb: 1.4 }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flex: 1 }}>
              <Database size={18} color="#98d9d8" />
              <Box>
                <Typography sx={{ fontWeight: 560, color: 'rgba(233, 237, 243, 0.92)' }}>
                  База знаний по разделам
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Тематические области нормативно-справочных документов для судостроительных проектов.
                </Typography>
              </Box>
            </Stack>
            <Chip size="small" label={`${MOCK_KNOWLEDGE_SECTIONS.length} разделов`} variant="outlined" />
          </Stack>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)', xl: 'repeat(6, 1fr)' }, gap: 1 }}>
            {MOCK_KNOWLEDGE_SECTIONS.map((section) => (
              <Paper
                key={section.id}
                variant="outlined"
                sx={{
                  p: 1.15,
                  minHeight: 112,
                  borderRadius: 2.1,
                  bgcolor: 'rgba(255,255,255,0.028)',
                  borderColor: 'rgba(198,216,240,0.22)',
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
                  color: 'rgba(230, 236, 244, 0.90)',
                  borderBottom: '1px solid rgba(181, 198, 220, 0.36)',
                  boxShadow: 'inset 0 -1px 0 rgba(181, 198, 220, 0.16), inset 0 1px 0 rgba(255,255,255,0.04)',
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
                  color: 'rgba(222, 230, 241, 0.84)',
                },
              }}
            >
            <TableHead>
              <TableRow sx={{ bgcolor: 'rgba(156, 176, 204, 0.075)' }}>
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
              {MOCK_DOCUMENTS.map((doc) => (
                <TableRow key={doc.id} hover>
                  <TableCell sx={{ fontWeight: 500 }}>{doc.name}</TableCell>
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
                    <IconButton size="small">
                      <MoreVertical size={16} />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Stack>
    </Container>
  );
};
