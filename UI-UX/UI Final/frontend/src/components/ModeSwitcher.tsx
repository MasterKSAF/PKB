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
  Menu,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  Ship,
  MessageSquare,
  Search,
  FileText,
  BarChart3,
  Video,
  History,
  Focus,
  Settings,
  ChevronDown,
  ChevronRight,
  Check,
  ClipboardList,
  Edit3,
  MoreVertical,
  Moon,
  Plus,
  ScanText,
  Sun,
  Trash2,
  X,
} from 'lucide-react';
import { useUIStore, AppTab, type KnowledgeProcessingSection } from '../store/uiStore';
import { getAccessibleTabs } from '../utils/access';
import { MOCK_CHAT_THREADS } from '../utils/mockData';
import { chatApi, clearGatewayTokens, projectsApi, type GatewayChatProject } from '../utils/http';

const NAV_ITEMS: Array<{ value: AppTab; label: string; icon: React.ReactNode }> = [
  { value: 'chat', label: 'Чат', icon: <MessageSquare size={18} /> },
  { value: 'search', label: 'Поиск', icon: <Search size={18} /> },
  { value: 'documents', label: 'База знаний', icon: <FileText size={18} /> },
  { value: 'knowledgeProcessing', label: 'Обработка базы знаний', icon: <ScanText size={18} /> },
  { value: 'history', label: 'История', icon: <History size={18} /> },
  { value: 'qa', label: 'QA', icon: <BarChart3 size={18} /> },
  { value: 'admin', label: 'Администрирование', icon: <Settings size={18} /> },
  { value: 'taskJournal', label: 'Журнал задач', icon: <ClipboardList size={18} /> },
];

const KNOWLEDGE_PROCESSING_SECTIONS: Array<{ value: KnowledgeProcessingSection; label: string; description: string }> = [
  { value: 'upload', label: 'Загрузка', description: 'файлы и очередь' },
  { value: 'drafts', label: 'Черновики', description: 'метаданные и решения' },
  { value: 'registry', label: 'Реестр', description: 'принятые документы' },
  { value: 'journal', label: 'Журналы', description: 'pipeline и мониторинг' },
];

const DEMO_CHAT_PROJECTS = [
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
      { id: 'chat-ocr', title: 'Контроль OCR' },
    ],
  },
];

const getGatewayErrorMessage = (error: unknown) => {
  const payload = (error as any)?.response?.data;
  const message = payload?.detail ?? payload?.message ?? payload?.error ?? (error as any)?.message;

  return typeof message === 'string' ? message : JSON.stringify(message ?? payload ?? error);
};

