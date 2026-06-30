import React, { useState } from 'react';
import { Alert, Box, Typography, Button, TextField, IconButton, Tooltip } from '@mui/material';
import { ThumbsUp, ThumbsDown, Send } from 'lucide-react';
import { feedbackApi } from '../utils/http';

interface FeedbackProps {
  messageId?: string;
  sessionId?: string;
}

export const Feedback: React.FC<FeedbackProps> = ({ messageId, sessionId }) => {
  const [useful, setUseful] = useState<boolean | null>(null);
  const [comment, setComment] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const toggleUseful = (nextValue: boolean) => {
    if (useful === nextValue) {
      setUseful(null);
      setComment('');
      setError('');
      return;
    }

    setUseful(nextValue);
    setError('');
  };

  const handleSend = async () => {
    if (useful === null) return;
    setError('');

    try {
      await feedbackApi.send({ useful, comment, messageId, sessionId });
      setSent(true);
    } catch (sendError: any) {
      setError(sendError?.message ?? 'Не удалось отправить отзыв.');
    }
  };

  if (sent) {
    return (
      <Box sx={{ py: 1 }}>
        <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          Спасибо за ваш отзыв. Это помогает улучшать ответы.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 1, borderTop: 1, borderColor: 'rgba(255, 255, 255, 0.05)' }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>
            Полезен ли был этот ответ?
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Полезно">
              <IconButton
                aria-label="Оценить ответ положительно"
                size="small"
                onClick={() => toggleUseful(true)}
                sx={{
                  color: useful === true ? 'success.main' : 'inherit',
                  bgcolor: useful === true ? 'rgba(46, 125, 50, 0.1)' : 'transparent',
                }}
              >
                <ThumbsUp size={16} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Неполезно">
              <IconButton
                aria-label="Оценить ответ отрицательно"
                size="small"
                onClick={() => toggleUseful(false)}
                sx={{
                  color: useful === false ? 'error.main' : 'inherit',
                  bgcolor: useful === false ? 'rgba(211, 47, 47, 0.1)' : 'transparent',
                }}
              >
                <ThumbsDown size={16} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {useful !== null && (
          <>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Что можно улучшить?"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'rgba(255, 255, 255, 0.03)',
                    fontSize: '0.8rem',
                  },
                }}
              />
              <Button
                variant="outlined"
                size="small"
                onClick={handleSend}
                startIcon={<Send size={14} />}
              >
                Отправить
              </Button>
            </Box>
            {error && (
              <Alert severity="warning" variant="outlined" sx={{ borderRadius: 2 }}>
                {error}
              </Alert>
            )}
          </>
        )}
      </Box>
    </Box>
  );
};
