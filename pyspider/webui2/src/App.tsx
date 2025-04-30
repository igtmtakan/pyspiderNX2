import { Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import ProjectDebug from './pages/ProjectDebug';
import ProjectDebugV2 from './pages/ProjectDebugV2';
import ProjectForm from './pages/ProjectForm';
import Tasks from './pages/Tasks';
import Results from './pages/Results';
import Monitor from './pages/Monitor';
import Settings from './pages/Settings';
import Login from './pages/Login';
import NotFound from './pages/NotFound';

function App() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Check user preference
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    setDarkMode(isDarkMode);

    // Apply dark mode class to html element
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', String(newDarkMode));

    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Projects />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/new"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <ProjectForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <ProjectDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id/edit"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <ProjectForm />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id/debug"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <ProjectDebug />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:id/debug-v2"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <ProjectDebugV2 />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/tasks"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Tasks />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/results"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Results />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/monitor"
          element={
            <ProtectedRoute>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Monitor />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute adminOnly>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Settings />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
