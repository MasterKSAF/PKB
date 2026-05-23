import { useEffect, useMemo } from 'react';
import {
  ThemeProvider,
  CssBaseline,
  Box,
  Typography,
  Chip,
  Stack,
  Button,
  Paper,
} from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Focus, LogOut, Minimize2, Moon, Sun, UserRound } from 'lucide-react';
import { getAppTheme } from './theme';
import { useUIStore } from './store/uiStore';
import { ModeSwitcher } from './components/ModeSwitcher';
import { Chat } from './components/Chat';
import { Search } from './components/Search';
import { DocumentRegistry } from './components/DocumentRegistry';
import { ChecksPanel } from './components/ChecksPanel';
import { Monitor } from './components/Monitor';
import { History } from './components/History';
import { AdminPanel } from './components/AdminPanel';
import { VideoGuideDialog } from './components/VideoGuideDialog';
import { LoginScreen } from './components/LoginScreen';
import { canAccessTab, getFallbackTab, TAB_DESCRIPTIONS, TAB_TITLES, USER_ROLE_BY_LABEL } from './utils/access';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  const {
    activeTab,
    apiStatus,
    adminUsers,
    currentRole,
    currentUserId,
    focusMode,
    isAuthenticated,
    logout,
    themeMode,
    workMode,
    setActiveTab,
    setCurrentRole,
    setFocusMode,
    setThemeMode,
    toggleWorkMode,
  } = useUIStore();
  const appTheme = useMemo(() => getAppTheme(themeMode), [themeMode]);
  const currentUser = adminUsers.find((user) => user.id === currentUserId) ?? adminUsers[0];
  const activeNavHeaderBackground = themeMode === 'dark' ? '#242829' : '#d3e4eb';
  const activeNavHeaderBorder = themeMode === 'dark' ? 'rgba(198, 216, 240, 0.38)' : 'rgba(14, 116, 144, 0.24)';

  useEffect(() => {
    document.body.dataset.pkbTheme = themeMode;
  }, [themeMode]);

  useEffect(() => {
    const userRole = USER_ROLE_BY_LABEL[currentUser.role] ?? 'user';
    if (userRole !== currentRole) {
      setCurrentRole(userRole);
    }
  }, [currentRole, currentUser.role, setCurrentRole]);

  useEffect(() => {
    if (!canAccessTab(currentRole, activeTab)) {
      setActiveTab(getFallbackTab(currentRole));
    }
  }, [activeTab, currentRole, setActiveTab]);

  const renderContent = () => {
    if (!canAccessTab(currentRole, activeTab)) {
      return <Chat />;
    }

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
      case 'admin':
        return <AdminPanel />;
      default:
        return <Chat />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={appTheme}>
        <CssBaseline />
        {!isAuthenticated ? (
          <LoginScreen />
        ) : (
        <Box
          data-pkb-theme={themeMode}
          sx={{
            display: 'flex',
            height: '100vh',
            overflow: 'hidden',
            bgcolor: 'background.default',
            background:
              themeMode === 'dark'
                ? 'radial-gradient(circle at 25% 0%, rgba(112,161,255,0.12), transparent 32%), linear-gradient(135deg, #0b0c0e 0%, #11131a 48%, #0b0c0e 100%)'
                : 'radial-gradient(circle at 24% 0%, rgba(14, 116, 144, 0.10), transparent 34%), radial-gradient(circle at 92% 18%, rgba(202, 138, 4, 0.08), transparent 28%), linear-gradient(135deg, #f3f6f8 0%, #eef3f7 48%, #e7edf2 100%)',
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
              boxShadow:
                focusMode || themeMode === 'light'
                  ? 'none'
                  : 'inset 1px 0 0 rgba(121, 191, 193, 0.08)',
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
                    bgcolor: themeMode === 'dark' ? 'rgba(22, 23, 27, 0.82)' : '#ffffff',
                    borderColor: themeMode === 'dark' ? 'rgba(255,255,255,0.10)' : 'rgba(15,23,42,0.14)',
                  }}
                >
                  <Stack direction="row" spacing={1.2} sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                      <Focus size={16} color={themeMode === 'dark' ? '#98d9d8' : '#2f7476'} />
                      <Typography
                        sx={{
                          color: themeMode === 'dark' ? 'rgba(228, 235, 247, 0.9)' : '#111827',
                          fontSize: '0.88rem',
                          fontWeight: 500,
                        }}
                      >
                        Фокус-режим: {TAB_TITLES[activeTab]}
                      </Typography>
                    </Stack>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Minimize2 size={14} />}
                      onClick={() => setFocusMode(false)}
                      sx={{
                        borderColor: themeMode === 'dark' ? 'rgba(184,196,216,0.20)' : 'rgba(15,23,42,0.18)',
                        color: themeMode === 'dark' ? 'rgba(228, 235, 247, 0.88)' : '#0f5f6f',
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
                className="workspace-header-panel"
                sx={{
                  px: { xs: 1.8, md: 2.3 },
                  pt: 0.92,
                  pb: 4.1,
                  mb: 1.5,
                  mt: 0.05,
                  border: themeMode === 'dark' ? '1.5px solid' : '1px solid',
                  borderColor: activeNavHeaderBorder,
                  borderRadius: 3,
                  backgroundColor: activeNavHeaderBackground,
                  backgroundImage: 'none',
                  boxShadow: themeMode === 'dark' ? 'inset 0 1px 0 rgba(255,255,255,0.045)' : 'none',
                }}
              >
                <Stack
                  direction={{ xs: 'column', md: 'row' }}
                  spacing={1.5}
                  sx={{ justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' } }}
                >
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography
                      variant="overline"
                      sx={{
                        display: 'block',
                        mb: 0.1,
                        color: themeMode === 'dark' ? 'rgba(198, 208, 222, 0.84)' : '#475569',
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
                        color: themeMode === 'dark' ? 'rgba(230, 236, 244, 0.86)' : '#111827',
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

                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{
                      alignItems: 'center',
                      justifyContent: { xs: 'flex-start', md: 'flex-end' },
                      flexWrap: 'wrap',
                    }}
                  >
                    <Paper
                      variant="outlined"
                      sx={{
                        px: 1.2,
                        py: 0.7,
                        minWidth: { xs: 260, md: 330 },
                        borderRadius: 2,
                        bgcolor: themeMode === 'dark' ? 'rgba(8, 12, 18, 0.42)' : '#f8fafc',
                        borderColor:
                          themeMode === 'dark' ? 'rgba(152, 217, 216, 0.22)' : 'rgba(15, 23, 42, 0.18)',
                      }}
                    >
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                        <UserRound size={16} color={themeMode === 'dark' ? '#98d9d8' : '#0f5f6f'} />
                        <Box sx={{ minWidth: 0 }}>
                          <Typography
                            component="span"
                            sx={{
                              display: 'block',
                              color: themeMode === 'dark' ? 'rgba(235, 241, 247, 0.92)' : '#111827',
                              fontSize: '0.82rem',
                              lineHeight: 1.05,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {currentUser.name}
                          </Typography>
                          <Typography
                            component="span"
                            sx={{
                              display: 'block',
                              color: themeMode === 'dark' ? 'rgba(171, 183, 201, 0.76)' : '#475569',
                              fontSize: '0.68rem',
                              lineHeight: 1.1,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {currentUser.position} · {currentUser.role}
                          </Typography>
                        </Box>
                      </Stack>
                    </Paper>

                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={themeMode === 'dark' ? <Moon size={15} /> : <Sun size={15} />}
                      onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
                      sx={{
                        height: 34,
                        px: 1.2,
                        borderColor:
                          themeMode === 'dark' ? 'rgba(124, 165, 214, 0.30)' : 'rgba(15, 23, 42, 0.18)',
                        color: themeMode === 'dark' ? 'rgba(224, 234, 245, 0.88)' : '#0f5f6f',
                      }}
                    >
                      {themeMode === 'dark' ? 'Тёмная' : 'Светлая'}
                    </Button>

                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<LogOut size={15} />}
                      onClick={logout}
                      sx={{
                        height: 34,
                        px: 1.15,
                        borderColor:
                          themeMode === 'dark' ? 'rgba(124, 165, 214, 0.26)' : 'rgba(15, 23, 42, 0.16)',
                        color: themeMode === 'dark' ? 'rgba(224, 234, 245, 0.82)' : '#475569',
                        textTransform: 'none',
                      }}
                    >
                      Выйти
                    </Button>

                    <Chip
                      label={
                        workMode === 'demo'
                          ? 'Демо-режим'
                          : apiStatus === 'online'
                          ? 'Система онлайн'
                          : 'Система офлайн'
                      }
                      color={workMode === 'demo' ? 'warning' : apiStatus === 'online' ? 'success' : 'error'}
                      variant="outlined"
                      onClick={toggleWorkMode}
                      sx={{
                        bgcolor: 'rgba(255,255,255,0.03)',
                        cursor: 'pointer',
                        userSelect: 'none',
                        '&:hover': {
                          filter: 'brightness(1.08)',
                        },
                      }}
                    />
                  </Stack>
                </Stack>
              </Box>
            )}

            <Box
              sx={{
                flexGrow: 1,
                overflowY: 'auto',
                position: 'relative',
                border: 'none',
                borderRadius: 0,
                bgcolor: 'transparent',
                boxShadow: 'none',
              }}
            >
              {renderContent()}
            </Box>
          </Box>
        </Box>
        )}
        <VideoGuideDialog />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
