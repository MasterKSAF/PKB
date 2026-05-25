import React, { useState, useRef, useEffect, useMemo } from 'react';
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
  Collapse,
  Alert,
  Stack,
  Dialog,
} from '@mui/material';
import {
  Send,
  User,
  Anchor,
  Ship,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ExternalLink,
  Bookmark,
  HelpCircle,
  ShieldCheck,
  X,
  FileText,
  Search,
  Download,
  Maximize2,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { chatApi } from '../utils/http';
import { ChatMessage, Citation } from '../utils/mockData';
import { Feedback } from './Feedback';
import { useUIStore } from '../store/uiStore';
import { downloadPreviewFile } from '../utils/downloadPreview';

const statusLabel = {
  answered: 'ответ найден',
  needs_clarification: 'нужно уточнение',
  insufficient_data: 'недостаточно данных',
  source_conflict: 'конфликт источников',
  not_found: 'ничего не найдено',
  backend_error: 'backend недоступен',
} as const;

type ChatPreview = Citation & {
  previewId: string;
  previewKind: 'source' | 'document';
};

function getAnswerPoints(content: string) {
  const lines = content
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  const numbered = lines
    .filter((line) => /^\d+[.)]\s+/.test(line))
    .map((line) => line.replace(/^\d+[.)]\s+/, ''));

  return numbered.length > 0 ? numbered : [content];
}

function mapCitationsToPoints(points: string[], citations: Citation[] = []) {
  return points.map((_, index) => {
    const citation = citations[index];
    return citation ? [citation] : [];
  });
}

