import React from 'react';
import { Typography, Container } from '@mui/material';

const UserDashboard: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        User Dashboard
      </Typography>
      <Typography variant="body1">
        User dashboard content will be displayed here.
      </Typography>
    </Container>
  );
};

export default UserDashboard;