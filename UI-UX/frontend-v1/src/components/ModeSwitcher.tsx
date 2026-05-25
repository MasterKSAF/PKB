import React from 'react';
import { Box, Typography, Button, Stack } from '@mui/material';
import {
  Anchor,
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
} from 'lucide-react';
import { useUIStore, AppTab } from '../store/uiStore';
import { ROLE_TAB_ACCESS } from '../utils/access';

const NAV_ITEMS: Array<{ value: AppTab; label: string; icon: React.ReactNode }> = [
  { value: 'chat', label: 'Чат', icon: <MessageSquare size={18} /> },
  { value: 'search', label: 'Поиск', icon: <Search size={18} /> },
  { value: 'documents', label: 'Реестр', icon: <FileText size={18} /> },
  { value: 'checks', label: 'Проверка', icon: <CheckCircle2 size={18} /> },
  { value: 'history', label: 'История', icon: <History size={18} /> },
  { value: 'qa', label: 'QA', icon: <BarChart3 size={18} /> },
  { value: 'admin', label: 'Администрирование', icon: <Settings size={18} /> },
];

export const ModeSwitcher: React.FC = () => {
  const { activeTab, currentRole, themeMode, setActiveTab, setVideoGuideOpen, setFocusMode } = useUIStore();
  const isLight = themeMode === 'light';
  const availableTabs = ROLE_TAB_ACCESS[currentRole];
  const visibleNavItems = NAV_ITEMS.filter((item) => availableTabs.includes(item.value));

  return (
    <Box
      sx={{
        width: 292,
        flexShrink: 0,
        borderRight: isLight ? '2px solid rgba(14, 116, 144, 0.26)' : '2px solid rgba(198, 216, 240, 0.40)',
        bgcolor: isLight ? '#eef3f7' : 'rgba(16, 17, 21, 0.96)',
        display: 'flex',
        flexDirection: 'column',
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
              background:
                'linear-gradient(145deg, rgba(18, 67, 75, 0.95), rgba(11, 28, 34, 0.92) 74%, rgba(165, 140, 255, 0.20))',
              border: '1px solid rgba(132, 210, 213, 0.22)',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.12), 0 8px 22px rgba(0,0,0,0.24)',
            }}
          >
            <Waves size={34} style={{ position: 'absolute', bottom: 6, opacity: 0.45, color: '#78c1c1' }} />
            <Anchor size={26} style={{ position: 'relative', zIndex: 1, color: '#98d9d8' }} />
          </Box>

          <Box sx={{ minWidth: 0, pt: 0.45 }}>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                px: 1.15,
                py: 0.55,
                borderRadius: 1.7,
                background:
                  'linear-gradient(145deg, rgba(7, 20, 24, 0.82), rgba(18, 32, 38, 0.72) 62%, rgba(35, 49, 56, 0.56) 100%)',
                border: '1px solid rgba(157, 219, 217, 0.18)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.08), 0 10px 18px rgba(0,0,0,0.18)',
              }}
            >
              <Typography
                sx={{
                  fontSize: '1.24rem',
                  lineHeight: 1.04,
                  fontWeight: 700,
                  letterSpacing: '0.015em',
                  color: '#98d9d8',
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
                color: isLight ? '#0f4f5c' : 'rgba(209, 225, 225, 0.72)',
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
            <Button
              key={item.value}
              variant={isActive ? 'contained' : 'text'}
              color={isActive ? 'primary' : 'inherit'}
              startIcon={item.icon}
              onClick={() => setActiveTab(item.value)}
              sx={{
                justifyContent: 'flex-start',
                px: 1.6,
                py: 1.18,
                borderRadius: 2.4,
                color: isActive ? (isLight ? '#0f172a' : '#edf2ea') : 'text.primary',
                bgcolor: isActive
                  ? isLight
                    ? 'rgba(14, 116, 144, 0.12)'
                    : 'rgba(108, 124, 108, 0.22)'
                  : 'transparent',
                border: '1px solid',
                borderColor: isActive
                  ? isLight
                    ? 'rgba(14, 116, 144, 0.24)'
                    : 'rgba(155, 169, 147, 0.34)'
                  : 'transparent',
                '&:hover': {
                  bgcolor: isActive
                    ? isLight
                      ? 'rgba(14, 116, 144, 0.16)'
                      : 'rgba(108, 124, 108, 0.28)'
                    : isLight
                      ? 'rgba(15, 23, 42, 0.05)'
                      : 'rgba(255,255,255,0.05)',
                },
              }}
            >
              {item.label}
            </Button>
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
    </Box>
  );
};
