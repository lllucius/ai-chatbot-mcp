import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Divider,
} from '@mui/material';
import {
  Refresh,
  Settings,
  PlayArrow,
  Stop,
  Info,
  Build,
  Storage,
  Security,
} from '@mui/icons-material';
import { ToolsService, ToolsData, Tool, ToolServer } from '../services';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SystemSettings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [toolsData, setToolsData] = useState<ToolsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testParams, setTestParams] = useState('{}');
  const [testResult, setTestResult] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadToolsData();
  }, []);

  const loadToolsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await ToolsService.listTools();
      if (response.success && response.data) {
        setToolsData(response.data);
      } else {
        setError('Failed to load tools data');
      }
    } catch (err) {
      setError('Failed to load tools data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshTools = async () => {
    setRefreshing(true);
    try {
      await ToolsService.refreshTools();
      await loadToolsData();
    } catch (err) {
      setError('Failed to refresh tools');
    } finally {
      setRefreshing(false);
    }
  };

  const handleTestTool = async () => {
    if (!selectedTool) return;
    
    try {
      const params = JSON.parse(testParams || '{}');
      const response = await ToolsService.testTool(selectedTool.name, params);
      setTestResult(response);
    } catch (err) {
      setTestResult({ success: false, error: 'Invalid JSON parameters or test failed' });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'success';
      case 'error': return 'error';
      case 'disconnected': return 'warning';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">System Settings</Typography>
        <Button
          variant="contained"
          startIcon={refreshing ? <CircularProgress size={16} /> : <Refresh />}
          onClick={handleRefreshTools}
          disabled={refreshing}
        >
          Refresh Tools
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          aria-label="system settings tabs"
        >
          <Tab label="MCP Tools" icon={<Build />} />
          <Tab label="Tool Servers" icon={<Storage />} />
          <Tab label="Security" icon={<Security />} />
          <Tab label="General" icon={<Settings />} />
        </Tabs>

        {/* MCP Tools Tab */}
        <TabPanel value={tabValue} index={0}>
          {toolsData && (
            <>
              {/* Tools Overview */}
              <Grid container spacing={3} mb={4}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{toolsData.total_tools}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Tools
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{toolsData.enabled_tools}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Enabled Tools
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{Object.keys(toolsData.servers).length}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Active Servers
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{toolsData.openai_tools.length}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        OpenAI Tools
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Tools Table */}
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Tool Name</TableCell>
                      <TableCell>Server</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>Usage Count</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(toolsData.tools).map(([toolName, tool]: [string, Tool]) => (
                      <TableRow key={toolName}>
                        <TableCell>{toolName}</TableCell>
                        <TableCell>{tool.server}</TableCell>
                        <TableCell>
                          <FormControlLabel
                            control={<Switch checked={tool.enabled} />}
                            label={tool.enabled ? 'Enabled' : 'Disabled'}
                          />
                        </TableCell>
                        <TableCell sx={{ maxWidth: 300 }}>
                          {tool.description || 'No description available'}
                        </TableCell>
                        <TableCell>{tool.usage_count}</TableCell>
                        <TableCell>
                          <IconButton
                            onClick={() => {
                              setSelectedTool(tool);
                              setTestDialogOpen(true);
                              setTestResult(null);
                              setTestParams('{}');
                            }}
                            size="small"
                            title="Test Tool"
                          >
                            <PlayArrow />
                          </IconButton>
                          <IconButton
                            onClick={() => {
                              setSelectedTool(tool);
                              // In a real implementation, show tool details
                            }}
                            size="small"
                            title="Tool Details"
                          >
                            <Info />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </TabPanel>

        {/* Tool Servers Tab */}
        <TabPanel value={tabValue} index={1}>
          {toolsData && (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Server Name</TableCell>
                    <TableCell>URL</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Tool Count</TableCell>
                    <TableCell>Response Time</TableCell>
                    <TableCell>Last Check</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.values(toolsData.servers).map((server: ToolServer) => (
                    <TableRow key={server.name}>
                      <TableCell>{server.name}</TableCell>
                      <TableCell>{server.url}</TableCell>
                      <TableCell>
                        <Chip 
                          label={server.status}
                          color={getStatusColor(server.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{server.tool_count}</TableCell>
                      <TableCell>{server.response_time || 'N/A'}</TableCell>
                      <TableCell>
                        {new Date(server.last_check).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Security Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Authentication Settings
                  </Typography>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Require authentication for all API calls"
                  />
                  <br />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Admin-only access to tool management"
                  />
                  <br />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Log all tool executions"
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Rate Limiting
                  </Typography>
                  <TextField
                    fullWidth
                    label="Max requests per minute"
                    defaultValue="100"
                    type="number"
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    label="Max concurrent requests"
                    defaultValue="10"
                    type="number"
                    margin="normal"
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* General Tab */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Configuration
                  </Typography>
                  <TextField
                    fullWidth
                    label="Application Name"
                    defaultValue="AI Chatbot Admin Dashboard"
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    label="Max file size (MB)"
                    defaultValue="10"
                    type="number"
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    label="Session timeout (minutes)"
                    defaultValue="1440"
                    type="number"
                    margin="normal"
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Logging & Monitoring
                  </Typography>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Enable debug logging"
                  />
                  <br />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Performance monitoring"
                  />
                  <br />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Error reporting"
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Tool Test Dialog */}
      <Dialog 
        open={testDialogOpen} 
        onClose={() => setTestDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Test Tool: {selectedTool?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {selectedTool?.description}
          </Typography>
          
          <TextField
            fullWidth
            label="Test Parameters (JSON)"
            multiline
            rows={4}
            value={testParams}
            onChange={(e) => setTestParams(e.target.value)}
            margin="normal"
            placeholder='{"param1": "value1", "param2": "value2"}'
          />
          
          {testResult && (
            <Box mt={2}>
              <Typography variant="h6" gutterBottom>
                Test Result:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(testResult, null, 2)}
                </pre>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>
            Close
          </Button>
          <Button 
            onClick={handleTestTool}
            variant="contained"
            disabled={!selectedTool}
          >
            Test Tool
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SystemSettings;