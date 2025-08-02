/**
 * Analytics Page Component
 * 
 * This page provides comprehensive analytics and insights for the AI Chatbot system:
 * - System overview with key metrics
 * - Interactive charts and visualizations using Chart.js
 * - Usage trends over time
 * - User activity statistics
 * - Performance metrics and health indicators
 * - Exportable reports and data visualization
 * - Real-time and historical data analysis
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  Tooltip,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Person as PersonIcon,
  Chat as ChatIcon,
  Description as DocumentIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

import { 
  PageHeader, 
  LoadingSpinner, 
  StatusChip,
  DataTable,
  type DataTableColumn,
} from '../components/common/CommonComponents';
import {
  useSystemStats,
  useUsageAnalytics,
  useUserStats,
  usePerformanceMetrics,
} from '../hooks/api';
import type { UsageAnalytics, UserStats, SystemStats } from '../types/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  Filler
);

// =============================================================================
// Analytics Stats Card Component
// =============================================================================

/**
 * Props for AnalyticsStatsCard component
 */
interface AnalyticsStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  trend?: {
    value: number;
    label: string;
    isPositive: boolean;
  };
}

/**
 * Statistics card component for analytics data
 */
function AnalyticsStatsCard({
  title,
  value,
  subtitle,
  icon,
  color = 'primary',
  trend,
}: AnalyticsStatsCardProps): JSX.Element {
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
            {trend && (
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mt: 1 }}>
                {trend.isPositive ? (
                  <TrendingUpIcon color="success" fontSize="small" />
                ) : (
                  <TrendingDownIcon color="error" fontSize="small" />
                )}
                <Typography 
                  variant="caption" 
                  color={trend.isPositive ? 'success.main' : 'error.main'}
                >
                  {trend.value > 0 ? '+' : ''}{trend.value}% {trend.label}
                </Typography>
              </Stack>
            )}
          </Box>
          <Avatar sx={{ bgcolor: `${color}.main`, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Stack>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Usage Trends Chart Component
// =============================================================================

/**
 * Props for UsageTrendsChart component
 */
interface UsageTrendsChartProps {
  data: UsageAnalytics[];
  period: number;
}

/**
 * Line chart showing usage trends over time
 */
function UsageTrendsChart({ data, period }: UsageTrendsChartProps): JSX.Element {
  const chartData = useMemo(() => {
    const labels = data.map(item => new Date(item.date).toLocaleDateString());
    
    return {
      labels,
      datasets: [
        {
          label: 'Messages',
          data: data.map(item => item.message_count),
          borderColor: 'rgb(25, 118, 210)',
          backgroundColor: 'rgba(25, 118, 210, 0.1)',
          fill: true,
          tension: 0.4,
        },
        {
          label: 'Active Users',
          data: data.map(item => item.active_users),
          borderColor: 'rgb(220, 0, 78)',
          backgroundColor: 'rgba(220, 0, 78, 0.1)',
          fill: true,
          tension: 0.4,
        },
        {
          label: 'Documents Uploaded',
          data: data.map(item => item.documents_uploaded),
          borderColor: 'rgb(46, 125, 50)',
          backgroundColor: 'rgba(46, 125, 50, 0.1)',
          fill: true,
          tension: 0.4,
        },
      ],
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `Usage Trends (Last ${period} days)`,
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Count',
        },
        beginAtZero: true,
      },
    },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ height: 400 }}>
          <Line data={chartData} options={options} />
        </Box>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Token Usage Chart Component
// =============================================================================

/**
 * Props for TokenUsageChart component
 */
interface TokenUsageChartProps {
  data: UsageAnalytics[];
}

/**
 * Bar chart showing token usage over time
 */
function TokenUsageChart({ data }: TokenUsageChartProps): JSX.Element {
  const chartData = useMemo(() => {
    const labels = data.map(item => new Date(item.date).toLocaleDateString());
    
    return {
      labels,
      datasets: [
        {
          label: 'Tokens Used',
          data: data.map(item => item.tokens_used),
          backgroundColor: 'rgba(255, 152, 0, 0.8)',
          borderColor: 'rgb(255, 152, 0)',
          borderWidth: 1,
        },
      ],
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Token Usage Over Time',
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Tokens',
        },
        beginAtZero: true,
      },
    },
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ height: 300 }}>
          <Bar data={chartData} options={options} />
        </Box>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Performance Metrics Chart Component
