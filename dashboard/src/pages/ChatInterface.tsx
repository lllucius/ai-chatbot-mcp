import React from 'react';
import { Typography, Container } from '@mui/material';

const ChatInterface: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Chat Interface
      </Typography>
      <Typography variant="body1">
        Chat interface will be displayed here.
      </Typography>
    </Container>
  );
};

export default ChatInterface;