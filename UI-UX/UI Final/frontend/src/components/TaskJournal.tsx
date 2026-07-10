import React, { useEffect, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  Container,
  MenuItem,
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
import { draftsApi, tasksApi, type GatewayTaskListItem, type GatewayTaskStatusDetail } from '../utils/http';
import { useUIStore } from '../store/uiStore';

const FieldLabel: React.FC<{ label: string; value: string; isLight: boolean }> = ({ label, value, isLight }) => (
  <React.Fragment>
    <Typography component="span" sx={{ color: isLight ? '#475569' : 'rgba(171, 183, 201, 0.7)', fontWeight: 520, whiteSpace: 'nowrap' }}>
      {label}
    </Typography>
    <Typography component="span" sx={{ color: isLight ? '#0f172a' : 'rgba(198, 216, 240, 0.88)', fontFamily: 'monospace', fontSize: '0.82rem' }}>
      {value}
    </Typography>
  </React.Fragment>
);

function statusColor(status: string) {
  const s = status.toLowerCase();
  if (s === 'completed' || s === 'success' || s === 'active') return 'success';
  if (s === 'pending' || s === 'queued' || s === 'processing') return 'warning';
  return 'error';
}

function fmtDateTime(iso?: string) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso.slice(0, 16);
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' });
}

const cellSx = {
  borderColor: 'rgba(198, 214, 236, 0.12)',
  color: 'rgba(198, 216, 240, 0.88)',
  fontSize: '0.82rem',
  py: 0.75,
  px: 1.2,
};

const headerCellSx = {
  ...cellSx,
  fontWeight: 600,
  color: 'rgba(171, 183, 201, 0.7)',
  fontSize: '0.73rem',
  textTransform: 'uppercase' as const,
  letterSpacing: '0.06em',
  py: 1,
};

type DraftOption = { id: string; label: string };

