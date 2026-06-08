import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Collapse,
  Container,
  Dialog,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  Database,
  FileText,
  Filter,
  Hash,
  Maximize2,
  Search as SearchIcon,
  X,
  Download,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '../utils/http';
import { useUIStore } from '../store/uiStore';
import { downloadPreviewFile } from '../utils/downloadPreview';
import { MOCK_KNOWLEDGE_SECTIONS } from '../utils/mockData';

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

function previewLinkButtonSx(isLight: boolean) {
  return {
  px: 0.9,
  py: 0.28,
  minWidth: 0,
  height: 'auto',
  fontSize: '0.74rem',
  color: isLight ? '#0f5f6f' : '#b8c4d8',
  border: isLight ? '1px solid rgba(15, 95, 111, 0.24)' : '1px solid rgba(184,196,216,0.20)',
  borderRadius: 999,
  bgcolor: isLight ? 'rgba(15, 95, 111, 0.06)' : 'rgba(184,196,216,0.06)',
  textTransform: 'none',
  '&:hover': {
    bgcolor: isLight ? 'rgba(15, 95, 111, 0.10)' : 'rgba(184,196,216,0.10)',
    borderColor: isLight ? 'rgba(15, 95, 111, 0.36)' : 'rgba(184,196,216,0.28)',
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

function highlightPreviewText(text: string, query: string, isLight: boolean, activeOccurrence = -1) {
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

export const Search: React.FC = () => {
  const themeMode = useUIStore((state) => state.themeMode);
  const isLight = themeMode === 'light';
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({ type: 'all', version: 'all' });
  const [advancedFiltersOpen, setAdvancedFiltersOpen] = useState(false);
  const [selectedSectionIds, setSelectedSectionIds] = useState<string[]>([]);
  const [openedDocuments, setOpenedDocuments] = useState<DocumentPreview[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [previewWidth, setPreviewWidth] = useState(420);
  const [previewZoom, setPreviewZoom] = useState(1);
  const [previewSearch, setPreviewSearch] = useState('');
  const [activePreviewSearchMatch, setActivePreviewSearchMatch] = useState(0);
  const [expandedPreviewOpen, setExpandedPreviewOpen] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const knowledgeSections = MOCK_KNOWLEDGE_SECTIONS;

  const activeDocument = openedDocuments.find((doc) => doc.id === activeDocumentId) ?? openedDocuments[0];
  const normalizedPreviewSearch = previewSearch.trim().toLowerCase();
  const previewSearchMatches = activeDocument ? countMatches(activeDocument.fragment, normalizedPreviewSearch) : 0;

  const searchQuery = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchApi.query(query),
    enabled: false,
  });
  const searchResults = Array.isArray(searchQuery.data) ? searchQuery.data : [];
  const filteredResults = searchResults.filter((item: any) => {
    const matchesType = filters.type === 'all' || item.type === filters.type;
    const matchesVersion =
      filters.version === 'all' ||
      (filters.version === 'actual' && !String(item.version ?? '').toLowerCase().includes('архив')) ||
      (filters.version === 'archive' && String(item.version ?? '').toLowerCase().includes('архив'));
    const matchesSection =
      selectedSectionIds.length === 0 ||
      selectedSectionIds.some((sectionId) => {
        const section = knowledgeSections.find((entry) => entry.id === sectionId);
        return section ? item.section === section.title : false;
      });

    return matchesType && matchesVersion && matchesSection;
  });
  const hasNoResults =
    searchQuery.isFetched &&
    !searchQuery.isError &&
    filteredResults.length === 0;

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

  useEffect(() => {
    setActivePreviewSearchMatch(0);
  }, [activeDocument?.id, normalizedPreviewSearch]);

  const handleSearch = () => {
    if (query.trim()) {
      void searchQuery.refetch();
    }
  };

  const toggleSectionFilter = (sectionId: string) => {
    setSelectedSectionIds((current) =>
      current.includes(sectionId) ? current.filter((id) => id !== sectionId) : [...current, sectionId],
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
            variant="outlined"
            sx={{
              p: 1.5,
              mb: 2,
              borderRadius: 3,
              bgcolor: 'rgba(22, 23, 27, 0.72)',
              border: '1.5px solid rgba(198, 216, 240, 0.34)',
              boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
            }}
          >
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ alignItems: { md: 'center' } }}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 190 }}>
                <Database size={17} color={isLight ? '#0f5f6f' : '#98d9d8'} />
                <Box>
                  <Typography sx={{ fontSize: '0.86rem', fontWeight: 560 }}>Поиск по базе знаний</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Разделы для сужения выдачи
                  </Typography>
                </Box>
              </Stack>
              <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                {knowledgeSections.map((section) => (
                  <Chip
                    key={section.id}
                    size="small"
                    label={`${section.title}: ${section.documents}`}
                    variant={selectedSectionIds.includes(section.id) ? 'filled' : 'outlined'}
                    onClick={() => toggleSectionFilter(section.id)}
                    sx={{
                      cursor: 'pointer',
                      borderColor: isLight ? 'rgba(15,95,111,0.20)' : 'rgba(152,217,216,0.22)',
                      color: isLight ? '#0f5f6f' : '#cfe7e7',
                      bgcolor: selectedSectionIds.includes(section.id)
                        ? isLight
                          ? '#e0f2fe'
                          : 'rgba(152,217,216,0.14)'
                        : isLight
                          ? 'rgba(15,95,111,0.045)'
                          : 'rgba(152,217,216,0.045)',
                    }}
                  />
                ))}
              </Stack>
            </Stack>
          </Paper>

          <Paper
            sx={{
              p: 3,
              mb: 3,
              borderRadius: 3,
              bgcolor: 'rgba(22, 23, 27, 0.72)',
              border: '1.5px solid rgba(198, 216, 240, 0.34)',
              boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
            }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box sx={{ display: 'flex', gap: 1.2, alignItems: 'stretch' }}>
                <TextField
                  size="small"
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
                  sx={{
                    '& .MuiInputBase-root': {
                      minHeight: 40,
                    },
                  }}
                />
                <Button className="app-action-button" variant="contained" onClick={handleSearch} disableElevation sx={{ minWidth: 108 }}>
                  Найти
                </Button>
                <Button
                  className="app-action-button"
                  variant="outlined"
                  onClick={() => {
                    setQuery('');
                    setFilters({ type: 'all', version: 'all' });
                    setSelectedSectionIds([]);
                  }}
                  sx={{ minWidth: 108 }}
                >
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
                <Button
                  className="app-action-button"
                  startIcon={<Filter size={16} />}
                  size="small"
                  onClick={() => setAdvancedFiltersOpen((open) => !open)}
                  sx={{ ml: 'auto' }}
                >
                  Расширенные фильтры
                </Button>
              </Box>

              <Collapse in={advancedFiltersOpen} timeout={180} unmountOnExit>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 1.4,
                    borderRadius: 2.5,
                    bgcolor: isLight ? 'rgba(248,250,252,0.72)' : 'rgba(8, 12, 18, 0.32)',
                    borderColor: isLight ? 'rgba(15,23,42,0.12)' : 'rgba(198,216,240,0.18)',
                  }}
                >
                  <Stack spacing={1}>
                    <Typography variant="caption" color="text.secondary">
                      Дополнительное сужение выдачи по разделам базы знаний
                    </Typography>
                    <Stack direction="row" spacing={0.8} useFlexGap sx={{ flexWrap: 'wrap' }}>
                      {knowledgeSections.map((section) => {
                        const selected = selectedSectionIds.includes(section.id);

                        return (
                          <Chip
                            key={section.id}
                            size="small"
                            label={section.title}
                            variant={selected ? 'filled' : 'outlined'}
                            onClick={() => toggleSectionFilter(section.id)}
                            onDelete={selected ? () => toggleSectionFilter(section.id) : undefined}
                            sx={{ cursor: 'pointer' }}
                          />
                        );
                      })}
                    </Stack>
                  </Stack>
                </Paper>
              </Collapse>
            </Box>
          </Paper>

          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {searchQuery.isError
                ? 'Поиск недоступен'
                : searchQuery.data
                  ? `Найдено результатов: ${filteredResults.length}`
                  : 'Готов к поиску'}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {searchQuery.isLoading && (
              <Typography sx={{ textAlign: 'center', py: 3 }} color="text.secondary">
                Выполнение поиска...
              </Typography>
            )}

            {searchQuery.isError && (
              <Alert severity="error" variant="outlined" sx={{ borderRadius: 2.5 }}>
                Серверная часть недоступна. Подключите систему или переключитесь в демонстрационный режим.
              </Alert>
            )}

            {hasNoResults && (
              <Alert severity="info" variant="outlined" sx={{ borderRadius: 2.5 }}>
                По запросу ничего не найдено. Случайный документ не подставляется: уточните формулировку, проект, раздел или документ.
              </Alert>
            )}

            {searchQuery.data && filteredResults.map((item: any, idx: number) => (
              <Paper
                key={idx}
                variant="outlined"
                sx={{
                  p: 2.5,
                  borderRadius: 3,
                  bgcolor: 'rgba(22, 23, 27, 0.64)',
                  borderColor: 'rgba(198, 216, 240, 0.32)',
                  borderWidth: 1.5,
                  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.035)',
                  '&:hover': { borderColor: 'rgba(152, 217, 216, 0.54)', bgcolor: 'rgba(22, 23, 27, 0.84)' },
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
                    <Button
                      variant="text"
                      className="source-link-button"
                      startIcon={<FileText size={14} />}
                      onClick={() => openDocument(item, idx)}
                      sx={previewLinkButtonSx(isLight)}
                    >
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
            borderLeft: isLight ? '1px solid rgba(15,23,42,0.14)' : '1px solid rgba(255,255,255,0.10)',
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
              '&:hover': { bgcolor: 'rgba(199,155,99,0.18)' },
            }}
          />

          <Box sx={{ p: 1.5, borderBottom: isLight ? '1px solid rgba(15,23,42,0.12)' : '1px solid rgba(255,255,255,0.08)' }}>
            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
              {openedDocuments.map((doc) => (
                <Chip
                  key={doc.id}
                  size="small"
                  label={`Страница ${doc.page}`}
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
            <Box className="preview-scroll-panel" sx={{ overflow: 'auto', flexGrow: 1 }}>
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
                  <Stack direction="row" spacing={0.7} sx={{ alignItems: 'center' }}>
                    <Button
                      variant="text"
                      size="small"
                      className="source-link-button"
                      startIcon={<Download size={14} />}
                      title={activeDocument.name}
                      onClick={() =>
                        downloadPreviewFile(
                          activeDocument.name,
                          `${activeDocument.name}\n${activeDocument.section}\nСтраница ${activeDocument.page}\n\n${activeDocument.fragment}`,
                        )
                      }
                      sx={{
                        ...previewLinkButtonSx(isLight),
                        justifyContent: 'flex-start',
                        textAlign: 'left',
                        flex: 1,
                        minWidth: 0,
                      }}
                    >
                      <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {activeDocument.name}
                      </Box>
                    </Button>
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
                    slotProps={{
                      input: {
                        startAdornment: <SearchIcon size={15} style={{ marginRight: 8, opacity: 0.62 }} />,
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
              <Stack
                spacing={1.5}
                sx={{
                  width: `${100 / previewZoom}%`,
                  transform: `scale(${previewZoom})`,
                  transformOrigin: 'top left',
                  transition: 'transform 160ms ease, width 160ms ease',
                }}
              >
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
                            <Box component="td" sx={{ border: '1px solid #c8d8c8', p: 1, fontSize: 12 }}>
                              {row % 3 === 0
                                ? highlightPreviewText(activeDocument.fragment, normalizedPreviewSearch, isLight, activePreviewSearchMatch)
                                : 'Значение из спецификации'}
                            </Box>
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
                      {highlightPreviewText(activeDocument.fragment, normalizedPreviewSearch, isLight, activePreviewSearchMatch)}
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
                      Оригинал страницы
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
                        {highlightPreviewText(activeDocument.fragment, normalizedPreviewSearch, isLight, activePreviewSearchMatch)}
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
                          Это отдельная страница исходного документа. В рабочем режиме здесь будет открываться оригинальный
                          файл или подготовленное изображение страницы, а панель сохранит прокрутку, масштабирование по ширине,
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

      <Dialog
        open={expandedPreviewOpen && Boolean(activeDocument)}
        onClose={() => setExpandedPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        {activeDocument && (
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
                <FileText size={18} color={isLight ? '#0284c7' : '#98d9d8'} />
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography title={activeDocument.name} sx={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {activeDocument.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Страница {activeDocument.page} · {activeDocument.section}
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
                      startAdornment: <SearchIcon size={15} style={{ marginRight: 8, opacity: 0.62 }} />,
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
                  minHeight: activeDocument.type === 'PDF' ? 720 : 560,
                  mx: 'auto',
                  p: 3.2,
                  borderRadius: 2,
                  bgcolor: activeDocument.type === 'DWG' ? '#111820' : activeDocument.type === 'XLSX' ? '#f7fbf6' : '#f4f1e8',
                  color: activeDocument.type === 'DWG' ? '#d8f0ff' : '#242424',
                  borderColor: activeDocument.type === 'DWG' ? 'rgba(145,184,255,0.45)' : '#d2cec2',
                  boxShadow: '0 22px 70px rgba(15, 23, 42, 0.20)',
                }}
              >
                <Typography variant="caption" sx={{ color: activeDocument.type === 'DWG' ? '#91b8ff' : '#777' }}>
                  {activeDocument.type} · Страница {activeDocument.page}
                </Typography>
                <Typography variant="h6" sx={{ mt: 1, mb: 1.2, color: activeDocument.type === 'DWG' ? '#d8f0ff' : '#1f1f1f', fontFamily: 'Georgia, serif' }}>
                  {activeDocument.section}
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
                    {highlightPreviewText(activeDocument.fragment, normalizedPreviewSearch, isLight, activePreviewSearchMatch)}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ mt: 2.4, lineHeight: 1.8, color: activeDocument.type === 'DWG' ? '#b9d8ff' : '#555' }}>
                  В рабочем режиме здесь будет отображаться оригинальный источник или подготовленное превью в формате,
                  который отдает контур базы знаний.
                </Typography>
              </Paper>
            </Box>
          </Box>
        )}
      </Dialog>
    </Box>
  );
};
