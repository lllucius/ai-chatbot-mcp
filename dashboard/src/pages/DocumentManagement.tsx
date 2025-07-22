import React from 'react';
import { Typography, Container } from '@mui/material';

const DocumentManagement: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Document Management
      </Typography>
      <Typography variant="body1">
        Document management interface will be displayed here.
      </Typography>
    </Container>
  );
};

export default DocumentManagement;