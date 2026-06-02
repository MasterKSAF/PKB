import React from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Collapse,
  IconButton,
  TextField,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Anchor,
  Ship,
  Waves,
  MessageSquare,
  Search,
  FileText,
  CheckCircle2,
  BarChart3,
  Video,
  History,
  Focus,
  Settings,
  ChevronDown,
  ChevronRight,
  Check,
  Edit3,
  Moon,
  Sun,
  Trash2,
  X,
} from 'lucide-react';
import { useUIStore, AppTab } from '../store/uiStore';
import { ROLE_TAB_ACCESS } from '../utils/access';
import { MOCK_CHAT_THREADS } from '../utils/mockData';

const NAV_ITEMS: Array<{ value: AppTab; label: string; icon: React.ReactNode }> = [
  { value: 'chat', label: 'Чат', icon: <MessageSquare size={18} /> },
  { value: 'search', label: 'Поиск', icon: <Search size={18} /> },
  { value: 'documents', label: 'База знаний', icon: <FileText size={18} /> },
  { value: 'checks', label: 'Проверка', icon: <CheckCircle2 size={18} /> },
  { value: 'history', label: 'История', icon: <History size={18} /> },
  { value: 'qa', label: 'QA', icon: <BarChart3 size={18} /> },
  { value: 'admin', label: 'Администрирование', icon: <Settings size={18} /> },
];

const CHAT_PROJECTS = [
  {
    id: 'project-223m',
    name: 'Проект 223-М',
    chats: [
      { id: 'chat-hull', title: 'Толщина листа корпуса' },
      { id: 'chat-materials', title: 'Материалы и ГОСТ' },
    ],
  },
  {
    id: 'project-arctic',
    name: 'Проект 22220',
    chats: [
      { id: 'chat-pumps', title: 'Насосные агрегаты' },
      { id: 'chat-cooling', title: 'Система охлаждения' },
    ],
  },
  {
    id: 'project-nsi',
    name: 'База НСИ',
    chats: [
      { id: 'chat-ocr', title: 'Проверка OCR' },
    ],
  },
];

