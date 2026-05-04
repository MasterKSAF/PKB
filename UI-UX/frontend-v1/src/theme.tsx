import { createTheme } from '@mui/material/styles';

export type AppThemeMode = 'dark' | 'light';

export const getAppTheme = (mode: AppThemeMode) =>
  createTheme({
  palette: {
    mode,
    primary: {
      main: '#c79b63',
      light: '#d9b783',
      dark: '#9f7440',
      contrastText: '#0f1115',
    },
    background: {
      default: mode === 'dark' ? '#0b0c0e' : '#f3f6f8',
      paper: mode === 'dark' ? '#16171b' : '#ffffff',
    },
    text: {
      primary: mode === 'dark' ? '#e1e1e1' : '#111827',
      secondary: mode === 'dark' ? '#9ba1a6' : '#475569',
    },
    divider: mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(15, 23, 42, 0.14)',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h5: {
      fontWeight: 600,
      letterSpacing: '-0.02em',
    },
    h6: {
      fontWeight: 500,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
      variants: [
        {
          props: { variant: 'contained', color: 'primary' },
          style: {
            color: '#0f1115',
            backgroundColor: '#c79b63',
            '&:hover': {
              backgroundColor: '#d9b783',
            },
          },
        },
      ],
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          maxWidth: 260,
          backgroundColor: mode === 'dark' ? '#1f2026' : '#ffffff',
          border: mode === 'dark' ? '1px solid rgba(255,255,255,0.12)' : '1px solid rgba(15,23,42,0.16)',
          color: mode === 'dark' ? '#e1e1e1' : '#111827',
          fontSize: 12,
          lineHeight: 1.45,
        },
      },
    },
  },
});

export const theme = getAppTheme('dark');
