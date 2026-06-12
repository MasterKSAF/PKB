import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, IconButton, Paper, Stack, TextField, Typography } from '@mui/material';
import { Eye, EyeOff, KeyRound, LogIn, Ship, UserRound } from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { authApi } from '../utils/http';

const DEMO_PASSWORD = 'demo';
const LOGIN_LIMITS = { min: 3, max: 64 };
const PASSWORD_LIMITS = { min: 4, max: 64 };

export const LoginScreen: React.FC = () => {
  const { adminUsers, login, setWorkMode, themeMode, workMode } = useUIStore();
  const isLight = themeMode === 'light';
  const lightLogoBlue = '#0284c7';
  const isDemoMode = workMode === 'demo';
  const [loginValue, setLoginValue] = useState('');
  const [passwordValue, setPasswordValue] = useState(DEMO_PASSWORD);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState('');

  useEffect(() => {
    setPasswordValue(workMode === 'demo' ? DEMO_PASSWORD : '');
    setAuthError('');
  }, [workMode]);

  const trimmedLogin = loginValue.trim();
  const trimmedPassword = passwordValue.trim();
  const loginError = Boolean(trimmedLogin) && (trimmedLogin.length < LOGIN_LIMITS.min || trimmedLogin.length > LOGIN_LIMITS.max);
  const passwordError =
    Boolean(trimmedPassword) && (trimmedPassword.length < PASSWORD_LIMITS.min || trimmedPassword.length > PASSWORD_LIMITS.max);
  const canSubmit = Boolean(trimmedLogin && trimmedPassword) && !loginError && !passwordError && !isSubmitting;

  const handleWorkModeChange = (mode: 'demo' | 'prod') => {
    if (mode === workMode) return;

    setWorkMode(mode);
    setLoginValue('');
    setPasswordValue(mode === 'demo' ? DEMO_PASSWORD : '');
    setAuthError('');
  };

  const handleLogin = async () => {
    if (!canSubmit) return;
    setAuthError('');
    setIsSubmitting(true);

    try {
      if (workMode === 'demo') {
        if (trimmedPassword !== DEMO_PASSWORD) {
          throw new Error('Неверный demo-пароль.');
        }

        const userByLogin = adminUsers.find((user) => user.login === trimmedLogin);
        if (!userByLogin) {
          throw new Error('Не найден demo-профиль с таким логином.');
        }

        login(userByLogin.id);
        return;
      }

      const profile = await authApi.login(trimmedLogin, trimmedPassword);
      login(profile.id);
    } catch (error: any) {
      setAuthError(error?.response?.data?.detail ?? error?.message ?? 'Не удалось выполнить вход.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box
      className="login-screen"
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
          width: 'min(680px, 100%)',
          p: { xs: 3, md: 3.4 },
          borderRadius: 4,
          bgcolor: isLight ? 'rgba(255,255,255,0.82)' : 'rgba(16, 17, 21, 0.92)',
          borderColor: isLight ? 'rgba(14, 116, 144, 0.20)' : 'rgba(198, 216, 240, 0.34)',
          boxShadow: isLight
            ? '0 24px 70px rgba(15, 23, 42, 0.12)'
            : '0 28px 80px rgba(0,0,0,0.36), inset 0 1px 0 rgba(255,255,255,0.06)',
        }}
      >
        <Stack spacing={2.4}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1.6}
            sx={{ alignItems: { xs: 'flex-start', sm: 'center' }, justifyContent: 'space-between' }}
          >
            <Stack direction="row" spacing={1.7} sx={{ alignItems: 'center' }}>
              <Box
                sx={{
                  width: 58,
                  height: 58,
                  borderRadius: '19px',
                  display: 'grid',
                  placeItems: 'center',
                  color: '#dfeeff',
                  background: isLight
                    ? 'linear-gradient(145deg, #f8fbff 0%, #e0f2fe 100%)'
                    : 'linear-gradient(145deg, rgba(18, 67, 75, 0.95), rgba(11, 28, 34, 0.92) 74%, rgba(165, 140, 255, 0.20))',
                  border: isLight ? '1px solid rgba(2, 132, 199, 0.26)' : '1px solid rgba(132, 210, 213, 0.22)',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: isLight
                    ? 'inset 0 1px 0 rgba(255,255,255,0.86), 0 10px 22px rgba(2,132,199,0.12)'
                    : 'none',
                }}
              >
                <Ship
                  size={30}
                  style={{
                    position: 'relative',
                    zIndex: 1,
                    color: isLight ? lightLogoBlue : '#98d9d8',
                    filter: isLight ? 'drop-shadow(0 2px 5px rgba(2, 132, 199, 0.28))' : 'none',
                  }}
                />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', minHeight: 58 }}>
                <Typography
                  sx={{
                    color: isLight ? lightLogoBlue : '#98d9d8',
                    fontSize: '1.5rem',
                    lineHeight: 1.05,
                    fontWeight: 700,
                    fontFamily: '"Trebuchet MS", "Segoe UI", sans-serif',
                  }}
                >
                  AI ассистент
                </Typography>
              </Box>
            </Stack>

            <Stack
              direction="row"
              spacing={0.7}
              sx={{
                p: 0.35,
                borderRadius: 2,
                border: isLight ? '1px solid rgba(15, 23, 42, 0.12)' : '1px solid rgba(198, 216, 240, 0.18)',
                bgcolor: isLight ? 'rgba(248, 250, 252, 0.92)' : 'rgba(8, 12, 18, 0.34)',
              }}
            >
              <Button
                size="small"
                variant={!isDemoMode ? 'contained' : 'text'}
                onClick={() => handleWorkModeChange('prod')}
                sx={{ minWidth: 116, textTransform: 'none' }}
              >
                Продуктивный
              </Button>
              <Button
                size="small"
                variant={isDemoMode ? 'contained' : 'text'}
                onClick={() => handleWorkModeChange('demo')}
                sx={{ minWidth: 72, textTransform: 'none' }}
              >
                Демо
              </Button>
            </Stack>
          </Stack>

          <Stack spacing={1.2}>
            <TextField
              size="small"
              label="Логин"
              value={loginValue}
              error={loginError}
              helperText={loginError ? `Логин: ${LOGIN_LIMITS.min}-${LOGIN_LIMITS.max} символа` : undefined}
              onChange={(event) => {
                setLoginValue(event.target.value);
                setAuthError('');
              }}
              slotProps={{
                input: {
                  inputProps: { minLength: LOGIN_LIMITS.min, maxLength: LOGIN_LIMITS.max },
                  startAdornment: <UserRound size={16} style={{ marginRight: 8, opacity: 0.7 }} />,
                },
              }}
            />
            <TextField
              size="small"
              label="Пароль"
              type={showPassword ? 'text' : 'password'}
              value={passwordValue}
              error={passwordError}
              helperText={passwordError ? `Пароль: ${PASSWORD_LIMITS.min}-${PASSWORD_LIMITS.max} символа` : undefined}
              onChange={(event) => {
                setPasswordValue(event.target.value);
                setAuthError('');
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && canSubmit) {
                  handleLogin();
                }
              }}
              slotProps={{
                input: {
                  inputProps: { minLength: PASSWORD_LIMITS.min, maxLength: PASSWORD_LIMITS.max },
                  startAdornment: <KeyRound size={16} style={{ marginRight: 8, opacity: 0.7 }} />,
                  endAdornment: (
                    <IconButton
                      aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
                      size="small"
                      onClick={() => setShowPassword((value) => !value)}
                      edge="end"
                      sx={{ color: isLight ? '#075985' : 'text.secondary' }}
                    >
                      {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                    </IconButton>
                  ),
                },
              }}
            />
          </Stack>

          {authError && (
            <Alert severity="error" variant="outlined" sx={{ borderRadius: 2 }}>
              {authError}
            </Alert>
          )}

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2}>
            <Button
              fullWidth
              className="app-action-button"
              variant="contained"
              startIcon={<LogIn size={17} />}
              onClick={handleLogin}
              disabled={!canSubmit}
            >
              {isSubmitting ? 'Вход...' : 'Войти'}
            </Button>
          </Stack>

          <Button
            variant="text"
            href="mailto:admin@example.com?subject=Доступ%20к%20AI%20ассистенту"
            sx={{ alignSelf: 'flex-start', px: 0, textTransform: 'none' }}
          >
            Забыли пароль или нет доступа? Связаться с администратором
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
};
