/**
 * Tools Page Component
 * 
 * Manages MCP (Model Context Protocol) tools and servers:
 * - View available tools and their status
 * - Enable/disable individual tools
 * - Manage MCP servers
 * - View tool usage statistics
 * - Configure tool settings
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Grid,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemAvatar,
  Avatar,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Build as ToolIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Storage as ServerIcon,
  PlayArrow as EnableIcon,
  Stop as DisableIcon,
  Assessment as StatsIcon,
  Settings as SettingsIcon,
  CheckCircle as ConnectedIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

import { 
  PageHeader, 
  LoadingSpinner, 
  StatusChip, 
  ConfirmDialog,
  EmptyState,
  DataTable,
  type DataTableColumn,
} from '../components/common/CommonComponents';
import {
  useMcpServers,
  useMcpTools,
  useToolStats,
  useAddMcpServer,
  useUpdateMcpServer,
  useDeleteMcpServer,
  useToggleTool,
} from '../hooks/api';
import type { McpServer, McpTool, ToolUsageStats } from '../types/api';

/**
 * Server form dialog component
 */
function ServerFormDialog({
  open,
  onClose,
  server,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  server?: McpServer;
  onSave: (server: Omit<McpServer, 'id' | 'created_at' | 'updated_at' | 'status' | 'last_connected'>) => void;
}): JSX.Element {
  const [formData, setFormData] = useState({
    name: server?.name || '',
    url: server?.url || '',
    description: server?.description || '',
    is_enabled: server?.is_enabled ?? true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.url.trim()) {
      newErrors.url = 'URL is required';
    } else {
      try {
        new URL(formData.url);
      } catch {
        newErrors.url = 'Please enter a valid URL';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validateForm()) {
      onSave(formData);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {server ? 'Edit MCP Server' : 'Add New MCP Server'}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            fullWidth
            label="Server Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            error={!!errors.name}
            helperText={errors.name || 'Human-readable name for the server'}
          />

          <TextField
            fullWidth
            label="Server URL"
            value={formData.url}
            onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
            error={!!errors.url}
            helperText={errors.url || 'MCP server endpoint URL'}
            placeholder="http://localhost:3000/mcp"
          />

          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            multiline
            rows={2}
            helperText="Optional description of the server's purpose"
          />

          <FormControlLabel
            control={
              <Switch
                checked={formData.is_enabled}
                onChange={(e) => setFormData(prev => ({ ...prev, is_enabled: e.target.checked }))}
              />
            }
            label="Enable server"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>
          {server ? 'Update' : 'Add'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * Server card component
 */
function ServerCard({ 
  server, 
  onEdit, 
  onDelete 
}: {
  server: McpServer;
  onEdit: (server: McpServer) => void;
  onDelete: (serverId: string) => void;
}): JSX.Element {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleAction = (action: () => void) => {
    action();
    handleMenuClose();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <ConnectedIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <WarningIcon color="warning" />;
    }
  };

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          {/* Header */}
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1}>
              <ServerIcon color="primary" />
              <Typography variant="h6">{server.name}</Typography>
            </Stack>
            <IconButton onClick={handleMenuClick}>
              <MoreIcon />
            </IconButton>
          </Stack>

          {/* Description */}
          {server.description && (
            <Typography variant="body2" color="text.secondary">
              {server.description}
            </Typography>
          )}

          {/* URL */}
          <Typography 
            variant="body2" 
            sx={{ 
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              bgcolor: 'grey.50',
              p: 1,
              borderRadius: 1,
            }}
          >
            {server.url}
          </Typography>

          {/* Status */}
          <Stack direction="row" spacing={2} alignItems="center">
            <Stack direction="row" alignItems="center" spacing={1}>
              {getStatusIcon(server.status)}
              <StatusChip
                status={
                  server.status === 'connected' ? 'success' :
                  server.status === 'error' ? 'error' : 'warning'
                }
                label={server.status.toUpperCase()}
                showIcon={false}
              />
            </Stack>
            <StatusChip
              status={server.is_enabled ? 'success' : 'default'}
              label={server.is_enabled ? 'Enabled' : 'Disabled'}
              showIcon={false}
            />
          </Stack>

          {/* Connection Info */}
          <Typography variant="caption" color="text.secondary">
            {server.last_connected 
              ? `Last connected: ${new Date(server.last_connected).toLocaleString()}`
              : 'Never connected'
            }
          </Typography>
        </Stack>

        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItem onClick={() => handleAction(() => onEdit(server))}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => onDelete(server.id))}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        </Menu>
      </CardContent>
    </Card>
  );
}

