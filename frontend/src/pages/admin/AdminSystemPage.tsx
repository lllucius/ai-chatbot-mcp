/**
 * Admin System Page - placeholder for system settings
 */

import React from 'react';
import { Box, Card, CardContent, Alert } from '@mui/material';
import { PageHeader } from '../../components/common/CommonComponents';

export default function AdminSystemPage(): React.ReactElement {
  return (
    <Box>
      <PageHeader
        title="System Settings"
        subtitle="Configure system-wide settings and parameters"
      />
      
      <Card>
        <CardContent>
          <Alert severity="info">
            System administration interface coming soon. This will include configuration 
            management, system maintenance, backup controls, and security settings.
          </Alert>
        </CardContent>
      </Card>
    </Box>
  );
}