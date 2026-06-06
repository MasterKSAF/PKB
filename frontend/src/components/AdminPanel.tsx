import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Container,
  Divider,
  FormControl,
  FormControlLabel,
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
  Typography,
} from '@mui/material';
import { ClipboardList, Save, Search, ShieldCheck, SlidersHorizontal, UserCog, Users } from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { ADMIN_SECTIONS_ACCESS, ROLE_LABELS } from '../utils/access';
import { MOCK_PROCESSING_LOGS, type AdminUser } from '../utils/mockData';
import { adminApi } from '../utils/http';

type RoleLabel = AdminUser['role'];
type AccessKey =
  | 'chat'
  | 'search'
  | 'documents'
  | 'history'
  | 'qa'
  | 'admin'
  | 'ocrArtifacts'
  | 'processingLogs';

const ROLE_OPTIONS: RoleLabel[] = ['Пользователь', 'Администратор знаний', 'Системный администратор'];

const GATEWAY_ROLE_BY_LABEL: Record<RoleLabel, string> = {
  Пользователь: 'engineer',
  'Администратор знаний': 'knowledge_admin',
  'Системный администратор': 'system_admin',
};

const ACCESS_OPTIONS: Array<{ key: AccessKey; label: string; description: string }> = [
  { key: 'chat', label: 'Чат', description: 'вопросы к ассистенту и просмотр ответов' },
  { key: 'search', label: 'Поиск', description: 'поиск документов и фрагментов по базе знаний' },
  { key: 'documents', label: 'База знаний', description: 'просмотр и обслуживание базы документов' },
  { key: 'history', label: 'История', description: 'журнал запросов и ответов' },
  { key: 'qa', label: 'QA', description: 'метрики качества и инженерские оценки' },
  { key: 'admin', label: 'Администрирование', description: 'пользователи, роли и права доступа' },
  { key: 'ocrArtifacts', label: 'OCR-артефакты', description: 'исходные тексты OCR и промежуточные результаты' },
  { key: 'processingLogs', label: 'Журналы', description: 'журналы обработки документов и действий' },
];

const DEFAULT_ACCESS_BY_ROLE: Record<RoleLabel, AccessKey[]> = {
  Пользователь: ['chat', 'search', 'history'],
  'Администратор знаний': ['chat', 'search', 'documents', 'history', 'qa', 'ocrArtifacts', 'processingLogs'],
  'Системный администратор': ACCESS_OPTIONS.map((item) => item.key),
};

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

function makeAccessText(keys: AccessKey[]) {
  if (keys.length === ACCESS_OPTIONS.length) return 'Все вкладки, роли, права, полный журнал';

  return ACCESS_OPTIONS.filter((item) => keys.includes(item.key))
    .map((item) => item.label)
    .join(', ');
}

function inferAccessKeys(user: AdminUser) {
  if (user.access.includes('Все вкладки')) return ACCESS_OPTIONS.map((item) => item.key);

  const matched = ACCESS_OPTIONS.filter((item) => user.access.includes(item.label)).map((item) => item.key);
  if (user.access.includes('OCR')) matched.push('ocrArtifacts');
  if (user.access.includes('журнал') || user.access.includes('Журналы')) matched.push('processingLogs');

  return Array.from(new Set(matched.length > 0 ? matched : DEFAULT_ACCESS_BY_ROLE[user.role]));
}

