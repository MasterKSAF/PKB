import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#c79b63',
      light: '#d9b783',
      dark: '#9f7440',
      contrastText: '#0f1115',
    },
    background: {
      default: '#0b0c0e',
      paper: '#16171b',
    },
    text: {
      primary: '#e1e1e1',
      secondary: '#9ba1a6',
    },
    divider: 'rgba(255, 255, 255, 0.08)',
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
          backgroundColor: '#1f2026',
          border: '1px solid rgba(255,255,255,0.12)',
          color: '#e1e1e1',
          fontSize: 12,
          lineHeight: 1.45,
        },
      },
    },
  },
});