function buildAnsweredView(content: string, citations: Citation[] = []) {
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

function highlightText(text: string, query: string, isLight: boolean) {
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

    parts.push(
      <Box
        component="mark"
        key={`${position}-${index}`}
        sx={{
          px: 0.35,
          py: 0.05,
          borderRadius: 0.7,
          color: isLight ? '#111827' : '#f8fbff',
          bgcolor: isLight ? 'rgba(202, 138, 4, 0.28)' : 'rgba(216, 176, 122, 0.36)',
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

export const Chat: React.FC = () => {
  const { appendChatMessages, chatMessages, themeMode } = useUIStore();
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
  const [activeSearchMatch, setActiveSearchMatch] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const activeCitation = openedCitations.find((citation) => citation.previewId === activeCitationId) ?? openedCitations[0];
  const normalizedChatSearch = chatSearch.trim().toLowerCase();
  const normalizedPreviewSearch = previewSearch.trim().toLowerCase();
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

  const chatMutation = useMutation({
    mutationFn: (q: string) => chatApi.send(q),
    onSuccess: (data) => {
      appendChatMessages([data]);
      setExpandedCitations((prev) => ({ ...prev, [data.id]: false }));
    },
  });

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return;

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

  const toggleCitations = (msgId: string) => {
    setExpandedCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const openPreview = (citation: Citation, previewKind: ChatPreview['previewKind']) => {
    const previewId = `${previewKind}-${citation.id}`;
    const preview: ChatPreview = {
      ...citation,
      page: previewKind === 'document' ? 1 : citation.page,
      previewId,
      previewKind,
    };

    setOpenedCitations((prev) => {
      if (prev.some((item) => item.previewId === previewId)) return prev;
      return [...prev, preview];
    });
    setActiveCitationId(previewId);
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
    <Box sx={{ display: 'flex', height: 'calc(100vh - 142px)', minHeight: 0 }}>
      <Box sx={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ flexGrow: 1, overflowY: 'auto', py: 3 }}>
          <Container maxWidth="md">
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.2 }}>
              {messages.map((msg) => {
                const isAssistant = msg.role === 'assistant';
                const answerPoints = isAssistant && msg.status === 'answered' ? getAnswerPoints(msg.content) : [];
                const answeredView =
                  isAssistant && msg.status === 'answered'
                    ? buildAnsweredView(msg.content, msg.citations)
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
                        {isLight ? <Ship size={18} /> : <Anchor size={18} />}
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
                              color={msg.status === 'answered' ? 'success' : msg.status === 'needs_clarification' ? 'warning' : 'error'}
                              variant="outlined"
                              sx={{ height: 22, ml: 'auto' }}
                            />
                          )}
                        </Box>

                        {answeredView ? (
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
                                  </Stack>
                                </Box>
                              </Box>
                            ))}
                          </Box>
                        ) : msg.status === 'not_found' || msg.status === 'backend_error' ? (
                          <Alert severity={msg.status === 'backend_error' ? 'error' : 'info'} variant="outlined" sx={{ mt: 1.4 }}>
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

                        {msg.limitation && msg.status !== 'answered' && (
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
                          <Feedback />
                        </Box>
                      )}

                      {isAssistant && msg.id === messages[messages.length - 1].id && (
                        <Box sx={{ mt: 1.4 }}>
                          <Feedback />
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
                <Box sx={{ display: 'flex', gap: 1.5 }}>
                  <Avatar
                    sx={{
                      bgcolor: isLight ? '#e0f2fe' : 'rgba(152, 217, 216, 0.16)',
                      color: assistantAccent,
                      width: 34,
                      height: 34,
                      border: isLight ? '1px solid rgba(2, 132, 199, 0.36)' : 'none',
                    }}
                  >
                    {isLight ? <Ship size={18} /> : <Anchor size={18} />}
                  </Avatar>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} thickness={5} />
                    <Typography variant="body2" color="text.secondary">
                      Подготовка ответа...
                    </Typography>
                  </Box>
                </Box>
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
                  placeholder="Задайте вопрос ассистенту"
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
                  disabled={chatMutation.isPending}
                  sx={{
                    ml: 0.8,
                    border: '1.5px solid',
                    borderColor: assistantAccent,
                    bgcolor: input.trim()
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
                          <IconButton
                            aria-label="Предыдущее совпадение"
                            size="small"
                            disabled={searchMatches.length === 0}
                            onClick={() => goToSearchMatch('prev')}
                            sx={{ width: 24, height: 24 }}
                          >
                            <ChevronLeft size={14} />
                          </IconButton>
                          <IconButton
                            aria-label="Следующее совпадение"
                            size="small"
                            disabled={searchMatches.length === 0}
                            onClick={() => goToSearchMatch('next')}
                            sx={{ width: 24, height: 24 }}
                          >
                            <ChevronRight size={14} />
                          </IconButton>
                          <IconButton
                            aria-label="Очистить поиск по чату"
                            size="small"
                            onClick={() => setChatSearch('')}
                            sx={{ width: 24, height: 24 }}
                          >
                            <X size={14} />
                          </IconButton>
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
            <Box className="preview-scroll-panel" sx={{ overflow: activeCitation.previewKind === 'document' ? 'auto' : 'hidden', flexGrow: 1 }}>
              <Box
                sx={{
                  position: 'sticky',
                  top: 0,
                  zIndex: 2,
                  px: 1.35,
                  py: 1,
                  bgcolor: isLight ? '#f5f7fa' : '#101116',
                  borderBottom: isLight ? '1px solid rgba(15,23,42,0.12)' : '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <Stack spacing={1}>
                  <Stack direction="row" spacing={0.8} sx={{ alignItems: 'center' }}>
                    <Button
                      variant="text"
                      size="small"
                      className="source-link-button"
                      startIcon={<Download size={14} />}
                      title={activeCitation.document}
                      onClick={() =>
                        downloadPreviewFile(
                          activeCitation.document,
                          `${activeCitation.document}\n${activeCitation.section}\nСтраница ${activeCitation.page}\n\n${activeCitation.text}`,
                        )
                      }
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
                    <IconButton size="small" onClick={() => setPreviewZoom((value) => Math.max(0.75, value - 0.1))}>
                      <ZoomOut size={16} />
                    </IconButton>
                    <Typography variant="caption" color="text.secondary" sx={{ minWidth: 42, textAlign: 'center' }}>
                      {Math.round(previewZoom * 100)}%
                    </Typography>
                    <IconButton size="small" onClick={() => setPreviewZoom((value) => Math.min(1.45, value + 0.1))}>
                      <ZoomIn size={16} />
                    </IconButton>
                    <IconButton size="small" onClick={() => setExpandedPreviewOpen(true)}>
                      <Maximize2 size={16} />
                    </IconButton>
                  </Stack>
                  <TextField
                    size="small"
                    value={previewSearch}
                    onChange={(event) => setPreviewSearch(event.target.value)}
                    placeholder="Поиск по открытому документу"
                    variant="outlined"
                    slotProps={{
                      input: {
                        startAdornment: <Search size={15} style={{ marginRight: 8, opacity: 0.62 }} />,
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
                    Страница {activeCitation.page}
                  </Typography>
                  <Typography variant="h6" sx={{ mt: 1, mb: 1, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                    {activeCitation.previewKind === 'document' ? 'Титульная страница документа' : activeCitation.section}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#555', mb: 2 }}>
                    {activeCitation.previewKind === 'source'
                      ? 'Открыта только страница, на которую ссылается ответ. Без перехода к остальным страницам документа.'
                      : 'Открыт весь документ: страницы идут ниже друг за другом, область просмотра прокручивается вниз.'}
                  </Typography>
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
                      {highlightText(activeCitation.text, normalizedPreviewSearch, isLight)}
                    </Typography>
                  </Box>
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
                  <Box sx={{ mt: 4, pt: 2, borderTop: '1px solid #d2cec2', color: '#777' }}>
                    <Typography variant="caption">
                      {activeCitation.previewKind === 'source'
                        ? `Страница ${activeCitation.page}`
                        : `Конец документа, страниц: 5`}
                    </Typography>
                  </Box>
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
                  placeholder="Поиск по документу"
                  sx={{ width: 260, display: { xs: 'none', md: 'block' } }}
                  slotProps={{
                    input: {
                      startAdornment: <Search size={15} style={{ marginRight: 8, opacity: 0.62 }} />,
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
                  Страница {activeCitation.page}
                </Typography>
                <Typography variant="h6" sx={{ mt: 1, mb: 1.2, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                  {activeCitation.previewKind === 'document' ? 'Титульная страница документа' : activeCitation.section}
                </Typography>
                <Typography variant="body2" sx={{ color: '#555', mb: 2.2 }}>
                  {activeCitation.previewKind === 'source'
                    ? 'Открыт фрагмент страницы, на который ссылается ответ ассистента.'
                    : 'Открыт демонстрационный просмотр всего документа с вертикальной прокруткой страниц.'}
                </Typography>
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
                    {highlightText(activeCitation.text, normalizedPreviewSearch, isLight)}
                  </Typography>
                </Box>
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
                        Здесь показана следующая часть исходного документа. При подключении backend в этой области будет
                        отображаться оригинальная страница или подготовленное preview с сохранением формата источника.
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
