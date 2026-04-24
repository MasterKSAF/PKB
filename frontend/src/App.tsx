import { ThemeProvider, CssBaseline, Box, Typography, Chip, Stack, Button, Paper } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Focus, Minimize2 } from 'lucide-react';
import { theme } from './theme';
import { useUIStore } from './store/uiStore';
import { ModeSwitcher } from './components/ModeSwitcher';
import { Chat } from './components/Chat';
import { Search } from './components/Search';
import { DocumentRegistry } from './components/DocumentRegistry';
import { ChecksPanel } from './components/ChecksPanel';
import { Monitor } from './components/Monitor';
import { History } from './components/History';
import { VideoGuideDialog } from './components/VideoGuideDialog';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const TAB_TITLES = {
  chat: 'Чат инженера',
  search: 'Поиск',
  documents: 'Реестр',
  checks: 'Проверка на соответствие требований НСИ',
  history: 'История',
  qa: 'QA',
} as const;

const TAB_DESCRIPTIONS = {
  chat: '',
  search: '',
  documents: '',
  checks: '',
  history: '',
  qa: '',
} as const;

export default function App() {
  const { activeTab, apiStatus, focusMode, setFocusMode } = useUIStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <Chat />;
      case 'search':
        return <Search />;
      case 'documents':
        return <DocumentRegistry />;
      case 'checks':
        return <ChecksPanel />;
      case 'history':
        return <History />;
      case 'qa':
        return <Monitor />;
      default:
        return <Chat />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            height: '100vh',
            overflow: 'hidden',
            bgcolor: 'background.default',
            background:
              'radial-gradient(circle at 25% 0%, rgba(112,161,255,0.12), transparent 32%), linear-gradient(135deg, #0b0c0e 0%, #11131a 48%, #0b0c0e 100%)',
          }}
        >
          {!focusMode && <ModeSwitcher />}

          <Box
            component="main"
            sx={{
              flexGrow: 1,
              minWidth: 0,
              display: 'flex',
              flexDirection: 'column',
              p: focusMode ? 0 : 2,
              pt: focusMode ? 0 : 1.8,
              pl: focusMode ? 0 : 2.6,
              boxShadow: focusMode ? 'none' : 'inset 1px 0 0 rgba(121, 191, 193, 0.08)',
            }}
          >
            {focusMode && (
              <Box sx={{ px: 3, pt: 2.2, pb: 0.4 }}>
                <Paper
                  variant="outlined"
                  sx={{
                    px: 1.4,
                    py: 1,
                    borderRadius: 2.4,
                    bgcolor: 'rgba(22, 23, 27, 0.82)',
                    borderColor: 'rgba(255,255,255,0.10)',
                  }}
                >
                  <Stack direction="row" spacing={1.2} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                      <Focus size={16} color="#98d9d8" />
                      <Typography sx={{ color: 'rgba(228, 235, 247, 0.9)', fontSize: '0.88rem', fontWeight: 500 }}>
                        Фокус-режим: {TAB_TITLES[activeTab]}
                      </Typography>
                    </Stack>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Minimize2 size={14} />}
                      onClick={() => setFocusMode(false)}
                      sx={{
                        borderColor: 'rgba(184,196,216,0.20)',
                        color: 'rgba(228, 235, 247, 0.88)',
                        textTransform: 'none',
                      }}
                    >
                      Выйти
                    </Button>
                  </Stack>
                </Paper>
              </Box>
            )}

            {!focusMode && (
              <Box
              sx={{
                px: { xs: 1.8, md: 2.3 },
                pt: 0.92,
                pb: 4.1,
                mb: 1.5,
                mt: 0.05,
                border: '1px solid',
                borderColor: 'rgba(255,255,255,0.10)',
                  borderRadius: 3,
                  bgcolor: 'rgba(22, 23, 27, 0.88)',
                  boxShadow: '0 18px 55px rgba(0,0,0,0.20)',
                }}
              >
                <Stack
                  direction={{ xs: 'column', md: 'row' }}
                  spacing={1.5}
                  sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' } }}
                >
                  <Box>
                    <Typography
                      variant="overline"
                      sx={{
                        display: 'block',
                        mb: 0.1,
                        color: 'rgba(198, 208, 222, 0.84)',
                        letterSpacing: '0.16em',
                        fontSize: '0.68rem',
                        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
                      }}
                    >
                      Рабочая область
                    </Typography>
                    <Typography
                      variant="h5"
                      sx={{
                        lineHeight: 1.1,
                        fontSize: { xs: '1.12rem', md: '1.28rem' },
                        fontWeight: 500,
                        color: 'rgba(230, 236, 244, 0.86)',
                        fontFamily: '"Segoe UI Variable Display", "Segoe UI", "Inter", sans-serif',
                      }}
                    >
                      {TAB_TITLES[activeTab]}
                    </Typography>
                    {TAB_DESCRIPTIONS[activeTab] && (
                      <Typography variant="body2" color="text.secondary">
                        {TAB_DESCRIPTIONS[activeTab]}
                      </Typography>
                    )}
                  </Box>

                  <Chip
                    label={
                      apiStatus === 'online'
                        ? 'Система онлайн'
                        : apiStatus === 'offline'
                          ? 'Система офлайн'
                          : 'Демо-режим'
                    }
                    color={apiStatus === 'online' ? 'success' : apiStatus === 'offline' ? 'error' : 'warning'}
                    variant="outlined"
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.03)',
                    }}
                  />
                </Stack>
              </Box>
            )}

            <Box
              sx={{
                flexGrow: 1,
                overflowY: 'auto',
                position: 'relative',
                border: activeTab === 'chat' || focusMode ? 'none' : '1px solid',
                borderColor: 'rgba(255,255,255,0.10)',
                borderRadius: activeTab === 'chat' || focusMode ? 0 : 3,
                bgcolor: activeTab === 'chat' || focusMode ? 'transparent' : 'rgba(12, 13, 17, 0.62)',
                boxShadow: activeTab === 'chat' || focusMode ? 'none' : 'inset 0 1px 0 rgba(255,255,255,0.03)',
              }}
            >
              {renderContent()}
            </Box>
          </Box>
        </Box>
        <VideoGuideDialog />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
