import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import { Anchor, LogIn, Moon, Sun, Waves } from 'lucide-react';
import { useUIStore } from '../store/uiStore';

export const LoginScreen: React.FC = () => {
  const { adminUsers, login, setThemeMode, themeMode } = useUIStore();
  const [selectedUserId, setSelectedUserId] = useState(adminUsers[0]?.id ?? '');
  const isLight = themeMode === 'light';

  const selectedUser = adminUsers.find((user) => user.id === selectedUserId) ?? adminUsers[0];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        p: 3,
        background: isLight
          ? 'radial-gradient(circle at 18% 8%, rgba(14, 116, 144, 0.12), transparent 30%), linear-gradient(135deg, #f3f6f8 0%, #e7edf2 100%)'
          : 'radial-gradient(circle at 22% 0%, rgba(112,161,255,0.12), transparent 32%), linear-gradient(135deg, #0b0c0e 0%, #11131a 48%, #0b0c0e 100%)',
      }}
    >
      <Paper
        variant="outlined"
        sx={{
          width: 'min(520px, 100%)',
          p: { xs: 3, md: 4 },
          borderRadius: 4,
          bgcolor: isLight ? 'rgba(255,255,255,0.78)' : 'rgba(16, 17, 21, 0.92)',
          borderColor: isLight ? 'rgba(14, 116, 144, 0.20)' : 'rgba(198, 216, 240, 0.34)',
          boxShadow: isLight
            ? '0 24px 70px rgba(15, 23, 42, 0.12)'
            : '0 28px 80px rgba(0,0,0,0.36), inset 0 1px 0 rgba(255,255,255,0.06)',
        }}
      >
        <Stack spacing={3}>
          <Stack direction="row" spacing={1.8} sx={{ alignItems: 'center' }}>
            <Box
              sx={{
                width: 62,
                height: 62,
                borderRadius: '20px',
                display: 'grid',
                placeItems: 'center',
                color: '#dfeeff',
                background:
                  'linear-gradient(145deg, rgba(18, 67, 75, 0.95), rgba(11, 28, 34, 0.92) 74%, rgba(165, 140, 255, 0.20))',
                border: '1px solid rgba(132, 210, 213, 0.22)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <Waves size={34} style={{ position: 'absolute', bottom: 6, opacity: 0.45, color: '#78c1c1' }} />
              <Anchor size={27} style={{ position: 'relative', zIndex: 1, color: '#98d9d8' }} />
            </Box>
            <Box>
              <Typography
                sx={{
                  color: '#98d9d8',
                  fontSize: '1.55rem',
                  lineHeight: 1.05,
                  fontWeight: 700,
                  fontFamily: '"Trebuchet MS", "Segoe UI", sans-serif',
                }}
              >
                AI ассистент
              </Typography>
              <Typography sx={{ mt: 0.5, color: isLight ? '#0f4f5c' : 'rgba(209, 225, 225, 0.72)' }}>
                вход в рабочий контур
              </Typography>
            </Box>
          </Stack>

          <Box>
            <Typography sx={{ mb: 1, fontWeight: 560 }}>Выберите пользователя</Typography>
            <FormControl fullWidth size="small">
              <InputLabel>Профиль</InputLabel>
              <Select
                label="Профиль"
                value={selectedUserId}
                onChange={(event) => setSelectedUserId(event.target.value)}
                renderValue={(value) => {
                  const user = adminUsers.find((item) => item.id === value) ?? selectedUser;

                  return (
                    <Box sx={{ minWidth: 0 }}>
                      <Typography sx={{ display: 'block', fontSize: '0.92rem', lineHeight: 1.15, fontWeight: 560 }}>
                        {user?.name}
                      </Typography>
                      <Typography
                        component="span"
                        sx={{
                          display: 'block',
                          mt: 0.15,
                          color: 'text.secondary',
                          fontSize: '0.76rem',
                          lineHeight: 1.15,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {user?.position} · {user?.role}
                      </Typography>
                    </Box>
                  );
                }}
                sx={{
                  minHeight: 58,
                  '& .MuiSelect-select': {
                    py: 0.75,
                    display: 'flex',
                    alignItems: 'center',
                  },
                }}
              >
                {adminUsers.map((user) => (
                  <MenuItem key={user.id} value={user.id}>
                    <Box>
                      <Typography sx={{ fontSize: '0.9rem', lineHeight: 1.2 }}>{user.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.position} · {user.role}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {selectedUser && (
              <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
                После входа будут доступны разделы согласно роли: {selectedUser.role}.
              </Typography>
            )}
          </Box>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2}>
            <Button
              fullWidth
              className="app-action-button"
              variant="contained"
              startIcon={<LogIn size={17} />}
              onClick={() => login(selectedUserId)}
              disabled={!selectedUserId}
            >
              Войти
            </Button>
            <Button
              variant="outlined"
              startIcon={themeMode === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
              onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
              sx={{ minWidth: 132 }}
            >
              {themeMode === 'dark' ? 'Тёмная' : 'Светлая'}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
};
