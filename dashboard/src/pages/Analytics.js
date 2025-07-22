import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
} from '@mui/material';
import {
  People,
  Description,
  Chat,
  TrendingUp,
  Download,
  DateRange,
  Schedule,
  Speed,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import axios from 'axios';

/**
 * Analytics Component
 * 
 * Comprehensive analytics dashboard providing:
 * - Real-time system metrics and KPIs
 * - User engagement and activity trends
 * - Document processing analytics
 * - Conversation insights and patterns
 * - Performance monitoring
 * - Exportable reports and data visualization
 */
const Analytics = () => {
  // State management for analytics data
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState('7d');
  const [analyticsData, setAnalyticsData] = useState({
    overview: {},
    userActivity: [],
    documentStats: [],
    conversationTrends: [],
    topUsers: [],
    systemMetrics: {},
  });

  /**
   * Fetches analytics data from the API
   */
  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Fetch different analytics endpoints
      const [overview, userActivity, documentStats, conversations, topUsers, systemMetrics] = await Promise.all([
        axios.get(`/api/v1/analytics/overview?period=${timeRange}`),
        axios.get(`/api/v1/analytics/user-activity?period=${timeRange}`),
        axios.get(`/api/v1/analytics/documents?period=${timeRange}`),
        axios.get(`/api/v1/analytics/conversations?period=${timeRange}`),
        axios.get(`/api/v1/analytics/top-users?period=${timeRange}&limit=10`),
        axios.get('/api/v1/analytics/system-metrics'),
      ]);

      setAnalyticsData({
        overview: overview.data,
        userActivity: userActivity.data.daily_activity || [],
        documentStats: documentStats.data.processing_stats || [],
        conversationTrends: conversations.data.trends || [],
        topUsers: topUsers.data.users || [],
        systemMetrics: systemMetrics.data,
      });

      setError('');
    } catch (err) {
      setError('Failed to load analytics data. Please try again.');
      console.error('Error fetching analytics:', err);
      
      // Use mock data as fallback
      setAnalyticsData({
        overview: {
          total_users: 156,
          active_users_today: 45,
          total_documents: 342,
          total_conversations: 1250,
          avg_response_time: 1.2,
          system_uptime: 99.8,
        },
        userActivity: generateMockUserActivity(),
        documentStats: generateMockDocumentStats(),
        conversationTrends: generateMockConversationTrends(),
        topUsers: generateMockTopUsers(),
        systemMetrics: {
          cpu_usage: 65,
          memory_usage: 78,
          disk_usage: 45,
          api_requests_per_minute: 120,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  // Load analytics on component mount and when time range changes
  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  /**
   * Generates mock user activity data
   */
  const generateMockUserActivity = () => {
    const days = parseInt(timeRange);
    return Array.from({ length: days }, (_, i) => {
      const date = format(subDays(new Date(), days - 1 - i), 'yyyy-MM-dd');
      return {
        date,
        active_users: Math.floor(Math.random() * 50) + 20,
        new_users: Math.floor(Math.random() * 10) + 1,
        total_sessions: Math.floor(Math.random() * 80) + 40,
      };
    });
  };

  /**
   * Generates mock document processing statistics
   */
  const generateMockDocumentStats = () => {
    const days = parseInt(timeRange);
    return Array.from({ length: days }, (_, i) => {
      const date = format(subDays(new Date(), days - 1 - i), 'yyyy-MM-dd');
      return {
        date,
        uploaded: Math.floor(Math.random() * 20) + 5,
        processed: Math.floor(Math.random() * 18) + 4,
        failed: Math.floor(Math.random() * 3),
      };
    });
  };

  /**
   * Generates mock conversation trends
   */
  const generateMockConversationTrends = () => {
    const days = parseInt(timeRange);
    return Array.from({ length: days }, (_, i) => {
      const date = format(subDays(new Date(), days - 1 - i), 'yyyy-MM-dd');
      return {
        date,
        conversations: Math.floor(Math.random() * 30) + 10,
        messages: Math.floor(Math.random() * 150) + 50,
        avg_length: Math.floor(Math.random() * 10) + 5,
      };
    });
  };

  /**
   * Generates mock top users data
   */
  const generateMockTopUsers = () => {
    const users = ['alice_dev', 'bob_admin', 'charlie_user', 'diana_analyst', 'eve_tester'];
    return users.map((username, i) => ({
      username,
      conversations: Math.floor(Math.random() * 50) + 20 - (i * 5),
      messages: Math.floor(Math.random() * 200) + 100 - (i * 20),
      documents: Math.floor(Math.random() * 20) + 5 - i,
      last_active: format(subDays(new Date(), i), 'yyyy-MM-dd'),
    }));
  };

  /**
   * Exports analytics data as JSON
   */
  const exportAnalytics = () => {
    const dataStr = JSON.stringify(analyticsData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `analytics_${timeRange}_${format(new Date(), 'yyyy-MM-dd')}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  // Chart colors
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  // Key metrics for overview cards
  const keyMetrics = [
    {
      title: 'Total Users',
      value: analyticsData.overview.total_users || 0,
      icon: <People />,
      color: 'primary',
      change: '+12%',
    },
    {
      title: 'Active Today',
      value: analyticsData.overview.active_users_today || 0,
      icon: <TrendingUp />,
      color: 'success',
      change: '+5%',
    },
    {
      title: 'Documents',
      value: analyticsData.overview.total_documents || 0,
      icon: <Description />,
      color: 'info',
      change: '+8%',
    },
    {
      title: 'Conversations',
      value: analyticsData.overview.total_conversations || 0,
      icon: <Chat />,
      color: 'warning',
      change: '+15%',
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            Analytics Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Comprehensive insights into system performance and user engagement
          </Typography>
        </div>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="14d">Last 14 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={exportAnalytics}
          >
            Export Data
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Key Metrics Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {keyMetrics.map((metric, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Card elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box>
                        <Typography color="text.secondary" gutterBottom variant="overline">
                          {metric.title}
                        </Typography>
                        <Typography variant="h4" component="div">
                          {metric.value.toLocaleString()}
                        </Typography>
                        <Chip
                          label={metric.change}
                          color="success"
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      </Box>
                      <Box
                        sx={{
                          bgcolor: `${metric.color}.light`,
                          borderRadius: 2,
                          p: 1,
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        {metric.icon}
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* System Metrics */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  System Performance
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h3" color="primary">
                        {analyticsData.systemMetrics.cpu_usage || 0}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        CPU Usage
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h3" color="warning.main">
                        {analyticsData.systemMetrics.memory_usage || 0}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Memory Usage
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  API Performance
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h3" color="success.main">
                        {analyticsData.overview.avg_response_time || 0}s
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Response Time
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h3" color="info.main">
                        {analyticsData.systemMetrics.api_requests_per_minute || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Requests/min
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>

          {/* Charts Section */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {/* User Activity Trends */}
            <Grid item xs={12} md={8}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  User Activity Trends
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={analyticsData.userActivity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="total_sessions" 
                      fill="#8884d8" 
                      stroke="#8884d8"
                      fillOpacity={0.6}
                      name="Total Sessions"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="active_users" 
                      stroke="#82ca9d" 
                      strokeWidth={2}
                      name="Active Users"
                    />
                    <Bar dataKey="new_users" fill="#ffc658" name="New Users" />
                  </ComposedChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Document Processing */}
            <Grid item xs={12} md={4}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Document Processing
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Processed', value: analyticsData.documentStats.reduce((acc, day) => acc + day.processed, 0) },
                        { name: 'Failed', value: analyticsData.documentStats.reduce((acc, day) => acc + day.failed, 0) },
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {[
                        { name: 'Processed', value: 85 },
                        { name: 'Failed', value: 15 },
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Conversation Trends */}
            <Grid item xs={12} md={8}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Conversation Analytics
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={analyticsData.conversationTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="conversations" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      name="Conversations"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="messages" 
                      stroke="#82ca9d" 
                      strokeWidth={2}
                      name="Messages"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avg_length" 
                      stroke="#ffc658" 
                      strokeWidth={2}
                      name="Avg Length"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            {/* Top Users */}
            <Grid item xs={12} md={4}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Top Active Users
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>User</TableCell>
                        <TableCell align="right">Messages</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analyticsData.topUsers.slice(0, 5).map((user, index) => (
                        <TableRow key={user.username}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Chip
                                label={index + 1}
                                size="small"
                                color={index < 3 ? 'primary' : 'default'}
                                sx={{ mr: 1, minWidth: 24 }}
                              />
                              {user.username}
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="bold">
                              {user.messages}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
};

export default Analytics;