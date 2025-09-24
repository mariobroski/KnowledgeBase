import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Komponenty układu
import Layout from './components/Layout';

// Strony
import PanelAdministratora from './pages/Dashboard';
import Documents from './pages/Articles';
import ArticleDetail from './pages/ArticleDetail';
import Facts from './pages/Facts';
import Graph from './pages/Graph';
import Search from './pages/Search';
import Analytics from './pages/Analytics';
import Profile from './pages/Profile';
import AdminPanel from './pages/AdminPanel';
import SystemSettings from './pages/SystemSettings';
import RAGSettings from './pages/RAGSettings';
import Benchmarks from './pages/Benchmarks';

// Motyw aplikacji
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          {/* Główne trasy aplikacji */}
          <Route path="/" element={<Layout><PanelAdministratora /></Layout>} />
          <Route path="/panel-administratora" element={<Layout><PanelAdministratora /></Layout>} />
          <Route path="/articles" element={<Layout><Documents /></Layout>} />
          <Route path="/articles/:id" element={<Layout><ArticleDetail /></Layout>} />
          <Route path="/facts" element={<Layout><Facts /></Layout>} />
          <Route path="/graph" element={<Layout><Graph /></Layout>} />
          <Route path="/search" element={<Layout><Search /></Layout>} />
          <Route path="/analytics" element={<Layout><Analytics /></Layout>} />
          <Route path="/benchmarks" element={<Layout><Benchmarks /></Layout>} />
          <Route path="/profile" element={<Layout><Profile /></Layout>} />
          <Route path="/admin" element={<Layout><AdminPanel /></Layout>} />
          <Route path="/system-settings" element={<Layout><SystemSettings /></Layout>} />
          <Route path="/rag-settings" element={<Layout><RAGSettings /></Layout>} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App;