export const TaskJournal: React.FC = () => {
  const { themeMode } = useUIStore();
  const isLight = themeMode === 'light';

  const [tasks, setTasks] = useState<GatewayTaskListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [draftNames, setDraftNames] = useState<Record<string, string>>({});
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterDraft, setFilterDraft] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [limit, setLimit] = useState(50);

  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskDetail, setTaskDetail] = useState<GatewayTaskStatusDetail | null>(null);
  const [taskLoading, setTaskLoading] = useState(false);
  const [selectedStepIdx, setSelectedStepIdx] = useState<number | null>(null);

  const loadData = () => {
    setLoading(true);
    setError('');
    setSelectedTaskId(null);
    setTaskDetail(null);
    setSelectedStepIdx(null);

    Promise.all([
      tasksApi.list({ status: filterStatus || undefined, pipelineType: filterType || undefined, pageSize: limit }),
      draftsApi.list({ pageSize: 200 }),
    ])
      .then(([taskResult, draftItems]) => {
        setTasks(taskResult.items);
        const names: Record<string, string> = {};
        for (const d of draftItems) {
          const id = String(d.draft_id);
          names[id] = d.display_name || d.original_filename || d.filename || d.title || `#${id}`;
        }
        setDraftNames(names);
      })
      .catch(() => setError('Не удалось загрузить данные'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const selectTask = (taskId: string) => {
    setSelectedTaskId(taskId);
    setSelectedStepIdx(null);
    setTaskLoading(true);
    tasksApi.detail(taskId)
      .then((detail) => setTaskDetail(detail))
      .catch(() => setTaskDetail(null))
      .finally(() => setTaskLoading(false));
  };

  const filteredTasks = tasks.filter((t) => {
    if (filterDraft && t.draftId !== filterDraft) return false;
    if (filterDateFrom && t.createdAt) {
      const d = t.createdAt.slice(0, 10);
      if (d < filterDateFrom) return false;
    }
    if (filterDateTo && t.createdAt) {
      const d = t.createdAt.slice(0, 10);
      if (d > filterDateTo) return false;
    }
    return true;
  });

  const draftOptions: DraftOption[] = [...new Set(tasks.map((t) => t.draftId))]
    .map((id) => ({ id, label: draftNames[id] ?? `#${id}` }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return (
    <Container maxWidth={false} disableGutters sx={{ py: 3, width: '100%' }}>
      <Stack spacing={2.5}>
        <Paper
          variant="outlined"
          sx={{
            p: 2.1,
            borderRadius: 3,
            bgcolor: 'rgba(22, 23, 27, 0.72)',
            borderColor: 'rgba(198, 216, 240, 0.34)',
            borderWidth: 1.5,
          }}
        >
          <Stack spacing={1.5}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' } }}>
              <Autocomplete
                size="small"
                options={draftOptions}
                value={draftOptions.find((o) => o.id === filterDraft) ?? null}
                onChange={(_, v) => setFilterDraft(v?.id ?? '')}
                onInputChange={(_, v) => {
                  if (!v) setFilterDraft('');
                }}
                getOptionLabel={(o) => o.label}
                isOptionEqualToValue={(a, b) => a.id === b.id}
                renderInput={(params) => (
                  <TextField {...params} label="Черновик" sx={{ width: { xs: '100%', md: 220 } }} />
                )}
                sx={{ width: { xs: '100%', md: 220 } }}
                clearOnBlur={false}
                disableClearable={false}
              />
              <TextField
                size="small"
                type="date"
                value={filterDateFrom}
                onChange={(e) => setFilterDateFrom(e.target.value)}
                sx={{ width: { xs: '100%', md: 150 } }}
                label="От"
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <TextField
                size="small"
                type="date"
                value={filterDateTo}
                onChange={(e) => setFilterDateTo(e.target.value)}
                sx={{ width: { xs: '100%', md: 150 } }}
                label="До"
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <TextField
                select
                size="small"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                sx={{ width: { xs: '100%', md: 140 } }}
                label="Статус"
              >
                <MenuItem value="">Все</MenuItem>
                <MenuItem value="active">Активные</MenuItem>
                <MenuItem value="completed">Завершённые</MenuItem>
                <MenuItem value="failed">Ошибки</MenuItem>
              </TextField>
              <TextField
                select
                size="small"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                sx={{ width: { xs: '100%', md: 140 } }}
                label="Тип"
              >
                <MenuItem value="">Все</MenuItem>
                <MenuItem value="formation">Формирование</MenuItem>
                <MenuItem value="indexation">Индексация</MenuItem>
              </TextField>
              <TextField
                select
                size="small"
                value={String(limit)}
                onChange={(e) => setLimit(Number(e.target.value))}
                sx={{ width: { xs: '100%', md: 100 } }}
                label="Кол-во"
              >
                <MenuItem value="20">20</MenuItem>
                <MenuItem value="50">50</MenuItem>
                <MenuItem value="100">100</MenuItem>
                <MenuItem value="200">200</MenuItem>
              </TextField>
              <Button variant="contained" className="app-action-button" size="small" onClick={loadData}>
                Загрузить
              </Button>
            </Stack>
          </Stack>
        </Paper>

        {error && <Alert severity="error" variant="outlined" sx={{ borderRadius: 2 }}>{error}</Alert>}

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Stack spacing={2} sx={{ flex: '0 0 440px', minWidth: 280 }}>
            <Paper
              variant="outlined"
              sx={{
                p: 0,
                borderRadius: 3,
                bgcolor: 'rgba(7, 14, 22, 0.94)',
                borderColor: 'rgba(198, 216, 240, 0.52)',
                borderWidth: 1.5,
                overflow: 'auto',
              }}
            >
              <Typography sx={{ p: 1.5, pb: 1, fontWeight: 540, fontSize: '0.95rem', color: 'rgba(233, 237, 243, 0.92)', borderBottom: '1px solid rgba(198, 214, 236, 0.24)' }}>
                Задачи{filteredTasks.length > 0 ? ` (${filteredTasks.length})` : ''}
              </Typography>
              {loading && <Typography variant="caption" sx={{ display: 'block', p: 1.5, color: 'rgba(171, 183, 201, 0.6)' }}>Загрузка...</Typography>}
              {!loading && filteredTasks.length === 0 && <Typography variant="caption" sx={{ display: 'block', p: 1.5, color: 'rgba(171, 183, 201, 0.6)' }}>Нет задач</Typography>}
              {!loading && filteredTasks.length > 0 && (
                <TableContainer>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ ...headerCellSx, width: 50 }}>ID</TableCell>
                        <TableCell sx={{ ...headerCellSx, width: 140 }}>Дата</TableCell>
                        <TableCell sx={headerCellSx}>Файл</TableCell>
                        <TableCell sx={{ ...headerCellSx, width: 90 }}>Статус</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredTasks.map((t) => (
                        <TableRow
                          key={t.taskId}
                          hover
                          selected={selectedTaskId === t.taskId}
                          onClick={() => selectTask(t.taskId)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell sx={{ ...cellSx, width: 50, borderLeft: selectedTaskId === t.taskId ? '3px solid #26c6b0' : '3px solid transparent', bgcolor: selectedTaskId === t.taskId ? 'rgba(38, 198, 176, 0.40)' : undefined }}>
                            <Typography sx={{ fontWeight: 600, color: selectedTaskId === t.taskId ? '#26c6b0' : '#9fd3ff', fontSize: '0.82rem' }}>#{t.taskId}</Typography>
                          </TableCell>
                          <TableCell sx={{ ...cellSx, width: 140, whiteSpace: 'nowrap', bgcolor: selectedTaskId === t.taskId ? 'rgba(38, 198, 176, 0.40)' : undefined }}>{fmtDateTime(t.createdAt)}</TableCell>
                          <TableCell sx={{ ...cellSx, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', bgcolor: selectedTaskId === t.taskId ? 'rgba(38, 198, 176, 0.40)' : undefined }}>
                            {draftNames[t.draftId] ?? `#${t.draftId}`}
                          </TableCell>
                          <TableCell sx={{ ...cellSx, width: 90, bgcolor: selectedTaskId === t.taskId ? 'rgba(38, 198, 176, 0.40)' : undefined }}>
                            <Chip label={t.status} size="small" color={statusColor(t.status) as 'success' | 'warning' | 'error'} variant="outlined" sx={{ height: 20, fontSize: '0.72rem' }} />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Paper>

            <Paper
              variant="outlined"
              sx={{
                p: 0,
                borderRadius: 3,
                bgcolor: 'rgba(7, 14, 22, 0.94)',
                borderColor: 'rgba(198, 216, 240, 0.52)',
                borderWidth: 1.5,
                overflow: 'auto',
              }}
            >
              <Typography sx={{ p: 1.5, pb: 1, fontWeight: 540, fontSize: '0.95rem', color: 'rgba(233, 237, 243, 0.92)', borderBottom: '1px solid rgba(198, 214, 236, 0.24)' }}>
                Шаги задачи
              </Typography>
              {!selectedTaskId && <Typography variant="caption" sx={{ display: 'block', p: 1.5, color: 'rgba(171, 183, 201, 0.6)' }}>Выберите задачу</Typography>}
              {taskLoading && <Typography variant="caption" sx={{ display: 'block', p: 1.5, color: 'rgba(171, 183, 201, 0.6)' }}>Загрузка...</Typography>}
              {taskDetail && taskDetail.steps.length === 0 && <Typography variant="caption" sx={{ display: 'block', p: 1.5, color: 'rgba(171, 183, 201, 0.6)' }}>Нет шагов</Typography>}
              {taskDetail && taskDetail.steps.length > 0 && (
                <TableContainer>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ ...headerCellSx, width: 40 }}>#</TableCell>
                        <TableCell sx={headerCellSx}>Шаг</TableCell>
                        <TableCell sx={headerCellSx}>Сервис</TableCell>
                        <TableCell sx={headerCellSx}>Статус</TableCell>
                        <TableCell sx={headerCellSx}>Ошибка</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {taskDetail.steps.map((step, idx) => {
                        const isSel = selectedStepIdx === idx;
                        return (
                        <TableRow
                          key={idx}
                          hover
                          selected={isSel}
                          onClick={() => setSelectedStepIdx(selectedStepIdx === idx ? null : idx)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell sx={{ ...cellSx, width: 40,
                            borderLeft: isSel ? '3px solid #26c6b0' : '3px solid transparent',
                            color: isSel ? '#26c6b0' : undefined,
                            fontWeight: isSel ? 700 : undefined,
                            bgcolor: isSel ? 'rgba(38, 198, 176, 0.40)' : undefined,
                          }}>{idx + 1}</TableCell>
                          <TableCell sx={{
                            ...cellSx, fontWeight: isSel ? 600 : 520,
                            color: isSel ? '#26c6b0' : '#9fd3ff',
                            bgcolor: isSel ? 'rgba(38, 198, 176, 0.40)' : undefined,
                          }}>{step.stepName}</TableCell>
                          <TableCell sx={{ ...cellSx, fontWeight: isSel ? 600 : undefined, color: isSel ? '#26c6b0' : undefined, bgcolor: isSel ? 'rgba(38, 198, 176, 0.40)' : undefined }}>{step.serviceName}</TableCell>
                          <TableCell sx={{ ...cellSx, bgcolor: isSel ? 'rgba(38, 198, 176, 0.40)' : undefined }}>
                            <Chip label={step.status} size="small" color={statusColor(step.status) as 'success' | 'warning' | 'error'} variant="outlined" sx={{ height: 20, fontSize: '0.72rem' }} />
                          </TableCell>
                          <TableCell sx={{ ...cellSx, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', bgcolor: isSel ? 'rgba(38, 198, 176, 0.40)' : undefined }}>
                            {step.errorMessage || '—'}
                          </TableCell>
                        </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Paper>
          </Stack>

          {selectedStepIdx !== null && taskDetail?.steps[selectedStepIdx] && (() => {
            const selectedStep = taskDetail.steps[selectedStepIdx];
            return (<Paper
              variant="outlined"
              sx={{
                flex: '1 1 500px',
                p: 2,
                borderRadius: 3,
                bgcolor: 'rgba(7, 14, 22, 0.94)',
                borderColor: 'rgba(152, 217, 216, 0.32)',
                borderWidth: 1.5,
                alignSelf: 'flex-start',
                maxHeight: 700,
                overflow: 'auto',
              }}
            >
              <Stack spacing={1.5}>
                <Typography sx={{ fontWeight: 540, color: 'rgba(233, 237, 243, 0.92)' }}>
                  {selectedStep.stepName} — полные данные
                </Typography>
                {selectedStep.errorMessage && <Alert severity="error" variant="outlined" sx={{ borderRadius: 1.5 }}>{selectedStep.errorMessage}</Alert>}

                <Box sx={{
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr',
                  gap: '6px 16px',
                  fontSize: '0.84rem',
                }}>
                  <FieldLabel label="Step" value={selectedStep.stepName} isLight={isLight} />
                  <FieldLabel label="Service" value={selectedStep.serviceName} isLight={isLight} />
                  <FieldLabel label="Status" value={selectedStep.status} isLight={isLight} />
                  <FieldLabel label="Error Code" value={selectedStep.errorCode ?? '—'} isLight={isLight} />
                  <FieldLabel label="Started" value={selectedStep.startedAt ?? '—'} isLight={isLight} />
                  <FieldLabel label="Completed" value={selectedStep.completedAt ?? '—'} isLight={isLight} />
                </Box>

                <Typography variant="caption" sx={{ fontWeight: 600, color: 'rgba(198, 216, 240, 0.7)' }}>Input Data</Typography>
                <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end', mt: -3, mb: 0.5 }}>
                  <Button size="small" variant="outlined" onClick={() => navigator.clipboard.writeText(JSON.stringify(selectedStep.inputData, null, 2))}>
                    Копировать
                  </Button>
                </Stack>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: '#f5f7fa',
                    border: '1px solid rgba(198, 216, 240, 0.3)',
                    fontFamily: 'monospace',
                    fontSize: '0.82rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    overflow: 'auto',
                    maxHeight: 300,
                    color: '#1e293b',
                  }}
                >
                  {JSON.stringify(selectedStep.inputData, null, 2)}
                </Box>

                <Typography variant="caption" sx={{ fontWeight: 600, color: 'rgba(198, 216, 240, 0.7)' }}>Output Data</Typography>
                <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end', mt: -3, mb: 0.5 }}>
                  <Button size="small" variant="outlined" onClick={() => navigator.clipboard.writeText(JSON.stringify(selectedStep.outputData, null, 2))}>
                    Копировать
                  </Button>
                </Stack>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: '#f5f7fa',
                    border: '1px solid rgba(198, 216, 240, 0.3)',
                    fontFamily: 'monospace',
                    fontSize: '0.82rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    overflow: 'auto',
                    maxHeight: 300,
                    color: '#1e293b',
                  }}
                >
                  {JSON.stringify(selectedStep.outputData, null, 2)}
                </Box>
              </Stack>
            </Paper>
          );
          })()}
        </Box>

      </Stack>
    </Container>
  );
};