/**
 * Tool card component
 */
function ToolCard({ 
  tool, 
  onToggle 
}: {
  tool: McpTool;
  onToggle: (toolId: string, enabled: boolean) => void;
}): JSX.Element {
  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          {/* Header */}
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1}>
              <ToolIcon color="primary" />
              <Typography variant="h6">{tool.name}</Typography>
            </Stack>
            <Switch
              checked={tool.is_enabled}
              onChange={(e) => onToggle(tool.id, e.target.checked)}
            />
          </Stack>

          {/* Description */}
          <Typography variant="body2" color="text.secondary">
            {tool.description}
          </Typography>

          {/* Usage Stats */}
          <Stack direction="row" spacing={1} alignItems="center">
            <Chip 
              label={`Used ${tool.usage_count} times`}
              size="small"
              variant="outlined"
              color="primary"
            />
            {tool.last_used && (
              <Typography variant="caption" color="text.secondary">
                Last used: {new Date(tool.last_used).toLocaleDateString()}
              </Typography>
            )}
          </Stack>

          {/* Server Info */}
          <Typography variant="caption" color="text.secondary">
            Server: {tool.server_id}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

/**
 * Tool statistics table component
 */
function ToolStatsTable({ 
  stats, 
  loading 
}: {
  stats: ToolUsageStats[];
  loading: boolean;
}): JSX.Element {
  const columns: DataTableColumn<ToolUsageStats>[] = [
    {
      id: 'tool',
      label: 'Tool',
      render: (_, stat) => (
        <Stack direction="row" alignItems="center" spacing={1}>
          <ToolIcon color="primary" />
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {stat.tool.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {stat.tool.description}
            </Typography>
          </Box>
        </Stack>
      ),
    },
    {
      id: 'usage_count',
      label: 'Usage Count',
      sortable: true,
      render: (_, stat) => stat.usage_count,
    },
    {
      id: 'avg_execution_time',
      label: 'Avg Execution Time',
      sortable: true,
      render: (_, stat) => `${stat.avg_execution_time}ms`,
    },
    {
      id: 'success_rate',
      label: 'Success Rate',
      sortable: true,
      render: (_, stat) => (
        <Chip
          label={`${Math.round(stat.success_rate * 100)}%`}
          size="small"
          color={stat.success_rate > 0.9 ? 'success' : stat.success_rate > 0.7 ? 'warning' : 'error'}
          variant="outlined"
        />
      ),
    },
    {
      id: 'last_used',
      label: 'Last Used',
      sortable: true,
      render: (_, stat) => stat.last_used 
        ? new Date(stat.last_used).toLocaleDateString()
        : 'Never',
    },
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Tool Usage Statistics
        </Typography>
        <DataTable
          columns={columns}
          data={stats}
          loading={loading}
          emptyState={{
            title: 'No usage statistics available',
            description: 'Tool statistics will appear here once tools are used.',
          }}
        />
      </CardContent>
    </Card>
  );
}

/**
 * Main tools page component
 */
export default function ToolsPage(): JSX.Element {
  const [serverDialogOpen, setServerDialogOpen] = useState(false);
  const [editingServer, setEditingServer] = useState<McpServer | undefined>(undefined);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [serverToDelete, setServerToDelete] = useState<string | null>(null);

  // API hooks
  const { data: servers = [], isLoading: serversLoading } = useMcpServers();
  const { data: tools = [], isLoading: toolsLoading } = useMcpTools();
  const { data: toolStats = [], isLoading: statsLoading } = useToolStats();
  
  const addServerMutation = useAddMcpServer();
  const updateServerMutation = useUpdateMcpServer();
  const deleteServerMutation = useDeleteMcpServer();
  const toggleToolMutation = useToggleTool();

  const handleAddServer = async (serverData: Omit<McpServer, 'id' | 'created_at' | 'updated_at' | 'status' | 'last_connected'>) => {
    try {
      await addServerMutation.mutateAsync(serverData);
      setServerDialogOpen(false);
      setEditingServer(undefined);
    } catch (error) {
      console.error('Failed to add server:', error);
    }
  };

  const handleEditServer = async (serverData: Omit<McpServer, 'id' | 'created_at' | 'updated_at' | 'status' | 'last_connected'>) => {
    if (!editingServer) return;

    try {
      await updateServerMutation.mutateAsync({
        serverId: editingServer.id,
        updates: serverData,
      });
      setServerDialogOpen(false);
      setEditingServer(undefined);
    } catch (error) {
      console.error('Failed to update server:', error);
    }
  };

  const handleDeleteServer = async () => {
    if (!serverToDelete) return;

    try {
      await deleteServerMutation.mutateAsync(serverToDelete);
      setDeleteDialogOpen(false);
      setServerToDelete(null);
    } catch (error) {
      console.error('Failed to delete server:', error);
    }
  };

  const handleToggleTool = async (toolId: string, enabled: boolean) => {
    try {
      await toggleToolMutation.mutateAsync({ toolId, enabled });
    } catch (error) {
      console.error('Failed to toggle tool:', error);
    }
  };

  const openEditDialog = (server: McpServer) => {
    setEditingServer(server);
    setServerDialogOpen(true);
  };

  const openAddDialog = () => {
    setEditingServer(undefined);
    setServerDialogOpen(true);
  };

  const isLoading = serversLoading || toolsLoading;

  return (
    <Box>
      <PageHeader
        title="MCP Tools"
        subtitle="Manage Model Context Protocol servers and tools for enhanced AI capabilities"
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={openAddDialog}
          >
            Add Server
          </Button>
        }
      />

      <Stack spacing={4}>
        {/* Overview Stats */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  {servers.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  MCP Servers
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="secondary.main">
                  {tools.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Available Tools
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {tools.filter(t => t.is_enabled).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Enabled Tools
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {servers.filter(s => s.status === 'connected').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Connected Servers
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* MCP Servers Section */}
        <Box>
          <Typography variant="h5" gutterBottom>
            MCP Servers
          </Typography>
          {isLoading ? (
            <LoadingSpinner message="Loading servers..." />
          ) : servers.length === 0 ? (
            <EmptyState
              icon={<ServerIcon sx={{ fontSize: 64 }} />}
              title="No MCP Servers"
              description="Add your first MCP server to start using external tools."
              action={
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={openAddDialog}
                >
                  Add First Server
                </Button>
              }
            />
          ) : (
            <Grid container spacing={3}>
              {servers.map((server) => (
                <Grid item xs={12} md={6} lg={4} key={server.id}>
                  <ServerCard
                    server={server}
                    onEdit={openEditDialog}
                    onDelete={(id) => {
                      setServerToDelete(id);
                      setDeleteDialogOpen(true);
                    }}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Box>

        {/* Tools Section */}
        <Box>
          <Typography variant="h5" gutterBottom>
            Available Tools
          </Typography>
          {toolsLoading ? (
            <LoadingSpinner message="Loading tools..." />
          ) : tools.length === 0 ? (
            <Alert severity="info">
              No tools available. Add MCP servers to see their tools here.
            </Alert>
          ) : (
            <Grid container spacing={3}>
              {tools.map((tool) => (
                <Grid item xs={12} md={6} lg={4} key={tool.id}>
                  <ToolCard
                    tool={tool}
                    onToggle={handleToggleTool}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Box>

        {/* Tool Statistics */}
        <ToolStatsTable stats={toolStats} loading={statsLoading} />
      </Stack>

      {/* Server Form Dialog */}
      <ServerFormDialog
        open={serverDialogOpen}
        onClose={() => {
          setServerDialogOpen(false);
          setEditingServer(undefined);
        }}
        server={editingServer}
        onSave={editingServer ? handleEditServer : handleAddServer}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete MCP Server"
        message="Are you sure you want to delete this MCP server? All associated tools will be disabled."
        confirmText="Delete"
        confirmColor="error"
        loading={deleteServerMutation.isPending}
        onConfirm={handleDeleteServer}
        onCancel={() => {
          setDeleteDialogOpen(false);
          setServerToDelete(null);
        }}
      />
    </Box>
  );
}