// =============================================================================

/**
 * Props for PerformanceChart component
 */
interface PerformanceChartProps {
  data: UsageAnalytics[];
}

/**
 * Line chart showing response time performance
 */
function PerformanceChart({ data }: PerformanceChartProps): JSX.Element {
  const chartData = useMemo(() => {
    const labels = data.map(item => new Date(item.date).toLocaleDateString());
    
    return {
      labels,
      datasets: [
        {
          label: 'Avg Response Time (ms)',
          data: data.map(item => item.avg_response_time),
          borderColor: 'rgb(156, 39, 176)',
          backgroundColor: 'rgba(156, 39, 176, 0.1)',
          fill: true,
          tension: 0.4,
        },
      ],
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'System Performance',
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Response Time (ms)',
        },
        beginAtZero: true,
      },
    },
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ height: 300 }}>
          <Line data={chartData} options={options} />
        </Box>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// User Activity Distribution Chart Component
// =============================================================================

/**
 * Props for UserActivityChart component
 */
interface UserActivityChartProps {
  stats: SystemStats;
}

/**
 * Doughnut chart showing user activity distribution
 */
function UserActivityChart({ stats }: UserActivityChartProps): JSX.Element {
  const chartData = useMemo(() => {
    const activeUsers = stats.active_users;
    const inactiveUsers = Math.max(0, stats.total_users - activeUsers);
    
    return {
      labels: ['Active Users', 'Inactive Users'],
      datasets: [
        {
          data: [activeUsers, inactiveUsers],
          backgroundColor: [
            'rgba(46, 125, 50, 0.8)',
            'rgba(158, 158, 158, 0.8)',
          ],
          borderColor: [
            'rgb(46, 125, 50)',
            'rgb(158, 158, 158)',
          ],
          borderWidth: 2,
        },
      ],
    };
  }, [stats]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: true,
        text: 'User Activity Distribution',
      },
    },
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ height: 300 }}>
          <Doughnut data={chartData} options={options} />
        </Box>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Top Users Table Component
// =============================================================================

/**
 * Props for TopUsersTable component
 */
interface TopUsersTableProps {
  users: UserStats[];
  loading: boolean;
}

/**
 * Table showing top users by activity
 */
