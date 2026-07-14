import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Container,
  TextField,
  IconButton,
  Typography,
  Paper,
  Avatar,
  Chip,
  Button,
  CircularProgress,
  LinearProgress,
  Collapse,
  Alert,
  Stack,
  Dialog,
  Slider,
  Tooltip,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Send,
  User,
  Ship,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ExternalLink,
  Bookmark,
  HelpCircle,
  MessageSquare,
  ShieldCheck,
  X,
  FileText,
  Search,
  Download,
  Maximize2,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { chatApi, projectsApi, sourceApi, type GatewayChatProject } from '../utils/http';
import { ChatMessage, Citation } from '../utils/mockData';
import { Feedback } from './Feedback';
import { useUIStore } from '../store/uiStore';
import { downloadPreviewFile } from '../utils/downloadPreview';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  getCitationDisplayIndex,
  parseInlineCitationMarkers,
  resolveCitationMarker,
} from '../utils/citations';

type ChatStatus = NonNullable<ChatMessage['status']>;

const statusLabel: Record<string, string> = {
  pending: 'ожидание',
  enriching: 'обогащение запроса',
  generating: 'генерация ответа',
  searching: 'поиск источников',
  analyzing: 'обращение к LLM',
  enriching_citations: 'обогащение цитат',
  answered: 'ответ найден',
  failed: 'ошибка',
  not_found: 'не найдено',
  out_of_scope: 'вне области знаний',
  needs_clarification: 'требуется уточнение',
  source_conflict: 'конфликт источников',
} as const;

const statusTone: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
  pending: 'warning',
  enriching: 'warning',
  searching: 'warning',
  generating: 'warning',
  analyzing: 'warning',
  enriching_citations: 'info',
  answered: 'success',
  failed: 'error',
  not_found: 'warning',
  out_of_scope: 'warning',
  needs_clarification: 'warning',
  source_conflict: 'warning',
};

type ChatPreview = Citation & {
  previewId: string;
  previewKind: 'source' | 'document';
  /** Исходный фрагмент цитирования — сохраняем отдельно от full_text страницы */
  originalFragment?: string;
  /** Ошибка загрузки (404, таймаут и т.д.) */
  previewError?: string;
};

function getGatewayErrorMessage(error: unknown) {
  const payload = (error as any)?.response?.data;
  const message = payload?.detail ?? payload?.message ?? payload?.error ?? (error as any)?.message;

  if (typeof message === 'string') return message;
  return JSON.stringify(message ?? payload ?? 'Неизвестная ошибка Gateway');
}

function getAnswerPoints(content: string) {
  const normalizedContent = stripLegacyCitationMarkers(content);
  const lines = normalizedContent
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  const numbered = lines
    .filter((line) => /^\d+[.)]\s+/.test(line))
    .map((line) => line.replace(/^\d+[.)]\s+/, ''));

  return numbered.length > 0 ? numbered : [normalizedContent];
}

function stripLegacyCitationMarkers(text: string) {
  return text.replace(/\s*%\[[^\]]*\]%/g, '');
}

function hasInlineCitationMarkers(content: string, citations: Citation[] = []) {
  return citations.length > 0 && parseInlineCitationMarkers(content).length > 0;
}

function mapCitationsToPoints(points: string[], citations: Citation[] = []) {
  return points.map((_, index) => {
    const citation = citations[index];
    return citation ? [citation] : [];
  });
}

function buildAnsweredView(content: string, citations: Citation[] = [], useSequentialMapping = false) {
  if (citations.length === 0 || hasInlineCitationMarkers(content, citations) || !useSequentialMapping) {
    return null;
  }

  const points = getAnswerPoints(content);
  const supportedCount = Math.min(points.length, citations.length);
  const supported = points.slice(0, supportedCount).map((text, index) => ({
    text,
    citation: citations[index],
  }));

  return {
    supported,
  };
}

function sourceButtonSx(isLight: boolean, fontSize = '0.74rem') {
  return {
    px: 0.9,
    py: 0.28,
    minWidth: 0,
    height: 'auto',
    fontSize,
    color: isLight ? '#075985' : '#b8c4d8',
    border: isLight ? '1px solid #7dd3fc' : '1px solid rgba(184,196,216,0.20)',
    borderRadius: 999,
    bgcolor: isLight ? '#e0f2fe' : 'rgba(184,196,216,0.06)',
    '&:hover': {
      bgcolor: isLight ? '#bae6fd' : 'rgba(184,196,216,0.10)',
      borderColor: isLight ? '#38bdf8' : 'rgba(184,196,216,0.28)',
    },
  } as const;
}

/** Подсветить originalFragment (если есть) внутри полного текста */
function highlightFragmentInText(
  fullText: string,
  fragment: string | undefined,
  isLight: boolean,
): React.ReactNode[] {
  if (!fragment || !fullText) return [fullText];

  const cleanFragment = fragment.trim();
  if (!cleanFragment) return [fullText];

  const parts: React.ReactNode[] = [];
  let cursor = 0;
  let index = fullText.indexOf(cleanFragment);
  let key = 0;

  while (index !== -1) {
    if (index > cursor) {
      parts.push(fullText.slice(cursor, index));
    }
    parts.push(
      <Box
        key={`fragment-${key}`}
        component="mark"
        sx={{
          px: 0.35,
          py: 0.05,
          borderRadius: 0.7,
          bgcolor: isLight ? 'rgba(56, 189, 248, 0.45)' : 'rgba(56, 189, 248, 0.40)',
          color: 'inherit',
          boxShadow: isLight
            ? '0 0 0 1px rgba(2, 132, 199, 0.30)'
            : '0 0 0 1px rgba(56, 189, 248, 0.30)',
        }}
      >
        {fullText.slice(index, index + cleanFragment.length)}
      </Box>,
    );
    cursor = index + cleanFragment.length;
    index = fullText.indexOf(cleanFragment, cursor);
    key++;
  }

  if (cursor < fullText.length) {
    parts.push(fullText.slice(cursor));
  }

  return parts.length ? parts : [fullText];
}

function countMatches(text: string, query: string) {
  if (!query) return 0;

  let count = 0;
  let position = text.toLowerCase().indexOf(query);

  while (position !== -1) {
    count += 1;
    position = text.toLowerCase().indexOf(query, position + query.length);
  }

  return count;
}

function highlightText(text: string, query: string, isLight: boolean, activeOccurrence = -1) {
  if (!query) return text;

  const lowerText = text.toLowerCase();
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  let position = lowerText.indexOf(query);
  let index = 0;

  while (position !== -1) {
    if (position > cursor) {
      parts.push(text.slice(cursor, position));
    }

    const isActive = index === activeOccurrence;

    parts.push(
      <Box
        component="mark"
        key={`${position}-${index}`}
        sx={{
          px: 0.35,
          py: 0.05,
          borderRadius: 0.7,
          color: isLight ? '#111827' : '#f8fbff',
          bgcolor: isActive
            ? isLight
              ? 'rgba(14, 165, 233, 0.34)'
              : 'rgba(56, 189, 248, 0.38)'
            : isLight
              ? 'rgba(202, 138, 4, 0.28)'
              : 'rgba(216, 176, 122, 0.36)',
          boxShadow: isLight
            ? '0 0 0 1px rgba(146, 64, 14, 0.16)'
            : '0 0 0 1px rgba(216, 176, 122, 0.22)',
        }}
      >
        {text.slice(position, position + query.length)}
      </Box>,
    );

    cursor = position + query.length;
    position = lowerText.indexOf(query, cursor);
    index += 1;
  }

  if (cursor < text.length) {
    parts.push(text.slice(cursor));
  }

  return parts;
}

