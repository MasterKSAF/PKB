import React from 'react';
import {
  Alert,
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
} from '@mui/material';
import { AlertCircle } from 'lucide-react';
import { MOCK_CHECKS } from '../utils/mockData';

export const ChecksPanel: React.FC = () => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'совпадает': return 'success';
      case 'внимание': return 'warning';
      case 'расхождение': return 'error';
      case 'на проверку': return 'info';
      default: return 'default';
    }
  };

  const issueCount = MOCK_CHECKS.filter((check) => check.status !== 'совпадает').length;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
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
                <TableCell>Параметр</TableCell>
                <TableCell>Документ</TableCell>
                <TableCell>Источник A</TableCell>
                <TableCell>Значение A</TableCell>
                <TableCell>Значение B</TableCell>
                <TableCell>Источник B</TableCell>
                <TableCell>Статус</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {MOCK_CHECKS.map((check) => (
                <TableRow key={check.id} hover>
                  <TableCell sx={{ fontWeight: 600 }}>{check.parameter}</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>{check.document}</TableCell>
                  <TableCell sx={{ fontSize: '0.75rem', opacity: 0.7 }}>{check.sourceA}</TableCell>
                  <TableCell sx={{ color: check.status === 'расхождение' ? 'error.main' : 'inherit' }}>{check.valueA}</TableCell>
                  <TableCell sx={{ color: check.status === 'расхождение' ? 'error.main' : 'inherit' }}>{check.valueB}</TableCell>
                  <TableCell sx={{ fontSize: '0.75rem', opacity: 0.7 }}>{check.sourceB}</TableCell>
                  <TableCell>
                    <Chip
                      label={check.status}
                      size="small"
                      color={getStatusColor(check.status) as 'success' | 'warning' | 'error' | 'info' | 'default'}
                      variant="outlined"
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

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
          Найдено записей, требующих внимания: {issueCount}. Система показывает расхождения, но финальное инженерное
          решение принимает сотрудник.
        </Alert>
      </Stack>
    </Container>
  );
};
