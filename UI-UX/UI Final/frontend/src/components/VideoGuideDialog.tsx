import React from 'react';
import { Alert, Box, Dialog, IconButton, Stack, Typography } from '@mui/material';
import { X } from 'lucide-react';
import { useUIStore } from '../store/uiStore';

const VIDEO_GUIDE_URL = String(import.meta.env.VITE_VIDEO_GUIDE_URL ?? '').trim();

export const VideoGuideDialog: React.FC = () => {
  const { themeMode, videoGuideOpen, setVideoGuideOpen } = useUIStore();
  const isLight = themeMode === 'light';

  return (
    <Dialog
      fullScreen
      open={videoGuideOpen}
      onClose={() => setVideoGuideOpen(false)}
      slotProps={{
        paper: {
          sx: {
            bgcolor: isLight ? '#eef2f5' : '#090b0e',
          },
        },
      }}
    >
      <Stack
        direction="row"
        spacing={2}
        sx={{
          minHeight: 64,
          px: { xs: 2, md: 3 },
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid',
          borderColor: isLight ? 'rgba(15,23,42,0.14)' : 'rgba(198,216,240,0.16)',
        }}
      >
        <Box>
          <Typography sx={{ fontWeight: 600 }}>Видеоинструкция</Typography>
          <Typography variant="caption" color="text.secondary">
            Демонстрация работы AI Assistant PKB
          </Typography>
        </Box>
        <IconButton aria-label="Закрыть видеоинструкцию" onClick={() => setVideoGuideOpen(false)}>
          <X size={22} />
        </IconButton>
      </Stack>

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          display: 'grid',
          placeItems: 'center',
          p: { xs: 2, md: 3 },
        }}
      >
        {VIDEO_GUIDE_URL ? (
          <Box
            component="video"
            src={VIDEO_GUIDE_URL}
            controls
            preload="metadata"
            sx={{
              display: 'block',
              width: '100%',
              height: 'calc(100vh - 112px)',
              objectFit: 'contain',
              bgcolor: '#000',
              borderRadius: 2,
            }}
          >
            Ваш браузер не поддерживает воспроизведение видео.
          </Box>
        ) : (
          <Alert severity="info" variant="outlined" sx={{ width: 'min(680px, 100%)' }}>
            Видеоинструкция пока не опубликована. Укажите адрес файла в переменной `VITE_VIDEO_GUIDE_URL`.
          </Alert>
        )}
      </Box>
    </Dialog>
  );
};
