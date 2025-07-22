import React from 'react';
import { Box, Skeleton, Card, CardContent } from '@mui/material';

interface LoadingSkeletonProps {
  type?: 'card' | 'list' | 'table' | 'chat';
  count?: number;
  height?: number | string;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ 
  type = 'card', 
  count = 3, 
  height = 100 
}) => {
  const renderCardSkeleton = () => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Skeleton variant="text" sx={{ fontSize: '1.5rem', mb: 1 }} />
        <Skeleton variant="text" sx={{ fontSize: '1rem', mb: 1 }} />
        <Skeleton variant="rectangular" height={height} />
      </CardContent>
    </Card>
  );

  const renderListSkeleton = () => (
    <Box sx={{ mb: 2 }}>
      <Skeleton variant="circular" width={40} height={40} sx={{ mb: 1 }} />
      <Skeleton variant="text" sx={{ fontSize: '1rem', mb: 0.5 }} />
      <Skeleton variant="text" sx={{ fontSize: '0.875rem' }} />
    </Box>
  );

  const renderTableSkeleton = () => (
    <Box sx={{ mb: 1 }}>
      <Skeleton variant="rectangular" height={50} sx={{ mb: 1 }} />
      <Skeleton variant="text" sx={{ fontSize: '1rem' }} />
    </Box>
  );

  const renderChatSkeleton = () => (
    <Box sx={{ mb: 2, display: 'flex', alignItems: 'flex-start', gap: 1 }}>
      <Skeleton variant="circular" width={32} height={32} />
      <Box sx={{ flex: 1 }}>
        <Skeleton variant="text" sx={{ fontSize: '0.875rem', mb: 0.5, width: '80%' }} />
        <Skeleton variant="rectangular" height={60} sx={{ borderRadius: 1 }} />
      </Box>
    </Box>
  );

  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return renderCardSkeleton();
      case 'list':
        return renderListSkeleton();
      case 'table':
        return renderTableSkeleton();
      case 'chat':
        return renderChatSkeleton();
      default:
        return renderCardSkeleton();
    }
  };

  return (
    <Box>
      {Array.from({ length: count }, (_, index) => (
        <Box key={index}>
          {renderSkeleton()}
        </Box>
      ))}
    </Box>
  );
};

export default LoadingSkeleton;