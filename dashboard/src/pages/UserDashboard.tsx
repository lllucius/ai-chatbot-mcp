import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  LinearProgress,
} from '@mui/material';
import {
  AccountCircle as AccountIcon,
  Description as DocumentIcon,
  Chat as ChatIcon,
  TrendingUp as TrendingIcon,
  CloudUpload as UploadIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { UserService, ConversationService, DocumentService, HealthService } from '../services';
import { useAuth } from '../services/AuthContext';
import { User, Conversation, Document } from '../types';

interface DashboardStats {
  totalDocuments: number;
  totalConversations: number;
  totalMessages: number;
  documentsProcessing: number;
  documentsCompleted: number;
  documentsFailed: number;
  recentActivity: Array<{
    type: string;
    title: string;
    timestamp: string;
    status?: string;
  }>;
}

const UserDashboard: React.FC = () => {
  const { user } = useAuth();
  const [userProfile, setUserProfile] = useState<User | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load user profile
      const profileResponse = await UserService.getMyProfile();
      if (profileResponse.success && profileResponse.data) {
        setUserProfile(profileResponse.data);
      }

      // Load conversations
      const conversationsResponse = await ConversationService.listConversations({ page: 1, size: 100 });
      const conversations = conversationsResponse.success ? conversationsResponse.data?.items || [] : [];

      // Load documents
      const documentsResponse = await DocumentService.listDocuments({ page: 1, size: 100 });
      const documents = documentsResponse.success ? documentsResponse.data?.items || [] : [];

      // Load system health
      const healthResponse = await HealthService.getHealth();
      if (healthResponse.success) {
        setSystemHealth(healthResponse.data);
      }

      // Calculate stats
      const totalMessages = conversations.reduce((sum, conv) => sum + conv.message_count, 0);
      const documentsProcessing = documents.filter(doc => doc.processing_status === 'processing').length;
      const documentsCompleted = documents.filter(doc => doc.processing_status === 'completed').length;
      const documentsFailed = documents.filter(doc => doc.processing_status === 'failed').length;

      // Create recent activity
      const recentActivity = [
        ...conversations.slice(0, 3).map(conv => ({
          type: 'conversation',
          title: conv.title,
          timestamp: conv.updated_at,
          status: conv.is_active ? 'Active' : 'Inactive',
        })),
        ...documents.slice(0, 3).map(doc => ({
          type: 'document',
          title: doc.title,
          timestamp: doc.updated_at,
          status: doc.processing_status,
        })),
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 5);

      setStats({
        totalDocuments: documents.length,
        totalConversations: conversations.length,
        totalMessages,
        documentsProcessing,
        documentsCompleted,
        documentsFailed,
        recentActivity,
      });

    } catch (error: any) {
      console.error('Failed to load dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'active':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
      case 'inactive':
        return 'error';
      default:
        return 'default';
    }
  };

  const documentStatusData = stats ? [
    { name: 'Completed', value: stats.documentsCompleted, color: '#4caf50' },
    { name: 'Processing', value: stats.documentsProcessing, color: '#ff9800' },
    { name: 'Failed', value: stats.documentsFailed, color: '#f44336' },
  ].filter(item => item.value > 0) : [];

  const activityData = stats ? [
    { name: 'Documents', value: stats.totalDocuments },
    { name: 'Conversations', value: stats.totalConversations },
    { name: 'Messages', value: stats.totalMessages },
  ] : [];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* User Profile Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccountIcon sx={{ mr: 2, fontSize: 40, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h6">{userProfile?.full_name || userProfile?.username}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {userProfile?.email}
                  </Typography>
                </Box>
              </Box>
              
              <Typography variant="body2" color="text.secondary">
                Member since: {userProfile ? formatDate(userProfile.created_at) : '—'}
              </Typography>
              
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Chip 
                  label={userProfile?.is_active ? 'Active' : 'Inactive'} 
                  size="small" 
                  color={userProfile?.is_active ? 'success' : 'default'} 
                />
                {userProfile?.is_superuser && (
                  <Chip label="Admin" size="small" color="primary" />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <DocumentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4">{stats?.totalDocuments || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Documents</Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <ChatIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                <Typography variant="h4">{stats?.totalConversations || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Conversations</Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <TrendingIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4">{stats?.totalMessages || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Messages</Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <UploadIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant="h4">{stats?.documentsProcessing || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Processing</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Grid>

        {/* Document Status Chart */}
        {documentStatusData.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>Document Status</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={documentStatusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {documentStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        )}

        {/* Activity Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Activity Overview</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Recent Activity</Typography>
            <List>
              {stats?.recentActivity.map((activity, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {activity.type === 'conversation' ? (
                      <ChatIcon color="primary" />
                    ) : (
                      <DocumentIcon color="secondary" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={activity.title}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          {formatDateTime(activity.timestamp)}
                        </Typography>
                        {activity.status && (
                          <Chip 
                            label={activity.status} 
                            size="small" 
                            color={getStatusColor(activity.status) as any}
                            sx={{ mt: 0.5 }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
              {(!stats?.recentActivity || stats.recentActivity.length === 0) && (
                <ListItem>
                  <ListItemText primary="No recent activity" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* System Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>System Status</Typography>
            {systemHealth ? (
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ScheduleIcon sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="body1">
                    System: Online
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary">
                  Last updated: {formatDateTime(systemHealth.timestamp || new Date().toISOString())}
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" gutterBottom>System Health</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={100} 
                    color="success"
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Unable to load system status
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default UserDashboard;