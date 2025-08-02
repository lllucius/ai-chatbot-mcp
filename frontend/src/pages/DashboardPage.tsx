/**
 * Dashboard Page Component
 * 
 * The main dashboard provides an overview of the AI Chatbot system including:
 * - System statistics and metrics
 * - Recent conversations
 * - Document processing status
 * - Quick actions and shortcuts
 * - Real-time system health indicators
 */

import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Stack,
  IconButton,
  Button,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Chat as ChatIcon,
  Description as DocumentIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Build as ToolsIcon,
  Add as AddIcon,
  Launch as LaunchIcon,
  AccessTime as TimeIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { PageHeader, LoadingSpinner, StatusChip } from '../components/common/CommonComponents';
import { useAuth } from '../contexts/AuthContext';
import {
  useSystemStats,
  useConversations,
  useDocuments,
  useSystemHealth,
} from '../hooks/api';

/**
 * Statistics card component for displaying key metrics
 */
function StatsCard({
  title,
  value,
  subtitle,
  icon,
  color = 'primary',
  action,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  action?: React.ReactNode;
}): React.ReactElement {
  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="text.secondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="h2" color={`${color}.main`}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar sx={{ bgcolor: `${color}.main`, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Stack>
        {action && (
          <Box sx={{ mt: 2 }}>
            {action}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Quick actions component with common tasks
 */
function QuickActions(): React.ReactElement {
  const navigate = useNavigate();

  const actions = [
    {
      label: 'Start New Chat',
      icon: <ChatIcon />,
      onClick: () => navigate('/chat'),
      color: 'primary' as const,
    },
    {
      label: 'Upload Document',
      icon: <DocumentIcon />,
      onClick: () => navigate('/documents'),
      color: 'secondary' as const,
    },
    {
      label: 'View Analytics',
      icon: <AnalyticsIcon />,
      onClick: () => navigate('/analytics'),
      color: 'success' as const,
    },
    {
      label: 'Manage Tools',
      icon: <ToolsIcon />,
      onClick: () => navigate('/tools'),
      color: 'warning' as const,
    },
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Stack spacing={1}>
          {actions.map((action, index) => (
            <Button
              key={index}
              variant="outlined"
              startIcon={action.icon}
              onClick={action.onClick}
              fullWidth
              sx={{ justifyContent: 'flex-start' }}
            >
              {action.label}
            </Button>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}

/**
 * Recent conversations list component
 */
function RecentConversations(): React.ReactElement {
  const navigate = useNavigate();
  const { data: conversationsData, isLoading } = useConversations(1, 5);

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Conversations
          </Typography>
          <LoadingSpinner message="Loading conversations..." />
        </CardContent>
      </Card>
    );
  }

  const conversations = conversationsData?.items || [];

  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h6">
            Recent Conversations
          </Typography>
          <IconButton onClick={() => navigate('/chat')}>
            <AddIcon />
          </IconButton>
        </Stack>

        {conversations.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              No conversations yet. Start your first chat!
            </Typography>
            <Button
              variant="contained"
              startIcon={<ChatIcon />}
              onClick={() => navigate('/chat')}
              sx={{ mt: 2 }}
            >
              Start Chat
            </Button>
          </Box>
        ) : (
          <List>
            {conversations.map((conversation) => (
              <ListItem
                key={conversation.id}
                component="button"
                onClick={() => navigate(`/chat/${conversation.id}`)}
              >
                <ListItemAvatar>
                  <Avatar>
                    <ChatIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={conversation.title}
                  secondary={
                    <Stack direction="row" spacing={1} alignItems="center">
                      <TimeIcon fontSize="small" />
                      <Typography variant="caption">
                        {new Date(conversation.updated_at).toLocaleDateString()}
                      </Typography>
                      {conversation.message_count && (
                        <Chip
                          label={`${conversation.message_count} messages`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Stack>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton edge="end">
                    <LaunchIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}

        {conversations.length > 0 && (
          <Button
            fullWidth
            variant="text"
            onClick={() => navigate('/chat')}
            sx={{ mt: 1 }}
          >
            View All Conversations
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Document processing status component
 */
function DocumentStatus(): React.ReactElement {
  const navigate = useNavigate();
  const { data: documentsData, isLoading } = useDocuments(1, 5);

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Document Processing
          </Typography>
          <LoadingSpinner message="Loading documents..." />
        </CardContent>
      </Card>
    );
  }

  const documents = documentsData?.items || [];
  const processingDocs = documents.filter(doc => doc.status === 'processing');
  const failedDocs = documents.filter(doc => doc.status === 'failed');

  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
          <Typography variant="h6">
            Document Processing
          </Typography>
          <IconButton onClick={() => navigate('/documents')}>
            <DocumentIcon />
          </IconButton>
        </Stack>

        {documents.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              No documents uploaded yet.
            </Typography>
            <Button
              variant="contained"
              startIcon={<DocumentIcon />}
              onClick={() => navigate('/documents')}
              sx={{ mt: 2 }}
            >
              Upload Document
            </Button>
          </Box>
        ) : (
          <>
            {processingDocs.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Currently Processing ({processingDocs.length})
                </Typography>
                {processingDocs.map((doc) => (
                  <Box key={doc.id} sx={{ mb: 1 }}>
                    <Typography variant="body2">{doc.title}</Typography>
                    <LinearProgress
                      variant="determinate"
                      value={doc.processing_progress || 0}
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                ))}
              </Box>
            )}

            {failedDocs.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="error" gutterBottom>
                  Failed Processing ({failedDocs.length})
                </Typography>
                {failedDocs.map((doc) => (
                  <Box key={doc.id} sx={{ mb: 1 }}>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <ErrorIcon color="error" fontSize="small" />
                      <Typography variant="body2">{doc.title}</Typography>
                    </Stack>
                  </Box>
                ))}
              </Box>
            )}

            <Button
              fullWidth
              variant="text"
              onClick={() => navigate('/documents')}
            >
              View All Documents
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * System health overview component
 */
function SystemHealthOverview(): React.ReactElement {
  const { data: health, isLoading } = useSystemHealth();

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Health
          </Typography>
          <LoadingSpinner message="Checking system health..." />
        </CardContent>
      </Card>
    );
  }

  if (!health) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Health
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Unable to load health status
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <SuccessIcon color="success" />;
      case 'degraded':
        return <WarningIcon color="warning" />;
      default:
        return <ErrorIcon color="error" />;
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          System Health
        </Typography>

        <Stack spacing={2}>
          <Stack direction="row" alignItems="center" spacing={1}>
            {getStatusIcon(health.status)}
            <StatusChip
              status={health.status === 'healthy' ? 'success' : health.status === 'degraded' ? 'warning' : 'error'}
              label={health.status.toUpperCase()}
            />
          </Stack>

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Service Status
            </Typography>
            <Stack spacing={1}>
              {Object.entries(health.checks).map(([service, check]) => (
                <Stack key={service} direction="row" alignItems="center" justifyContent="space-between">
                  <Typography variant="body2">{service}</Typography>
                  <StatusChip
                    status={check.status === 'healthy' ? 'success' : check.status === 'degraded' ? 'warning' : 'error'}
                    label={check.status}
                    showIcon={false}
                  />
                </Stack>
              ))}
            </Stack>
          </Box>

          <Typography variant="caption" color="text.secondary">
            Uptime: {Math.floor(health.uptime / 3600)}h {Math.floor((health.uptime % 3600) / 60)}m
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

/**
 * Main dashboard page component
 */
export default function DashboardPage(): React.ReactElement {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useSystemStats();

  return (
    <Box>
      <PageHeader
        title={`Welcome back, ${user?.full_name || 'User'}!`}
        subtitle="Here's an overview of your AI assistant platform"
      />

      <Grid container spacing={3}>
        {/* Statistics Row */}
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total Conversations"
            value={statsLoading ? '...' : stats?.total_conversations || 0}
            subtitle="All time"
            icon={<ChatIcon />}
            color="primary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Documents Processed"
            value={statsLoading ? '...' : stats?.total_documents || 0}
            subtitle="Ready for search"
            icon={<DocumentIcon />}
            color="secondary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Active Users"
            value={statsLoading ? '...' : stats?.active_users || 0}
            subtitle="Last 30 days"
            icon={<PeopleIcon />}
            color="success"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Avg Response Time"
            value={statsLoading ? '...' : `${stats?.avg_response_time || 0}ms`}
            subtitle="System performance"
            icon={<TrendingUpIcon />}
            color="warning"
          />
        </Grid>

        {/* Main Content Row */}
        <Grid item xs={12} md={8}>
          <Stack spacing={3}>
            <RecentConversations />
            <DocumentStatus />
          </Stack>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Stack spacing={3}>
            <QuickActions />
            <SystemHealthOverview />
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
}