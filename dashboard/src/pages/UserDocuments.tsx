import React from 'react';
import { Typography, Container } from '@mui/material';

const UserDocuments: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        My Documents
      </Typography>
      <Typography variant="body1">
        User documents will be displayed here.
      </Typography>
    </Container>
  );
};

export default UserDocuments;