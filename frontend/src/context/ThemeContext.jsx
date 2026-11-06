import { createContext, useContext, useState, useMemo, useCallback } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [darkMode, setDarkMode] = useState(true);

  const toggleTheme = useCallback(() => {
    setDarkMode((prev) => !prev);
  }, []);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? 'dark' : 'light',
          ...(darkMode
            ? {
                // Dark mode colors
                primary: {
                  main: '#818CF8',
                },
                secondary: {
                  main: '#EC4899',
                },
                background: {
                  default: '#0F172A',
                  paper: '#1E293B',
                },
                text: {
                  primary: '#E2E8F0',
                  secondary: '#94A3B8',
                },
              }
            : {
                // Light mode colors
                primary: {
                  main: '#4F46E5',
                },
                secondary: {
                  main: '#EC4899',
                },
                background: {
                  default: '#F8FAFC',
                  paper: '#FFFFFF',
                },
                text: {
                  primary: '#1E293B',
                  secondary: '#64748B',
                },
              }),
        },
        shape: {
          borderRadius: 12,
        },
        components: {
          MuiDrawer: {
            styleOverrides: {
              paper: {
                backgroundColor: darkMode ? '#1E293B' : '#FFFFFF',
                borderRight: 'none',
              },
            },
          },
        },
      }),
    [darkMode]
  );

  const contextValue = useMemo(() => ({
    darkMode,
    toggleTheme
  }), [darkMode, toggleTheme]);

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
