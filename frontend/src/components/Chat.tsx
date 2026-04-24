import React, { useState, useRef, useEffect } from 'react';
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
} from '@mui/material';
import {
  Send,
  User,
  Anchor,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Bookmark,
  HelpCircle,
  ShieldCheck,
  X,
  FileText,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { chatApi } from '../utils/http';
import { ChatMessage, MOCK_CHATS, Citation } from '../utils/mockData';
import { Feedback } from './Feedback';

const statusLabel = {
  answered: 'ответ найден',
  needs_clarification: 'нужно уточнение',
  insufficient_data: 'недостаточно данных',
  source_conflict: 'конфликт источников',
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

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(MOCK_CHATS);
  const [input, setInput] = useState('');
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});
  const [openedCitations, setOpenedCitations] = useState<ChatPreview[]>([]);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);
  const [previewWidth, setPreviewWidth] = useState(420);
  const [isResizing, setIsResizing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeCitation = openedCitations.find((citation) => citation.previewId === activeCitationId) ?? openedCitations[0];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
      setMessages((prev) => [...prev, data]);
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

    setMessages((prev) => [...prev, userMessage]);
    chatMutation.mutate(input);
    setInput('');
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
                    sx={{
                      display: 'flex',
                      gap: 1.5,
                      alignItems: 'flex-start',
                      justifyContent: isAssistant ? 'flex-start' : 'flex-end',
                    }}
                  >
                    {isAssistant && (
                      <Avatar sx={{ bgcolor: 'rgba(152, 217, 216, 0.16)', color: '#98d9d8', width: 34, height: 34, mt: 0.55 }}>
                        <Anchor size={18} />
                      </Avatar>
                    )}

                    <Box sx={{ maxWidth: '84%', minWidth: 0 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          borderRadius: isAssistant ? '18px 18px 18px 6px' : '18px 18px 6px 18px',
                          bgcolor: isAssistant ? 'rgba(255,255,255,0.045)' : 'rgba(255,255,255,0.075)',
                          border: '1px solid',
                          borderColor: isAssistant ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.12)',
                        }}
                      >
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            mb: 1.15,
                            pb: 1.15,
                            borderBottom: '1px solid rgba(255,255,255,0.14)',
                          }}
                        >
                          <Typography
                            variant="caption"
                            sx={{
                              fontWeight: 600,
                              letterSpacing: '0.04em',
                              color: isAssistant ? '#98d9d8' : '#d8b07a',
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
                                    {item.text}
                                  </Typography>
                                  <Stack direction="row" spacing={1.4} useFlexGap sx={{ flexWrap: 'wrap', mt: 0.6 }}>
                                    <Button
                                      size="small"
                                      variant="text"
                                      startIcon={<ExternalLink size={14} />}
                                      sx={{ px: 0.9, py: 0.28, minWidth: 0, height: 'auto', fontSize: '0.74rem', color: '#b8c4d8', border: '1px solid rgba(184,196,216,0.20)', borderRadius: 999, bgcolor: 'rgba(184,196,216,0.06)' }}
                                      onClick={() => openPreview(item.citation, 'source')}
                                    >
                                      Страница
                                    </Button>
                                    <Button
                                      size="small"
                                      variant="text"
                                      startIcon={<FileText size={14} />}
                                      sx={{ px: 0.9, py: 0.28, minWidth: 0, height: 'auto', fontSize: '0.74rem', color: '#b8c4d8', border: '1px solid rgba(184,196,216,0.20)', borderRadius: 999, bgcolor: 'rgba(184,196,216,0.06)' }}
                                      onClick={() => openPreview(item.citation, 'document')}
                                    >
                                      Документ
                                    </Button>
                                  </Stack>
                                </Box>
                              </Box>
                            ))}
                          </Box>
                        ) : (
                          <Typography
                            variant="body1"
                            sx={{
                              lineHeight: 1.75,
                              whiteSpace: 'pre-wrap',
                              fontWeight: 400,
                              color: isAssistant ? 'text.primary' : '#f4fbff',
                              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                              fontSize: '0.95rem',
                              mt: 0.85,
                            }}
                          >
                            {msg.content}
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
                              sx={{ borderColor: 'rgba(255,255,255,0.14)' }}
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
                                      borderColor: 'rgba(255,255,255,0.10)',
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
                                        sx={{ px: 0.9, py: 0.28, minWidth: 0, height: 'auto', fontSize: '0.76rem', color: '#b8c4d8', border: '1px solid rgba(184,196,216,0.20)', borderRadius: 999, bgcolor: 'rgba(184,196,216,0.06)' }}
                                        onClick={() => openPreview(cite, 'source')}
                                      >
                                        Страница
                                      </Button>
                                      <Button
                                        size="small"
                                        variant="text"
                                        startIcon={<FileText size={14} />}
                                        sx={{ px: 0.9, py: 0.28, minWidth: 0, height: 'auto', fontSize: '0.76rem', color: '#b8c4d8', border: '1px solid rgba(184,196,216,0.20)', borderRadius: 999, bgcolor: 'rgba(184,196,216,0.06)' }}
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
                      <Avatar sx={{ bgcolor: 'rgba(216,176,122,0.16)', color: '#d8b07a', width: 34, height: 34, mt: 0.55 }}>
                        <User size={20} />
                      </Avatar>
                    )}
                  </Box>
                );
              })}

              {chatMutation.isPending && (
                <Box sx={{ display: 'flex', gap: 1.5 }}>
                  <Avatar sx={{ bgcolor: 'rgba(152, 217, 216, 0.16)', color: '#98d9d8', width: 34, height: 34 }}>
                    <Anchor size={18} />
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
            borderTop: '1px solid rgba(255,255,255,0.08)',
            pb: 2.5,
            pt: 2,
            bgcolor: 'transparent',
          }}
        >
          <Container maxWidth="md">
            <Paper
              elevation={0}
              sx={{
                p: '8px 10px',
                display: 'flex',
                alignItems: 'center',
                borderRadius: 3,
                border: '1px solid rgba(255,255,255,0.22)',
                bgcolor: '#101116',
                boxShadow: '0 14px 40px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.04)',
              }}
            >
              <TextField
                fullWidth
                multiline
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
                sx={{ ml: 1, flex: 1 }}
                slotProps={{
                  input: { disableUnderline: true },
                }}
              />

              <IconButton
                color="primary"
                onClick={handleSend}
                disabled={!input.trim() || chatMutation.isPending}
                sx={{
                  bgcolor: input.trim() ? 'primary.main' : 'rgba(255,255,255,0.04)',
                  color: input.trim() ? '#0b0c0e' : 'grey.600',
                  '&:hover': { bgcolor: 'primary.light' },
                }}
              >
                <Send size={20} />
              </IconButton>
            </Paper>
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
            borderLeft: '1px solid rgba(255,255,255,0.10)',
            bgcolor: '#101116',
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

          <Box sx={{ p: 1.5, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              {openedCitations.map((citation) => (
                <Chip
                  key={citation.previewId}
                  size="small"
                  label={`${citation.previewKind === 'source' ? 'страница' : 'документ'} · стр. ${citation.page}`}
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
            <Box sx={{ overflow: activeCitation.previewKind === 'document' ? 'auto' : 'hidden', flexGrow: 1 }}>
              <Box
                sx={{
                  position: 'sticky',
                  top: 0,
                  zIndex: 2,
                  p: 2,
                  pb: 1.5,
                  bgcolor: '#101116',
                  borderBottom: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                  <FileText size={18} />
                  <Typography variant="subtitle2">
                    {activeCitation.previewKind === 'source' ? 'Страница документа' : 'Документ PDF'}
                  </Typography>
                </Stack>

                <Box sx={{ mt: 1.5 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                    {activeCitation.document}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {activeCitation.previewKind === 'document'
                      ? `с первой страницы · ${activeCitation.version}`
                      : `${activeCitation.section} · стр. ${activeCitation.page} · ${activeCitation.version}`}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ p: 2 }}>
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
                    transformOrigin: 'top left',
                  }}
                >
                  <Typography variant="caption" sx={{ color: '#666', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    {activeCitation.previewKind === 'source' ? 'Страница / один лист' : 'PDF / полный документ'}
                  </Typography>
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
                      border: '2px solid rgba(112,161,255,0.55)',
                      bgcolor: 'rgba(112,161,255,0.08)',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="body2" sx={{ lineHeight: 1.8 }}>
                      {activeCitation.text}
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
                          здесь будет отображаться оригинальная страница PDF с сохранением нумерации, масштаба
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
    </Box>
  );
};
