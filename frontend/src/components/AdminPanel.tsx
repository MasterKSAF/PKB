import React from 'react';
import {
  Box,
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
  Typography,
} from '@mui/material';
import { ClipboardList, ShieldCheck, UserCog, Users } from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { ADMIN_SECTIONS_ACCESS, ROLE_LABELS } from '../utils/access';
import { MOCK_ADMIN_USERS, MOCK_PROCESSING_LOGS } from '../utils/mockData';

const TABLE_SX = {
  borderRadius: 3,
  bgcolor: 'rgba(7, 14, 22, 0.94)',
  borderWidth: 1.5,
  borderColor: 'rgba(198, 216, 240, 0.52)',
  boxShadow:
    '0 0 0 1px rgba(198, 216, 240, 0.32), 0 0 0 3px rgba(102, 142, 198, 0.14), inset 0 1px 0 rgba(255,255,255,0.03)',
} as const;

const tableCellSx = {
  '& .MuiTableCell-root': {
    borderBottomColor: 'rgba(198, 214, 236, 0.24)',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    verticalAlign: 'top',
    py: 1.25,
    px: 1.55,
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
  '& .MuiTableBody-root .MuiTableRow-root:hover': {
    bgcolor: 'rgba(123, 166, 227, 0.05)',
  },
  '& .MuiTableBody-root .MuiTableCell-root': {
    fontSize: '0.83rem',
    lineHeight: 1.55,
    color: 'rgba(222, 230, 241, 0.84)',
  },
} as const;

function statusColor(status: string) {
  if (status === 'Активен' || status === 'Выполнена' || status === 'Не требуется') return 'success';
  if (status === 'Ожидает настройки' || status === 'Запланирована') return 'warning';
  return 'error';
}

const SummaryCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string;
  note: string;
  accent: string;
}> = ({ icon, label, value, note, accent }) => (
  <Paper
    variant="outlined"
    sx={{
      p: 2.2,
      minHeight: 128,
      height: '100%',
      borderRadius: 2.5,
      bgcolor: 'rgba(12, 18, 26, 0.9)',
      borderColor: 'rgba(154, 188, 232, 0.18)',
      boxShadow: '0 0 0 1px rgba(124, 165, 214, 0.08), inset 0 1px 0 rgba(255,255,255,0.03)',
    }}
  >
    <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', height: '100%' }}>
      <Box
        sx={{
          flexShrink: 0,
          p: 1,
          borderRadius: 1.7,
          bgcolor: 'rgba(255,255,255,0.03)',
          color: accent,
          border: '1px solid rgba(154, 188, 232, 0.16)',
        }}
      >
        {icon}
      </Box>
      <Box sx={{ minWidth: 0 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.35 }}>
          {label}
        </Typography>
        <Typography
          sx={{
            lineHeight: 1.18,
            fontWeight: 540,
            fontSize: '1.05rem',
            color: 'rgba(233, 237, 243, 0.92)',
            overflowWrap: 'anywhere',
          }}
        >
          {value}
        </Typography>
        <Typography
          variant="caption"
          sx={{ display: 'block', mt: 0.35, color: 'rgba(171, 183, 201, 0.72)', lineHeight: 1.35 }}
        >
          {note}
        </Typography>
      </Box>
    </Stack>
  </Paper>
);

