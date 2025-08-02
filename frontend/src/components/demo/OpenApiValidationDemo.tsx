/**
 * OpenAPI Validation Demo Component
 * 
 * This component demonstrates the enhanced API service with OpenAPI validation.
 * It shows how request/response validation works and provides examples of
 * successful and failed validation scenarios.
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  Stack,
  TextField,
  Paper,
  Chip,
  Divider,
  CircularProgress,
  Grid,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Code as CodeIcon,
  Verified as ValidatedIcon,
} from '@mui/icons-material';
import {
  useEnhancedBasicHealth,
  useEnhancedDetailedHealth,
  useEnhancedCurrentUser,
  useEnhancedConversations,
  useEnhancedCreateConversation,
  useValidationErrorHandler,
} from '../../hooks/api-validated';

/**
 * Demo component for OpenAPI validation features
 */
export function OpenApiValidationDemo(): React.ReactElement {
  const [testTitle, setTestTitle] = useState('Test Conversation');
  const [validationLog, setValidationLog] = useState<Array<{
    timestamp: string;
    operation: string;
    status: 'success' | 'error';
    message: string;
  }>>([]);

  // Enhanced hooks with validation
  const { data: basicHealth, isLoading: basicHealthLoading, error: basicHealthError } = useEnhancedBasicHealth();
  const { data: detailedHealth, isLoading: detailedHealthLoading, error: detailedHealthError } = useEnhancedDetailedHealth();
  const { data: currentUser, isLoading: userLoading, error: userError } = useEnhancedCurrentUser();
  const { data: conversations, isLoading: conversationsLoading, error: conversationsError } = useEnhancedConversations();
  const createConversation = useEnhancedCreateConversation();
  
  const handleValidationError = useValidationErrorHandler();

  /**
   * Add entry to validation log
   */
  const addLogEntry = (operation: string, status: 'success' | 'error', message: string) => {
    setValidationLog(prev => [{
      timestamp: new Date().toLocaleTimeString(),
      operation,
      status,
      message,
    }, ...prev.slice(0, 9)]); // Keep only last 10 entries
  };

  /**
   * Test creating a conversation with validation
   */
  const handleCreateConversation = async () => {
    try {
      const result = await createConversation.mutateAsync(testTitle);
      addLogEntry('createConversation', 'success', `Created conversation: ${result.title}`);
    } catch (error) {
      const errorMessage = handleValidationError(error);
      addLogEntry('createConversation', 'error', errorMessage);
    }
  };

  /**
   * Test validation with invalid data
   */
  const handleTestInvalidData = async () => {
    try {
      // This should fail validation due to empty title
      await createConversation.mutateAsync('');
    } catch (error) {
      const errorMessage = handleValidationError(error);
      addLogEntry('createConversation (invalid)', 'error', errorMessage);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ValidatedIcon color="primary" />
        OpenAPI Validation Demo
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        This page demonstrates the enhanced API service with OpenAPI validation. 
        All requests and responses are validated against the OpenAPI specification.
      </Typography>

      <Grid container spacing={3}>
        {/* API Status Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CodeIcon />
                API Health & Validation Status
              </Typography>
              
              <Stack spacing={2}>
                {/* Basic Health */}
                <Box>
                  <Typography variant="subtitle2">Basic Health Check</Typography>
                  {basicHealthLoading ? (
                    <CircularProgress size={20} />
                  ) : basicHealthError ? (
                    <Alert severity="error">
                      {handleValidationError(basicHealthError)}
                    </Alert>
                  ) : (
                    <Chip 
                      icon={<SuccessIcon />} 
                      label={`Validated: ${basicHealth?.success ? 'Healthy' : 'Unhealthy'}`}
                      color="success" 
                      size="small" 
                    />
                  )}
                </Box>

                {/* Detailed Health */}
                <Box>
                  <Typography variant="subtitle2">Detailed Health Check</Typography>
                  {detailedHealthLoading ? (
                    <CircularProgress size={20} />
                  ) : detailedHealthError ? (
                    <Alert severity="error">
                      {handleValidationError(detailedHealthError)}
                    </Alert>
                  ) : (
                    <Chip 
                      icon={<SuccessIcon />} 
                      label={`Validated: ${Object.keys(detailedHealth || {}).length} checks`}
                      color="success" 
                      size="small" 
                    />
                  )}
                </Box>

                {/* Current User */}
                <Box>
                  <Typography variant="subtitle2">Current User</Typography>
                  {userLoading ? (
                    <CircularProgress size={20} />
                  ) : userError ? (
                    <Alert severity="error">
                      {handleValidationError(userError)}
                    </Alert>
                  ) : (
                    <Chip 
                      icon={<SuccessIcon />} 
                      label={`Validated: ${currentUser?.username || 'Anonymous'}`}
                      color="success" 
                      size="small" 
                    />
                  )}
                </Box>

                {/* Conversations */}
                <Box>
                  <Typography variant="subtitle2">Conversations</Typography>
                  {conversationsLoading ? (
                    <CircularProgress size={20} />
                  ) : conversationsError ? (
                    <Alert severity="error">
                      {handleValidationError(conversationsError)}
                    </Alert>
                  ) : (
                    <Chip 
                      icon={<SuccessIcon />} 
                      label={`Validated: ${conversations?.items?.length || 0} conversations`}
                      color="success" 
                      size="small" 
                    />
                  )}
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Validation Testing Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Request Validation
              </Typography>
              
              <Stack spacing={2}>
                <TextField
                  label="Conversation Title"
                  value={testTitle}
                  onChange={(e) => setTestTitle(e.target.value)}
                  fullWidth
                  size="small"
                  helperText="Test creating a conversation with validation"
                />
                
                <Stack direction="row" spacing={1}>
                  <Button
                    variant="contained"
                    onClick={handleCreateConversation}
                    disabled={createConversation.isPending}
                    size="small"
                  >
                    {createConversation.isPending ? 'Creating...' : 'Create (Valid)'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={handleTestInvalidData}
                    disabled={createConversation.isPending}
                    size="small"
                  >
                    Test Invalid Data
                  </Button>
                </Stack>
                
                {createConversation.error && (
                  <Alert severity="error">
                    {handleValidationError(createConversation.error)}
                  </Alert>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Validation Log Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Validation Log
              </Typography>
              
              {validationLog.length === 0 ? (
                <Typography color="text.secondary">
                  No validation events yet. Try testing the API operations above.
                </Typography>
              ) : (
                <Stack spacing={1}>
                  {validationLog.map((entry, index) => (
                    <Paper key={index} sx={{ p: 2, backgroundColor: entry.status === 'error' ? 'error.light' : 'success.light' }}>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        {entry.status === 'error' ? <ErrorIcon color="error" /> : <SuccessIcon color="success" />}
                        <Typography variant="body2" component="code">
                          [{entry.timestamp}] {entry.operation}
                        </Typography>
                        <Chip 
                          label={entry.status} 
                          size="small" 
                          color={entry.status === 'error' ? 'error' : 'success'} 
                        />
                      </Stack>
                      <Typography variant="body2" sx={{ mt: 1, pl: 4 }}>
                        {entry.message}
                      </Typography>
                    </Paper>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ my: 3 }} />

      <Alert severity="info">
        <Typography variant="body2">
          <strong>Validation Features:</strong>
          <br />
          • All API requests are validated against OpenAPI schemas before sending
          <br />
          • All API responses are validated to ensure they match expected structure
          <br />
          • TypeScript types are auto-generated from the OpenAPI specification
          <br />
          • Runtime validation provides immediate feedback on data issues
          <br />
          • Enhanced error handling with detailed validation information
        </Typography>
      </Alert>
    </Box>
  );
}