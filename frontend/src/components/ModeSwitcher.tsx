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
} from 'lucide-react';
import { useUIStore, AppTab } from '../store/uiStore';

const NAV_ITEMS: Array<{ value: AppTab; label: string; icon: React.ReactNode }> = [
  { value: 'chat', label: 'Чат', icon: <MessageSquare size={18} /> },
  { value: 'search', label: 'Поиск', icon: <Search size={18} /> },
  { value: 'documents', label: 'Реестр', icon: <FileText size={18} /> },
  { value: 'checks', label: 'Проверка', icon: <CheckCircle2 size={18} /> },
  { value: 'history', label: 'История', icon: <History size={18} /> },
  { value: 'qa', label: 'QA', icon: <BarChart3 size={18} /> },
];

export const ModeSwitcher: React.FC = () => {
  const { activeTab, setActiveTab, setVideoGuideOpen } = useUIStore();

  return (
    <Box
      sx={{
        width: 292,
        flexShrink: 0,
        borderRight: '1px solid rgba(121, 191, 193, 0.28)',
        bgcolor: 'rgba(16, 17, 21, 0.96)',
        display: 'flex',
        flexDirection: 'column',
        p: 2,
        gap: 2.5,
        boxShadow: '14px 0 40px rgba(0,0,0,0.20), inset -1px 0 0 rgba(178, 209, 238, 0.10)',
      }}
    >
      <Box
        sx={{
          p: 2.2,
          borderRadius: 3.2,
          border: '1px solid rgba(92, 168, 178, 0.26)',
          background:
            'linear-gradient(160deg, rgba(9, 28, 33, 0.98), rgba(13, 52, 59, 0.96) 52%, rgba(9, 22, 28, 0.98) 100%)',
          boxShadow: '0 20px 42px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.10)',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 92% 10%, rgba(121, 203, 198, 0.22), transparent 24%), radial-gradient(circle at 10% 100%, rgba(165, 140, 255, 0.18), transparent 28%)',
            pointerEvents: 'none',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            left: 16,
            right: 16,
            bottom: 14,
            height: 1,
            background: 'linear-gradient(90deg, transparent, rgba(208, 171, 112, 0.42), transparent)',
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

          <Box sx={{ minWidth: 0 }}>
            <Typography
              sx={{
                fontSize: '1.32rem',
                lineHeight: 1.08,
                fontWeight: 800,
                letterSpacing: '0.01em',
                color: '#98d9d8',
              }}
            >
              AI ассистент
            </Typography>

            <Typography
              variant="caption"
              sx={{
                display: 'block',
                mt: 0.8,
                color: 'rgba(209, 225, 225, 0.72)',
              }}
            >
              инженерные документы и нормативная база
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
            color: 'rgba(198, 208, 222, 0.84)',
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
        {NAV_ITEMS.map((item) => {
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
                color: isActive ? '#edf2ea' : 'text.primary',
                bgcolor: isActive ? 'rgba(108, 124, 108, 0.22)' : 'transparent',
                border: '1px solid',
                borderColor: isActive ? 'rgba(155, 169, 147, 0.34)' : 'transparent',
                '&:hover': {
                  bgcolor: isActive ? 'rgba(108, 124, 108, 0.28)' : 'rgba(255,255,255,0.05)',
                },
              }}
            >
              {item.label}
            </Button>
          );
        })}
      </Stack>

      <Box sx={{ mt: 'auto', pt: 2, borderTop: '1px solid rgba(157, 205, 225, 0.12)' }}>
        <Button
          variant="outlined"
          fullWidth
          startIcon={<Video size={16} />}
          onClick={() => setVideoGuideOpen(true)}
          sx={{ borderColor: 'rgba(124, 165, 214, 0.30)', color: '#d9b173' }}
        >
          Видеоинструкция
        </Button>
      </Box>
    </Box>
  );
};
