import { ThemeProvider, CssBaseline, Box, Typography, Chip, Stack } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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
  checks: 'Сверка',
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
  const { activeTab, apiStatus } = useUIStore();

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
          <ModeSwitcher />

          <Box
            component="main"
            sx={{
              flexGrow: 1,
              minWidth: 0,
              display: 'flex',
              flexDirection: 'column',
              p: 2,
              pt: 2.1,
              pl: 2.6,
              boxShadow: 'inset 1px 0 0 rgba(121, 191, 193, 0.08)',
            }}
          >
            <Box
              sx={{
                px: { xs: 1.8, md: 2.3 },
                py: 0.95,
                mb: 1.5,
                mt: 0,
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
                  sx={{ bgcolor: 'rgba(255,255,255,0.03)' }}
                />
              </Stack>
            </Box>

            <Box
              sx={{
                flexGrow: 1,
                overflowY: 'auto',
                position: 'relative',
                border: activeTab === 'chat' ? 'none' : '1px solid',
                borderColor: 'rgba(255,255,255,0.10)',
                borderRadius: activeTab === 'chat' ? 0 : 3,
                bgcolor: activeTab === 'chat' ? 'transparent' : 'rgba(12, 13, 17, 0.62)',
                boxShadow: activeTab === 'chat' ? 'none' : 'inset 0 1px 0 rgba(255,255,255,0.03)',
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
