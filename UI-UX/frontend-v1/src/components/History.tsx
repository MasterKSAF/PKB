import React, { useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Container,
  FormControl,
  IconButton,
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
import { Download, ExternalLink, FileText, MessageSquarePlus, Search, X } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../utils/http';
import type { AnswerStatus, Citation, QueryHistoryItem } from '../utils/mockData';
import { useUIStore } from '../store/uiStore';

type HistoryPreview = Citation & {
  previewKind: 'source' | 'document';
};

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

const tableShellSx = {
  borderRadius: 3,
  bgcolor: 'rgba(7, 14, 22, 0.94)',
  borderWidth: 1.5,
  borderColor: 'rgba(194, 213, 238, 0.48)',
  boxShadow:
    '0 0 0 1px rgba(194, 213, 238, 0.28), 0 0 0 3px rgba(102, 142, 198, 0.12), inset 0 1px 0 rgba(255,255,255,0.02)',
} as const;

const tableSx = {
  '& .MuiTableCell-root': {
    borderBottomColor: 'rgba(198, 214, 236, 0.24)',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    verticalAlign: 'top',
    py: 1.25,
    px: 1.45,
  },
  '& .MuiTableHead-root .MuiTableCell-root': {
    color: 'rgba(230, 236, 244, 0.90)',
    borderBottom: '1px solid rgba(181, 198, 220, 0.30)',
    boxShadow: 'inset 0 -1px 0 rgba(181, 198, 220, 0.12), inset 0 1px 0 rgba(255,255,255,0.03)',
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
    fontSize: '0.82rem',
    lineHeight: 1.5,
    color: 'rgba(222, 230, 241, 0.84)',
  },
} as const;

function csvEscape(value: string | number) {
  return `"${String(value).replaceAll('"', '""')}"`;
}

function citationButtonSx(themeMode: 'dark' | 'light') {
  const isLight = themeMode === 'light';

  return {
    px: 0.9,
    py: 0.28,
    minWidth: 0,
    height: 'auto',
    fontSize: '0.74rem',
    color: isLight ? '#334155' : '#b8c4d8',
    border: isLight ? '1px solid rgba(51,65,85,0.20)' : '1px solid rgba(184,196,216,0.20)',
    borderRadius: 999,
    bgcolor: isLight ? 'rgba(51,65,85,0.04)' : 'rgba(184,196,216,0.06)',
  } as const;
}

export const History: React.FC = () => {
  const { setActiveTab, setChatMessages, themeMode } = useUIStore();
  const [queryFilter, setQueryFilter] = useState('');
  const [userFilter, setUserFilter] = useState('all');
  const [projectFilter, setProjectFilter] = useState('all');
  const [topicFilter, setTopicFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<'all' | AnswerStatus>('all');
  const [expandedHistoryId, setExpandedHistoryId] = useState<string | null>(null);
  const [activePreview, setActivePreview] = useState<HistoryPreview | null>(null);

  const { data = [] } = useQuery<QueryHistoryItem[]>({
    queryKey: ['history'],
    queryFn: historyApi.get,
  });

  const users = useMemo(() => Array.from(new Set(data.map((item) => item.user))), [data]);
  const projects = useMemo(() => Array.from(new Set(data.map((item) => item.project))), [data]);
  const topics = useMemo(() => Array.from(new Set(data.map((item) => item.topic))), [data]);

  const filteredData = useMemo(() => {
    const normalized = queryFilter.trim().toLowerCase();

    return data.filter((item) => {
      const chatText = item.messages.map((message) => message.content).join(' ');
      const matchesQuery =
        !normalized ||
        [item.query, item.answer, item.session, item.project, item.topic, chatText].some((value) =>
          value.toLowerCase().includes(normalized),
        );
      const matchesUser = userFilter === 'all' || item.user === userFilter;
      const matchesProject = projectFilter === 'all' || item.project === projectFilter;
      const matchesTopic = topicFilter === 'all' || item.topic === topicFilter;
      const matchesStatus = statusFilter === 'all' || item.status === statusFilter;

      return matchesQuery && matchesUser && matchesProject && matchesTopic && matchesStatus;
    });
  }, [data, projectFilter, queryFilter, statusFilter, topicFilter, userFilter]);

  const handleExport = () => {
    const rows = [
      ['Дата', 'Пользователь', 'Проект', 'Тема', 'Сессия', 'Запрос', 'Ответ', 'Источники', 'Статус'],
      ...filteredData.map((item) => [
        item.createdAt,
        item.user,
        item.project,
        item.topic,
        item.session,
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
    link.download = 'pkb_history_filtered.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleContinueChat = (item: QueryHistoryItem) => {
    setChatMessages(item.messages);
    setActiveTab('chat');
  };

  const handleOpenPreview = (citation: Citation, previewKind: HistoryPreview['previewKind']) => {
    setActivePreview({
      ...citation,
      page: previewKind === 'document' ? 1 : citation.page,
      previewKind,
    });
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 142px)', minHeight: 0 }}>
      <Box sx={{ flex: 1, minWidth: 0, overflowY: 'auto' }}>
        <Container maxWidth="xl" sx={{ py: 3.2 }}>
          <Stack spacing={2.4}>
            <Paper
              variant="outlined"
              sx={{
                p: 1.25,
                borderRadius: 3,
                bgcolor: 'rgba(22, 23, 27, 0.72)',
                borderColor: 'rgba(198, 216, 240, 0.34)',
                borderWidth: 1.5,
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
              }}
            >
              <Stack spacing={1}>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ alignItems: { md: 'center' } }}>
                  <TextField
                    size="small"
                    label="Поиск по чатам"
                    value={queryFilter}
                    onChange={(event) => setQueryFilter(event.target.value)}
                    sx={{ width: { xs: '100%', md: 310 } }}
                    slotProps={{
                      input: {
                        startAdornment: <Search size={17} style={{ marginRight: 10, opacity: 0.65 }} />,
                      },
                    }}
                  />

                  <Button
                    className="app-action-button"
                    variant="contained"
                    startIcon={<Download size={16} />}
                    onClick={handleExport}
                    disableElevation
                    sx={{ whiteSpace: 'nowrap', minWidth: 128 }}
                  >
                    Экспорт
                  </Button>
                </Stack>

                <Stack
                  direction="row"
                  spacing={1}
                  useFlexGap
                  sx={{
                    alignItems: 'center',
                    flexWrap: 'wrap',
                  }}
                >
                  <FormControl size="small" sx={{ width: { xs: 'calc(50% - 4px)', md: 180 } }}>
                    <InputLabel>Пользователь</InputLabel>
                    <Select label="Пользователь" value={userFilter} onChange={(event) => setUserFilter(event.target.value)}>
                      <MenuItem value="all">Все</MenuItem>
                      {users.map((user) => (
                        <MenuItem key={user} value={user}>
                          {user}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl size="small" sx={{ width: { xs: 'calc(50% - 4px)', md: 160 } }}>
                    <InputLabel>Проект</InputLabel>
                    <Select label="Проект" value={projectFilter} onChange={(event) => setProjectFilter(event.target.value)}>
                      <MenuItem value="all">Все</MenuItem>
                      {projects.map((project) => (
                        <MenuItem key={project} value={project}>
                          {project}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl size="small" sx={{ width: { xs: 'calc(50% - 4px)', md: 150 } }}>
                    <InputLabel>Тема</InputLabel>
                    <Select label="Тема" value={topicFilter} onChange={(event) => setTopicFilter(event.target.value)}>
                      <MenuItem value="all">Все</MenuItem>
                      {topics.map((topic) => (
                        <MenuItem key={topic} value={topic}>
                          {topic}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl size="small" sx={{ width: { xs: 'calc(50% - 4px)', md: 185 } }}>
                    <InputLabel>Статус</InputLabel>
                    <Select
                      label="Статус"
                      value={statusFilter}
                      onChange={(event) => setStatusFilter(event.target.value as 'all' | AnswerStatus)}
                    >
                      <MenuItem value="all">Все статусы</MenuItem>
                      {Object.entries(statusLabel).map(([status, label]) => (
                        <MenuItem key={status} value={status}>
                          {label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Stack>
              </Stack>
            </Paper>

            <TableContainer component={Paper} variant="outlined" sx={tableShellSx}>
              <Table size="small" sx={tableSx}>
                <TableHead>
                  <TableRow sx={{ bgcolor: 'rgba(156, 176, 204, 0.075)' }}>
                    <TableCell>Дата</TableCell>
                    <TableCell>Пользователь</TableCell>
                    <TableCell>Проект</TableCell>
                    <TableCell>Тема</TableCell>
                    <TableCell>Сессия / запрос</TableCell>
                    <TableCell>Источники</TableCell>
                    <TableCell>Статус</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredData.map((item) => {
                    const expanded = expandedHistoryId === item.id;

                    return (
                      <React.Fragment key={item.id}>
                        <TableRow
                          hover
                          onClick={() => {
                            setExpandedHistoryId(expanded ? null : item.id);
                            if (!expanded) setActivePreview(null);
                          }}
                          sx={{
                            cursor: 'pointer',
                            bgcolor: expanded ? 'rgba(152, 217, 216, 0.08) !important' : undefined,
                            outline: expanded ? '1px solid rgba(152, 217, 216, 0.24)' : 'none',
                          }}
                        >
                          <TableCell sx={{ whiteSpace: 'nowrap', color: 'text.secondary' }}>{item.createdAt}</TableCell>
                          <TableCell>{item.user}</TableCell>
                          <TableCell>{item.project}</TableCell>
                          <TableCell>{item.topic}</TableCell>
                          <TableCell sx={{ maxWidth: 340 }}>
                            <Typography sx={{ fontSize: '0.82rem', fontWeight: 520 }}>{item.session}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {item.query}
                            </Typography>
                          </TableCell>
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

                        {expanded && (
                          <TableRow>
                            <TableCell colSpan={7} sx={{ p: 0, bgcolor: 'rgba(5, 10, 16, 0.72)' }}>
                              <Box sx={{ p: 2 }}>
                                <Paper
                                  variant="outlined"
                                  sx={{
                                    p: 2,
                                    borderRadius: 2.6,
                                    bgcolor: 'rgba(22, 23, 27, 0.78)',
                                    borderColor: 'rgba(198, 216, 240, 0.34)',
                                    borderWidth: 1.5,
                                    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
                                  }}
                                >
                                  <Stack spacing={1.5}>
                                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' } }}>
                                      <Box sx={{ flex: 1, minWidth: 0 }}>
                                        <Typography sx={{ fontWeight: 560, color: 'text.primary' }}>{item.session}</Typography>
                                        <Typography variant="caption" color="text.secondary">
                                          {item.project} · {item.topic} · {item.user}
                                        </Typography>
                                      </Box>
                                      <Button
                                        size="small"
                                        variant="outlined"
                                        className="app-action-button"
                                        startIcon={<MessageSquarePlus size={15} />}
                                        onClick={() => handleContinueChat(item)}
                                        sx={{ whiteSpace: 'nowrap', alignSelf: { xs: 'flex-start', md: 'center' } }}
                                      >
                                        Продолжить чат
                                      </Button>
                                    </Stack>

                                    <Stack spacing={1.1}>
                                      {item.messages.map((message) => {
                                        const isAssistant = message.role === 'assistant';

                                        return (
                                          <Paper
                                            key={message.id}
                                            variant="outlined"
                                            sx={{
                                              p: 1.35,
                                              borderRadius: 2.2,
                                              bgcolor: isAssistant ? 'rgba(255,255,255,0.045)' : 'rgba(255,255,255,0.07)',
                                              borderColor: 'rgba(198, 216, 240, 0.26)',
                                              borderWidth: 1.5,
                                            }}
                                          >
                                            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.9 }}>
                                              <Typography
                                                variant="caption"
                                                sx={{
                                                  color: isAssistant ? '#98d9d8' : '#d8b07a',
                                                  fontWeight: 600,
                                                  letterSpacing: '0.04em',
                                                }}
                                              >
                                                {isAssistant ? 'Ассистент' : 'Запрос инженера'}
                                              </Typography>
                                              <Typography variant="caption" color="text.secondary">
                                                {message.timestamp}
                                              </Typography>
                                            </Stack>
                                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>
                                              {message.content}
                                            </Typography>

                                            {message.citations && message.citations.length > 0 && (
                                              <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', mt: 1 }}>
                                                {message.citations.map((citation, index) => (
                                                  <Stack key={citation.id} direction="row" spacing={0.7} sx={{ alignItems: 'center' }}>
                                                    <Typography variant="caption" color="text.secondary">
                                                      {index + 1}.
                                                    </Typography>
                                                    <Button
                                                      size="small"
                                                      variant="text"
                                                      startIcon={<ExternalLink size={14} />}
                                                      className="source-link-button"
                                                      sx={citationButtonSx(themeMode)}
                                                      onClick={() => handleOpenPreview(citation, 'source')}
                                                    >
                                                      Страница
                                                    </Button>
                                                    <Button
                                                      size="small"
                                                      variant="text"
                                                      startIcon={<FileText size={14} />}
                                                      className="source-link-button"
                                                      sx={citationButtonSx(themeMode)}
                                                      onClick={() => handleOpenPreview(citation, 'document')}
                                                    >
                                                      Документ
                                                    </Button>
                                                  </Stack>
                                                ))}
                                              </Stack>
                                            )}
                                          </Paper>
                                        );
                                      })}
                                    </Stack>
                                  </Stack>
                                </Paper>
                              </Box>
                            </TableCell>
                          </TableRow>
                        )}
                      </React.Fragment>
                    );
                  })}

                  {filteredData.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>
                        История по текущим фильтрам не найдена.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Stack>
        </Container>
      </Box>

      {activePreview && (
        <Box
          sx={{
            width: 420,
            minWidth: 340,
            borderLeft: '1.5px solid rgba(198, 216, 240, 0.22)',
            bgcolor: '#101116',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box sx={{ p: 1.5, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
              <FileText size={18} />
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="subtitle2">
                  {activePreview.previewKind === 'source' ? 'Страница документа' : 'Документ'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {activePreview.previewKind === 'document'
                    ? `с первой страницы · ${activePreview.version}`
                    : `${activePreview.section} · стр. ${activePreview.page}`}
                </Typography>
              </Box>
              <IconButton size="small" onClick={() => setActivePreview(null)} sx={{ color: 'text.secondary' }}>
                <X size={16} />
              </IconButton>
            </Stack>
          </Box>

          <Box sx={{ overflow: activePreview.previewKind === 'document' ? 'auto' : 'hidden', flexGrow: 1, p: 2 }}>
            <Paper
              variant="outlined"
              sx={{
                minHeight: activePreview.previewKind === 'document' ? 860 : 520,
                p: 2.4,
                borderRadius: 2,
                bgcolor: '#f4f1e8',
                color: '#242424',
                borderColor: 'rgba(255,255,255,0.12)',
              }}
            >
              <Typography variant="caption" sx={{ color: '#666', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {activePreview.previewKind === 'source' ? 'Страница / один лист' : 'Полный документ'}
              </Typography>
              <Typography variant="h6" sx={{ mt: 1, mb: 1, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                {activePreview.document}
              </Typography>
              <Typography variant="body2" sx={{ color: '#555', mb: 2 }}>
                {activePreview.section} · стр. {activePreview.page} · {activePreview.version}
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
                [1, 2, 3].map((pageOffset) => (
                  <Box key={pageOffset} sx={{ mt: 4, pt: 3, minHeight: 420, borderTop: '1px solid #d2cec2' }}>
                    <Typography variant="caption" sx={{ color: '#777' }}>
                      Страница {activePreview.page + pageOffset}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1, lineHeight: 1.85 }}>
                      Здесь будет продолжение исходного документа в том формате, который отдаст база знаний или backend
                      предпросмотра.
                    </Typography>
                  </Box>
                ))}
            </Paper>
          </Box>
        </Box>
      )}
    </Box>
  );
};