function TopUsersTable({ users, loading }: TopUsersTableProps): JSX.Element {
  const columns: DataTableColumn<UserStats>[] = [
    {
      id: 'user',
      label: 'User',
      render: (_, userStat) => (
        <Stack direction="row" alignItems="center" spacing={1}>
          <Avatar sx={{ width: 32, height: 32 }}>
            {userStat.user.full_name.charAt(0).toUpperCase()}
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {userStat.user.full_name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {userStat.user.email}
            </Typography>
          </Box>
        </Stack>
      ),
    },
    {
      id: 'conversations',
      label: 'Conversations',
      render: (_, userStat) => userStat.conversation_count,
    },
    {
      id: 'messages',
      label: 'Messages',
      render: (_, userStat) => userStat.message_count,
    },
    {
      id: 'tokens',
      label: 'Tokens Used',
      render: (_, userStat) => userStat.total_tokens.toLocaleString(),
    },
    {
      id: 'documents',
      label: 'Documents',
      render: (_, userStat) => userStat.document_count,
    },
    {
      id: 'last_active',
      label: 'Last Active',
      render: (_, userStat) => new Date(userStat.last_active).toLocaleDateString(),
    },
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Top Active Users
        </Typography>
        <DataTable
          columns={columns}
          data={users}
          loading={loading}
          emptyState={{
            title: 'No user data available',
            description: 'User statistics will appear here once there is activity.',
          }}
        />
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Main Analytics Page Component
// =============================================================================

/**
 * Main analytics page component
 */
export default function AnalyticsPage(): JSX.Element {
  const [period, setPeriod] = useState(30);

  // API hooks
  const { data: systemStats, isLoading: statsLoading, refetch: refetchStats } = useSystemStats();
  const { data: usageData, isLoading: usageLoading, refetch: refetchUsage } = useUsageAnalytics(period);
  const { data: userStatsData, isLoading: userStatsLoading } = useUserStats(1, 10);
  const { data: performanceData, isLoading: performanceLoading } = usePerformanceMetrics();

  /**
   * Handle data export
   */
  const handleExportData = () => {
    const exportData = {
      systemStats,
      usageData,
      userStats: userStatsData?.items,
      performanceData,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics-export-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  /**
   * Handle refresh all data
   */
  const handleRefreshAll = () => {
    refetchStats();
    refetchUsage();
  };

  if (statsLoading) {
    return <LoadingSpinner message="Loading analytics..." />;
  }

  const stats = systemStats || {
    total_users: 0,
    active_users: 0,
    total_conversations: 0,
    total_messages: 0,
    total_documents: 0,
    total_chunks: 0,
    total_tokens_used: 0,
    avg_response_time: 0,
  };

  const usage = usageData || [];
  const users = userStatsData?.items || [];

  return (
    <Box>
      <PageHeader
        title="Analytics"
        subtitle="Comprehensive insights and performance metrics for your AI assistant"
        actions={
          <Stack direction="row" spacing={1}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Time Period</InputLabel>
              <Select
                value={period}
                onChange={(e) => setPeriod(Number(e.target.value))}
                label="Time Period"
              >
                <MenuItem value={7}>Last 7 days</MenuItem>
                <MenuItem value={30}>Last 30 days</MenuItem>
                <MenuItem value={90}>Last 90 days</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportData}
            >
              Export Data
            </Button>
            <Tooltip title="Refresh data">
              <IconButton onClick={handleRefreshAll}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        }
      />

      <Grid container spacing={3}>
        {/* Key Metrics Row */}
        <Grid item xs={12} sm={6} md={3}>
          <AnalyticsStatsCard
            title="Total Users"
            value={stats.total_users}
            subtitle={`${stats.active_users} active`}
            icon={<PersonIcon />}
            color="primary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <AnalyticsStatsCard
            title="Conversations"
            value={stats.total_conversations}
            subtitle="All time"
            icon={<ChatIcon />}
            color="secondary"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <AnalyticsStatsCard
            title="Documents"
            value={stats.total_documents}
            subtitle={`${stats.total_chunks} chunks`}
            icon={<DocumentIcon />}
            color="success"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <AnalyticsStatsCard
            title="Avg Response Time"
            value={`${stats.avg_response_time}ms`}
            subtitle="System performance"
            icon={<SpeedIcon />}
            color="warning"
          />
        </Grid>

        {/* Charts Row */}
        <Grid item xs={12} lg={8}>
          {usageLoading ? (
            <LoadingSpinner message="Loading usage trends..." />
          ) : (
            <UsageTrendsChart data={usage} period={period} />
          )}
        </Grid>

        <Grid item xs={12} lg={4}>
          <UserActivityChart stats={stats} />
        </Grid>

        {/* Secondary Charts Row */}
        <Grid item xs={12} md={6}>
          {usageLoading ? (
            <LoadingSpinner message="Loading token usage..." />
          ) : (
            <TokenUsageChart data={usage} />
          )}
        </Grid>

        <Grid item xs={12} md={6}>
          {usageLoading ? (
            <LoadingSpinner message="Loading performance data..." />
          ) : (
            <PerformanceChart data={usage} />
          )}
        </Grid>

        {/* User Statistics Table */}
        <Grid item xs={12}>
          <TopUsersTable users={users} loading={userStatsLoading} />
        </Grid>

        {/* Additional Metrics */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Overview
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="primary.main">
                      {stats.total_messages.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Messages
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="secondary.main">
                      {stats.total_tokens_used.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Tokens Used
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="success.main">
                      {stats.total_chunks.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Document Chunks
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="warning.main">
                      {Math.round((stats.active_users / Math.max(stats.total_users, 1)) * 100)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      User Engagement
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}