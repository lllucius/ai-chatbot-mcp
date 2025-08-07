/**
 * SDK Test Page to demonstrate the TypeScript SDK functionality
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Stack,
  Divider,
} from '@mui/material';
import sdkService from '../services/sdk-service';

export function SdkTestPage(): React.ReactElement {
  const [isTestingHealth, setIsTestingHealth] = useState(false);
  const [healthResult, setHealthResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const testHealthCheck = async () => {
    setIsTestingHealth(true);
    setError(null);
    setHealthResult(null);

    try {
      const health = await sdkService.getHealth();
      setHealthResult(health);
    } catch (err: any) {
      setError(err.message || 'Health check failed');
    } finally {
      setIsTestingHealth(false);
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        TypeScript SDK Test Page
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        This page demonstrates the new TypeScript SDK functionality for the AI Chatbot MCP API.
      </Typography>

      <Stack spacing={3}>
        {/* SDK Information */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              SDK Information
            </Typography>
            <Typography variant="body2" color="text.secondary">
              SDK Ready: {sdkService.isReady() ? '✅ Yes' : '❌ No'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Authenticated: {sdkService.isAuthenticated() ? '✅ Yes' : '❌ No'}
            </Typography>
          </CardContent>
        </Card>

        {/* Health Check Test */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Health Check Test
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Test the basic health endpoint using the TypeScript SDK.
            </Typography>
            
            <Button
              variant="contained"
              onClick={testHealthCheck}
              disabled={isTestingHealth}
              startIcon={isTestingHealth ? <CircularProgress size={20} /> : null}
            >
              {isTestingHealth ? 'Testing...' : 'Test Health Check'}
            </Button>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                <strong>Error:</strong> {error}
              </Alert>
            )}

            {healthResult && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <strong>Success!</strong> Health check completed.
                <pre style={{ marginTop: 8, fontSize: '0.875rem' }}>
                  {JSON.stringify(healthResult, null, 2)}
                </pre>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* SDK Features */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              SDK Features
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              The TypeScript SDK provides the following features:
            </Typography>
            
            <Stack spacing={1}>
              <Typography variant="body2">
                ✅ <strong>Complete API Coverage:</strong> Access to all backend endpoints
              </Typography>
              <Typography variant="body2">
                ✅ <strong>Type Safety:</strong> Full TypeScript support with interfaces
              </Typography>
              <Typography variant="body2">
                ✅ <strong>Authentication:</strong> Automatic token management
              </Typography>
              <Typography variant="body2">
                ✅ <strong>Error Handling:</strong> Structured error handling
              </Typography>
              <Typography variant="body2">
                ✅ <strong>Streaming:</strong> Support for real-time chat streaming
              </Typography>
              <Typography variant="body2">
                ✅ <strong>Cross-Platform:</strong> Works in browser and Node.js
              </Typography>
            </Stack>
          </CardContent>
        </Card>

        {/* Code Example */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Usage Example
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Here's how to use the TypeScript SDK:
            </Typography>
            
            <Box 
              sx={{ 
                bgcolor: 'grey.100', 
                p: 2, 
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                overflow: 'auto'
              }}
            >
              <pre>{`import { AiChatbotSdk } from '@ai-chatbot-mcp/sdk';

// Initialize the SDK
const sdk = new AiChatbotSdk({
  baseUrl: 'https://api.example.com',
  timeout: 30000
});

// Authenticate
const token = await sdk.auth.login({
  username: 'user',
  password: 'password'
});

// Create conversation
const conversation = await sdk.conversations.create({
  title: 'My Chat'
});

// Send message
const response = await sdk.conversations.chat({
  conversation_id: conversation.id,
  message: 'Hello!'
});

// Upload document
const document = await sdk.documents.upload(file, {
  title: 'My Document'
});

// Search documents
const results = await sdk.search.hybridSearch(
  'machine learning', 10
);`}</pre>
            </Box>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}