export const ModeSwitcher: React.FC = () => {
  const {
    activeProjectId,
    activeThreadId,
    activeKnowledgeProcessingSection,
    activeTab,
    adminUsers,
    currentRole,
    currentUserId,
    themeMode,
    chatTreeOpen,
    chatProjectsRefreshKey,
    setActiveProjectId,
    setActiveThreadId,
    setActiveKnowledgeProcessingSection,
    setActiveTab,
    setChatMessages,
    setChatTreeOpen,
    setThemeMode,
    setVideoGuideOpen,
    setFocusMode,
    workMode,
    setCurrentGatewaySessionId,
  } = useUIStore();
  const isLight = themeMode === 'light';
  const lightShipBlue = '#0284c7';
  const currentUser = adminUsers.find((user) => user.id === currentUserId) ?? null;
  const availableTabs = React.useMemo(
    () => getAccessibleTabs(currentRole, currentUser?.availableTabs, workMode, currentUser?.permissions),
    [currentRole, currentUser?.availableTabs, currentUser?.permissions, workMode],
  );
  const visibleNavItems = NAV_ITEMS.filter((item) =>
    item.value === 'taskJournal' ? availableTabs.includes('admin') : availableTabs.includes(item.value),
  );
  // chatTreeOpen в сторе (uiStore) — управляется из Chat.tsx
  const [knowledgeProcessingTreeOpen, setKnowledgeProcessingTreeOpen] = React.useState(false);
  const [expandedProjects, setExpandedProjects] = React.useState<Record<string, boolean>>({});
  const [chatProjects, setChatProjects] = React.useState<GatewayChatProject[]>(() =>
    workMode === 'prod' ? [] : DEMO_CHAT_PROJECTS,
  );
  // activeThreadId теперь в сторе (uiStore), доступен из Chat.tsx для подсветки дерева
  const [editingThreadId, setEditingThreadId] = React.useState<string | null>(null);
  const [draftTitle, setDraftTitle] = React.useState('');
  const [deleteCandidate, setDeleteCandidate] = React.useState<{ projectId: string; chatId: string; title: string } | null>(null);
  const [editingProjectId, setEditingProjectId] = React.useState<string | null>(null);
  const [projectDraftName, setProjectDraftName] = React.useState('');
  const [deleteProjectCandidate, setDeleteProjectCandidate] = React.useState<{
    projectId: string;
    name: string;
    chatsCount: number;
  } | null>(null);
  const [projectMenuAnchor, setProjectMenuAnchor] = React.useState<HTMLElement | null>(null);
  const [projectMenuTarget, setProjectMenuTarget] = React.useState<{ projectId: string; name: string; chatsCount: number } | null>(
    null,
  );
  const [chatMenuAnchor, setChatMenuAnchor] = React.useState<HTMLElement | null>(null);
  const [chatMenuTarget, setChatMenuTarget] = React.useState<{ projectId: string; chatId: string; title: string } | null>(
    null,
  );
  const [gatewayNavigationError, setGatewayNavigationError] = React.useState('');
  React.useEffect(() => {
    if (workMode !== 'prod') {
      clearGatewayTokens();
      setGatewayNavigationError('');
      setChatProjects(DEMO_CHAT_PROJECTS);
      setActiveThreadId('chat-hull');
      setChatMessages(MOCK_CHAT_THREADS['chat-hull'] ?? []);
      return;
    }

    let isMounted = true;
    const activeProjectIdSnapshot = useUIStore.getState().activeProjectId;
    setChatMessages([]);
    setActiveThreadId('');
    setCurrentGatewaySessionId(null);
    setChatProjects([]);

    void projectsApi
      .list()
      .then((projects) => {
        if (!isMounted) return;
        const nextProjects = projects.length ? projects : [];
        setChatProjects(nextProjects);
        setGatewayNavigationError('');

        if (!nextProjects.some((project) => project.id === activeProjectIdSnapshot) && nextProjects[0]?.id) {
          setActiveProjectId(nextProjects[0].id);
        }
      })
      .catch((error) => {
        if (!isMounted) return;
        setChatProjects([]);
        setGatewayNavigationError(`Не удалось загрузить проекты из Gateway: ${getGatewayErrorMessage(error)}`);
      });

    return () => {
      isMounted = false;
    };
  }, [setActiveProjectId, setChatMessages, setCurrentGatewaySessionId, workMode]);

  // Перезагружать проекты при триггере из Chat.tsx (создание/выбор чата)
  React.useEffect(() => {
    if (workMode !== 'prod') return;

    let isMounted = true;
    projectsApi
      .list()
      .then((projects) => {
        if (!isMounted) return;
        setChatProjects(projects.length ? projects : []);
        setGatewayNavigationError('');
      })
      .catch((error) => {
        if (!isMounted) return;
        setGatewayNavigationError(`Не удалось загрузить проекты: ${getGatewayErrorMessage(error)}`);
      });

    return () => {
      isMounted = false;
    };
  }, [chatProjectsRefreshKey, workMode]);

  // Раскрывать проект в дереве при установке activeProjectId (из Chat.tsx или дерева)
  React.useEffect(() => {
    if (activeProjectId) {
      setExpandedProjects((prev) => ({ ...prev, [activeProjectId]: true }));
    }
  }, [activeProjectId]);

  const toggleProject = (projectId: string) => {
    setExpandedProjects((state) => ({ ...state, [projectId]: !state[projectId] }));
  };

  const createProject = async () => {
    const newProjectNumber = chatProjects.filter((project) => project.name.startsWith('Новый проект')).length + 1;
    const projectId = `project-${Date.now()}`;
    const name = `Новый проект ${newProjectNumber}`;

    setGatewayNavigationError('');
    setChatTreeOpen(true);
    setActiveTab('chat');

    if (workMode === 'prod') {
      try {
        const createdProject = await projectsApi.create(name);

        setChatProjects((projects) => [{ ...createdProject, chats: [] }, ...projects]);
        setExpandedProjects((state) => ({ ...state, [createdProject.id]: true }));
        setActiveProjectId(createdProject.id);
        setActiveThreadId('');
        setCurrentGatewaySessionId(null);
        setChatMessages([]);
        setEditingProjectId(createdProject.id);
        setProjectDraftName(createdProject.name);
      } catch (error) {
        setGatewayNavigationError(`Не удалось создать проект: ${getGatewayErrorMessage(error)}`);
      }
      return;
    }

    setChatProjects((projects) => [{ id: projectId, name, chats: [] }, ...projects]);
    setExpandedProjects((state) => ({ ...state, [projectId]: true }));
    setActiveProjectId(projectId);
    setActiveThreadId('');
    setCurrentGatewaySessionId(null);
    setChatMessages([]);
    setEditingProjectId(projectId);
    setProjectDraftName(name);
  };

  const handleNavClick = (tab: AppTab) => {
    if (tab === 'chat') {
      setActiveTab('chat');
      setChatTreeOpen(!chatTreeOpen);
      setKnowledgeProcessingTreeOpen(false);
      return;
    }

    if (tab === 'knowledgeProcessing') {
      setActiveTab('knowledgeProcessing');
      setKnowledgeProcessingTreeOpen(true);
      setChatTreeOpen(false);
      return;
    }

    setChatTreeOpen(false);
    setKnowledgeProcessingTreeOpen(true);
    setActiveTab(tab);
  };

  const selectKnowledgeProcessingSection = (section: KnowledgeProcessingSection) => {
    setActiveTab('knowledgeProcessing');
    setActiveKnowledgeProcessingSection(section);
    setKnowledgeProcessingTreeOpen(true);
    setChatTreeOpen(false);
  };

  const selectThread = async (projectId: string, chatId: string) => {
    setActiveProjectId(projectId);
    setActiveThreadId(chatId);
    setActiveTab('chat');

    if (workMode === 'prod') {
      setChatMessages([]);
      try {
        const session = await chatApi.getSession(chatId);
        setCurrentGatewaySessionId(chatId);
        setChatMessages(session.messages);
        setGatewayNavigationError('');
      } catch (error) {
        setCurrentGatewaySessionId(null);
        setActiveThreadId('');
        setChatMessages([]);
        setGatewayNavigationError(`Не удалось загрузить чат: ${getGatewayErrorMessage(error)}`);
      }
      return;
    }

    setCurrentGatewaySessionId(chatId);
    setChatMessages(MOCK_CHAT_THREADS[chatId] ?? []);
  };

  const createThread = async (projectId: string) => {
    const project = chatProjects.find((item) => item.id === projectId);
    const newThreadNumber = (project?.chats.filter((chat) => chat.title.startsWith('Новый чат')).length ?? 0) + 1;
    const chatId = `chat-${projectId}-${Date.now()}`;
    const title = `Новый чат ${newThreadNumber}`;

    setGatewayNavigationError('');
    setExpandedProjects((state) => ({ ...state, [projectId]: true }));
    setActiveProjectId(projectId);
    setActiveTab('chat');

    if (workMode === 'prod') {
      try {
        const created = await chatApi.createSession(title, projectId);
        const gatewayChatId = created.session_id ?? created.id ?? created.session?.session_id;
        const gatewayTitle = created.title ?? title;

        if (!gatewayChatId) throw new Error('Gateway did not return session_id for created chat.');

        setChatProjects((projects) =>
          projects.map((item) =>
            item.id === projectId
              ? {
                  ...item,
                  chats: [{ id: gatewayChatId, title: gatewayTitle }, ...item.chats],
                }
              : item,
          ),
        );
        setActiveThreadId(gatewayChatId);
        setCurrentGatewaySessionId(gatewayChatId);
        setChatMessages([]);
        setEditingThreadId(gatewayChatId);
        setDraftTitle(gatewayTitle);
      } catch (error) {
        setGatewayNavigationError(`Не удалось создать чат: ${getGatewayErrorMessage(error)}`);
      }
      return;
    }

    setChatProjects((projects) =>
      projects.map((item) =>
        item.id === projectId
          ? {
              ...item,
              chats: [{ id: chatId, title }, ...item.chats],
            }
          : item,
        ),
    );
    setActiveThreadId(chatId);
    setCurrentGatewaySessionId(chatId);
    setChatMessages([]);
    setEditingThreadId(chatId);
    setDraftTitle(title);
  };

  const startRename = (chatId: string, title: string) => {
    setEditingThreadId(chatId);
    setDraftTitle(title);
  };

  const startRenameProject = (projectId: string, name: string) => {
    setEditingProjectId(projectId);
    setProjectDraftName(name);
  };

  const saveProjectRename = async () => {
    if (!editingProjectId || !projectDraftName.trim()) {
      setEditingProjectId(null);
      return;
    }

    const projectId = editingProjectId;
    const name = projectDraftName.trim();

    setGatewayNavigationError('');

    if (workMode === 'prod') {
      try {
        const updatedProject = await projectsApi.update(projectId, { name });

        setChatProjects((projects) =>
          projects.map((project) =>
            project.id === projectId
              ? { ...project, ...updatedProject, chats: project.chats, name: updatedProject.name ?? name }
              : project,
          ),
        );
        setEditingProjectId(null);
      } catch (error) {
        setGatewayNavigationError(`Не удалось переименовать проект: ${getGatewayErrorMessage(error)}`);
      }
      return;
    }

    setChatProjects((projects) =>
      projects.map((project) =>
        project.id === projectId ? { ...project, name } : project,
      ),
    );
    setEditingProjectId(null);
  };

  const saveRename = async () => {
    if (!editingThreadId || !draftTitle.trim()) {
      setEditingThreadId(null);
      return;
    }

    const sessionId = editingThreadId;
    const title = draftTitle.trim();

    setGatewayNavigationError('');

    if (workMode === 'prod') {
      try {
        await chatApi.updateSession(sessionId, { title });

        setChatProjects((projects) =>
          projects.map((project) => ({
            ...project,
            chats: project.chats.map((chat) =>
              chat.id === sessionId ? { ...chat, title } : chat,
            ),
          })),
        );
        setEditingThreadId(null);
      } catch (error) {
        setGatewayNavigationError(`Не удалось переименовать чат: ${getGatewayErrorMessage(error)}`);
      }
      return;
    }

    setChatProjects((projects) =>
      projects.map((project) => ({
        ...project,
        chats: project.chats.map((chat) =>
          chat.id === sessionId ? { ...chat, title } : chat,
        ),
      })),
    );
    setEditingThreadId(null);
  };

  const requestDeleteThread = (projectId: string, chatId: string, title: string) => {
    setDeleteCandidate({ projectId, chatId, title });
  };

  const openChatMenu = (event: React.MouseEvent<HTMLElement>, projectId: string, chatId: string, title: string) => {
    event.stopPropagation();
    setChatMenuAnchor(event.currentTarget);
    setChatMenuTarget({ projectId, chatId, title });
  };

  const closeChatMenu = () => {
    setChatMenuAnchor(null);
    setChatMenuTarget(null);
  };

  const handleChatMenuRename = () => {
    if (!chatMenuTarget) return;
    startRename(chatMenuTarget.chatId, chatMenuTarget.title);
    closeChatMenu();
  };

  const handleChatMenuDelete = () => {
    if (!chatMenuTarget) return;
    requestDeleteThread(chatMenuTarget.projectId, chatMenuTarget.chatId, chatMenuTarget.title);
    closeChatMenu();
  };

  const requestDeleteProject = (projectId: string, name: string, chatsCount: number) => {
    setDeleteProjectCandidate({ projectId, name, chatsCount });
  };

  const openProjectMenu = (
    event: React.MouseEvent<HTMLElement>,
    projectId: string,
    name: string,
    chatsCount: number,
  ) => {
    event.stopPropagation();
    setProjectMenuAnchor(event.currentTarget);
    setProjectMenuTarget({ projectId, name, chatsCount });
  };

  const closeProjectMenu = () => {
    setProjectMenuAnchor(null);
    setProjectMenuTarget(null);
  };

  const handleProjectMenuRename = () => {
    if (!projectMenuTarget) return;
    startRenameProject(projectMenuTarget.projectId, projectMenuTarget.name);
    closeProjectMenu();
  };

  const handleProjectMenuDelete = () => {
    if (!projectMenuTarget) return;
    requestDeleteProject(projectMenuTarget.projectId, projectMenuTarget.name, projectMenuTarget.chatsCount);
    closeProjectMenu();
  };

  const confirmDeleteThread = async () => {
    if (!deleteCandidate) return;
    const candidate = deleteCandidate;

    setGatewayNavigationError('');

    if (workMode === 'prod') {
      try {
        await chatApi.deleteSession(candidate.chatId);
      } catch (error) {
        setGatewayNavigationError(`Не удалось удалить чат: ${getGatewayErrorMessage(error)}`);
        return;
      }
    }

    setChatProjects((projects) =>
      projects.map((project) =>
        project.id === candidate.projectId
          ? {
              ...project,
              chats: project.chats.filter((chat) => chat.id !== candidate.chatId),
            }
          : project,
      ),
    );

    if (activeThreadId === candidate.chatId) {
      setActiveThreadId('');
      setCurrentGatewaySessionId(null);
      setChatMessages([]);
    }

    setDeleteCandidate(null);
  };

  const confirmDeleteProject = async () => {
    if (!deleteProjectCandidate) return;
    const candidate = deleteProjectCandidate;

    const remainingProjects = chatProjects.filter((project) => project.id !== candidate.projectId);
    const deletedProject = chatProjects.find((project) => project.id === candidate.projectId);
    const shouldResetThread = deletedProject?.chats.some((chat) => chat.id === activeThreadId);

    setGatewayNavigationError('');

    if (workMode === 'prod') {
      try {
        await projectsApi.delete(candidate.projectId);
      } catch (error) {
        setGatewayNavigationError(`Не удалось удалить проект: ${getGatewayErrorMessage(error)}`);
        return;
      }
    }

    setChatProjects(remainingProjects);
    setExpandedProjects((state) => {
      const nextState = { ...state };
      delete nextState[candidate.projectId];
      return nextState;
    });

    if (activeProjectId === candidate.projectId) {
      setActiveProjectId(remainingProjects[0]?.id ?? '');
    }

    if (shouldResetThread || activeProjectId === candidate.projectId) {
      setActiveThreadId('');
      setCurrentGatewaySessionId(null);
      setChatMessages([]);
    }

    setDeleteProjectCandidate(null);
  };

  return (
    <Box
      className="app-navigation-panel"
      sx={{
        width: 316,
        minWidth: 316,
        flexBasis: 316,
        flexShrink: 0,
        borderRight: isLight ? '2px solid rgba(14, 116, 144, 0.26)' : '2px solid rgba(152, 217, 216, 0.52)',
        bgcolor: isLight ? '#f8fafc' : '#2a2f30',
        background: isLight
          ? '#f8fafc'
          : 'linear-gradient(180deg, #303637 0%, #292f30 46%, #222829 100%)',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        overflowX: 'hidden',
        scrollbarGutter: 'stable',
        boxSizing: 'border-box',
        p: 2,
        gap: 2.5,
        boxShadow: isLight
          ? '14px 0 36px rgba(15, 23, 42, 0.08), inset -1px 0 0 rgba(255,255,255,0.72)'
          : '30px 0 72px rgba(0,0,0,0.58), inset -1px 0 0 rgba(152, 217, 216, 0.34), inset 1px 0 0 rgba(255,255,255,0.07), inset 0 0 0 1px rgba(255,255,255,0.025)',
      }}
    >
      <Box
        className="workspace-header-panel"
        sx={{
          p: 1.75,
          pb: 1.35,
          height: 89,
          minHeight: 89,
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
        <Stack
          direction="row"
          spacing={1.35}
          sx={{ alignItems: 'center', position: 'relative', zIndex: 1, minWidth: 0, flexWrap: 'nowrap' }}
        >
          <Box
            sx={{
              width: 54,
              height: 54,
              minWidth: 54,
              flexShrink: 0,
              borderRadius: '17px',
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
            <Ship
              size={30}
              style={{
                position: 'relative',
                zIndex: 1,
                color: isLight ? lightShipBlue : '#98d9d8',
                filter: isLight ? 'drop-shadow(0 2px 5px rgba(2, 132, 199, 0.28))' : 'none',
              }}
            />
          </Box>

          <Box
            sx={{
              minWidth: 0,
              maxWidth: 'calc(100% - 70px)',
              flex: '0 1 auto',
              height: 54,
              overflow: 'hidden',
              display: 'inline-flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                maxWidth: '100%',
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
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                AI ассистент
              </Typography>
            </Box>

            <Typography
              variant="overline"
              sx={{
                display: 'block',
                color: isLight ? '#475569' : 'rgba(198, 208, 222, 0.84)',
                letterSpacing: '0.16em',
                fontSize: '0.68rem',
                lineHeight: 1,
                fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                textAlign: 'center',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              СВЕРКА С НСИ
            </Typography>
          </Box>
        </Stack>
      </Box>

      {gatewayNavigationError && workMode === 'prod' && (
        <Alert severity="error" variant="outlined" onClose={() => setGatewayNavigationError('')}>
          {gatewayNavigationError}
        </Alert>
      )}

      <Stack spacing={0.8}>
        <Typography
          variant="overline"
          sx={{
            display: 'block',
            mb: 0.1,
            color: isLight ? '#475569' : 'rgba(198, 208, 222, 0.84)',
            letterSpacing: '0.16em',
            fontSize: '0.68rem',
            lineHeight: 1,
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
                    <Stack
                      direction="row"
                      sx={{
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: 1,
                        mb: 0.6,
                      }}
                    >
                      <Typography
                        variant="caption"
                        sx={{
                          display: 'block',
                          color: isLight ? '#64748b' : 'rgba(198,208,222,0.72)',
                          letterSpacing: '0.06em',
                        }}
                      >
                        Мои проекты
                      </Typography>
                      <Tooltip title="Создать новый проект">
                        <Button
                          size="small"
                          startIcon={<Plus size={12} />}
                          onClick={() => void createProject()}
                          sx={{
                            width: 74,
                            minHeight: 24,
                            px: 0.75,
                            py: 0.15,
                            borderRadius: 1.4,
                            fontSize: '0.68rem',
                            color: isLight ? '#075985' : '#98d9d8',
                            border: '1px solid',
                            borderColor: isLight ? 'rgba(14, 116, 144, 0.24)' : 'rgba(152, 217, 216, 0.22)',
                            bgcolor: isLight ? 'rgba(224, 242, 254, 0.64)' : 'rgba(152, 217, 216, 0.06)',
                          }}
                        >
                          Проект
                        </Button>
                      </Tooltip>
                    </Stack>
                    <Stack spacing={0.6}>
                      {chatProjects.map((project) => {
                        const isProjectActive = activeProjectId === project.id;
                        const isProjectEditing = editingProjectId === project.id;

                        return (
                          <Box key={project.id}>
                            <Box
                              sx={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 0.25,
                                borderRadius: 1.8,
                                border: '1px solid',
                                borderColor: isProjectActive
                                  ? isLight
                                    ? '#bae6fd'
                                    : 'rgba(152, 217, 216, 0.22)'
                                  : isLight
                                    ? 'rgba(148, 163, 184, 0.16)'
                                    : 'rgba(198, 216, 240, 0.10)',
                                bgcolor: isProjectActive
                                  ? isLight
                                    ? 'rgba(56, 189, 248, 0.12)'
                                    : 'rgba(152, 217, 216, 0.08)'
                                  : isLight
                                    ? 'rgba(248, 250, 252, 0.58)'
                                    : 'rgba(255,255,255,0.018)',
                              }}
                            >
                              {isProjectEditing ? (
                                <>
                                  <TextField
                                    size="small"
                                    variant="standard"
                                    value={projectDraftName}
                                    autoFocus
                                    onChange={(event) => setProjectDraftName(event.target.value)}
                                    onKeyDown={(event) => {
                                      if (event.key === 'Enter') void saveProjectRename();
                                      if (event.key === 'Escape') setEditingProjectId(null);
                                    }}
                                    slotProps={{
                                      input: {
                                        disableUnderline: true,
                                        sx: {
                                          fontSize: '0.78rem',
                                          px: 0.8,
                                          py: 0.35,
                                          color: isLight ? '#075985' : '#98d9d8',
                                          fontWeight: 650,
                                        },
                                      },
                                    }}
                                    sx={{ flex: 1, minWidth: 0 }}
                                  />
                                  <IconButton size="small" onClick={() => void saveProjectRename()} sx={{ width: 25, height: 25 }}>
                                    <Check size={13} />
                                  </IconButton>
                                  <IconButton
                                    size="small"
                                    onClick={() => setEditingProjectId(null)}
                                    sx={{ width: 25, height: 25 }}
                                  >
                                    <X size={13} />
                                  </IconButton>
                                </>
                              ) : (
                                <>
                                  <Button
                                    size="small"
                                    startIcon={
                                      expandedProjects[project.id] ? <ChevronDown size={14} /> : <ChevronRight size={14} />
                                    }
                                    onClick={() => toggleProject(project.id)}
                                    sx={{
                                      flex: 1,
                                      minWidth: 0,
                                      justifyContent: 'flex-start',
                                      px: 0.75,
                                      py: 0.5,
                                      minHeight: 30,
                                      borderRadius: 1.6,
                                      color: isProjectActive ? (isLight ? '#075985' : '#98d9d8') : 'text.secondary',
                                      fontWeight: isProjectActive ? 650 : 500,
                                    }}
                                  >
                                    <Box
                                      component="span"
                                      sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                    >
                                      {project.name}
                                    </Box>
                                  </Button>
                                  <Tooltip title="Действия с проектом">
                                    <IconButton
                                      size="small"
                                      onClick={(event) => openProjectMenu(event, project.id, project.name, project.chats.length)}
                                      sx={{
                                        width: 25,
                                        height: 25,
                                        mr: 0.25,
                                        color: isProjectActive ? (isLight ? '#075985' : '#98d9d8') : 'text.secondary',
                                      }}
                                    >
                                      <MoreVertical size={13} />
                                    </IconButton>
                                  </Tooltip>
                                </>
                              )}
                          </Box>
                          <Collapse in={Boolean(expandedProjects[project.id])} timeout={180} unmountOnExit>
                            <Stack
                              spacing={0.3}
                              sx={{
                                mt: 0.4,
                                ml: 2.2,
                                pl: 0.9,
                                borderLeft: isLight ? '1px solid rgba(14, 116, 144, 0.18)' : '1px solid rgba(152, 217, 216, 0.14)',
                              }}
                            >
                              <Stack
                                direction="row"
                                sx={{
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  gap: 0.6,
                                  px: 0.35,
                                  py: 0.15,
                                }}
                              >
                                <Typography
                                  variant="caption"
                                  sx={{
                                    color: isLight ? '#64748b' : 'rgba(198,208,222,0.66)',
                                    fontSize: '0.66rem',
                                    letterSpacing: '0.04em',
                                  }}
                                >
                                  Чаты
                                </Typography>
                                <Tooltip title="Создать новый чат в проекте">
                                  <Button
                                    size="small"
                                    startIcon={<Plus size={12} />}
                                    onClick={() => createThread(project.id)}
                                    sx={{
                                      width: 74,
                                      minHeight: 24,
                                      px: 0.75,
                                      py: 0.15,
                                      borderRadius: 1.4,
                                      fontSize: '0.68rem',
                                      color: isLight ? '#075985' : '#98d9d8',
                                      border: '1px solid',
                                      borderColor: isLight ? 'rgba(14, 116, 144, 0.24)' : 'rgba(152, 217, 216, 0.22)',
                                      bgcolor: isLight ? 'rgba(224, 242, 254, 0.64)' : 'rgba(152, 217, 216, 0.06)',
                                    }}
                                  >
                                    Чат
                                  </Button>
                                </Tooltip>
                              </Stack>
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
                                        <Tooltip title="Действия с чатом">
                                          <IconButton
                                            size="small"
                                            onClick={(event) => openChatMenu(event, project.id, chat.id, chat.title)}
                                            sx={{
                                              width: 24,
                                              height: 24,
                                              color: isChatActive ? (isLight ? '#075985' : '#98d9d8') : 'text.secondary',
                                            }}
                                          >
                                            <MoreVertical size={12} />
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
                        );
                      })}
                    </Stack>
                  </Box>
                </Collapse>
              )}

              {item.value === 'knowledgeProcessing' && (
                <Collapse in={knowledgeProcessingTreeOpen} timeout={220} unmountOnExit>
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
                      Рабочие зоны
                    </Typography>
                    <Stack spacing={0.35}>
                      {KNOWLEDGE_PROCESSING_SECTIONS.map((section) => {
                        const isSectionActive =
                          activeTab === 'knowledgeProcessing' && activeKnowledgeProcessingSection === section.value;

                        return (
                          <Button
                            key={section.value}
                            size="small"
                            onClick={() => selectKnowledgeProcessingSection(section.value)}
                            sx={{
                              justifyContent: 'flex-start',
                              minHeight: 34,
                              px: 0.75,
                              py: 0.42,
                              borderRadius: 1.5,
                              textTransform: 'none',
                              color: isSectionActive ? (isLight ? '#0f172a' : '#edf2ea') : 'text.secondary',
                              bgcolor: isSectionActive
                                ? isLight
                                  ? '#e0f2fe'
                                  : 'rgba(152, 217, 216, 0.10)'
                                : 'transparent',
                              border: '1px solid',
                              borderColor: isSectionActive
                                ? isLight
                                  ? '#bae6fd'
                                  : 'rgba(152, 217, 216, 0.20)'
                                : 'transparent',
                              '&:hover': {
                                bgcolor: isLight ? 'rgba(224, 242, 254, 0.68)' : 'rgba(152, 217, 216, 0.08)',
                              },
                            }}
                          >
                            <Box sx={{ minWidth: 0, textAlign: 'left' }}>
                              <Typography
                                component="span"
                                sx={{
                                  display: 'block',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                  fontSize: '0.74rem',
                                  fontWeight: isSectionActive ? 650 : 520,
                                }}
                              >
                                {section.label}
                              </Typography>
                              <Typography
                                component="span"
                                sx={{
                                  display: 'block',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                  fontSize: '0.64rem',
                                  color: isLight ? 'rgba(71, 85, 105, 0.82)' : 'rgba(198,208,222,0.64)',
                                }}
                              >
                                {section.description}
                              </Typography>
                            </Box>
                          </Button>
                        );
                      })}
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

      <Menu
        anchorEl={projectMenuAnchor}
        open={Boolean(projectMenuAnchor)}
        onClose={closeProjectMenu}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{
          paper: {
            sx: {
              minWidth: 178,
              borderRadius: 2,
              border: isLight ? '1px solid rgba(14, 116, 144, 0.18)' : '1px solid rgba(198, 216, 240, 0.20)',
              bgcolor: isLight ? '#ffffff' : 'rgba(18, 20, 24, 0.98)',
              boxShadow: isLight
                ? '0 18px 40px rgba(15, 23, 42, 0.14)'
                : '0 20px 48px rgba(0,0,0,0.42)',
            },
          },
        }}
      >
        <MenuItem onClick={handleProjectMenuRename} sx={{ gap: 1.1, fontSize: '0.86rem' }}>
          <Edit3 size={15} />
          Редактировать проект
        </MenuItem>
        <MenuItem
          className="app-danger-menu-item"
          onClick={handleProjectMenuDelete}
          sx={{ gap: 1.1, fontSize: '0.86rem', color: isLight ? '#991b1b' : '#ee8f80' }}
        >
          <Trash2 size={15} />
          Удалить проект
        </MenuItem>
      </Menu>

      <Menu
        anchorEl={chatMenuAnchor}
        open={Boolean(chatMenuAnchor)}
        onClose={closeChatMenu}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{
          paper: {
            sx: {
              minWidth: 160,
              borderRadius: 2,
              border: isLight ? '1px solid rgba(14, 116, 144, 0.18)' : '1px solid rgba(198, 216, 240, 0.20)',
              bgcolor: isLight ? '#ffffff' : 'rgba(18, 20, 24, 0.98)',
              boxShadow: isLight
                ? '0 18px 40px rgba(15, 23, 42, 0.14)'
                : '0 20px 48px rgba(0,0,0,0.42)',
            },
          },
        }}
      >
        <MenuItem onClick={handleChatMenuRename} sx={{ gap: 1.1, fontSize: '0.86rem' }}>
          <Edit3 size={15} />
          Редактировать чат
        </MenuItem>
        <MenuItem
          className="app-danger-menu-item"
          onClick={handleChatMenuDelete}
          sx={{ gap: 1.1, fontSize: '0.86rem', color: isLight ? '#991b1b' : '#ee8f80' }}
        >
          <Trash2 size={15} />
          Удалить чат
        </MenuItem>
      </Menu>

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

      <Dialog
        open={Boolean(deleteProjectCandidate)}
        onClose={() => setDeleteProjectCandidate(null)}
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
          Удалить проект?
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.65 }}>
            Вы уверены, что хотите удалить проект «{deleteProjectCandidate?.name}»?
            {deleteProjectCandidate?.chatsCount
              ? ` Вместе с проектом будет удалено чатов: ${deleteProjectCandidate.chatsCount}.`
              : ' В проекте пока нет чатов.'}
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.4, pt: 0.6 }}>
          <Button variant="outlined" color="inherit" onClick={() => setDeleteProjectCandidate(null)}>
            Отмена
          </Button>
          <Button variant="contained" color="error" startIcon={<Trash2 size={15} />} onClick={() => void confirmDeleteProject()}>
            Удалить проект
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