export const ModeSwitcher: React.FC = () => {
  const {
    activeProjectId,
    activeTab,
    currentRole,
    themeMode,
    setActiveProjectId,
    setActiveTab,
    setChatMessages,
    setThemeMode,
    setVideoGuideOpen,
    setFocusMode,
  } = useUIStore();
  const isLight = themeMode === 'light';
  const lightShipBlue = '#0284c7';
  const availableTabs = ROLE_TAB_ACCESS[currentRole];
  const visibleNavItems = NAV_ITEMS.filter((item) => availableTabs.includes(item.value));
  const [chatTreeOpen, setChatTreeOpen] = React.useState(false);
  const [expandedProjects, setExpandedProjects] = React.useState<Record<string, boolean>>({});
  const [chatProjects, setChatProjects] = React.useState(CHAT_PROJECTS);
  const [activeThreadId, setActiveThreadId] = React.useState('chat-hull');
  const [editingThreadId, setEditingThreadId] = React.useState<string | null>(null);
  const [draftTitle, setDraftTitle] = React.useState('');
  const [deleteCandidate, setDeleteCandidate] = React.useState<{ projectId: string; chatId: string; title: string } | null>(null);

  const toggleProject = (projectId: string) => {
    setExpandedProjects((state) => ({ ...state, [projectId]: !state[projectId] }));
  };

  const handleNavClick = (tab: AppTab) => {
    if (tab === 'chat') {
      setActiveTab('chat');
      setChatTreeOpen((open) => !open);
      return;
    }

    setChatTreeOpen(false);
    setActiveTab(tab);
  };

  const selectThread = (projectId: string, chatId: string) => {
    setActiveProjectId(projectId);
    setActiveThreadId(chatId);
    setChatMessages(MOCK_CHAT_THREADS[chatId] ?? []);
    setActiveTab('chat');
  };

  const startRename = (chatId: string, title: string) => {
    setEditingThreadId(chatId);
    setDraftTitle(title);
  };

  const saveRename = () => {
    if (!editingThreadId || !draftTitle.trim()) {
      setEditingThreadId(null);
      return;
    }

    setChatProjects((projects) =>
      projects.map((project) => ({
        ...project,
        chats: project.chats.map((chat) =>
          chat.id === editingThreadId ? { ...chat, title: draftTitle.trim() } : chat,
        ),
      })),
    );
    setEditingThreadId(null);
  };

  const requestDeleteThread = (projectId: string, chatId: string, title: string) => {
    setDeleteCandidate({ projectId, chatId, title });
  };

  const confirmDeleteThread = () => {
    if (!deleteCandidate) return;

    setChatProjects((projects) =>
      projects.map((project) =>
        project.id === deleteCandidate.projectId
          ? {
              ...project,
              chats: project.chats.filter((chat) => chat.id !== deleteCandidate.chatId),
            }
          : project,
      ),
    );

    if (activeThreadId === deleteCandidate.chatId) {
      setActiveThreadId('');
      setChatMessages([]);
    }

    setDeleteCandidate(null);
  };

  return (
    <Box
      sx={{
        width: 292,
        flexShrink: 0,
        borderRight: isLight ? '2px solid rgba(14, 116, 144, 0.26)' : '2px solid rgba(198, 216, 240, 0.40)',
        bgcolor: isLight ? '#f8fafc' : 'rgba(16, 17, 21, 0.96)',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        p: 2,
        gap: 2.5,
        boxShadow: isLight
          ? '14px 0 36px rgba(15, 23, 42, 0.08), inset -1px 0 0 rgba(255,255,255,0.72)'
          : '16px 0 42px rgba(0,0,0,0.24), inset -1px 0 0 rgba(198, 216, 240, 0.18)',
      }}
    >
      <Box
        className="workspace-header-panel"
        sx={{
          p: 2.2,
          pb: 1.45,
          height: 89,
          flexShrink: 0,
          boxSizing: 'border-box',
          borderRadius: 3.2,
          border: isLight ? '1px solid rgba(14, 116, 144, 0.24)' : '1.5px solid rgba(198, 216, 240, 0.38)',
          background: isLight ? 'rgba(14, 116, 144, 0.12)' : 'rgba(152, 217, 216, 0.16)',
          boxShadow: isLight
            ? '0 16px 34px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255,255,255,0.58)'
            : '0 20px 42px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.08)',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            inset: 0,
            background: 'transparent',
            pointerEvents: 'none',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            left: 16,
            right: 16,
            bottom: 14,
            height: 1,
            background: 'transparent',
            pointerEvents: 'none',
          },
        }}
      >
        <Stack direction="row" spacing={1.6} sx={{ alignItems: 'center', position: 'relative', zIndex: 1 }}>
          <Box
            sx={{
              width: 58,
              height: 58,
              borderRadius: '18px',
              display: 'grid',
              placeItems: 'center',
              color: '#dfeeff',
              background: isLight
                ? 'linear-gradient(145deg, #f8fbff 0%, #e0f2fe 100%)'
                : 'linear-gradient(145deg, rgba(18, 67, 75, 0.95), rgba(11, 28, 34, 0.92) 74%, rgba(165, 140, 255, 0.20))',
              border: isLight ? '1px solid rgba(2, 132, 199, 0.26)' : '1px solid rgba(132, 210, 213, 0.22)',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: isLight
                ? 'inset 0 1px 0 rgba(255,255,255,0.86), 0 10px 22px rgba(2,132,199,0.12)'
                : 'inset 0 1px 0 rgba(255,255,255,0.12), 0 8px 22px rgba(0,0,0,0.24)',
            }}
          >
            {isLight ? (
              <Ship
                size={30}
                style={{
                  position: 'relative',
                  zIndex: 1,
                  color: lightShipBlue,
                  filter: 'drop-shadow(0 2px 5px rgba(2, 132, 199, 0.28))',
                }}
              />
            ) : (
              <>
                <Waves size={34} style={{ position: 'absolute', bottom: 6, opacity: 0.45, color: '#78c1c1' }} />
                <Anchor size={26} style={{ position: 'relative', zIndex: 1, color: '#98d9d8' }} />
              </>
            )}
          </Box>

          <Box sx={{ minWidth: 0, pt: 0.45 }}>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                px: 1.15,
                py: 0.55,
                borderRadius: 1.7,
                background: isLight
                  ? 'linear-gradient(145deg, rgba(248,251,255,0.92), rgba(224,242,254,0.78))'
                  : 'linear-gradient(145deg, rgba(7, 20, 24, 0.82), rgba(18, 32, 38, 0.72) 62%, rgba(35, 49, 56, 0.56) 100%)',
                border: isLight ? '1px solid rgba(2, 132, 199, 0.22)' : '1px solid rgba(157, 219, 217, 0.18)',
                boxShadow: isLight
                  ? 'inset 0 1px 0 rgba(255,255,255,0.82), 0 8px 16px rgba(2,132,199,0.08)'
                  : 'inset 0 1px 0 rgba(255,255,255,0.08), 0 10px 18px rgba(0,0,0,0.18)',
              }}
            >
              <Typography
                sx={{
                  fontSize: '1.24rem',
                  lineHeight: 1.04,
                  fontWeight: 700,
                  letterSpacing: '0.015em',
                  color: isLight ? lightShipBlue : '#98d9d8',
                  fontFamily: '"Trebuchet MS", "Segoe UI", sans-serif',
                }}
              >
                AI ассистент
              </Typography>
            </Box>

            <Typography
              variant="caption"
              sx={{
                display: 'block',
                mt: 0.8,
            color: isLight ? '#075985' : 'rgba(209, 225, 225, 0.72)',
                fontWeight: isLight ? 650 : 400,
                textAlign: 'center',
              }}
            >
              сверка с НСИ
            </Typography>
          </Box>
        </Stack>
      </Box>

      <Stack spacing={0.8}>
        <Typography
          variant="overline"
          sx={{
            display: 'block',
            mb: 0.1,
            color: isLight ? '#475569' : 'rgba(198, 208, 222, 0.84)',
            letterSpacing: '0.16em',
            fontSize: '0.68rem',
            fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
            textAlign: 'center',
          }}
        >
          Навигация
        </Typography>
      </Stack>

      <Stack spacing={1}>
        {visibleNavItems.map((item) => {
          const isActive = activeTab === item.value;

          return (
            <Box key={item.value}>
              <Button
                variant={isActive ? 'contained' : 'text'}
                color={isActive ? 'primary' : 'inherit'}
                startIcon={item.icon}
                onClick={() => handleNavClick(item.value)}
                sx={{
                  justifyContent: 'flex-start',
                  width: '100%',
                  px: 1.6,
                  py: 1.18,
                  borderRadius: 2.4,
                  color: isActive ? (isLight ? '#0f172a' : '#edf2ea') : 'text.primary',
                  bgcolor: isActive
                    ? isLight
                      ? '#e0f2fe'
                      : 'rgba(108, 124, 108, 0.22)'
                    : 'transparent',
                  border: '1px solid',
                  borderColor: isActive
                    ? isLight
                      ? '#7dd3fc'
                      : 'rgba(155, 169, 147, 0.34)'
                    : 'transparent',
                  '&:hover': {
                    bgcolor: isActive
                      ? isLight
                        ? '#bae6fd'
                        : 'rgba(108, 124, 108, 0.28)'
                      : isLight
                        ? '#f1f5f9'
                        : 'rgba(255,255,255,0.05)',
                  },
                }}
              >
                {item.label}
              </Button>

              {item.value === 'chat' && (
                <Collapse in={chatTreeOpen} timeout={220} unmountOnExit>
                  <Box
                    sx={{
                      mt: 0.8,
                      ml: 0.6,
                      pl: 1.1,
                      borderLeft: isLight ? '2px solid #bae6fd' : '2px solid rgba(198, 216, 240, 0.24)',
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        display: 'block',
                        mb: 0.6,
                        color: isLight ? '#64748b' : 'rgba(198,208,222,0.72)',
                        letterSpacing: '0.06em',
                      }}
                    >
                      Мои проекты
                    </Typography>
                    <Stack spacing={0.45}>
                      {chatProjects.map((project) => (
                        <Box key={project.id}>
                          <Button
                            fullWidth
                            size="small"
                            startIcon={
                              expandedProjects[project.id] ? <ChevronDown size={14} /> : <ChevronRight size={14} />
                            }
                            onClick={() => toggleProject(project.id)}
                            sx={{
                              justifyContent: 'flex-start',
                              px: 0.9,
                              py: 0.55,
                              minHeight: 30,
                              borderRadius: 1.6,
                              color: activeProjectId === project.id ? (isLight ? '#075985' : '#98d9d8') : 'text.secondary',
                              bgcolor:
                                activeProjectId === project.id
                                  ? isLight
                                    ? 'rgba(56, 189, 248, 0.12)'
                                    : 'rgba(152, 217, 216, 0.08)'
                                  : 'transparent',
                            }}
                          >
                            <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {project.name}
                            </Box>
                          </Button>
                          <Collapse in={Boolean(expandedProjects[project.id])} timeout={180} unmountOnExit>
                            <Stack spacing={0.25} sx={{ mt: 0.35, ml: 2 }}>
                              {project.chats.map((chat) => {
                                const isChatActive = activeThreadId === chat.id;
                                const isEditing = editingThreadId === chat.id;

                                return (
                                  <Box
                                    key={chat.id}
                                    sx={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: 0.35,
                                      borderRadius: 1.5,
                                      bgcolor: isChatActive
                                        ? isLight
                                          ? '#e0f2fe'
                                          : 'rgba(152, 217, 216, 0.10)'
                                        : 'transparent',
                                      border: '1px solid',
                                      borderColor: isChatActive
                                        ? isLight
                                          ? '#bae6fd'
                                          : 'rgba(152, 217, 216, 0.20)'
                                        : 'transparent',
                                    }}
                                  >
                                    {isEditing ? (
                                      <>
                                        <TextField
                                          size="small"
                                          variant="standard"
                                          value={draftTitle}
                                          autoFocus
                                          onChange={(event) => setDraftTitle(event.target.value)}
                                          onKeyDown={(event) => {
                                            if (event.key === 'Enter') saveRename();
                                            if (event.key === 'Escape') setEditingThreadId(null);
                                          }}
                                          slotProps={{
                                            input: {
                                              disableUnderline: true,
                                              sx: { fontSize: '0.72rem', px: 0.6, py: 0.3 },
                                            },
                                          }}
                                          sx={{ flex: 1, minWidth: 0 }}
                                        />
                                        <IconButton size="small" onClick={saveRename} sx={{ width: 24, height: 24 }}>
                                          <Check size={13} />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => setEditingThreadId(null)} sx={{ width: 24, height: 24 }}>
                                          <X size={13} />
                                        </IconButton>
                                      </>
                                    ) : (
                                      <>
                                        <Button
                                          size="small"
                                          onClick={() => selectThread(project.id, chat.id)}
                                          sx={{
                                            flex: 1,
                                            minWidth: 0,
                                            justifyContent: 'flex-start',
                                            px: 0.75,
                                            py: 0.42,
                                            minHeight: 28,
                                            fontSize: '0.72rem',
                                            color: isChatActive ? (isLight ? '#0f172a' : '#edf2ea') : 'text.secondary',
                                          }}
                                        >
                                          <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {chat.title}
                                          </Box>
                                        </Button>
                                        <Tooltip title="Переименовать чат">
                                          <IconButton
                                            size="small"
                                            onClick={() => startRename(chat.id, chat.title)}
                                            sx={{ width: 24, height: 24, color: 'text.secondary' }}
                                          >
                                            <Edit3 size={12} />
                                          </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Удалить чат">
                                          <IconButton
                                            size="small"
                                            onClick={() => requestDeleteThread(project.id, chat.id, chat.title)}
                                            sx={{ width: 24, height: 24, color: 'text.secondary' }}
                                          >
                                            <Trash2 size={12} />
                                          </IconButton>
                                        </Tooltip>
                                      </>
                                    )}
                                  </Box>
                                );
                              })}
                            </Stack>
                          </Collapse>
                        </Box>
                      ))}
                    </Stack>
                  </Box>
                </Collapse>
              )}
            </Box>
          );
        })}
      </Stack>

      <Box
        sx={{
          mt: 'auto',
          pt: 2,
          borderTop: isLight ? '1px solid rgba(15, 23, 42, 0.12)' : '1px solid rgba(157, 205, 225, 0.12)',
        }}
      >
        <Button
          variant="outlined"
          fullWidth
          startIcon={<Focus size={16} />}
          onClick={() => setFocusMode(true)}
          sx={{
            mb: 1.2,
            borderColor: isLight ? 'rgba(15, 23, 42, 0.18)' : 'rgba(124, 165, 214, 0.30)',
            color: isLight ? '#0f5f6f' : 'rgba(224, 234, 245, 0.88)',
          }}
        >
          Фокус-режим
        </Button>
        <Button
          variant="outlined"
          fullWidth
          startIcon={themeMode === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
          onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
          sx={{
            mb: 1.2,
            borderColor: isLight ? '#cbd5e1' : 'rgba(124, 165, 214, 0.30)',
            color: isLight ? '#075985' : 'rgba(224, 234, 245, 0.88)',
          }}
        >
          {themeMode === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
        </Button>
        <Button
          variant="outlined"
          fullWidth
          startIcon={<Video size={16} />}
          onClick={() => setVideoGuideOpen(true)}
          sx={{
            borderColor: isLight ? 'rgba(15, 23, 42, 0.18)' : 'rgba(124, 165, 214, 0.30)',
            color: isLight ? '#9f7440' : '#d9b173',
          }}
        >
          Видеоинструкция
        </Button>
      </Box>

      <Dialog
        open={Boolean(deleteCandidate)}
        onClose={() => setDeleteCandidate(null)}
        maxWidth="xs"
        fullWidth
        slotProps={{
          paper: {
            sx: {
              borderRadius: 3,
              border: isLight ? '1px solid rgba(14, 116, 144, 0.22)' : '1.5px solid rgba(198, 216, 240, 0.30)',
              bgcolor: isLight ? '#ffffff' : 'rgba(18, 20, 24, 0.98)',
              boxShadow: isLight
                ? '0 24px 70px rgba(15, 23, 42, 0.16)'
                : '0 28px 80px rgba(0,0,0,0.44)',
            },
          },
        }}
      >
        <DialogTitle sx={{ pb: 0.7, fontSize: '1.05rem', fontWeight: 700 }}>
          Удалить чат?
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.65 }}>
            Вы уверены, что хотите удалить чат «{deleteCandidate?.title}»?
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.4, pt: 0.6 }}>
          <Button variant="outlined" color="inherit" onClick={() => setDeleteCandidate(null)}>
            Отмена
          </Button>
          <Button variant="contained" color="error" startIcon={<Trash2 size={15} />} onClick={confirmDeleteThread}>
            Удалить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
