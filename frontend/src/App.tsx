import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import Header from './components/Header'
import Footer from './components/Footer'
import HomePage from './pages/HomePage'
import SolvePage from './pages/SolvePage'
import ResultPage from './pages/ResultPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import './App.css'

// Layout wrapper component
const MainLayout = ({ children, darkMode, toggleDarkMode }: { 
  children: React.ReactNode, 
  darkMode: boolean, 
  toggleDarkMode: () => void 
}) => {
  return (
    <div className="app-container">
      <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
      <main className="main-content">{children}</main>
      <Footer />
    </div>
  );
};

function App() {
  // State for dark/light mode
  const [darkMode, setDarkMode] = useState(true);

  // Create theme based on dark/light mode preference
  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#3f51b5',
      },
      secondary: {
        main: '#f50057',
      },
      background: {
        default: darkMode ? '#121212' : '#f5f5f5',
        paper: darkMode ? '#1e1e1e' : '#ffffff',
      }
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
      }
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
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

  // Toggle dark/light mode
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          {/* Result page without standard layout */}
          <Route path="/result/:taskId" element={<ResultPage />} />
          
          {/* All other pages with standard layout */}
          <Route path="/" element={
            <MainLayout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
              <HomePage />
            </MainLayout>
          } />          
          <Route path="/solve" element={
            <MainLayout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
              <SolvePage />
            </MainLayout>
          } />
          <Route path="/login" element={
            <MainLayout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
              <LoginPage />
            </MainLayout>
          } />
          <Route path="*" element={
            <MainLayout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
              <NotFoundPage />
            </MainLayout>
          } />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