function sameAccess(left: AccessKey[], right: AccessKey[]) {
  const a = [...left].sort().join('|');
  const b = [...right].sort().join('|');
  return a === b;
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
      bgcolor: 'rgba(22, 23, 27, 0.72)',
      borderColor: 'rgba(198, 216, 240, 0.34)',
      borderWidth: 1.5,
      boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
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
          border: '1.5px solid rgba(198, 216, 240, 0.24)',
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
  const {
    adminAuditLog,
    adminUsers,
    addAdminAuditLogItem,
    currentRole,
    currentUserId,
    setAdminUsers,
    themeMode,
    updateAdminUser,
    workMode,
  } = useUIStore();
  const isLight = themeMode === 'light';
  const currentUser = adminUsers.find((user) => user.id === currentUserId) ?? adminUsers[0];
  const availableSections = ADMIN_SECTIONS_ACCESS[currentRole];
  const canManageUsers = availableSections.includes('users');
  const canManagePermissions = availableSections.includes('permissions');
  const canSeeFullLogs = currentRole === 'systemAdmin';
  const [gatewayProcessingLogs, setGatewayProcessingLogs] = useState<typeof MOCK_PROCESSING_LOGS>([]);
  const processingLogs = gatewayProcessingLogs.length ? gatewayProcessingLogs : MOCK_PROCESSING_LOGS;
  const logs = canSeeFullLogs
    ? processingLogs
    : processingLogs.filter((log) => log.visibility !== 'Администратор');
  const contentAdminCards = [
    {
      label: 'Документы',
      value: 'загрузка и версии',
      note: 'файлы, ссылки, источник хранения',
      icon: <ClipboardList size={17} />,
      accent: '#9fb6d8',
    },
    {
      label: 'OCR',
      value: 'повторная обработка',
      note: 'страницы, качество распознавания',
      icon: <SlidersHorizontal size={17} />,
      accent: '#98d9d8',
    },
    {
      label: 'Артефакты',
      value: 'текст, чанки, индекс',
      note: 'то, что передается в поиск и LLM',
      icon: <ShieldCheck size={17} />,
      accent: '#d9b783',
    },
    {
      label: 'Журналы',
      value: 'обработка и ошибки',
      note: 'контроль pipeline и повторных попыток',
      icon: <UserCog size={17} />,
      accent: '#c5afff',
    },
  ];

  const [selectedUserId, setSelectedUserId] = useState(currentUser?.id ?? adminUsers[0]?.id ?? '');
  const selectedUser = adminUsers.find((user) => user.id === selectedUserId) ?? adminUsers[0];
  const [searchQuery, setSearchQuery] = useState('');
  const [adminNotice, setAdminNotice] = useState('');
  const [draftRole, setDraftRole] = useState<RoleLabel>(selectedUser?.role ?? 'Пользователь');
  const [draftAccess, setDraftAccess] = useState<AccessKey[]>(selectedUser ? inferAccessKeys(selectedUser) : []);

  useEffect(() => {
    let alive = true;

    void adminApi.users().then((users) => {
      if (alive && users.length) {
        setAdminUsers(users);
      }
    });

    void adminApi.audit().then((items) => {
      if (alive && items.length) {
        setGatewayProcessingLogs(items);
      }
    });

    return () => {
      alive = false;
    };
  }, [setAdminUsers, workMode]);

  useEffect(() => {
    if (!adminUsers.some((user) => user.id === selectedUserId) && adminUsers[0]) {
      setSelectedUserId(adminUsers[0].id);
    }
  }, [adminUsers, selectedUserId]);

  useEffect(() => {
    if (!selectedUser) return;
    setDraftRole(selectedUser.role);
    setDraftAccess(inferAccessKeys(selectedUser));
  }, [selectedUser]);

  const filteredUsers = useMemo(() => {
    const normalized = searchQuery.trim().toLowerCase();
    if (!normalized) return adminUsers;

    return adminUsers.filter((user) =>
      [user.name, user.position, user.login, user.role].some((value) => value.toLowerCase().includes(normalized)),
    );
  }, [adminUsers, searchQuery]);

  const savedAccess = selectedUser ? inferAccessKeys(selectedUser) : [];
  const hasChanges = Boolean(selectedUser) && (draftRole !== selectedUser.role || !sameAccess(draftAccess, savedAccess));
  const enabledUsersCount = adminUsers.filter((user) => user.status === 'Активен').length;
  const editingOwnSystemRole = currentRole === 'systemAdmin' && selectedUser?.id === currentUserId;

  const handleRoleChange = (role: RoleLabel) => {
    if (editingOwnSystemRole) return;

    setDraftRole(role);
    setDraftAccess(DEFAULT_ACCESS_BY_ROLE[role]);
  };

  const handleAccessToggle = (key: AccessKey) => {
    setDraftAccess((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key],
    );
  };

  const handleReset = () => {
    if (!selectedUser) return;
    setDraftRole(selectedUser.role);
    setDraftAccess(inferAccessKeys(selectedUser));
  };

  const handleSave = () => {
    if (!selectedUser || !canManagePermissions) return;

    const nextAccess = makeAccessText(draftAccess);
    updateAdminUser(selectedUser.id, {
      role: editingOwnSystemRole ? selectedUser.role : draftRole,
      access: nextAccess,
      status: selectedUser.status === 'Ожидает настройки' ? 'Активен' : selectedUser.status,
    });

    addAdminAuditLogItem({
      id: `audit-${Date.now()}`,
      time: new Date().toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
      actor: currentUser.name,
      target: selectedUser.name,
      action: 'Изменены роль и права',
      details: `Роль: ${editingOwnSystemRole ? selectedUser.role : draftRole}. Доступ: ${nextAccess}.`,
    });

    if (workMode === 'prod') {
      void adminApi
        .updateUser(selectedUser.id, {
          role: GATEWAY_ROLE_BY_LABEL[editingOwnSystemRole ? selectedUser.role : draftRole],
        })
        .then(() => setAdminNotice(`Права пользователя «${selectedUser.name}» отправлены в серверную часть`))
        .catch(() => setAdminNotice('Серверная часть не приняла изменение прав. Локально правка отображена в интерфейсе'));
    }
  };

  return (
    <Container
      maxWidth="lg"
      sx={{
        py: 4,
        ...(isLight && {
          '& .MuiPaper-root': {
            bgcolor: 'rgba(255,255,255,0.86) !important',
            borderColor: 'rgba(14,116,144,0.22) !important',
            boxShadow: '0 10px 26px rgba(15,23,42,0.055) !important',
          },
          '& .MuiTableContainer-root': {
            bgcolor: 'rgba(255,255,255,0.94) !important',
          },
          '& .MuiTableHead-root .MuiTableCell-root': {
            color: '#0f172a !important',
            borderBottomColor: 'rgba(14,116,144,0.22) !important',
          },
          '& .MuiTableBody-root .MuiTableCell-root': {
            color: '#1e293b !important',
          },
          '& .MuiTypography-root': {
            color: '#0f172a',
          },
          '& .MuiTypography-caption': {
            color: '#475569 !important',
          },
        }),
      }}
    >
      <Stack spacing={3}>
        <Paper
          variant="outlined"
          sx={{
          p: 2.1,
            borderRadius: 3,
            bgcolor: 'rgba(22, 23, 27, 0.72)',
            borderColor: 'rgba(198, 216, 240, 0.34)',
            borderWidth: 1.5,
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
          }}
        >
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.6} sx={{ alignItems: { md: 'center' } }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="overline" sx={{ color: 'rgba(198, 208, 222, 0.78)', letterSpacing: '0.14em' }}>
                Управление доступом
              </Typography>
              <Typography sx={{ mt: 0.3, color: 'rgba(233, 237, 243, 0.92)', fontSize: '1.05rem', fontWeight: 520 }}>
                {currentUser.name} · {currentUser.position}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.6, color: 'rgba(171, 183, 201, 0.78)' }}>
                Текущая роль: {ROLE_LABELS[currentRole]}. В демонстрационном режиме изменения сохраняются в интерфейсе
                и попадают в административный журнал. В рабочем режиме права передаются в контур заказчика.
              </Typography>
            </Box>
            <Chip
              label={canManagePermissions ? 'Доступно редактирование' : 'Только просмотр'}
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
              value={`${adminUsers.length}`}
              note={`активных: ${enabledUsersCount}`}
              accent="#9fb6d8"
            />
          </Box>
          <Box sx={{ flex: '1 1 210px', minWidth: 210 }}>
            <SummaryCard
              icon={<ShieldCheck size={19} />}
              label="Права доступа"
              value={canManagePermissions ? 'настройка' : 'просмотр'}
              note="роли, вкладки, журналы"
              accent="#98d9d8"
            />
          </Box>
          <Box sx={{ flex: '1 1 210px', minWidth: 210 }}>
            <SummaryCard
              icon={<ClipboardList size={19} />}
              label="Административный журнал"
              value={`${adminAuditLog.length}`}
              note="изменения ролей и прав"
              accent="#d9b783"
            />
          </Box>
          <Box sx={{ flex: '1 1 210px', minWidth: 210 }}>
            <SummaryCard
              icon={<UserCog size={19} />}
              label="Выбран пользователь"
              value={selectedUser?.name ?? 'Не выбран'}
              note={selectedUser?.role ?? 'роль не задана'}
              accent="#c5afff"
            />
          </Box>
        </Box>

        <Paper
          variant="outlined"
          sx={{
            p: 2.1,
            borderRadius: 3,
            bgcolor: 'rgba(22, 23, 27, 0.72)',
            borderColor: 'rgba(198, 216, 240, 0.34)',
            borderWidth: 1.5,
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
          }}
        >
          <Stack spacing={1.35}>
            <Box>
              <Typography sx={{ fontWeight: 560, color: 'rgba(233, 237, 243, 0.92)' }}>
                Управление контентом базы знаний
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Администратор знаний видит полный цикл обработки документа: от загрузки до индексации.
              </Typography>
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 1.15 }}>
              {contentAdminCards.map((item) => (
                <Paper
                  key={item.label}
                  variant="outlined"
                  onClick={() =>
                    setAdminNotice(
                      `${item.label}: действие будет открывать соответствующий раздел администрирования базы знаний в рабочем режиме.`,
                    )
                  }
                  sx={{
                    p: 1.35,
                    borderRadius: 2.2,
                    bgcolor: 'rgba(255,255,255,0.025)',
                    borderColor: 'rgba(198,216,240,0.22)',
                    cursor: 'pointer',
                    transition: 'transform 160ms ease, border-color 160ms ease',
                    '&:hover': {
                      transform: 'translateY(-1px)',
                      borderColor: isLight ? 'rgba(2,132,199,0.44)' : 'rgba(152,217,216,0.42)',
                    },
                  }}
                >
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
                    <Box
                      sx={{
                        p: 0.8,
                        borderRadius: 1.6,
                        color: item.accent,
                        bgcolor: 'rgba(255,255,255,0.035)',
                        border: '1px solid rgba(198,216,240,0.18)',
                      }}
                    >
                      {item.icon}
                    </Box>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography sx={{ fontSize: '0.84rem', fontWeight: 560 }}>{item.label}</Typography>
                      <Typography variant="caption" sx={{ display: 'block', mt: 0.25, color: 'rgba(233,237,243,0.86)' }}>
                        {item.value}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.35, lineHeight: 1.35 }}>
                        {item.note}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>
              ))}
            </Box>
            {adminNotice && (
              <Alert severity="info" variant="outlined" onClose={() => setAdminNotice('')} sx={{ borderRadius: 2 }}>
                {adminNotice}
              </Alert>
            )}
          </Stack>
        </Paper>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'minmax(0, 1.35fr) minmax(360px, 0.9fr)' }, gap: 2.4 }}>
          <Paper
            variant="outlined"
            sx={{
              p: 2.1,
              borderRadius: 3,
              bgcolor: 'rgba(22, 23, 27, 0.72)',
              borderColor: 'rgba(198, 216, 240, 0.34)',
              borderWidth: 1.5,
              boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
            }}
          >
            <Stack spacing={1.6}>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' } }}>
                <Typography sx={{ flex: 1, fontWeight: 540, color: 'rgba(233, 237, 243, 0.92)' }}>
                  Пользователи и роли
                </Typography>
                <TextField
                  size="small"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Найти пользователя"
                  slotProps={{
                    input: {
                      startAdornment: <Search size={16} style={{ marginRight: 8, opacity: 0.7 }} />,
                    },
                  }}
                  sx={{ width: { xs: '100%', md: 260 } }}
                />
              </Stack>

              <TableContainer component={Paper} variant="outlined" sx={TABLE_SX}>
                <Table size="small" sx={tableCellSx}>
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'rgba(156, 176, 204, 0.075)' }}>
                      <TableCell>Пользователь</TableCell>
                      <TableCell>Логин</TableCell>
                      <TableCell>Роль</TableCell>
                      <TableCell>Статус</TableCell>
                      <TableCell>Последний вход</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredUsers.map((user) => {
                      const selected = user.id === selectedUser?.id;

                      return (
                        <TableRow
                          key={user.id}
                          hover
                          onClick={() => setSelectedUserId(user.id)}
                          sx={{
                            cursor: 'pointer',
                            bgcolor: selected ? 'rgba(152, 217, 216, 0.08) !important' : undefined,
                            outline: selected ? '1px solid rgba(152, 217, 216, 0.22)' : 'none',
                          }}
                        >
                          <TableCell>
                            <Typography sx={{ fontWeight: 520, fontSize: '0.84rem' }}>{user.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {user.position}
                            </Typography>
                          </TableCell>
                          <TableCell>{user.login}</TableCell>
                          <TableCell>{user.role}</TableCell>
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
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </Stack>
          </Paper>

          <Paper
            variant="outlined"
            sx={{
              p: 2.1,
              borderRadius: 3,
              bgcolor: 'rgba(22, 23, 27, 0.72)',
              borderColor: 'rgba(198, 216, 240, 0.34)',
              borderWidth: 1.5,
              boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
            }}
          >
            <Stack spacing={1.8}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <SlidersHorizontal size={18} color="#98d9d8" />
                <Box sx={{ flex: 1 }}>
                  <Typography sx={{ fontWeight: 540, color: 'rgba(233, 237, 243, 0.92)' }}>
                    Настройка прав доступа
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {selectedUser ? `${selectedUser.name} · ${selectedUser.login}` : 'Пользователь не выбран'}
                  </Typography>
                </Box>
                {hasChanges && <Chip size="small" label="есть изменения" color="warning" variant="outlined" />}
              </Stack>

              {editingOwnSystemRole && (
                <Alert severity="info" variant="outlined" sx={{ borderRadius: 2 }}>
                  Роль текущего системного администратора защищена от случайного понижения в демонстрационном режиме.
                </Alert>
              )}

              <FormControl size="small" fullWidth disabled={!canManagePermissions || editingOwnSystemRole}>
                <InputLabel>Роль</InputLabel>
                <Select
                  value={draftRole}
                  label="Роль"
                  onChange={(event) => handleRoleChange(event.target.value as RoleLabel)}
                >
                  {ROLE_OPTIONS.map((role) => (
                    <MenuItem key={role} value={role}>
                      {role}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)' }} />

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 0.75 }}>
                {ACCESS_OPTIONS.map((option) => (
                  <FormControlLabel
                    key={option.key}
                    control={
                      <Checkbox
                        checked={draftAccess.includes(option.key)}
                        onChange={() => handleAccessToggle(option.key)}
                        disabled={!canManagePermissions}
                        sx={{ color: 'rgba(152,217,216,0.66)' }}
                      />
                    }
                    label={
                      <Box>
                        <Typography sx={{ fontSize: '0.84rem', lineHeight: 1.2 }}>{option.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {option.description}
                        </Typography>
                      </Box>
                    }
                    sx={{
                      m: 0,
                      px: 1,
                      py: 0.7,
                      borderRadius: 1.6,
                      border: '1.5px solid rgba(198, 216, 240, 0.24)',
                      bgcolor: draftAccess.includes(option.key) ? 'rgba(152,217,216,0.055)' : 'rgba(255,255,255,0.015)',
                    }}
                  />
                ))}
              </Box>

              <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                <Button variant="outlined" className="app-action-button" onClick={handleReset} disabled={!hasChanges}>
                  Сбросить
                </Button>
                <Button
                  variant="contained"
                  className="app-action-button"
                  startIcon={<Save size={16} />}
                  onClick={handleSave}
                  disabled={!canManagePermissions || !hasChanges}
                  disableElevation
                >
                  Сохранить изменения
                </Button>
              </Stack>
            </Stack>
          </Paper>
        </Box>

        <Stack spacing={1.25}>
          <Box>
            <Typography sx={{ mb: 0.85, fontWeight: 540, color: 'rgba(233, 237, 243, 0.92)' }}>
              Административный журнал изменений
            </Typography>
            <TableContainer component={Paper} variant="outlined" sx={TABLE_SX}>
              <Table size="small" sx={tableCellSx}>
                <TableHead>
                  <TableRow sx={{ bgcolor: 'rgba(156, 176, 204, 0.075)' }}>
                    <TableCell>Время</TableCell>
                    <TableCell>Кто изменил</TableCell>
                    <TableCell>Объект</TableCell>
                    <TableCell>Действие</TableCell>
                    <TableCell>Детали</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {adminAuditLog.map((entry) => (
                    <TableRow key={entry.id} hover>
                      <TableCell sx={{ whiteSpace: 'nowrap', color: '#9fd3ff' }}>{entry.time}</TableCell>
                      <TableCell sx={{ fontWeight: 520 }}>{entry.actor}</TableCell>
                      <TableCell>{entry.target}</TableCell>
                      <TableCell>{entry.action}</TableCell>
                      <TableCell sx={{ color: 'rgba(171, 183, 201, 0.86)' }}>{entry.details}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box sx={{ mt: 0.7 }}>
            <Typography sx={{ mb: 0.85, fontWeight: 540, color: 'rgba(233, 237, 243, 0.92)' }}>
              Журнал обработки документов
            </Typography>
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
          </Box>
        </Stack>
      </Stack>
    </Container>
  );
};
