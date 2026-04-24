import React, { useMemo, useState } from 'react';
import {
  Button,
  Chip,
  Container,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from '@mui/material';
import { Download, Search } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../utils/http';
import type { AnswerStatus, QueryHistoryItem } from '../utils/mockData';

const statusLabel: Record<AnswerStatus, string> = {
  answered: 'ответ найден',
  needs_clarification: 'нужно уточнение',
  insufficient_data: 'недостаточно данных',
  source_conflict: 'конфликт источников',
};

const statusColor: Record<AnswerStatus, 'success' | 'warning' | 'error' | 'info'> = {
  answered: 'success',
  needs_clarification: 'warning',
  insufficient_data: 'error',
  source_conflict: 'info',
};

function csvEscape(value: string | number) {
  return `"${String(value).replaceAll('"', '""')}"`;
}

export const History: React.FC = () => {
  const [queryFilter, setQueryFilter] = useState('');
  const [userFilter, setUserFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'all' | AnswerStatus>('all');

  const { data = [] } = useQuery<QueryHistoryItem[]>({
    queryKey: ['history'],
    queryFn: historyApi.get,
  });

  const users = useMemo(() => Array.from(new Set(data.map((item) => item.user))), [data]);

  const filteredData = useMemo(() => {
    const normalized = queryFilter.trim().toLowerCase();

    return data.filter((item) => {
      const matchesQuery =
        !normalized ||
        item.query.toLowerCase().includes(normalized) ||
        item.answer.toLowerCase().includes(normalized);
      const matchesUser = userFilter === 'all' || item.user === userFilter;
      const matchesStatus = statusFilter === 'all' || item.status === statusFilter;

      return matchesQuery && matchesUser && matchesStatus;
    });
  }, [data, queryFilter, statusFilter, userFilter]);

  const handleExport = () => {
    const rows = [
      ['Дата', 'Пользователь', 'Запрос', 'Ответ', 'Источники', 'Статус'],
      ...filteredData.map((item) => [
        item.createdAt,
        item.user,
        item.query,
        item.answer,
        item.sources,
        statusLabel[item.status],
      ]),
    ];

    const csv = rows.map((row) => row.map(csvEscape).join(';')).join('\n');
    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'okb_history_filtered.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            borderRadius: 3,
            bgcolor: 'rgba(22, 23, 27, 0.72)',
            borderColor: 'rgba(255,255,255,0.10)',
          }}
        >
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.4} sx={{ alignItems: { md: 'center' } }}>
            <TextField
              size="small"
              label="Поиск по запросу или ответу"
              value={queryFilter}
              onChange={(event) => setQueryFilter(event.target.value)}
              sx={{ width: { xs: '100%', md: 330 } }}
              slotProps={{
                input: {
                  startAdornment: <Search size={17} style={{ marginRight: 10, opacity: 0.65 }} />,
                },
              }}
            />

            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Пользователь</InputLabel>
              <Select label="Пользователь" value={userFilter} onChange={(event) => setUserFilter(event.target.value)}>
                <MenuItem value="all">Все</MenuItem>
                {users.map((user) => (
                  <MenuItem key={user} value={user}>{user}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 210 }}>
              <InputLabel>Статус</InputLabel>
              <Select label="Статус" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as 'all' | AnswerStatus)}>
                <MenuItem value="all">Все статусы</MenuItem>
                {Object.entries(statusLabel).map(([status, label]) => (
                  <MenuItem key={status} value={status}>{label}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              variant="contained"
              startIcon={<Download size={16} />}
              onClick={handleExport}
              sx={{ ml: { md: 'auto' }, whiteSpace: 'nowrap', minWidth: 128 }}
            >
              Экспорт
            </Button>
          </Stack>
        </Paper>

        <TableContainer
          component={Paper}
          variant="outlined"
          sx={{
            borderRadius: 3,
            bgcolor: 'rgba(7, 14, 22, 0.94)',
            borderColor: 'rgba(124, 165, 214, 0.12)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.02)',
          }}
        >
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
                <TableCell>Дата</TableCell>
                <TableCell>Пользователь</TableCell>
                <TableCell>Запрос</TableCell>
                <TableCell>Ответ</TableCell>
                <TableCell>Источники</TableCell>
                <TableCell>Статус</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredData.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell sx={{ whiteSpace: 'nowrap', color: 'text.secondary' }}>{item.createdAt}</TableCell>
                  <TableCell>{item.user}</TableCell>
                  <TableCell sx={{ maxWidth: 260 }}>{item.query}</TableCell>
                  <TableCell sx={{ maxWidth: 320, color: 'text.secondary' }}>{item.answer}</TableCell>
                  <TableCell>{item.sources}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={statusLabel[item.status]}
                      color={statusColor[item.status]}
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
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
