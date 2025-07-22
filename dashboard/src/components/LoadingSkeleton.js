import React from 'react';
import { Box, Skeleton, Grid, Paper, Card, CardContent } from '@mui/material';

/**
 * LoadingSkeleton Component
 * 
 * Provides skeleton loading screens for different page types to improve
 * perceived performance while data is being fetched.
 */

/**
 * Dashboard loading skeleton with cards and charts
 */
export const DashboardSkeleton = () => (
  <Box>
    <Skeleton variant="text" width="40%" height={48} sx={{ mb: 1 }} />
    <Skeleton variant="text" width="60%" height={24} sx={{ mb: 3 }} />
    
    {/* Stats cards */}
    <Grid container spacing={3} sx={{ mb: 4 }}>
      {[1, 2, 3, 4].map((i) => (
        <Grid item xs={12} sm={6} md={3} key={i}>
          <Card>
            <CardContent>
              <Skeleton variant="text" width="60%" height={20} />
              <Skeleton variant="text" width="40%" height={40} />
              <Skeleton variant="text" width="50%" height={16} />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>

    {/* Charts */}
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Paper sx={{ p: 3 }}>
          <Skeleton variant="text" width="30%" height={28} sx={{ mb: 2 }} />
          <Skeleton variant="rectangular" width="100%" height={300} />
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 3 }}>
          <Skeleton variant="text" width="40%" height={28} sx={{ mb: 2 }} />
          <Skeleton variant="rectangular" width="100%" height={300} />
        </Paper>
      </Grid>
    </Grid>
  </Box>
);

/**
 * Table loading skeleton for lists and data tables
 */
export const TableSkeleton = ({ rows = 5, columns = 4 }) => (
  <Box>
    <Skeleton variant="text" width="40%" height={48} sx={{ mb: 1 }} />
    <Skeleton variant="text" width="60%" height={24} sx={{ mb: 3 }} />
    
    {/* Search bar */}
    <Paper sx={{ p: 2, mb: 3 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Skeleton variant="rectangular" height={40} />
        </Grid>
        <Grid item xs={12} md={3}>
          <Skeleton variant="rectangular" height={40} />
        </Grid>
        <Grid item xs={12} md={3}>
          <Skeleton variant="rectangular" height={40} />
        </Grid>
      </Grid>
    </Paper>

    {/* Table */}
    <Paper>
      {/* Table header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Grid container spacing={2}>
          {Array.from({ length: columns }).map((_, i) => (
            <Grid item xs={12 / columns} key={i}>
              <Skeleton variant="text" width="80%" height={20} />
            </Grid>
          ))}
        </Grid>
      </Box>
      
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <Box key={rowIndex} sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Grid container spacing={2} alignItems="center">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Grid item xs={12 / columns} key={colIndex}>
                {colIndex === 0 ? (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Skeleton variant="circular" width={32} height={32} sx={{ mr: 2 }} />
                    <Box>
                      <Skeleton variant="text" width="80%" height={20} />
                      <Skeleton variant="text" width="60%" height={16} />
                    </Box>
                  </Box>
                ) : colIndex === columns - 1 ? (
                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                  </Box>
                ) : (
                  <Skeleton variant="text" width="70%" height={20} />
                )}
              </Grid>
            ))}
          </Grid>
        </Box>
      ))}
    </Paper>
  </Box>
);

/**
 * Chat interface loading skeleton
 */
export const ChatSkeleton = () => (
  <Box sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
    <Skeleton variant="text" width="40%" height={48} sx={{ mb: 3 }} />
    
    {/* Messages area */}
    <Paper sx={{ flex: 1, p: 2, mb: 2 }}>
      {[1, 2, 3].map((i) => (
        <Box key={i} sx={{ display: 'flex', mb: 3, alignItems: 'flex-start' }}>
          <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
          <Box sx={{ flex: 1 }}>
            <Skeleton variant="text" width="20%" height={16} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="80%" height={20} />
            <Skeleton variant="text" width="60%" height={20} />
          </Box>
        </Box>
      ))}
    </Paper>

    {/* Input area */}
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Skeleton variant="rectangular" sx={{ flex: 1 }} height={40} />
        <Skeleton variant="rectangular" width={100} height={40} />
      </Box>
    </Paper>
  </Box>
);

/**
 * Profile/Settings loading skeleton
 */
export const ProfileSkeleton = () => (
  <Box>
    <Skeleton variant="text" width="40%" height={48} sx={{ mb: 1 }} />
    <Skeleton variant="text" width="60%" height={24} sx={{ mb: 3 }} />
    
    <Grid container spacing={3}>
      {/* Main content */}
      <Grid item xs={12} md={8}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Skeleton variant="circular" width={24} height={24} sx={{ mr: 2 }} />
            <Skeleton variant="text" width="30%" height={28} />
          </Box>
          
          <Grid container spacing={3}>
            {Array.from({ length: 6 }).map((_, i) => (
              <Grid item xs={12} md={6} key={i}>
                <Skeleton variant="rectangular" height={56} />
              </Grid>
            ))}
          </Grid>
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Skeleton variant="rectangular" width={120} height={40} />
          </Box>
        </Paper>
        
        {/* Additional sections */}
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Skeleton variant="circular" width={24} height={24} sx={{ mr: 2 }} />
            <Skeleton variant="text" width="30%" height={28} />
          </Box>
          <Grid container spacing={3}>
            {Array.from({ length: 3 }).map((_, i) => (
              <Grid item xs={12} md={4} key={i}>
                <Skeleton variant="rectangular" height={56} />
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Grid>

      {/* Sidebar */}
      <Grid item xs={12} md={4}>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Skeleton variant="circular" width={60} height={60} sx={{ mr: 2 }} />
              <Box>
                <Skeleton variant="text" width="80%" height={24} />
                <Skeleton variant="rectangular" width={60} height={20} />
              </Box>
            </Box>
            <Skeleton variant="text" width="100%" height={16} />
            <Skeleton variant="text" width="80%" height={16} />
          </CardContent>
        </Card>
        
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Skeleton variant="circular" width={24} height={24} sx={{ mr: 2 }} />
            <Skeleton variant="text" width="50%" height={24} />
          </Box>
          {Array.from({ length: 5 }).map((_, i) => (
            <Box key={i} sx={{ mb: 2 }}>
              <Skeleton variant="text" width="90%" height={16} />
              <Skeleton variant="text" width="60%" height={14} />
            </Box>
          ))}
        </Paper>
      </Grid>
    </Grid>
  </Box>
);

/**
 * Generic form loading skeleton
 */
export const FormSkeleton = ({ fields = 6 }) => (
  <Box>
    <Skeleton variant="text" width="40%" height={48} sx={{ mb: 1 }} />
    <Skeleton variant="text" width="60%" height={24} sx={{ mb: 3 }} />
    
    <Paper sx={{ p: 3 }}>
      <Grid container spacing={3}>
        {Array.from({ length: fields }).map((_, i) => (
          <Grid item xs={12} md={6} key={i}>
            <Skeleton variant="text" width="30%" height={20} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={56} />
          </Grid>
        ))}
      </Grid>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Skeleton variant="rectangular" width={100} height={40} />
        <Skeleton variant="rectangular" width={120} height={40} />
      </Box>
    </Paper>
  </Box>
);

/**
 * Analytics charts loading skeleton
 */
export const AnalyticsSkeleton = () => (
  <Box>
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
      <Box>
        <Skeleton variant="text" width="40%" height={48} />
        <Skeleton variant="text" width="60%" height={24} />
      </Box>
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Skeleton variant="rectangular" width={120} height={40} />
        <Skeleton variant="rectangular" width={100} height={40} />
      </Box>
    </Box>

    {/* KPI Cards */}
    <Grid container spacing={3} sx={{ mb: 4 }}>
      {[1, 2, 3, 4].map((i) => (
        <Grid item xs={12} sm={6} md={3} key={i}>
          <Card>
            <CardContent>
              <Skeleton variant="text" width="60%" height={20} />
              <Skeleton variant="text" width="40%" height={40} />
              <Skeleton variant="rectangular" width={60} height={20} />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>

    {/* Charts */}
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Paper sx={{ p: 3 }}>
          <Skeleton variant="text" width="30%" height={28} sx={{ mb: 2 }} />
          <Skeleton variant="rectangular" width="100%" height={300} />
        </Paper>
      </Grid>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 3 }}>
          <Skeleton variant="text" width="40%" height={28} sx={{ mb: 2 }} />
          <Skeleton variant="circular" width={200} height={200} sx={{ mx: 'auto' }} />
        </Paper>
      </Grid>
    </Grid>
  </Box>
);

const LoadingSkeleton = {
  Dashboard: DashboardSkeleton,
  Table: TableSkeleton,
  Chat: ChatSkeleton,
  Profile: ProfileSkeleton,
  Form: FormSkeleton,
  Analytics: AnalyticsSkeleton,
};

export default LoadingSkeleton;