function renderInlineCitationText(
  content: string,
  citations: Citation[] = [],
  openCitation: (citation: Citation, previewKind: ChatPreview['previewKind']) => void,
  query: string,
  isLight: boolean,
  useSequentialNumbers = false,
) {
  const cleanContent = stripLegacyCitationMarkers(content);
  const markers = parseInlineCitationMarkers(cleanContent);
  const nodes: React.ReactNode[] = [];
  let cursor = 0;

  markers.forEach((marker) => {
    const markerStart = marker.start;
    const markerEnd = marker.end;
    const before = cleanContent.slice(cursor, markerStart);

    if (before) {
      nodes.push(...React.Children.toArray(highlightText(before, query, isLight)));
    }

    const citation = resolveCitationMarker(marker, citations, useSequentialNumbers);

    if (citation) {
      const displayIndex = getCitationDisplayIndex(citation, citations);
      nodes.push(
        <Button
          key={`inline-source-${displayIndex}-${markerStart}`}
          size="small"
          variant="text"
          className="source-link-button"
          title={`${citation.document} · ${citation.section}`}
          sx={{
            ...sourceButtonSx(isLight, '0.72rem'),
            display: 'inline-flex',
            mx: 0.25,
            px: 0.7,
            py: 0.08,
            minHeight: 0,
            height: 21,
            verticalAlign: 'baseline',
          }}
          onClick={() => openCitation(citation, 'source')}
        >
          [{displayIndex}]
        </Button>,
      );
    } else {
      nodes.push(marker.raw);
    }

    cursor = markerEnd;
  });

  if (cursor < cleanContent.length) {
    nodes.push(...React.Children.toArray(highlightText(cleanContent.slice(cursor), query, isLight)));
  }

  return nodes.length ? nodes : highlightText(cleanContent, query, isLight);
}

