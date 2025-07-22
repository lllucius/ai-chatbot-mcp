import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Chat,
  Description,
  Schedule,
  TrendingUp,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useAuth } from '../services/AuthContext';

const UserDashboard = () => {
  const { user } = useAuth();

  // Mock user data - replace with real API calls
  const userStats = {
    totalConversations: 42,
    documentsUploaded: 12,
    messagesThisWeek: 156,
    averageSessionTime: '8.5 min',
  };

  const conversationHistory = [
    { date: '2024-01-01', conversations: 3, messages: 15 },
    { date: '2024-01-02', conversations: 5, messages: 22 },
    { date: '2024-01-03', conversations: 2, messages: 10 },
    { date: '2024-01-04', conversations: 4, messages: 18 },
    { date: '2024-01-05', conversations: 6, messages: 28 },
    { date: '2024-01-06', conversations: 3, messages: 12 },
    { date: '2024-01-07', conversations: 7, messages: 32 },
  ];

  const recentConversations = [
    { 
      id: 1, 
      title: "Python API Development", 
      lastMessage: "How do I implement rate limiting?",
      timestamp: "2 hours ago",
      messageCount: 15 
    },
    { 
      id: 2, 
      title: "React Best Practices", 
      lastMessage: "What's the difference between useState and useReducer?",
      timestamp: "1 day ago",
      messageCount: 8 
    },
    { 
      id: 3, 
      title: "Database Design", 
      lastMessage: "Should I use MongoDB or PostgreSQL?",
      timestamp: "2 days ago",
      messageCount: 12 
    },
  ];

  const recentDocuments = [
    { id: 1, title: "API Documentation", type: "PDF", size: "2.4 MB", status: "Processed" },
    { id: 2, title: "User Manual", type: "DOCX", size: "1.8 MB", status: "Processing" },
    { id: 3, title: "Project Notes", type: "TXT", size: "156 KB", status: "Processed" },
  ];

  const StatCard = ({ title, value, icon, color = 'primary', subtitle }) => (
    <Card elevation={2}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" gutterBottom variant="overline">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              bgcolor: `${color}.light`,
              borderRadius: 2,
              p: 1,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome back, {user?.full_name || user?.username}!
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 4 }}>
        Here's your activity summary and recent interactions
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Conversations"
            value={userStats.totalConversations}
            icon={<Chat sx={{ color: 'primary.main' }} />}
            subtitle="Total discussions"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Documents"
            value={userStats.documentsUploaded}
            icon={<Description sx={{ color: 'secondary.main' }} />}
            color="secondary"
            subtitle="Uploaded & processed"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Messages"
            value={userStats.messagesThisWeek}
            icon={<TrendingUp sx={{ color: 'success.main' }} />}
            color="success"
            subtitle="This week"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg. Session"
            value={userStats.averageSessionTime}
            icon={<Schedule sx={{ color: 'warning.main' }} />}
            color="warning"
            subtitle="Per conversation"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Activity Chart */}
        <Grid item xs={12} md={8}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Your Activity (Last 7 Days)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={conversationHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="conversations" 
                  stroke="#2196f3" 
                  strokeWidth={2}
                  name="Conversations"
                />
                <Line 
                  type="monotone" 
                  dataKey="messages" 
                  stroke="#f50057" 
                  strokeWidth={2}
                  name="Messages"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Conversations */}
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ p: 3, height: 380 }}>
            <Typography variant="h6" gutterBottom>
              Recent Conversations
            </Typography>
            <List sx={{ height: 300, overflow: 'auto' }}>
              {recentConversations.map((conversation) => (
                <ListItem key={conversation.id} alignItems="flex-start" sx={{ px: 0 }}>
                  <ListItemIcon>
                    <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                      <Chat sx={{ fontSize: 16 }} />
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={conversation.title}
                    secondary={
                      <>
                        <Typography variant="body2" color="text.secondary">
                          {conversation.lastMessage}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip 
                            label={`${conversation.messageCount} messages`}
                            size="small"
                            variant="outlined"
                            color="primary"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {conversation.timestamp}
                          </Typography>
                        </Box>
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Recent Documents */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Documents
            </Typography>
            <List>
              {recentDocuments.map((doc) => (
                <ListItem key={doc.id} sx={{ px: 0 }}>
                  <ListItemIcon>
                    <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                      <Description sx={{ fontSize: 16 }} />
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={doc.title}
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Chip 
                          label={doc.type}
                          size="small"
                          variant="outlined"
                        />
                        <Chip 
                          label={doc.status}
                          size="small"
                          color={doc.status === 'Processed' ? 'success' : 'warning'}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {doc.size}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Weekly Messages Chart */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Daily Messages
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={conversationHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="messages" fill="#2196f3" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default UserDashboard;