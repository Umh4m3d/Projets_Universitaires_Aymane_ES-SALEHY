import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2563EB',
      light: '#EFF6FF',
      dark: '#1D4ED8',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#64748B',
    },
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    success: { main: '#16A34A', light: '#DCFCE7' },
    warning: { main: '#D97706', light: '#FEF3C7' },
    error:   { main: '#DC2626', light: '#FEF2F2' },
    text: {
      primary:   '#0F172A',
      secondary: '#64748B',
    },
    divider: '#E2E8F0',
  },
  typography: {
    fontFamily: '"Inter", system-ui, sans-serif',
    h4: { fontWeight: 700, fontSize: '1.5rem',  letterSpacing: '-0.02em' },
    h5: { fontWeight: 600, fontSize: '1.25rem', letterSpacing: '-0.01em' },
    h6: { fontWeight: 600, fontSize: '1rem' },
    subtitle1: { fontWeight: 500, color: '#64748B' },
    body1: { fontSize: '0.875rem' },
    body2: { fontSize: '0.8125rem', color: '#64748B' },
    caption: { fontSize: '0.75rem',  color: '#94A3B8' },
  },
  shape: { borderRadius: 10 },
  shadows: [
    'none',
    '0px 1px 3px rgba(0,0,0,0.06), 0px 1px 2px rgba(0,0,0,0.04)',
    '0px 4px 6px -1px rgba(0,0,0,0.07), 0px 2px 4px -2px rgba(0,0,0,0.05)',
    '0px 10px 15px -3px rgba(0,0,0,0.08), 0px 4px 6px -4px rgba(0,0,0,0.05)',
    ...Array(21).fill('none'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
          fontSize: '0.875rem',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0px 1px 3px rgba(0,0,0,0.06), 0px 1px 2px rgba(0,0,0,0.04)',
          borderRadius: 12,
          border: '1px solid #F1F5F9',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#F8FAFC',
            color: '#64748B',
            fontWeight: 600,
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            borderBottom: '1px solid #E2E8F0',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: '#F1F5F9',
          fontSize: '0.875rem',
          padding: '14px 16px',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, fontSize: '0.75rem', borderRadius: 6 },
      },
    },
    MuiTextField: {
      defaultProps: { size: 'small' },
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            fontSize: '0.875rem',
          },
        },
      },
    },
    MuiSelect: {
      defaultProps: { size: 'small' },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          marginBottom: 2,
          '&.Mui-selected': {
            backgroundColor: '#EFF6FF',
            color: '#2563EB',
            '& .MuiListItemIcon-root': { color: '#2563EB' },
            '&:hover': { backgroundColor: '#DBEAFE' },
          },
          '&:hover': { backgroundColor: '#F8FAFC' },
        },
      },
    },
  },
})

export default theme
