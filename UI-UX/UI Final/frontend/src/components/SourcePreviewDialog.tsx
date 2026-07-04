import React from 'react';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
} from '@mui/material';
import { ExternalLink, FileText } from 'lucide-react';

type Citation = {
  id: string;
  document: string;
  section: string;
  page: number;
  text: string;
  version: string;
  documentUrl?: string;
  pagePreviewUrl?: string;
};

interface SourcePreviewDialogProps {
  open: boolean;
  onClose: () => void;
  citation: Citation | null;
}

export const SourcePreviewDialog: React.FC<SourcePreviewDialogProps> = ({ open, onClose, citation }) => {
  if (!citation) return null;

  const hasImage = Boolean(citation.pagePreviewUrl);
  const hasDocument = Boolean(citation.documentUrl);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>Просмотр источника</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="h6" sx={{ fontSize: 18 }}>
                {citation.document}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {citation.section}
              </Typography>
            </Box>

            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
              <Chip label={`Стр. ${citation.page}`} variant="outlined" />
              <Chip label={citation.version} variant="outlined" />
              {hasDocument && <Chip label="PDF" variant="outlined" color="primary" size="small" />}
            </Stack>
          </Stack>

          <Divider />

          {/* Изображение страницы (если доступно) */}
          {hasImage && (
            <Box
              sx={{
                borderRadius: 2,
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                justifyContent: 'center',
                bgcolor: '#fff',
                maxHeight: '65vh',
              }}
            >
              <img
                src={citation.pagePreviewUrl}
                alt={`Страница ${citation.page} документа`}
                style={{ maxWidth: '100%', maxHeight: '65vh', objectFit: 'contain' }}
              />
            </Box>
          )}

          {/* PDF через iframe (если нет изображения, но есть URL документа) */}
          {!hasImage && hasDocument && (
            <Box
              sx={{
                borderRadius: 2,
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.08)',
                bgcolor: '#fff',
                height: '65vh',
              }}
            >
              <iframe
                src={citation.documentUrl}
                title="PDF документ"
                style={{ width: '100%', height: '100%', border: 'none' }}
              />
            </Box>
          )}

          {/* Текст (показываем всегда) */}
          <Box
            sx={{
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 2,
              p: 2,
              bgcolor: 'rgba(255,255,255,0.02)',
            }}
          >
            <Stack spacing={1.5}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <FileText size={18} />
                <Typography variant="subtitle2" color="primary">
                  {hasImage || hasDocument ? 'Текст фрагмента' : 'Пример страницы источника'}
                </Typography>
              </Stack>

              <Box
                sx={{
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.08)',
                  bgcolor: '#0f1217',
                  p: 3,
                  minHeight: 160,
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  Страница {citation.page}
                </Typography>
                <Typography variant="body2" sx={{ mt: 2, lineHeight: 1.8, color: 'text.primary' }}>
                  {citation.text}
                </Typography>
              </Box>
            </Stack>
          </Box>

          <Typography variant="body2" color="text.secondary">
            Предпросмотр источника показывает документ, страницу и найденный фрагмент, чтобы пользователь мог быстро
            перейти к первоисточнику.
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Закрыть</Button>
        <Button
          variant="contained"
          endIcon={<ExternalLink size={16} />}
          onClick={() => {
            if (citation.documentUrl) {
              window.open(citation.documentUrl, '_blank', 'noopener,noreferrer');
            }
          }}
          disabled={!citation.documentUrl}
        >
          Открыть PDF
        </Button>
      </DialogActions>
    </Dialog>
  );
};
