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
};

interface SourcePreviewDialogProps {
  open: boolean;
  onClose: () => void;
  citation: Citation | null;
}

export const SourcePreviewDialog: React.FC<SourcePreviewDialogProps> = ({ open, onClose, citation }) => {
  if (!citation) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
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
            </Stack>
          </Stack>

          <Divider />

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
                  Пример страницы источника
                </Typography>
              </Stack>

              <Box
                sx={{
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.08)',
                  bgcolor: '#0f1217',
                  p: 3,
                  minHeight: 280,
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
            Это demo-preview источника: здесь показывается пример документа, страницы и фрагмента, чтобы пользователь
            понимал, как будет выглядеть переход к первоисточнику.
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Закрыть</Button>
        <Button variant="contained" endIcon={<ExternalLink size={16} />}>
          Открыть документ
        </Button>
      </DialogActions>
    </Dialog>
  );
};
