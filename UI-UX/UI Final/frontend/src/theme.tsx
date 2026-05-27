import { createTheme } from '@mui/material/styles';

export type AppThemeMode = 'dark' | 'light';

export const getAppTheme = (mode: AppThemeMode) =>
  createTheme({
  palette: {
    mode,
    primary: {
      main: mode === 'dark' ? '#c79b63' : '#38bdf8',
      light: mode === 'dark' ? '#d9b783' : '#7dd3fc',
      dark: mode === 'dark' ? '#9f7440' : '#075985',
      contrastText: mode === 'dark' ? '#0f1115' : '#0f172a',
    },
    background: {
      default: mode === 'dark' ? '#0b0c0e' : '#f1f5f9',
      paper: mode === 'dark' ? '#16171b' : '#ffffff',
    },
    text: {
      primary: mode === 'dark' ? '#e1e1e1' : '#1e293b',
      secondary: mode === 'dark' ? '#9ba1a6' : '#64748b',
    },
    divider: mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : '#e2e8f0',
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
            color: mode === 'dark' ? '#0f1115' : '#0f172a',
            backgroundColor: mode === 'dark' ? '#c79b63' : '#38bdf8',
            '&:hover': {
              backgroundColor: mode === 'dark' ? '#d9b783' : '#7dd3fc',
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
          border: mode === 'dark' ? '1px solid rgba(255,255,255,0.12)' : '1px solid #e2e8f0',
          color: mode === 'dark' ? '#e1e1e1' : '#1e293b',
          fontSize: 12,
          lineHeight: 1.45,
        },
      },
    },
  },
});

export const theme = getAppTheme('dark');
