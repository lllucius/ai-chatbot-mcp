import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, Button, Container } from '@mui/material';
import { Chat, AdminPanelSettings, Dashboard } from '@mui/icons-material';
import AdminDashboard from './pages/AdminDashboard';
import UserDashboard from './pages/UserDashboard';
import ChatInterface from './pages/ChatInterface';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './services/AuthContext';
import Sidebar from './components/Sidebar';

function AppContent() {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState('chat');

  const handleViewChange = (view) => {
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
          <Routes>
            <Route path="/" element={<Navigate to="/chat" />} />
            <Route path="/chat" element={<ChatInterface />} />
            <Route path="/dashboard" element={<UserDashboard />} />
            {user.is_superuser && (
              <Route path="/admin" element={<AdminDashboard />} />
            )}
            <Route path="*" element={<Navigate to="/chat" />} />
          </Routes>
        </Container>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;