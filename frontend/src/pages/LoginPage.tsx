/**
 * Login Page Component
 * 
 * This page provides the user authentication interface with options to
 * switch between login and registration forms. It includes proper error
 * handling, validation, and responsive design.
 */

import React, { useState } from 'react';
import { Box, Container, Paper, Typography, Stack } from '@mui/material';
import { LoginForm, RegisterForm } from '../components/auth/AuthComponents';

/**
 * Login page component with toggle between login and register
 */
export default function LoginPage(): JSX.Element {
  const [isRegistering, setIsRegistering] = useState(false);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Stack spacing={4} alignItems="center">
          {/* App branding */}
          <Box textAlign="center">
            <Typography 
              variant="h2" 
              component="h1" 
              sx={{ 
                color: 'white',
                fontWeight: 700,
                mb: 1,
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              }}
            >
              AI Chatbot
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'rgba(255,255,255,0.9)',
                textShadow: '0 1px 2px rgba(0,0,0,0.2)',
              }}
            >
              Advanced AI Assistant Platform
            </Typography>
          </Box>

          {/* Authentication form */}
          {isRegistering ? (
            <RegisterForm
              onSwitchToLogin={() => setIsRegistering(false)}
              onRegisterSuccess={() => setIsRegistering(false)}
            />
          ) : (
            <LoginForm
              onSwitchToRegister={() => setIsRegistering(true)}
            />
          )}
        </Stack>
      </Container>
    </Box>
  );
}