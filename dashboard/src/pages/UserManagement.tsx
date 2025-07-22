import React from 'react';
import { Typography, Container } from '@mui/material';

const UserManagement: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        User Management
      </Typography>
      <Typography variant="body1">
        User management interface will be displayed here.
      </Typography>
    </Container>
  );
};

export default UserManagement;