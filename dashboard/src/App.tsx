import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, Button, Container } from '@mui/material';
import { Chat, AdminPanelSettings, Dashboard } from '@mui/icons-material';
import AdminDashboard from './pages/AdminDashboard';
import UserDashboard from './pages/UserDashboard';
import ChatInterface from './pages/ChatInterface';
import Login from './pages/Login';
import UserManagement from './pages/UserManagement';
import DocumentManagement from './pages/DocumentManagement';
import Analytics from './pages/Analytics';
import SystemSettings from './pages/SystemSettings';
import UserProfile from './pages/UserProfile';
import UserDocuments from './pages/UserDocuments';
import { AuthProvider, useAuth } from './services/AuthContext';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';

function AppContent(): JSX.Element {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [currentView, setCurrentView] = useState<string>('chat');

  const handleViewChange = (view: string): void => {
    setCurrentView(view);
    setSidebarOpen(false); // Close sidebar on mobile after selection
  };

  if (!user) {
    return <Login />;
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Chat sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AI Chatbot Platform
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            Welcome, {user.username}
          </Typography>
          <Button color="inherit" onClick={logout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Sidebar 
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentView={currentView}
        onViewChange={handleViewChange}
        isAdmin={user.is_superuser}
      />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: 8,
          ml: sidebarOpen ? '240px' : 0,
          transition: 'margin 0.3s ease',
        }}
      >
        <Container maxWidth="xl">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Navigate to="/chat" />} />
              <Route path="/chat" element={<ChatInterface />} />
              <Route path="/dashboard" element={<UserDashboard />} />
              <Route path="/documents" element={<UserDocuments />} />
              <Route path="/profile" element={<UserProfile />} />
              {user.is_superuser && (
                <>
                  <Route path="/admin" element={<AdminDashboard />} />
                  <Route path="/admin/users" element={<UserManagement />} />
                  <Route path="/admin/documents" element={<DocumentManagement />} />
                  <Route path="/admin/analytics" element={<Analytics />} />
                  <Route path="/admin/settings" element={<SystemSettings />} />
                </>
              )}
              <Route path="*" element={<Navigate to="/chat" />} />
            </Routes>
          </ErrorBoundary>
        </Container>
      </Box>
    </Box>
  );
}

function App(): JSX.Element {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;