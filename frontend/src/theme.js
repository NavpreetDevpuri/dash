// src/theme.js
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#1976d2' },
    secondary: { main: '#9c27b0' },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    allVariants: { color: '#fff' },
  },
});

export default theme;