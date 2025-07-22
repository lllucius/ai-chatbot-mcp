import React from 'react';
import { Typography, Container } from '@mui/material';

const UserProfile: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        User Profile
      </Typography>
      <Typography variant="body1">
        User profile settings will be displayed here.
      </Typography>
    </Container>
  );
};

export default UserProfile;