export const AdminPanel: React.FC = () => {
  const { currentRole, currentUserId } = useUIStore();
  const currentUser = MOCK_ADMIN_USERS.find((user) => user.id === currentUserId) ?? MOCK_ADMIN_USERS[0];
  const availableSections = ADMIN_SECTIONS_ACCESS[currentRole];
  const canManageUsers = availableSections.includes('users');
  const canManagePermissions = availableSections.includes('permissions');
  const canSeeFullLogs = currentRole === 'system_admin';
  const logs = canSeeFullLogs
    ? MOCK_PROCESSING_LOGS
    : MOCK_PROCESSING_LOGS.filter((log) => log.visibility !== 'Администратор');

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Paper
          variant="outlined"
          sx={{
            p: 2.1,
            borderRadius: 3,
            bgcolor: 'rgba(16, 18, 24, 0.88)',
            borderColor: 'rgba(154, 188, 232, 0.16)',
            boxShadow: '0 0 0 1px rgba(124, 165, 214, 0.08), inset 0 1px 0 rgba(255,255,255,0.03)',
          }}
        >
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.6} sx={{ alignItems: { md: 'center' } }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="overline" sx={{ color: 'rgba(198, 208, 222, 0.78)', letterSpacing: '0.14em' }}>
                Доступ по роли
              </Typography>
              <Typography sx={{ mt: 0.3, color: 'rgba(233, 237, 243, 0.92)', fontSize: '1.05rem', fontWeight: 520 }}>
                {currentUser.name} · {currentUser.position}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.6, color: 'rgba(171, 183, 201, 0.78)' }}>
                Роль доступа: {ROLE_LABELS[currentRole]}. В реальном контуре эти данные приходят от backend после
                авторизации, а backend дополнительно проверяет права на каждый запрос.
              </Typography>
            </Box>
            <Chip
              label={canSeeFullLogs ? 'Полный административный доступ' : 'Доступ к базе НСИ и журналу обработки'}
              variant="outlined"
              sx={{ borderColor: 'rgba(152, 217, 216, 0.32)', color: '#98d9d8', bgcolor: 'rgba(152,217,216,0.05)' }}
            />
          </Stack>
        </Paper>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2.4 }}>
          <Box sx={{ flex: '1 1 210px', minWidth: 210 }}>
            <SummaryCard
              icon={<Users size={19} />}
              label="Пользователи"
              value={`${MOCK_ADMIN_USERS.length}`}
              note={canManageUsers ? 'доступно управление' : 'просмотр ограничен'}
              accent="#9fb6d8"
            />
          </Box>
          <Box sx={{ flex: '1 1 210px', minWidth: 210 }}>
            <SummaryCard
              icon={<ShieldCheck size={19} />}
              label="Права доступа"
              value={canManagePermissions ? 'настройка' : 'ограничено'}
              note="роли, разделы, журналы"
              accent="#98d9d8"
            />
          </Box>
          <Box sx={{ flex: '1 1 210px', minWidth: 210 }}>
            <SummaryCard
              icon={<ClipboardList size={19} />}
              label="Административный журнал"
              value={`${logs.length}`}
              note={canSeeFullLogs ? 'полный доступ' : 'ограниченный доступ'}
              accent="#d9b783"
            />
          </Box>
          <Box sx={{ flex: '1 1 210px', minWidth: 210 }}>
            <SummaryCard
              icon={<UserCog size={19} />}
              label="Текущая роль"
              value={ROLE_LABELS[currentRole]}
              note="по выбранному пользователю"
              accent="#c5afff"
            />
          </Box>
        </Box>

        {canManageUsers && (
          <TableContainer component={Paper} variant="outlined" sx={TABLE_SX}>
            <Table size="small" sx={tableCellSx}>
              <TableHead>
                <TableRow sx={{ bgcolor: 'rgba(156, 176, 204, 0.075)' }}>
                  <TableCell>Пользователь</TableCell>
                  <TableCell>Должность</TableCell>
                  <TableCell>Логин</TableCell>
                  <TableCell>Роль</TableCell>
                  <TableCell>Доступ</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Последний вход</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {MOCK_ADMIN_USERS.map((user) => (
                  <TableRow key={user.id} hover>
                    <TableCell sx={{ fontWeight: 520 }}>{user.name}</TableCell>
                    <TableCell>{user.position}</TableCell>
                    <TableCell>{user.login}</TableCell>
                    <TableCell>{user.role}</TableCell>
                    <TableCell sx={{ color: 'rgba(171, 183, 201, 0.86)' }}>{user.access}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.status}
                        size="small"
                        color={statusColor(user.status) as 'success' | 'warning' | 'error'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>{user.lastSeen}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {canManagePermissions && (
          <Paper
            variant="outlined"
            sx={{
              p: 2.1,
              borderRadius: 3,
              bgcolor: 'rgba(16, 18, 24, 0.86)',
              borderColor: 'rgba(154, 188, 232, 0.16)',
            }}
          >
            <Typography sx={{ mb: 1.4, fontWeight: 540, color: 'rgba(233, 237, 243, 0.92)' }}>
              Настройка прав доступа
            </Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.4} sx={{ alignItems: 'stretch' }}>
              {[
                ['Документы', 'доступ по проекту, типу документа и роли'],
                ['OCR-артефакты', 'видимость исходного текста и промежуточных результатов'],
                ['Журналы', 'инженер видит ограниченный журнал, администратор полный'],
              ].map(([title, text]) => (
                <Paper
                  variant="outlined"
                  key={title}
                  sx={{
                    flex: 1,
                    minHeight: 128,
                    height: '100%',
                    p: 2.2,
                    borderRadius: 2.5,
                    bgcolor: 'rgba(12, 18, 26, 0.9)',
                    borderColor: 'rgba(154, 188, 232, 0.18)',
                    boxShadow: '0 0 0 1px rgba(124, 165, 214, 0.08), inset 0 1px 0 rgba(255,255,255,0.03)',
                  }}
                >
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.5 }}>
                    <UserCog size={16} color="#98d9d8" />
                    <Typography sx={{ fontWeight: 520 }}>{title}</Typography>
                  </Stack>
                  <Typography variant="body2" sx={{ color: 'rgba(171, 183, 201, 0.76)' }}>
                    {text}
                  </Typography>
                </Paper>
              ))}
            </Stack>
          </Paper>
        )}

        <TableContainer component={Paper} variant="outlined" sx={TABLE_SX}>
          <Table size="small" sx={tableCellSx}>
            <TableHead>
              <TableRow sx={{ bgcolor: 'rgba(156, 176, 204, 0.075)' }}>
                <TableCell>Время</TableCell>
                <TableCell>Документ</TableCell>
                <TableCell>Этап</TableCell>
                <TableCell>Событие</TableCell>
                <TableCell>Повторная попытка</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id} hover>
                  <TableCell sx={{ whiteSpace: 'nowrap', color: '#9fd3ff' }}>{log.time}</TableCell>
                  <TableCell sx={{ fontWeight: 520 }}>{log.document}</TableCell>
                  <TableCell>{log.stage}</TableCell>
                  <TableCell sx={{ color: 'rgba(171, 183, 201, 0.86)' }}>{log.event}</TableCell>
                  <TableCell>
                    <Chip
                      label={log.retryStatus}
                      size="small"
                      color={statusColor(log.retryStatus) as 'success' | 'warning' | 'error'}
                      variant="outlined"
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
