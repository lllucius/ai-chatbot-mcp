import React from 'react';
import { Typography, Container } from '@mui/material';

const AdminDashboard: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>
      <Typography variant="body1">
        Admin dashboard content will be displayed here.
      </Typography>
    </Container>
  );
};

export default AdminDashboard;