import React from 'react';
import {
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
import { AlertTriangle, CheckCircle2, FileText, MoreVertical, RefreshCw, Upload } from 'lucide-react';
import { MOCK_DOCUMENTS } from '../utils/mockData';

const TABLE_SX = {
  borderRadius: 3,
  bgcolor: 'rgba(7, 14, 22, 0.94)',
  borderColor: 'rgba(124, 165, 214, 0.12)',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.02)',
} as const;

export const DocumentRegistry: React.FC = () => {
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

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={2}
          sx={{ justifyContent: 'flex-end', alignItems: { xs: 'flex-start', md: 'center' } }}
        >
          <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
            <Button variant="contained" startIcon={<Upload size={16} />}>
              Загрузить документ
            </Button>
            <Button variant="outlined" startIcon={<RefreshCw size={16} />}>
              Обновить индекс
            </Button>
            <Button variant="outlined" startIcon={<RefreshCw size={16} />}>
              Переобработать OCR
            </Button>
          </Stack>
        </Stack>

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
                  bgcolor: 'rgba(12, 18, 26, 0.9)',
                  borderColor: 'rgba(255,255,255,0.08)',
                  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.02)',
                }}
              >
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 1.7,
                    bgcolor: 'rgba(255,255,255,0.03)',
                    color: stat.color,
                    border: '1px solid rgba(255,255,255,0.06)',
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

        <TableContainer component={Paper} variant="outlined" sx={TABLE_SX}>
          <Table
            size="small"
            sx={{
              '& .MuiTableCell-root': {
                borderBottomColor: 'rgba(255,255,255,0.06)',
              },
              '& .MuiTableHead-root .MuiTableCell-root': {
                color: 'rgba(230, 236, 244, 0.90)',
                borderBottom: '1px solid rgba(181, 198, 220, 0.30)',
                boxShadow: 'inset 0 -1px 0 rgba(181, 198, 220, 0.12), inset 0 1px 0 rgba(255,255,255,0.03)',
                fontWeight: 600,
                letterSpacing: '0.01em',
              },
              '& .MuiTableHead-root .MuiTableCell-root:not(:last-child)': {
                borderRight: '1px solid rgba(255,255,255,0.04)',
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
                <TableCell align="right"></TableCell>
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
                    <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                      <Box
                        sx={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          bgcolor: doc.indexStatus === 'Индексировано' ? 'success.main' : 'warning.main',
                        }}
                      />
                      <Typography variant="caption">{doc.indexStatus}</Typography>
                    </Box>
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