export const Chat: React.FC = () => {
  const {
    appendChatMessages,
    chatMessages,
    currentGatewaySessionId,
    themeMode,
    workMode,
    activeProjectId,
    chatTreeOpen,
    setActiveProjectId,
    setActiveThreadId,
    setActiveTab,
    setChatMessages,
    setChatTreeOpen,
    triggerChatProjectsRefresh,
    setCurrentGatewaySessionId,
  } = useUIStore();
  const isLight = themeMode === 'light';
  const assistantAccent = isLight ? '#0284c7' : '#98d9d8';
  const messages = chatMessages;
  const [input, setInput] = useState('');
  const [chatSearch, setChatSearch] = useState('');
  const [previewSearch, setPreviewSearch] = useState('');
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});
  const [openedCitations, setOpenedCitations] = useState<ChatPreview[]>([]);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);
  const [previewWidth, setPreviewWidth] = useState(420);
  const [previewZoom, setPreviewZoom] = useState(1);
  const [expandedPreviewOpen, setExpandedPreviewOpen] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [downloadAnchorEl, setDownloadAnchorEl] = useState<HTMLElement | null>(null);
  const [activeSearchMatch, setActiveSearchMatch] = useState(0);
  const [activePreviewSearchMatch, setActivePreviewSearchMatch] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const activeCitation = openedCitations.find((citation) => citation.previewId === activeCitationId) ?? openedCitations[0];
  const normalizedChatSearch = chatSearch.trim().toLowerCase();
  const normalizedPreviewSearch = previewSearch.trim().toLowerCase();
  const previewSearchMatches = activeCitation ? countMatches(activeCitation.text, normalizedPreviewSearch) : 0;
  const searchMatches = useMemo(
    () =>
      normalizedChatSearch
        ? messages.flatMap((message) =>
            Array.from({ length: countMatches(message.content, normalizedChatSearch) }, (_, occurrence) => ({
              messageId: message.id,
              occurrence,
            })),
          )
        : [],
    [messages, normalizedChatSearch],
  );
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    setActiveSearchMatch(0);
  }, [normalizedChatSearch]);

  useEffect(() => {
    setActivePreviewSearchMatch(0);
  }, [activeCitation?.previewId, normalizedPreviewSearch]);

  useEffect(() => {
    if (!normalizedChatSearch || searchMatches.length === 0) return;

    const targetMessageId = searchMatches[activeSearchMatch]?.messageId;
    const target = targetMessageId ? messageRefs.current[targetMessageId] : null;

    target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [activeSearchMatch, normalizedChatSearch, searchMatches]);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (event: MouseEvent) => {
      const nextWidth = window.innerWidth - event.clientX - 24;
      setPreviewWidth(Math.min(720, Math.max(320, nextWidth)));
    };

    const handleMouseUp = () => setIsResizing(false);

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const [chatStatus, setChatStatus] = useState<string | null>(null);
  const [chatStatusMessage, setChatStatusMessage] = useState<string | null>(null);
  const [chatProgress, setChatProgress] = useState<number>(0);
  const chatMutation = useMutation({
    mutationFn: (q: string) => chatApi.send(q, (status, message, progress) => { setChatStatus(status); setChatStatusMessage(message ?? null); if (typeof progress === 'number') setChatProgress(progress); }),
    onSuccess: (data) => {
      appendChatMessages([data]);
      setExpandedCitations((prev) => ({ ...prev, [data.id]: false }));
      setChatStatus(null);
      setChatStatusMessage(null);
      setChatProgress(0);
    },
    onError: () => { setChatStatus(null); setChatStatusMessage(null); setChatProgress(0); },
  });
  const [guardActionLoading, setGuardActionLoading] = useState(false);
  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
    enabled: workMode === 'prod' && !currentGatewaySessionId,
    staleTime: 30_000,
  });
  const mustSelectGatewayChat = workMode === 'prod' && !currentGatewaySessionId;

  /** Взять последний проект (по updatedAt) или создать новый, если нет проектов */
  const resolveLastProject = useCallback(async (): Promise<GatewayChatProject> => {
    let projects = projectsQuery.data ?? [];
    if (projects.length === 0) {
      const created = await projectsApi.create('Новый проект');
      projects = [created];
    }
    // Сортируем по updatedAt (новые в конце), чтобы взять действительно последний
    const sorted = [...projects].sort((a, b) => {
      const aTime = a.chats?.[0]?.updatedAt ? new Date(a.chats[0].updatedAt).getTime() : 0;
      const bTime = b.chats?.[0]?.updatedAt ? new Date(b.chats[0].updatedAt).getTime() : 0;
      return aTime - bTime;
    });
    return sorted[sorted.length - 1] ?? projects[0];
  }, [projectsQuery.data]);

  const handleCreateChat = useCallback(async () => {
    if (projectsQuery.isLoading) return;
    setGuardActionLoading(true);
    try {
      const lastProject = await resolveLastProject();
      setActiveProjectId(lastProject.id);
      setActiveTab('chat');
      setChatTreeOpen(true);

      const session = await chatApi.createSession('Новый чат', lastProject.id);
      const gatewayChatId = String(session.session_id ?? session.id);
      setCurrentGatewaySessionId(gatewayChatId);
      setActiveThreadId(gatewayChatId);
      setChatMessages([]);
      triggerChatProjectsRefresh();
    } catch (error) {
      console.error('Failed to create chat:', error);
    } finally {
      setGuardActionLoading(false);
    }
  }, [resolveLastProject, projectsQuery.isLoading, setActiveProjectId, setActiveThreadId, setActiveTab, setChatTreeOpen, setChatMessages, setCurrentGatewaySessionId, triggerChatProjectsRefresh]);

  const handleLastChat = useCallback(async () => {
    if (projectsQuery.isLoading) return;
    setGuardActionLoading(true);
    try {
      const lastProject = await resolveLastProject();
      setActiveProjectId(lastProject.id);
      setActiveTab('chat');
      setChatTreeOpen(true);

      // Последний чат в проекте (по порядку в массиве chats)
      const lastChat = lastProject.chats?.[lastProject.chats.length - 1];
      if (lastChat) {
        const session = await chatApi.getSession(lastChat.id);
        setCurrentGatewaySessionId(lastChat.id);
        setActiveThreadId(lastChat.id);
        setChatMessages(session.messages);
      } else {
        const session = await chatApi.createSession('Новый чат', lastProject.id);
        const gatewayChatId = String(session.session_id ?? session.id);
        setCurrentGatewaySessionId(gatewayChatId);
        setActiveThreadId(gatewayChatId);
        setChatMessages([]);
      }
      triggerChatProjectsRefresh();
    } catch (error) {
      console.error('Failed to open last chat:', error);
    } finally {
      setGuardActionLoading(false);
    }
  }, [resolveLastProject, projectsQuery.isLoading, setActiveProjectId, setActiveThreadId, setActiveTab, setChatTreeOpen, setChatMessages, setCurrentGatewaySessionId, triggerChatProjectsRefresh]);

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return;
    if (mustSelectGatewayChat) {
      chatMutation.reset();
      return;
    }

    chatMutation.reset();

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    appendChatMessages([userMessage]);
    chatMutation.mutate(input);
    setInput('');
  };

  const goToSearchMatch = (direction: 'prev' | 'next') => {
    if (searchMatches.length === 0) return;

    setActiveSearchMatch((current) =>
      direction === 'next'
        ? (current + 1) % searchMatches.length
        : (current - 1 + searchMatches.length) % searchMatches.length,
    );
  };

  const goToPreviewSearchMatch = (direction: 'prev' | 'next') => {
    if (previewSearchMatches === 0) return;

    setActivePreviewSearchMatch((current) =>
      direction === 'next'
        ? (current + 1) % previewSearchMatches
        : (current - 1 + previewSearchMatches) % previewSearchMatches,
    );
  };

  const toggleCitations = (msgId: string) => {
    setExpandedCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const openPreview = (citation: Citation, previewKind: ChatPreview['previewKind']) => {
    const previewId = `${previewKind}-${citation.id}`;
    const originalFragment = citation.text;
    const preview: ChatPreview = {
      ...citation,
      page: previewKind === 'document' ? 1 : citation.page,
      previewId,
      previewKind,
      originalFragment,
    };

    setOpenedCitations((prev) => {
      if (prev.some((item) => item.previewId === previewId)) return prev;
      return [...prev, preview];
    });
    setActiveCitationId(previewId);

    void sourceApi
      .preview(citation, previewKind)
      .then((hydratedCitation) => {
        setOpenedCitations((prev) =>
          prev.map((item) =>
            item.previewId === previewId
              ? {
                  ...item,
                  ...hydratedCitation,
                  page: previewKind === 'document' ? 1 : hydratedCitation.page,
                  previewId,
                  previewKind,
                  originalFragment,
                }
              : item,
          ),
        );
      })
      .catch(() => undefined);
  };

  const closePreview = (previewId: string) => {
    setOpenedCitations((prev) => {
      const next = prev.filter((item) => item.previewId !== previewId);
      if (activeCitationId === previewId) {
        setActiveCitationId(next[0]?.previewId ?? null);
      }
      return next;
    });
  };

  return (
    <Box sx={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <Box sx={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flexGrow: 1, overflowY: 'auto', py: 3 }}>
          <Container maxWidth="md">
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.2 }}>
              {messages.map((msg) => {
                const isAssistant = msg.role === 'assistant';
                const useDemoCitationMapping = workMode === 'demo';
                const answerPoints = isAssistant && msg.status === 'answered' ? getAnswerPoints(msg.content) : [];
                const hasInlineCitations =
                  isAssistant && msg.status === 'answered' && hasInlineCitationMarkers(msg.content, msg.citations);
                const answeredView =
                  isAssistant && msg.status === 'answered'
                    ? buildAnsweredView(msg.content, msg.citations, useDemoCitationMapping)
                    : null;

                return (
                  <Box
                    key={msg.id}
                    ref={(node: HTMLDivElement | null) => {
                      messageRefs.current[msg.id] = node;
                    }}
                    sx={{
                      display: 'flex',
                      gap: 1.5,
                      alignItems: 'flex-start',
                      justifyContent: isAssistant ? 'flex-start' : 'flex-end',
                      borderRadius: 3,
                    }}
                  >
                    {isAssistant && (
                      <Avatar
                        sx={{
                          bgcolor: isLight ? '#e0f2fe' : 'rgba(152, 217, 216, 0.16)',
                          color: assistantAccent,
                          width: 34,
                          height: 34,
                          mt: 0.55,
                          border: '1px solid',
                          borderColor: isLight ? 'rgba(2, 132, 199, 0.36)' : 'rgba(152, 217, 216, 0.26)',
                          boxShadow: isLight
                            ? 'inset 0 1px 0 rgba(255,255,255,0.70), 0 2px 7px rgba(2,132,199,0.13)'
                            : 'inset 0 1px 0 rgba(255,255,255,0.08), 0 6px 14px rgba(0,0,0,0.16)',
                        }}
                      >
                        <Ship size={18} />
                      </Avatar>
                    )}

                    <Box sx={{ maxWidth: '84%', minWidth: 0 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          borderRadius: '18px',
                          bgcolor: isLight
                            ? isAssistant
                              ? '#ffffff'
                              : '#f3f7f8'
                            : isAssistant
                              ? 'rgba(255,255,255,0.045)'
                              : 'rgba(255,255,255,0.075)',
                          border: isLight ? '1px solid' : '1.5px solid',
                          borderColor: isLight
                            ? isAssistant
                              ? 'rgba(15,23,42,0.14)'
                              : 'rgba(15,95,111,0.20)'
                            : isAssistant
                              ? 'rgba(198, 216, 240, 0.30)'
                              : 'rgba(198, 216, 240, 0.30)',
                          boxShadow: isLight ? 'none' : 'inset 0 1px 0 rgba(255,255,255,0.035)',
                        }}
                      >
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            mb: 1.15,
                            pb: 1.15,
                            borderBottom: isLight ? '1px solid rgba(15,23,42,0.14)' : '1.5px solid rgba(198, 216, 240, 0.26)',
                          }}
                        >
                          <Typography
                            variant="caption"
                            sx={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              px: 0.8,
                              py: 0.22,
                              borderRadius: 999,
                              border: '1px solid',
                              borderColor: isAssistant
                                ? isLight
                                  ? 'rgba(2, 132, 199, 0.36)'
                                  : 'rgba(152, 217, 216, 0.24)'
                                : isLight
                                  ? 'rgba(159, 116, 64, 0.34)'
                                  : 'rgba(216, 176, 122, 0.24)',
                              bgcolor: isAssistant
                                ? isLight
                                  ? '#e0f2fe'
                                  : 'rgba(152, 217, 216, 0.07)'
                                : isLight
                                  ? '#fff6e8'
                                  : 'rgba(216,176,122,0.07)',
                              boxShadow: isLight
                                ? 'inset 0 1px 0 rgba(255,255,255,0.70), 0 1px 2px rgba(15,23,42,0.06)'
                                : 'inset 0 1px 0 rgba(255,255,255,0.06)',
                              fontWeight: 600,
                              letterSpacing: '0.04em',
                              color: isAssistant ? assistantAccent : isLight ? '#8a5f2b' : '#d8b07a',
                              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                              fontSize: '0.79rem',
                            }}
                          >
                            {isAssistant ? 'Ассистент' : 'Запрос инженера'}
                          </Typography>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{
                              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                              fontSize: '0.79rem',
                            }}
                          >
                            {msg.timestamp}
                          </Typography>
                          {isAssistant && msg.status && (
                            <Chip
                              size="small"
                              label={statusLabel[msg.status]}
                              color={statusTone[msg.status]}
                              variant="outlined"
                              sx={{ height: 22, ml: 'auto' }}
                            />
                          )}
                        </Box>

                        {hasInlineCitations ? (
                          <Typography
                            component="div"
                            variant="body1"
                            sx={{
                              lineHeight: 1.75,
                              whiteSpace: 'pre-wrap',
                              fontWeight: 400,
                              color: 'text.primary',
                              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                              fontSize: '0.95rem',
                              mt: 0.85,
                            }}
                          >
                            {renderInlineCitationText(
                              msg.content,
                              msg.citations,
                              openPreview,
                              normalizedChatSearch,
                              isLight,
                              useDemoCitationMapping,
                            )}
                          </Typography>
                        ) : answeredView ? (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.45, mt: 0.85 }}>
                            {answeredView.supported.map((item, index) => (
                              <Box key={`${msg.id}-supported-${index}`} sx={{ display: 'flex', gap: 1.1, alignItems: 'flex-start' }}>
                                <Typography
                                  variant="body2"
                                  sx={{
                                    minWidth: 20,
                                    fontWeight: 400,
                                    color: 'text.primary',
                                    pt: 0.15,
                                    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                                    fontSize: '0.95rem',
                                  }}
                                >
                                  {index + 1}.
                                </Typography>
                                <Box sx={{ flex: 1 }}>
                                  <Typography
                                    variant="body2"
                                    sx={{
                                      lineHeight: 1.7,
                                      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                                      fontSize: '0.95rem',
                                    }}
                                  >
                                    {highlightText(item.text, normalizedChatSearch, isLight)}
                                  </Typography>
                                  <Stack direction="row" spacing={1.4} useFlexGap sx={{ flexWrap: 'wrap', mt: 0.6 }}>
                                    <Tooltip
                                      title={
                                        <Box sx={{ maxWidth: 320 }}>
                                          <Typography variant="caption" sx={{ fontWeight: 700, display: 'block' }}>
                                            {item.citation.document}
                                          </Typography>
                                          <Typography variant="caption" sx={{ display: 'block', mt: 0.25, opacity: 0.85 }}>
                                            {item.citation.section}
                                          </Typography>
                                          {item.citation.text && (
                                            <Typography
                                              variant="caption"
                                              sx={{
                                                display: 'block',
                                                mt: 0.5,
                                                p: 0.75,
                                                borderRadius: 0.6,
                                                bgcolor: 'rgba(255,255,255,0.08)',
                                                lineHeight: 1.4,
                                                maxHeight: 120,
                                                overflow: 'hidden',
                                              }}
                                            >
                                              {item.citation.text.length > 250
                                                ? item.citation.text.slice(0, 250) + '…'
                                                : item.citation.text}
                                            </Typography>
                                          )}
                                        </Box>
                                      }
                                      placement="top"
                                      arrow
                                    >
                                      <Button
                                        size="small"
                                        variant="text"
                                        startIcon={<ExternalLink size={14} />}
                                        className="source-link-button"
                                        sx={sourceButtonSx(isLight)}
                                        onClick={() => openPreview(item.citation, 'source')}
                                      >
                                        Страница
                                      </Button>
                                    </Tooltip>
                                    <Tooltip
                                      title={
                                        <Box sx={{ maxWidth: 300 }}>
                                          <Typography variant="caption" sx={{ fontWeight: 700, display: 'block' }}>
                                            {item.citation.document}
                                          </Typography>
                                          <Typography variant="caption" sx={{ display: 'block', mt: 0.25, opacity: 0.85 }}>
                                            {item.citation.section}
                                          </Typography>
                                        </Box>
                                      }
                                      placement="top"
                                      arrow
                                    >
                                      <Button
                                        size="small"
                                        variant="text"
                                        startIcon={<FileText size={14} />}
                                        className="source-link-button"
                                        sx={sourceButtonSx(isLight)}
                                        onClick={() => openPreview(item.citation, 'document')}
                                      >
                                        Документ
                                      </Button>
                                    </Tooltip>
                                  </Stack>
                                </Box>
                              </Box>
                            ))}
                          </Box>
                        ) : msg.status === 'failed' ? (
                          <Alert severity="error" variant="outlined" sx={{ mt: 1.4 }}>
                            {highlightText(msg.content, normalizedChatSearch, isLight)}
                          </Alert>
                        ) : (
                          <Typography
                            variant="body1"
                            sx={{
                              lineHeight: 1.75,
                              whiteSpace: 'pre-wrap',
                              fontWeight: 400,
                              color: isAssistant ? 'text.primary' : isLight ? '#111827' : '#f4fbff',
                              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                              fontSize: '0.95rem',
                              mt: 0.85,
                            }}
                          >
                            {highlightText(msg.content, normalizedChatSearch, isLight)}
                          </Typography>
                        )}

                        {msg.limitation && (
                          <Alert severity="warning" variant="outlined" sx={{ mt: 2 }}>
                            {msg.limitation}
                          </Alert>
                        )}

                        {answerPoints.length === 0 && msg.citations && msg.citations.length > 0 && (
                          <Box sx={{ mt: 2 }}>
                            <Button
                              size="small"
                              variant="outlined"
                              color="inherit"
                              onClick={() => toggleCitations(msg.id)}
                              endIcon={expandedCitations[msg.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                              sx={{ borderColor: 'rgba(198, 216, 240, 0.30)', borderWidth: 1.5 }}
                            >
                              Страницы ({msg.citations.length})
                            </Button>

                            <Collapse in={expandedCitations[msg.id]}>
                              <Box component="ol" sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1.2, pl: 2.4 }}>
                                {msg.citations.map((cite) => (
                                  <Box component="li" key={cite.id} sx={{ pl: 0.5 }}>
                                    <Paper
                                    variant="outlined"
                                    sx={{
                                      p: 1.5,
                                      bgcolor: 'rgba(0,0,0,0.16)',
                                      borderColor: 'rgba(198, 216, 240, 0.28)',
                                      borderWidth: 1.5,
                                    }}
                                  >
                                    <Typography variant="caption" sx={{ fontWeight: 700, color: 'primary.light', display: 'block' }}>
                                      {cite.document} · {cite.version}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                      {cite.section} · стр. {cite.page}
                                    </Typography>

                                    <Stack direction="row" spacing={1.5} useFlexGap sx={{ flexWrap: 'wrap' }}>
                                      <Tooltip
                                        title={
                                          <Box sx={{ maxWidth: 300 }}>
                                            <Typography variant="caption" sx={{ fontWeight: 700, display: 'block' }}>
                                              {cite.document}
                                            </Typography>
                                            <Typography variant="caption" sx={{ display: 'block', mt: 0.25 }}>
                                              {cite.section}
                                            </Typography>
                                          </Box>
                                        }
                                        placement="top"
                                        arrow
                                      >
                                        <Button
                                          size="small"
                                          variant="text"
                                          startIcon={<ExternalLink size={14} />}
                                          className="source-link-button"
                                          sx={sourceButtonSx(isLight, '0.76rem')}
                                          onClick={() => openPreview(cite, 'source')}
                                        >
                                          Страница
                                        </Button>
                                      </Tooltip>
                                      <Tooltip
                                        title={`${cite.document} · ${cite.section}`}
                                        placement="top"
                                        arrow
                                      >
                                        <Button
                                          size="small"
                                          variant="text"
                                          startIcon={<FileText size={14} />}
                                          className="source-link-button"
                                          sx={sourceButtonSx(isLight, '0.76rem')}
                                          onClick={() => openPreview(cite, 'document')}
                                        >
                                          Документ
                                        </Button>
                                      </Tooltip>
                                    </Stack>
                                    </Paper>
                                  </Box>
                                ))}
                              </Box>
                            </Collapse>
                          </Box>
                        )}
                      </Paper>

                      {false && isAssistant && msg.id === messages[messages.length - 1].id && (
                        <Box sx={{ mt: 1.4 }}>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1.5 }}>
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<HelpCircle size={14} />}
                              onClick={() => setInput('Уточняю: проект 21900M2, конструкция корпуса, актуальная версия НСИ.')}
                            >
                              Уточнить запрос
                            </Button>
                            <Button size="small" variant="outlined" startIcon={<Bookmark size={14} />}>
                              Сохранить в историю
                            </Button>
                            <Button size="small" variant="outlined" startIcon={<ShieldCheck size={14} />}>
                              На ручную проверку
                            </Button>
                          </Box>
                          <Feedback messageId={msg.id} sessionId={currentGatewaySessionId ?? undefined} />
                        </Box>
                      )}

                      {isAssistant && msg.id === messages[messages.length - 1].id && (
                        <Box sx={{ mt: 1.4 }}>
                          <Feedback messageId={msg.id} sessionId={currentGatewaySessionId ?? undefined} />
                        </Box>
                      )}
                    </Box>

                    {!isAssistant && (
                      <Avatar
                        sx={{
                          bgcolor: isLight ? '#fff6e8' : 'rgba(216,176,122,0.16)',
                          color: isLight ? '#8a5f2b' : '#d8b07a',
                          width: 34,
                          height: 34,
                          mt: 0.55,
                          border: '1px solid',
                          borderColor: isLight ? 'rgba(159, 116, 64, 0.34)' : 'rgba(216, 176, 122, 0.26)',
                          boxShadow: isLight
                            ? 'inset 0 1px 0 rgba(255,255,255,0.70), 0 1px 2px rgba(15,23,42,0.08)'
                            : 'inset 0 1px 0 rgba(255,255,255,0.08), 0 6px 14px rgba(0,0,0,0.16)',
                        }}
                      >
                        <User size={20} />
                      </Avatar>
                    )}
                  </Box>
                );
              })}

              {chatMutation.isPending && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
                    <Avatar
                      sx={{
                        bgcolor: isLight ? '#e0f2fe' : 'rgba(152, 217, 216, 0.16)',
                        color: assistantAccent,
                        width: 34,
                        height: 34,
                        border: isLight ? '1px solid rgba(2, 132, 199, 0.36)' : 'none',
                      }}
                    >
                      <Ship size={18} />
                    </Avatar>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.3 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                        {chatStatus ? (statusLabel as Record<string, string>)[chatStatus] ?? chatStatus : 'Подготовка ответа...'}
                      </Typography>
                      {chatStatusMessage && (
                        <Typography variant="caption" color="text.secondary" sx={{ opacity: 0.7 }}>
                          {chatStatusMessage}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={chatProgress}
                    sx={{
                      borderRadius: 1,
                      height: 3,
                      bgcolor: isLight ? 'rgba(2, 132, 199, 0.12)' : 'rgba(152, 217, 216, 0.12)',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: assistantAccent,
                        transition: 'transform .4s linear',
                      },
                    }}
                  />
                </Box>
              )}
              {mustSelectGatewayChat && !guardActionLoading && (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2.5, py: 6 }}>
                  <Typography variant="h6" color="text.secondary" sx={{ mb: 0.5 }}>
                    Выберите или создайте чат
                  </Typography>
                  <Stack direction="row" spacing={1.5}>
                    <Button
                      variant="contained"
                      startIcon={<HelpCircle size={16} />}
                      onClick={handleCreateChat}
                      disableElevation
                      sx={{
                        px: 2,
                        py: 1.2,
                        borderRadius: 2.4,
                        fontSize: '0.88rem',
                        fontWeight: 500,
                        textTransform: 'none',
                        color: isLight ? '#0f172a' : '#edf2ea',
                        bgcolor: isLight ? '#e0f2fe' : 'rgba(108, 124, 108, 0.22)',
                        border: '1px solid',
                        borderColor: isLight ? '#7dd3fc' : 'rgba(155, 169, 147, 0.34)',
                        '&:hover': {
                          bgcolor: isLight ? '#bae6fd' : 'rgba(108, 124, 108, 0.28)',
                        },
                      }}
                    >
                      Создать чат
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<MessageSquare size={16} />}
                      onClick={handleLastChat}
                      sx={{
                        px: 2,
                        py: 1.2,
                        borderRadius: 2.4,
                        fontSize: '0.88rem',
                        fontWeight: 500,
                        textTransform: 'none',
                        color: isLight ? '#075985' : '#b8c4d8',
                        borderColor: isLight ? 'rgba(14, 116, 144, 0.24)' : 'rgba(152, 217, 216, 0.22)',
                        bgcolor: isLight ? 'rgba(224, 242, 254, 0.64)' : 'rgba(152, 217, 216, 0.06)',
                        '&:hover': {
                          bgcolor: isLight ? '#e0f2fe' : 'rgba(152, 217, 216, 0.16)',
                          borderColor: isLight ? 'rgba(14, 116, 144, 0.50)' : 'rgba(152, 217, 216, 0.50)',
                        },
                      }}
                    >
                      Последний чат
                    </Button>
                  </Stack>
                </Box>
              )}
              {guardActionLoading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress size={24} />
                </Box>
              )}
              {chatMutation.isError && !mustSelectGatewayChat && (
                <Alert severity="error" variant="outlined" sx={{ borderRadius: 2.2 }}>
                  {getGatewayErrorMessage(chatMutation.error)}
                </Alert>
              )}
              <div ref={messagesEndRef} />
            </Box>
          </Container>
        </Box>

        <Box
          sx={{
            borderTop: '1.5px solid rgba(198, 216, 240, 0.22)',
            pb: 2.4,
            pt: 1.8,
            bgcolor: 'transparent',
          }}
        >
          <Container maxWidth="lg">
            <Stack direction={{ xs: 'column', lg: 'row' }} spacing={1.1} sx={{ alignItems: 'stretch' }}>
              <Paper
                elevation={0}
                sx={{
                  p: '10px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  minHeight: 58,
                  flex: { lg: 1.65 },
                  borderRadius: 3,
                  border: isLight ? '1px solid rgba(15,23,42,0.18)' : '1.5px solid rgba(198, 216, 240, 0.34)',
                  bgcolor: isLight ? 'rgba(255,255,255,0.78)' : 'rgba(22, 23, 27, 0.72)',
                  boxShadow: isLight ? '0 6px 18px rgba(15,23,42,0.05)' : 'inset 0 1px 0 rgba(255,255,255,0.045)',
                }}
              >
                <TextField
                  fullWidth
                  multiline
                  minRows={1}
                  maxRows={4}
                  placeholder={mustSelectGatewayChat ? 'Создайте или выберите чат через меню' : 'Задайте вопрос ассистенту'}
                  variant="standard"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  sx={{ ml: 0.6, flex: 1 }}
                  slotProps={{
                    input: {
                      disableUnderline: true,
                      sx: {
                        alignItems: 'center',
                        fontSize: '0.96rem',
                        lineHeight: 1.55,
                      },
                    },
                  }}
                />

                <IconButton
                  aria-label="Отправить вопрос"
                  color="primary"
                  onClick={handleSend}
                  disabled={chatMutation.isPending || mustSelectGatewayChat}
                  sx={{
                    ml: 0.8,
                    border: '1.5px solid',
                    borderColor: assistantAccent,
                    bgcolor: input.trim() && !mustSelectGatewayChat
                      ? isLight
                        ? 'rgba(2, 132, 199, 0.13)'
                        : 'rgba(152, 217, 216, 0.16)'
                      : isLight
                        ? 'rgba(2, 132, 199, 0.05)'
                        : 'rgba(152, 217, 216, 0.06)',
                    color: assistantAccent,
                    '&:hover': {
                      bgcolor: isLight ? 'rgba(2, 132, 199, 0.18)' : 'rgba(152, 217, 216, 0.22)',
                    },
                    '&.Mui-disabled': {
                      color: assistantAccent,
                      borderColor: assistantAccent,
                      opacity: 0.55,
                    },
                  }}
                >
                  <Send size={20} />
                </IconButton>
              </Paper>

              <Paper
                elevation={0}
                sx={{
                  p: '10px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  minHeight: 58,
                  flex: { lg: 0.95 },
                  maxWidth: { lg: 430 },
                  borderRadius: 3,
                  border: isLight ? '1px solid rgba(15,23,42,0.18)' : '1.5px solid rgba(198, 216, 240, 0.34)',
                  bgcolor: isLight ? 'rgba(255,255,255,0.62)' : 'rgba(22, 23, 27, 0.54)',
                  boxShadow: isLight ? '0 6px 18px rgba(15,23,42,0.035)' : 'inset 0 1px 0 rgba(255,255,255,0.035)',
                }}
              >
                <TextField
                  fullWidth
                  size="small"
                  value={chatSearch}
                  onChange={(event) => setChatSearch(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && normalizedChatSearch) {
                      event.preventDefault();
                      goToSearchMatch(event.shiftKey ? 'prev' : 'next');
                    }
                  }}
                  placeholder="Поиск по чату"
                  variant="standard"
                  slotProps={{
                    input: {
                      disableUnderline: true,
                      startAdornment: <Search size={16} style={{ marginRight: 10, opacity: 0.65 }} />,
                      endAdornment: normalizedChatSearch ? (
                        <Stack
                          direction="row"
                          spacing={0.25}
                          sx={{ alignItems: 'center', ml: 0.8 }}
                          onMouseDown={(event) => event.preventDefault()}
                        >
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ whiteSpace: 'nowrap', minWidth: 44, textAlign: 'right' }}
                          >
                            {searchMatches.length > 0 ? `${activeSearchMatch + 1}/${searchMatches.length}` : '0/0'}
                          </Typography>
                          <Tooltip title="Предыдущее совпадение">
                            <span>
                              <IconButton
                                aria-label="Предыдущее совпадение"
                                size="small"
                                disabled={searchMatches.length === 0}
                                onClick={() => goToSearchMatch('prev')}
                                sx={{ width: 24, height: 24 }}
                              >
                                <ChevronLeft size={14} />
                              </IconButton>
                            </span>
                          </Tooltip>
                          <Tooltip title="Следующее совпадение">
                            <span>
                              <IconButton
                                aria-label="Следующее совпадение"
                                size="small"
                                disabled={searchMatches.length === 0}
                                onClick={() => goToSearchMatch('next')}
                                sx={{ width: 24, height: 24 }}
                              >
                                <ChevronRight size={14} />
                              </IconButton>
                            </span>
                          </Tooltip>
                          <Tooltip title="Очистить поиск">
                            <IconButton
                              aria-label="Очистить поиск по чату"
                              size="small"
                              onClick={() => setChatSearch('')}
                              sx={{ width: 24, height: 24 }}
                            >
                              <X size={14} />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      ) : null,
                      sx: {
                        fontSize: '0.9rem',
                        lineHeight: 1.45,
                      },
                    },
                  }}
                />
              </Paper>
            </Stack>
          </Container>
        </Box>
      </Box>

      {openedCitations.length > 0 && (
        <Box
          sx={{
            width: previewWidth,
            minWidth: 320,
            maxWidth: 720,
            position: 'relative',
            borderLeft: isLight ? '2px solid rgba(14, 116, 144, 0.26)' : '2px solid rgba(198, 216, 240, 0.40)',
            bgcolor: isLight ? '#f5f7fa' : '#101116',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            onMouseDown={() => setIsResizing(true)}
            sx={{
              position: 'absolute',
              left: -5,
              top: 0,
              bottom: 0,
              width: 10,
              cursor: 'col-resize',
              '&:hover': { bgcolor: 'rgba(112,161,255,0.20)' },
            }}
          />

          <Box sx={{ p: 1.5, borderBottom: isLight ? '1px solid rgba(15,23,42,0.12)' : '1px solid rgba(255,255,255,0.08)' }}>
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              {openedCitations.map((citation) => (
                <Chip
                  key={citation.previewId}
                  size="small"
                  label={citation.previewKind === 'source' ? `Страница ${citation.page}` : 'Документ'}
                  color={citation.previewId === activeCitation?.previewId ? 'primary' : 'default'}
                  variant={citation.previewId === activeCitation?.previewId ? 'filled' : 'outlined'}
                  onClick={() => setActiveCitationId(citation.previewId)}
                  onDelete={() => closePreview(citation.previewId)}
                  deleteIcon={<X size={14} />}
                />
              ))}
            </Stack>
          </Box>

          {activeCitation && (
            <Box className="preview-scroll-panel" sx={{ overflow: 'auto', flexGrow: 1 }}>
              <Box
                sx={{
                  position: 'sticky',
                  top: 0,
                  zIndex: 2,
                  px: 1.35,
                  py: 1,
                  bgcolor: isLight ? '#f5f7fa' : '#101116',
                  borderBottom: isLight ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <Stack spacing={1}>
                  <Stack direction="row" spacing={0.8} sx={{ alignItems: 'center' }}>
                    <Button
                      variant="text"
                      size="small"
                      className="source-link-button"
                      id="download-source-button"
                      startIcon={<Download size={14} />}
                      title={activeCitation.document}
                      onClick={(e) => setDownloadAnchorEl(e.currentTarget)}
                      sx={{
                        ...sourceButtonSx(isLight, '0.82rem'),
                        justifyContent: 'flex-start',
                        textAlign: 'left',
                        px: 0.9,
                        flex: 1,
                        minWidth: 0,
                      }}
                    >
                      <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {activeCitation.document}
                      </Box>
                    </Button>
                    <Menu
                      anchorEl={downloadAnchorEl}
                      open={Boolean(downloadAnchorEl)}
                      onClose={() => setDownloadAnchorEl(null)}
                      slotProps={{
                        paper: {
                          sx: {
                            bgcolor: isLight ? '#fff' : '#1e1f23',
                            border: '1px solid',
                            borderColor: isLight ? 'rgba(15,23,42,0.12)' : 'rgba(198,216,240,0.20)',
                            borderRadius: 2,
                            minWidth: 190,
                          },
                        },
                      }}
                    >
                      <MenuItem
                        onClick={() => {
                          setDownloadAnchorEl(null);
                          downloadPreviewFile(
                            activeCitation.document,
                            `${activeCitation.document}\n${activeCitation.section}\nСтраница ${activeCitation.page}\n\n${activeCitation.text}`,
                          );
                        }}
                      >
                        <FileText size={15} style={{ marginRight: 10 }} />
                        Скачать как TXT
                      </MenuItem>
                      {activeCitation.documentUrl && (
                        <MenuItem
                          onClick={() => {
                            setDownloadAnchorEl(null);
                            window.open(activeCitation.documentUrl, '_blank', 'noopener,noreferrer');
                          }}
                        >
                          <FileText size={15} style={{ marginRight: 10 }} />
                          Скачать PDF
                        </MenuItem>
                      )}
                    </Menu>
                    <Tooltip title="Уменьшить масштаб">
                      <IconButton size="small" onClick={() => setPreviewZoom((value) => Math.max(0.75, value - 0.1))}>
                        <ZoomOut size={16} />
                      </IconButton>
                    </Tooltip>
                    <Slider
                      size="small"
                      value={Math.round(previewZoom * 100)}
                      min={75}
                      max={160}
                      step={5}
                      onChange={(_, value) => setPreviewZoom(Number(value) / 100)}
                      aria-label="Масштаб документа"
                      sx={{ width: 82, mx: 0.5 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: 42, textAlign: 'center' }}>
                      {Math.round(previewZoom * 100)}%
                    </Typography>
                    <Tooltip title="Увеличить масштаб">
                      <IconButton size="small" onClick={() => setPreviewZoom((value) => Math.min(1.6, value + 0.1))}>
                        <ZoomIn size={16} />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Открыть крупнее">
                      <IconButton size="small" onClick={() => setExpandedPreviewOpen(true)}>
                        <Maximize2 size={16} />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                  <TextField
                    size="small"
                    value={previewSearch}
                    onChange={(event) => setPreviewSearch(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' && normalizedPreviewSearch) {
                        event.preventDefault();
                        goToPreviewSearchMatch(event.shiftKey ? 'prev' : 'next');
                      }
                    }}
                    placeholder="Поиск по открытому документу"
                    variant="outlined"
                    slotProps={{
                      input: {
                        startAdornment: <Search size={15} style={{ marginRight: 8, opacity: 0.62 }} />,
                        endAdornment: normalizedPreviewSearch ? (
                          <Stack
                            direction="row"
                            spacing={0.25}
                            sx={{ alignItems: 'center', ml: 0.8 }}
                            onMouseDown={(event) => event.preventDefault()}
                          >
                            <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
                              {previewSearchMatches > 0 ? `${activePreviewSearchMatch + 1}/${previewSearchMatches}` : '0/0'}
                            </Typography>
                            <Tooltip title="Предыдущее совпадение">
                              <span>
                                <IconButton
                                  aria-label="Предыдущее совпадение в документе"
                                  size="small"
                                  disabled={previewSearchMatches === 0}
                                  onClick={() => goToPreviewSearchMatch('prev')}
                                  sx={{ width: 24, height: 24 }}
                                >
                                  <ChevronLeft size={14} />
                                </IconButton>
                              </span>
                            </Tooltip>
                            <Tooltip title="Следующее совпадение">
                              <span>
                                <IconButton
                                  aria-label="Следующее совпадение в документе"
                                  size="small"
                                  disabled={previewSearchMatches === 0}
                                  onClick={() => goToPreviewSearchMatch('next')}
                                  sx={{ width: 24, height: 24 }}
                                >
                                  <ChevronRight size={14} />
                                </IconButton>
                              </span>
                            </Tooltip>
                            <Tooltip title="Очистить поиск">
                              <IconButton
                                aria-label="Очистить поиск по документу"
                                size="small"
                                onClick={() => setPreviewSearch('')}
                                sx={{ width: 24, height: 24 }}
                              >
                                <X size={14} />
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        ) : null,
                      },
                    }}
                  />
                </Stack>
              </Box>

              <Box sx={{ p: 1.5 }}>
              <Stack spacing={1.5}>
                <Paper
                  variant="outlined"
                  sx={{
                    minHeight: activeCitation.previewKind === 'document' ? 980 : 520,
                    p: 2.4,
                    borderRadius: 2,
                    bgcolor: '#f4f1e8',
                    color: '#242424',
                    borderColor: 'rgba(255,255,255,0.12)',
                    width: `${100 / previewZoom}%`,
                    transform: `scale(${previewZoom})`,
                    transformOrigin: 'top left',
                    transition: 'transform 160ms ease, width 160ms ease',
                  }}
                >
                  <Typography variant="caption" sx={{ color: '#777' }}>
                    {activeCitation.previewKind === 'source'
                      ? `${activeCitation.document} · стр. ${activeCitation.page}`
                      : `Страница ${activeCitation.page}`}
                  </Typography>

                  {activeCitation.previewError && (
                    <Alert severity="warning" variant="outlined" sx={{ mt: 2, mb: 2 }}>
                      {activeCitation.previewError}
                    </Alert>
                  )}

                  {activeCitation.previewKind === 'source' && activeCitation.pageMarkdown ? (
                    <Box
                      sx={{
                        borderRadius: 1.5,
                        border: '1px solid rgba(0,0,0,0.08)',
                        bgcolor: '#f4f1e8',
                        p: 2,
                        color: '#202020',
                        fontFamily: 'Georgia, serif',
                        '& table': { borderCollapse: 'collapse', width: '100%', my: 1, '& th, & td': { border: '1px solid', borderColor: 'divider', p: 1, textAlign: 'left' } },
                        '& th': { bgcolor: 'action.hover' },
                        '& code': { bgcolor: 'action.hover', px: 0.5, borderRadius: 0.5, fontSize: '0.85em' },
                        '& pre': { bgcolor: 'grey.900', color: 'grey.100', p: 1.5, borderRadius: 1, overflow: 'auto', fontSize: '0.85em' },
                        '& img': { maxWidth: '100%', height: 'auto', display: 'block', my: 1 },
                      }}
                    >
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {activeCitation.pageMarkdown}
                      </ReactMarkdown>
                    </Box>
                  ) : activeCitation.previewKind === 'source' ? (
                    <>
                      {/* Изображение страницы — если доступно (fallback) */}
                      {activeCitation.pagePreviewUrl && (
                        <Box
                          sx={{
                            borderRadius: 1.5,
                            overflow: 'hidden',
                            border: '1px solid rgba(0,0,0,0.08)',
                            display: 'flex',
                            justifyContent: 'center',
                            bgcolor: '#fff',
                            maxHeight: '60vh',
                            mb: 2,
                          }}
                        >
                          <img
                            src={activeCitation.pagePreviewUrl}
                            alt={`Страница ${activeCitation.page}`}
                            style={{ maxWidth: '100%', maxHeight: '60vh', objectFit: 'contain' }}
                            onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                          />
                        </Box>
                      )}

                      <Typography variant="body2" sx={{ mb: 1, color: '#555' }}>
                        Цитируемый фрагмент:
                      </Typography>
                      <Box
                        sx={{
                          p: 2,
                          border: '2px solid rgba(56, 189, 248, 0.55)',
                          bgcolor: 'rgba(56, 189, 248, 0.10)',
                          borderRadius: 1,
                        }}
                      >
                        <Typography variant="body2" sx={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                          {activeCitation.originalFragment && !normalizedPreviewSearch
                            ? highlightFragmentInText(activeCitation.text, activeCitation.originalFragment, isLight)
                            : highlightText(activeCitation.text, normalizedPreviewSearch, isLight, activePreviewSearchMatch)}
                        </Typography>
                      </Box>
                    </>
                  ) : (
                    <Box
                      sx={{
                        mt: 2,
                        p: 2,
                        border: '2px solid rgba(56, 189, 248, 0.55)',
                        bgcolor: 'rgba(56, 189, 248, 0.10)',
                        borderRadius: 1,
                      }}
                    >
                      <Typography variant="body2" sx={{ lineHeight: 1.8 }}>
                        {highlightText(activeCitation.text, normalizedPreviewSearch, isLight, activePreviewSearchMatch)}
                      </Typography>
                    </Box>
                  )}

                  {activeCitation.previewKind === 'document' && [1, 2, 3, 4].map((pageOffset) => {
                    const pageNumber = activeCitation.page + pageOffset;
                    return (
                      <Box
                        key={pageNumber}
                        sx={{
                          mt: 4,
                          pt: 3,
                          minHeight: 520,
                          borderTop: '1px solid #d2cec2',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: '#777' }}>
                          Страница {pageNumber}
                        </Typography>
                        <Typography variant="subtitle2" sx={{ color: '#1f1f1f', fontWeight: 700, mt: 1, mb: 1 }}>
                          Раздел {pageOffset + 1}. Связанные требования
                        </Typography>
                        <Typography variant="body2" sx={{ lineHeight: 1.85 }}>
                          На этой странице показана другая часть исходного документа: таблицы, пояснения,
                          ссылки на связанные разделы и порядок применения требований. При реальном подключении
                          здесь будет отображаться оригинальная страница документа с сохранением нумерации, масштаба
                          и вертикальной прокрутки всего документа.
                        </Typography>
                      </Box>
                    );
                  })}
                  {activeCitation.previewKind !== 'source' && (
                    <Box sx={{ mt: 4, pt: 2, borderTop: '1px solid #d2cec2', color: '#777' }}>
                      <Typography variant="caption">
                        Конец документа, страниц: 5
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Stack>
              </Box>
            </Box>
          )}
        </Box>
      )}

      <Dialog
        open={expandedPreviewOpen && Boolean(activeCitation)}
        onClose={() => setExpandedPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        {activeCitation && (
          <Box
            sx={{
              bgcolor: isLight ? '#f8fafc' : '#101116',
              color: 'text.primary',
              border: isLight ? '1px solid #bae6fd' : '1px solid rgba(198, 216, 240, 0.32)',
            }}
          >
            <Box
              sx={{
                px: 2,
                py: 1.3,
                borderBottom: isLight ? '1px solid #dbeafe' : '1px solid rgba(255,255,255,0.08)',
              }}
            >
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <FileText size={18} color={assistantAccent} />
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    title={activeCitation.document}
                    sx={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                  >
                    {activeCitation.document}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {activeCitation.previewKind === 'source' ? `Страница ${activeCitation.page}` : 'Документ'} · {activeCitation.section}
                  </Typography>
                </Box>
                <TextField
                  size="small"
                  value={previewSearch}
                  onChange={(event) => setPreviewSearch(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && normalizedPreviewSearch) {
                      event.preventDefault();
                      goToPreviewSearchMatch(event.shiftKey ? 'prev' : 'next');
                    }
                  }}
                  placeholder="Поиск по документу"
                  sx={{ width: 260, display: { xs: 'none', md: 'block' } }}
                  slotProps={{
                    input: {
                      startAdornment: <Search size={15} style={{ marginRight: 8, opacity: 0.62 }} />,
                      endAdornment: normalizedPreviewSearch ? (
                        <Stack
                          direction="row"
                          spacing={0.25}
                          sx={{ alignItems: 'center', ml: 0.8 }}
                          onMouseDown={(event) => event.preventDefault()}
                        >
                          <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
                            {previewSearchMatches > 0 ? `${activePreviewSearchMatch + 1}/${previewSearchMatches}` : '0/0'}
                          </Typography>
                          <Tooltip title="Предыдущее совпадение">
                            <span>
                              <IconButton
                                aria-label="Предыдущее совпадение в документе"
                                size="small"
                                disabled={previewSearchMatches === 0}
                                onClick={() => goToPreviewSearchMatch('prev')}
                                sx={{ width: 24, height: 24 }}
                              >
                                <ChevronLeft size={14} />
                              </IconButton>
                            </span>
                          </Tooltip>
                          <Tooltip title="Следующее совпадение">
                            <span>
                              <IconButton
                                aria-label="Следующее совпадение в документе"
                                size="small"
                                disabled={previewSearchMatches === 0}
                                onClick={() => goToPreviewSearchMatch('next')}
                                sx={{ width: 24, height: 24 }}
                              >
                                <ChevronRight size={14} />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </Stack>
                      ) : null,
                    },
                  }}
                />
                <IconButton onClick={() => setExpandedPreviewOpen(false)}>
                  <X size={18} />
                </IconButton>
              </Stack>
            </Box>

            <Box className="preview-scroll-panel" sx={{ maxHeight: '76vh', overflow: 'auto', p: 2.4 }}>
              <Paper
                variant="outlined"
                sx={{
                  maxWidth: 820,
                  minHeight: activeCitation.previewKind === 'document' ? 980 : 560,
                  mx: 'auto',
                  p: 3.2,
                  borderRadius: 2,
                  bgcolor: '#f4f1e8',
                  color: '#242424',
                  borderColor: '#d2cec2',
                  boxShadow: '0 22px 70px rgba(15, 23, 42, 0.20)',
                }}
              >
                <Typography variant="caption" sx={{ color: '#777' }}>
                  {activeCitation.previewKind === 'source'
                    ? `${activeCitation.document} · стр. ${activeCitation.page}`
                    : `Страница ${activeCitation.page}`}
                </Typography>

                {activeCitation.previewKind === 'source' ? (
                  <>
                    {/* Изображение страницы */}
                    {activeCitation.pagePreviewUrl && (
                      <Box
                        sx={{
                          borderRadius: 1.5,
                          overflow: 'hidden',
                          border: '1px solid rgba(0,0,0,0.08)',
                          display: 'flex',
                          justifyContent: 'center',
                          bgcolor: '#fff',
                          my: 2,
                        }}
                      >
                        <img
                          src={activeCitation.pagePreviewUrl}
                          alt={`Страница ${activeCitation.page}`}
                          style={{ maxWidth: '100%', objectFit: 'contain' }}
                          onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                        />
                      </Box>
                    )}
                    <Typography variant="body2" sx={{ mb: 1, color: '#555' }}>
                      Цитируемый фрагмент:
                    </Typography>
                    <Box
                      sx={{
                        p: 2.2,
                        border: '2px solid rgba(56, 189, 248, 0.55)',
                        bgcolor: 'rgba(56, 189, 248, 0.10)',
                        borderRadius: 1,
                      }}
                    >
                      <Typography variant="body2" sx={{ lineHeight: 1.85, whiteSpace: 'pre-wrap' }}>
                        {activeCitation.originalFragment && !normalizedPreviewSearch
                          ? highlightFragmentInText(activeCitation.text, activeCitation.originalFragment, isLight)
                          : highlightText(activeCitation.text, normalizedPreviewSearch, isLight, activePreviewSearchMatch)}
                      </Typography>
                    </Box>
                  </>
                ) : (
                  <Box
                    sx={{
                      mt: 2,
                      p: 2.2,
                      border: '2px solid rgba(56, 189, 248, 0.55)',
                      bgcolor: 'rgba(56, 189, 248, 0.10)',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="body2" sx={{ lineHeight: 1.85 }}>
                      {highlightText(activeCitation.text, normalizedPreviewSearch, isLight, activePreviewSearchMatch)}
                    </Typography>
                  </Box>
                )}
                {activeCitation.previewKind === 'document' &&
                  [1, 2, 3].map((pageOffset) => (
                    <Box key={pageOffset} sx={{ mt: 4, pt: 3, minHeight: 420, borderTop: '1px solid #d2cec2' }}>
                      <Typography variant="caption" sx={{ color: '#777' }}>
                        Страница {activeCitation.page + pageOffset}
                      </Typography>
                      <Typography variant="subtitle2" sx={{ color: '#1f1f1f', fontWeight: 700, mt: 1, mb: 1 }}>
                        Связанный раздел документа
                      </Typography>
                      <Typography variant="body2" sx={{ lineHeight: 1.85 }}>
                        Здесь показана следующая часть исходного документа. В рабочем режиме в этой области будет
                        отображаться оригинальная страница или подготовленное превью с сохранением формата источника.
                      </Typography>
                    </Box>
                  ))}
              </Paper>
            </Box>
          </Box>
        )}
      </Dialog>
    </Box>
  );
};
