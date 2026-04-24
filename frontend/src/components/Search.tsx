import React, { useEffect, useState } from 'react';
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
  TextField,
  Typography,
} from '@mui/material';
import { ExternalLink, FileText, Filter, Hash, Search as SearchIcon, X } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '../utils/http';

type DocumentPreview = {
  id: string;
  name: string;
  type: string;
  source: string;
  version: string;
  page: number;
  section: string;
  fragment: string;
};

export const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({ type: 'all', version: 'all' });
  const [openedDocuments, setOpenedDocuments] = useState<DocumentPreview[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [previewWidth, setPreviewWidth] = useState(420);
  const [isResizing, setIsResizing] = useState(false);

  const activeDocument = openedDocuments.find((doc) => doc.id === activeDocumentId) ?? openedDocuments[0];

  const searchQuery = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchApi.query(query),
    enabled: false,
  });

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

  const handleSearch = () => {
    if (query.trim()) {
      void searchQuery.refetch();
    }
  };

  const openDocument = (item: any, index: number) => {
    const preview: DocumentPreview = {
      id: item.id ?? `search-doc-${index}`,
      name: item.name,
      type: item.type ?? 'PDF',
      source: item.source,
      version: item.version,
      page: 1,
      section: item.section ?? 'Фрагмент базы знаний',
      fragment: item.fragment,
    };

    setOpenedDocuments((prev) => {
      if (prev.some((doc) => doc.id === preview.id)) return prev;
      return [...prev, preview];
    });
    setActiveDocumentId(preview.id);
  };

  const closeDocument = (documentId: string) => {
    setOpenedDocuments((prev) => {
      const next = prev.filter((doc) => doc.id !== documentId);
      if (activeDocumentId === documentId) {
        setActiveDocumentId(next[0]?.id ?? null);
      }
      return next;
    });
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 142px)', minHeight: 0 }}>
      <Box sx={{ flex: 1, minWidth: 0, overflowY: 'auto' }}>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Paper
            sx={{
              p: 3,
              mb: 3,
              borderRadius: 3,
              bgcolor: 'rgba(22, 23, 27, 0.72)',
              border: '1px solid rgba(255,255,255,0.10)',
            }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  fullWidth
                  placeholder="Введите запрос для поиска по документам..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  slotProps={{
                    input: {
                      startAdornment: <SearchIcon size={20} style={{ marginRight: 12, opacity: 0.65 }} />,
                    },
                  }}
                />
                <Button variant="contained" size="large" onClick={handleSearch} disableElevation>
                  Найти
                </Button>
                <Button variant="outlined" size="large" onClick={() => { setQuery(''); }}>
                  Сбросить
                </Button>
              </Box>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel>Тип документа</InputLabel>
                  <Select label="Тип документа" value={filters.type} onChange={(e) => setFilters({ ...filters, type: e.target.value })}>
                    <MenuItem value="all">Все типы</MenuItem>
                    <MenuItem value="PDF">PDF</MenuItem>
                    <MenuItem value="DWG">DWG</MenuItem>
                    <MenuItem value="XLSX">Excel</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel>Версия</InputLabel>
                  <Select label="Версия" value={filters.version} onChange={(e) => setFilters({ ...filters, version: e.target.value })}>
                    <MenuItem value="all">Любая</MenuItem>
                    <MenuItem value="actual">Актуальная</MenuItem>
                    <MenuItem value="archive">Архив</MenuItem>
                  </Select>
                </FormControl>
                <Button startIcon={<Filter size={16} />} size="small" sx={{ ml: 'auto' }}>
                  Расширенные фильтры
                </Button>
              </Box>
            </Box>
          </Paper>

          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {searchQuery.data ? `Найдено результатов: ${searchQuery.data.length}` : 'Готов к поиску'}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {searchQuery.isLoading && (
              <Typography sx={{ textAlign: 'center', py: 3 }} color="text.secondary">
                Выполнение поиска...
              </Typography>
            )}

            {searchQuery.data && searchQuery.data.map((item: any, idx: number) => (
              <Paper
                key={idx}
                variant="outlined"
                sx={{
                  p: 2.5,
                  borderRadius: 3,
                  bgcolor: 'rgba(22, 23, 27, 0.64)',
                  borderColor: 'rgba(255,255,255,0.10)',
                  '&:hover': { borderColor: 'primary.main', bgcolor: 'rgba(22, 23, 27, 0.84)' },
                  transition: 'border-color 0.2s, background-color 0.2s',
                }}
              >
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 200px' }, gap: 2 }}>
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                      <Hash size={18} color="#70a1ff" />
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{item.name}</Typography>
                      <Chip label={`${Math.round(item.relevance * 100)}%`} size="small" color="primary" variant="outlined" sx={{ height: 20, fontSize: '0.7rem' }} />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
                      "...{item.fragment}..."
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>Источник</Typography>
                        <Typography variant="body2">{item.source}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>Версия</Typography>
                        <Typography variant="body2">{item.version}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>Статус</Typography>
                        <Typography variant="body2" color="success.main">Проверено</Typography>
                      </Box>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: { md: 'flex-end' } }}>
                    <Button variant="text" endIcon={<ExternalLink size={16} />} onClick={() => openDocument(item, idx)}>
                      Открыть документ
                    </Button>
                  </Box>
                </Box>
              </Paper>
            ))}
          </Box>
        </Container>
      </Box>

      {openedDocuments.length > 0 && (
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
              '&:hover': { bgcolor: 'rgba(199,155,99,0.18)' },
            }}
          />

          <Box sx={{ p: 1.5, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              {openedDocuments.map((doc) => (
                <Chip
                  key={doc.id}
                  size="small"
                  label={`стр. ${doc.page}`}
                  color={doc.id === activeDocument?.id ? 'primary' : 'default'}
                  variant={doc.id === activeDocument?.id ? 'filled' : 'outlined'}
                  onClick={() => setActiveDocumentId(doc.id)}
                  onDelete={() => closeDocument(doc.id)}
                  deleteIcon={<X size={14} />}
                />
              ))}
            </Stack>
          </Box>

          {activeDocument && (
            <Box sx={{ overflow: 'auto', flexGrow: 1 }}>
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
                  <Typography variant="subtitle2">Превью документа</Typography>
                </Stack>

                <Box sx={{ mt: 1.5 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                    {activeDocument.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {activeDocument.type} · с первой страницы · {activeDocument.version}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ p: 2 }}>
              <Stack spacing={1.5}>
                {activeDocument.type === 'XLSX' ? (
                  <Paper
                    variant="outlined"
                    sx={{
                      minHeight: 900,
                      p: 2,
                      borderRadius: 2,
                      bgcolor: '#f7fbf6',
                      color: '#1d2b1f',
                      borderColor: 'rgba(255,255,255,0.12)',
                      overflowX: 'auto',
                    }}
                  >
                    <Typography variant="caption" sx={{ color: '#4b604d', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Excel / табличный документ
                    </Typography>
                    <Box component="table" sx={{ mt: 2, borderCollapse: 'collapse', minWidth: 620, width: '100%' }}>
                      <Box component="thead">
                        <Box component="tr">
                          {['A', 'B', 'C', 'D', 'E'].map((cell) => (
                            <Box component="th" key={cell} sx={{ border: '1px solid #c8d8c8', p: 1, bgcolor: '#dfeee0', fontSize: 12 }}>
                              {cell}
                            </Box>
                          ))}
                        </Box>
                      </Box>
                      <Box component="tbody">
                        {Array.from({ length: 28 }).map((_, row) => (
                          <Box component="tr" key={row}>
                            <Box component="td" sx={{ border: '1px solid #c8d8c8', p: 1, fontSize: 12 }}>{row + 1}</Box>
                            <Box component="td" sx={{ border: '1px solid #c8d8c8', p: 1, fontSize: 12 }}>Параметр {row + 1}</Box>
                            <Box component="td" sx={{ border: '1px solid #c8d8c8', p: 1, fontSize: 12 }}>{activeDocument.version}</Box>
                            <Box component="td" sx={{ border: '1px solid #c8d8c8', p: 1, fontSize: 12 }}>{row % 3 === 0 ? activeDocument.fragment : 'Значение из спецификации'}</Box>
                            <Box component="td" sx={{ border: '1px solid #c8d8c8', p: 1, fontSize: 12 }}>Проверено</Box>
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  </Paper>
                ) : activeDocument.type === 'DWG' ? (
                  <Paper
                    variant="outlined"
                    sx={{
                      minHeight: 980,
                      p: 2.4,
                      borderRadius: 2,
                      bgcolor: '#111820',
                      color: '#d8f0ff',
                      borderColor: 'rgba(255,255,255,0.12)',
                      backgroundImage:
                        'linear-gradient(rgba(112,161,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(112,161,255,0.10) 1px, transparent 1px)',
                      backgroundSize: '28px 28px',
                    }}
                  >
                    <Typography variant="caption" sx={{ color: '#91b8ff', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      DWG / чертежный лист
                    </Typography>
                    <Box sx={{ mt: 3, height: 620, border: '2px solid rgba(216,240,255,0.55)', position: 'relative' }}>
                      <Box sx={{ position: 'absolute', left: '10%', top: '18%', width: '72%', height: '34%', border: '2px solid #91b8ff' }} />
                      <Box sx={{ position: 'absolute', left: '20%', top: '28%', width: '42%', height: '16%', border: '1px dashed #f0c36d' }} />
                      <Box sx={{ position: 'absolute', right: 16, bottom: 16, border: '1px solid #91b8ff', p: 1.5, width: 180 }}>
                        <Typography variant="caption">Лист: {activeDocument.page}</Typography>
                        <Typography variant="caption" sx={{ display: 'block' }}>Версия: {activeDocument.version}</Typography>
                        <Typography variant="caption" sx={{ display: 'block' }}>{activeDocument.name}</Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" sx={{ mt: 3, lineHeight: 1.8 }}>
                      {activeDocument.fragment}
                    </Typography>
                  </Paper>
                ) : (
                  <Paper
                    variant="outlined"
                    sx={{
                      minHeight: 1160,
                      p: 2.4,
                      borderRadius: 2,
                      bgcolor: '#f4f1e8',
                      color: '#242424',
                      borderColor: 'rgba(255,255,255,0.12)',
                    }}
                  >
                    <Typography variant="caption" sx={{ color: '#666', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      PDF / оригинал страницы
                    </Typography>
                    <Typography variant="h6" sx={{ mt: 2, mb: 1, color: '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                      {activeDocument.section}
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
                        {activeDocument.fragment}
                      </Typography>
                    </Box>
                    {Array.from({ length: 6 }).map((_, part) => {
                      const pageNumber = activeDocument.page + part;
                      return (
                      <Box
                        key={pageNumber}
                        sx={{
                          mt: 4,
                          pt: 3,
                          minHeight: 500,
                          borderTop: part === 0 ? 'none' : '1px solid #d2cec2',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: '#777' }}>
                          Страница {pageNumber}
                        </Typography>
                        <Typography variant="subtitle2" sx={{ color: '#1f1f1f', fontWeight: 700, mt: 1, mb: 1 }}>
                          Раздел {part + 1}. Материалы документа
                        </Typography>
                        <Typography variant="body2" sx={{ lineHeight: 1.85 }}>
                          Это отдельная страница исходного PDF. При реальном подключении backend отдаст оригинальный
                          файл или изображение страницы, а панель сохранит прокрутку, масштабирование по ширине,
                          нумерацию страниц и переход между открытыми документами.
                        </Typography>
                      </Box>
                    );
                    })}
                  </Paper>
                )}
              </Stack>
              </Box>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};
