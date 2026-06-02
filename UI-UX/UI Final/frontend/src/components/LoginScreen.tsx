import React, { useMemo, useState } from 'react';
import { Box, Button, IconButton, Paper, Stack, TextField, Typography } from '@mui/material';
import { Anchor, Database, Eye, EyeOff, KeyRound, LogIn, Moon, Settings, Ship, Sun, UserRound, Waves } from 'lucide-react';
import { useUIStore } from '../store/uiStore';

const ROLE_ORDER = ['Пользователь', 'Администратор знаний', 'Системный администратор'] as const;
const ROLE_FALLBACK_USER_ID: Record<(typeof ROLE_ORDER)[number], string> = {
  Пользователь: 'u1',
  'Администратор знаний': 'u3',
  'Системный администратор': 'u4',
};
const DEMO_PASSWORD = 'demo';
const LOGIN_LIMITS = { min: 3, max: 64 };
const PASSWORD_LIMITS = { min: 4, max: 64 };

export const LoginScreen: React.FC = () => {
  const { adminUsers, login, setThemeMode, themeMode } = useUIStore();
  const isLight = themeMode === 'light';
  const lightShipBlue = '#0284c7';

  const roleProfiles = useMemo(
    () =>
      ROLE_ORDER
        .map((role) => ({
          role,
          user: adminUsers.find((item) => item.role === role) ?? adminUsers.find((item) => item.id === ROLE_FALLBACK_USER_ID[role]),
        }))
        .filter((profile) => Boolean(profile.user)),
    [adminUsers],
  );
  const [selectedUserId, setSelectedUserId] = useState(roleProfiles[2]?.user?.id ?? roleProfiles[0]?.user?.id ?? '');
  const selectedUser = adminUsers.find((user) => user.id === selectedUserId) ?? roleProfiles[0]?.user;
  const [loginValue, setLoginValue] = useState(selectedUser?.login ?? '');
  const [passwordValue, setPasswordValue] = useState(DEMO_PASSWORD);
  const [showPassword, setShowPassword] = useState(false);
  const trimmedLogin = loginValue.trim();
  const trimmedPassword = passwordValue.trim();
  const loginError = Boolean(trimmedLogin) && (trimmedLogin.length < LOGIN_LIMITS.min || trimmedLogin.length > LOGIN_LIMITS.max);
  const passwordError =
    Boolean(trimmedPassword) && (trimmedPassword.length < PASSWORD_LIMITS.min || trimmedPassword.length > PASSWORD_LIMITS.max);
  const canSubmit = Boolean(trimmedLogin && trimmedPassword) && !loginError && !passwordError;

  const handleProfileSelect = (userId: string) => {
    const user = adminUsers.find((item) => item.id === userId);
    if (!user) return;

    setSelectedUserId(user.id);
    setLoginValue(user.login);
    setPasswordValue(DEMO_PASSWORD);
  };

  const handleLogin = () => {
    if (!canSubmit) return;

    const userByLogin = adminUsers.find((user) => user.login === trimmedLogin);
    login(userByLogin?.id ?? selectedUserId);
  };

  const getRoleIcon = (role: string) => {
    if (role === 'Системный администратор') return <Settings size={19} />;
    if (role === 'Администратор знаний') return <Database size={19} />;
    return <UserRound size={19} />;
  };

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
              {isLight ? (
                <Ship
                  size={30}
                  style={{
                    position: 'relative',
                    zIndex: 1,
                    color: lightShipBlue,
                    filter: 'drop-shadow(0 2px 5px rgba(2, 132, 199, 0.28))',
                  }}
                />
              ) : (
                <>
                  <Waves size={32} style={{ position: 'absolute', bottom: 6, opacity: 0.45, color: '#78c1c1' }} />
                  <Anchor size={25} style={{ position: 'relative', zIndex: 1, color: '#98d9d8' }} />
                </>
              )}
            </Box>
            <Box>
              <Typography
                sx={{
                  color: isLight ? lightShipBlue : '#98d9d8',
                  fontSize: '1.5rem',
                  lineHeight: 1.05,
                  fontWeight: 700,
                  fontFamily: '"Trebuchet MS", "Segoe UI", sans-serif',
                }}
              >
                AI ассистент
              </Typography>
              <Typography sx={{ mt: 0.45, color: isLight ? '#0f4f5c' : 'rgba(209, 225, 225, 0.72)' }}>
                сверка с НСИ
              </Typography>
            </Box>
          </Stack>

          <Stack spacing={1.2}>
            <TextField
              size="small"
              label="Логин"
              value={loginValue}
              error={loginError}
              helperText={`Логин: ${LOGIN_LIMITS.min}-${LOGIN_LIMITS.max} символа`}
              onChange={(event) => setLoginValue(event.target.value)}
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
              helperText={`Пароль: ${PASSWORD_LIMITS.min}-${PASSWORD_LIMITS.max} символа`}
              onChange={(event) => setPasswordValue(event.target.value)}
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

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 1 }}>
            {roleProfiles.map((profile) => {
              const user = profile.user;
              if (!user) return null;

              const selected = user.id === selectedUserId;

              return (
                <Paper
                  key={user.id}
                  variant="outlined"
                  onClick={() => handleProfileSelect(user.id)}
                  sx={{
                    p: 1.3,
                    borderRadius: 2.6,
                    cursor: 'pointer',
                    bgcolor: selected
                      ? isLight
                        ? 'rgba(15, 95, 111, 0.10)'
                        : 'rgba(152, 217, 216, 0.08)'
                      : isLight
                        ? 'rgba(255,255,255,0.76)'
                        : 'rgba(255,255,255,0.035)',
                    borderColor: selected
                      ? isLight
                        ? 'rgba(15, 95, 111, 0.34)'
                        : 'rgba(152, 217, 216, 0.38)'
                      : isLight
                        ? 'rgba(15,23,42,0.12)'
                        : 'rgba(198,216,240,0.18)',
                    '&:hover': {
                      borderColor: isLight ? 'rgba(2, 132, 199, 0.62)' : 'rgba(152, 217, 216, 0.38)',
                      boxShadow: isLight
                        ? '0 10px 24px rgba(2, 132, 199, 0.14), inset 0 1px 0 rgba(255,255,255,0.82)'
                        : '0 10px 24px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.08)',
                      transform: 'translateY(-1px)',
                    },
                    '&:focus-within': {
                      borderColor: isLight ? '#0284c7' : '#98d9d8',
                    },
                    transition: 'border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease',
                  }}
                >
                  <Stack spacing={0.85}>
                    <Box
                      sx={{
                        width: 34,
                        height: 34,
                        borderRadius: 1.7,
                        display: 'grid',
                        placeItems: 'center',
                        color: isLight ? '#0f5f6f' : '#98d9d8',
                        bgcolor: isLight ? '#eef7f8' : 'rgba(152,217,216,0.08)',
                        border: isLight ? '1px solid rgba(15,95,111,0.18)' : '1px solid rgba(152,217,216,0.18)',
                      }}
                    >
                      {getRoleIcon(profile.role)}
                    </Box>
                    <Box>
                      <Typography sx={{ fontSize: '0.88rem', fontWeight: 600, lineHeight: 1.2 }}>{profile.role}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.login}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>
              );
            })}
          </Box>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2}>
            <Button
              fullWidth
              className="app-action-button"
              variant="contained"
              startIcon={<LogIn size={17} />}
              onClick={handleLogin}
              disabled={!canSubmit}
            >
              Войти
            </Button>
            <Button
              variant="outlined"
              startIcon={themeMode === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
              onClick={() => setThemeMode(themeMode === 'dark' ? 'light' : 'dark')}
              sx={{ minWidth: 132 }}
            >
              {themeMode === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
};
