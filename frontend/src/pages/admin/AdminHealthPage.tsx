/**
 * Admin Health Page - placeholder for system health monitoring
 */

import React from 'react';
import { Box, Card, CardContent, Alert } from '@mui/material';
import { PageHeader } from '../../components/common/CommonComponents';

export default function AdminHealthPage(): React.ReactElement {
  return (
    <Box>
      <PageHeader
        title="System Health"
        subtitle="Monitor system health, performance, and status"
      />
      
      <Card>
        <CardContent>
          <Alert severity="info">
            System health monitoring interface coming soon. This will include real-time 
            health status, performance metrics, error tracking, and system diagnostics.
          </Alert>
        </CardContent>
      </Card>
    </Box>
  );
}