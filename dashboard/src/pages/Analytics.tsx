import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  TrendingUp,
  People,
  Chat,
  Description,
  AccessTime,
  Memory,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { UserService, ConversationService, DocumentService } from '../services';

interface AnalyticsData {
  totalUsers: number;
  totalConversations: number;
  totalDocuments: number;
  totalMessages: number;
  avgResponseTime: number;
  totalTokens: number;
  dailyActivity: Array<{
    date: string;
    conversations: number;
    messages: number;
    tokens: number;
  }>;
  userActivity: Array<{
    username: string;
    messageCount: number;
    conversationCount: number;
  }>;
  documentStats: Array<{
    type: string;
    count: number;
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Analytics: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Mock data for now - in real implementation, these would be API calls
      const mockData: AnalyticsData = {
        totalUsers: 45,
        totalConversations: 234,
        totalDocuments: 89,
        totalMessages: 1456,
        avgResponseTime: 1250,
        totalTokens: 45678,
        dailyActivity: [
          { date: '2024-01-15', conversations: 12, messages: 45, tokens: 2340 },
          { date: '2024-01-16', conversations: 18, messages: 67, tokens: 3120 },
          { date: '2024-01-17', conversations: 15, messages: 52, tokens: 2890 },
          { date: '2024-01-18', conversations: 22, messages: 78, tokens: 4120 },
          { date: '2024-01-19', conversations: 19, messages: 61, tokens: 3456 },
          { date: '2024-01-20', conversations: 25, messages: 89, tokens: 4789 },
          { date: '2024-01-21', conversations: 21, messages: 74, tokens: 3967 },
        ],
        userActivity: [
          { username: 'admin', messageCount: 156, conversationCount: 23 },
          { username: 'user1', messageCount: 89, conversationCount: 12 },
          { username: 'user2', messageCount: 67, conversationCount: 8 },
          { username: 'user3', messageCount: 45, conversationCount: 6 },
          { username: 'user4', messageCount: 34, conversationCount: 4 },
        ],
        documentStats: [
          { type: 'PDF', count: 45 },
          { type: 'DOCX', count: 23 },
          { type: 'TXT', count: 12 },
          { type: 'MD', count: 9 },
        ],
      };
      
      setAnalyticsData(mockData);
    } catch (err) {
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
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

  if (error) {
    return (
      <Container>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Analytics Dashboard
        </Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            label="Time Range"
          >
            <MenuItem value="1d">Last 24h</MenuItem>
            <MenuItem value="7d">Last 7 days</MenuItem>
            <MenuItem value="30d">Last 30 days</MenuItem>
            <MenuItem value="90d">Last 90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {analyticsData && (
        <>
          {/* Key Metrics Cards */}
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} sm={6} md={2}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1}>
                    <People color="primary" />
                    <Typography variant="h6">{analyticsData.totalUsers}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Users
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Chat color="primary" />
                    <Typography variant="h6">{analyticsData.totalConversations}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Conversations
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Description color="primary" />
                    <Typography variant="h6">{analyticsData.totalDocuments}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Documents
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1}>
                    <AccessTime color="primary" />
                    <Typography variant="h6">{analyticsData.avgResponseTime}ms</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Avg Response Time
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Memory color="primary" />
                    <Typography variant="h6">{analyticsData.totalTokens.toLocaleString()}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Tokens
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1}>
                    <TrendingUp color="primary" />
                    <Typography variant="h6">{analyticsData.totalMessages}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Messages
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Daily Activity Chart */}
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} lg={8}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Daily Activity
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={analyticsData.dailyActivity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="conversations" stroke="#8884d8" name="Conversations" />
                    <Line type="monotone" dataKey="messages" stroke="#82ca9d" name="Messages" />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
            
            <Grid item xs={12} lg={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Document Types
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={analyticsData.documentStats}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                      label={({ type, count }) => `${type}: ${count}`}
                    >
                      {analyticsData.documentStats.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          </Grid>

          {/* User Activity */}
          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  User Activity
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analyticsData.userActivity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="username" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="messageCount" fill="#8884d8" name="Messages" />
                    <Bar dataKey="conversationCount" fill="#82ca9d" name="Conversations" />
                  </BarChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
            
            <Grid item xs={12} lg={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Token Usage Over Time
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={analyticsData.dailyActivity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="tokens" stroke="#ff7300" name="Tokens Used" />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  );
};

export default Analytics;