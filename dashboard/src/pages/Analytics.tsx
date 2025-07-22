import React from 'react';
import { Typography, Container } from '@mui/material';

const Analytics: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Analytics
      </Typography>
      <Typography variant="body1">
        Analytics dashboard will be displayed here.
      </Typography>
    </Container>
  );
};

export default Analytics;