import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Box,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Alert,
  Snackbar,
  Fab,
} from '@mui/material';
import {
  Upload,
  Delete,
  Refresh,
  MoreVert,
  GetApp,
  Visibility,
  Edit,
  Search,
  Add,
  Notifications,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { DocumentService } from '../services';
import { Document } from '../types';

interface UploadProgress {
  id: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  message?: string;
}

const DocumentManagement: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [notifications, setNotifications] = useState<string[]>([]);
  const [notificationOpen, setNotificationOpen] = useState(false);

  useEffect(() => {
    loadDocuments();
    
    // Set up polling for upload progress
    const interval = setInterval(checkUploadProgress, 2000);
    
    return () => clearInterval(interval);
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await DocumentService.listDocuments();
      if (response.success && response.data) {
        setDocuments(response.data.items || []);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkUploadProgress = async () => {
    // Check for completed/failed uploads and show notifications
    setUploadProgress(prev => {
      const updated = prev.map(upload => {
        if (upload.status === 'uploading' && Math.random() > 0.7) {
          return { ...upload, status: 'processing' as const };
        }
        if (upload.status === 'processing' && Math.random() > 0.8) {
          const completed = Math.random() > 0.1;
          if (completed) {
            addNotification(`Document "${upload.filename}" processed successfully!`);
            return { ...upload, status: 'completed' as const, progress: 100 };
          } else {
            addNotification(`Failed to process document "${upload.filename}"`);
            return { ...upload, status: 'failed' as const, message: 'Processing failed' };
          }
        }
        if (upload.status === 'uploading') {
          return { ...upload, progress: Math.min(upload.progress + Math.random() * 20, 95) };
        }
        return upload;
      });

      // Remove completed/failed uploads after 5 seconds
      return updated.filter(upload => 
        upload.status === 'uploading' || upload.status === 'processing' ||
        (Date.now() - parseInt(upload.id)) < 5000
      );
    });
  };

  const addNotification = (message: string) => {
    setNotifications(prev => [...prev, message]);
    setNotificationOpen(true);
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      const uploadId = Date.now().toString() + Math.random().toString(36).substr(2, 9);
      
      // Add to upload progress
      setUploadProgress(prev => [...prev, {
        id: uploadId,
        filename: file.name,
        progress: 0,
        status: 'uploading',
      }]);

      // Simulate upload - in real implementation, this would be actual file upload
      setTimeout(() => {
        setUploadProgress(prev => 
          prev.map(upload => 
            upload.id === uploadId 
              ? { ...upload, progress: 100, status: 'processing' }
              : upload
          )
        );
      }, 2000 + Math.random() * 3000);
    });

    setUploadDialogOpen(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    multiple: true,
  });

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, document: Document) => {
    setAnchorEl(event.currentTarget);
    setSelectedDocument(document);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDocument(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Document Management</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            startIcon={<Upload />}
            onClick={() => setUploadDialogOpen(true)}
          >
            Upload Documents
          </Button>
          <IconButton onClick={loadDocuments}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Upload Progress Cards */}
      {uploadProgress.length > 0 && (
        <Grid container spacing={2} mb={3}>
          {uploadProgress.map(upload => (
            <Grid item xs={12} md={6} lg={4} key={upload.id}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" noWrap>
                    {upload.filename}
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1} mt={1}>
                    <LinearProgress 
                      variant="determinate" 
                      value={upload.progress} 
                      sx={{ flexGrow: 1 }}
                    />
                    <Typography variant="caption">
                      {Math.round(upload.progress)}%
                    </Typography>
                  </Box>
                  <Chip 
                    label={upload.status}
                    size="small"
                    color={getStatusColor(upload.status) as any}
                    sx={{ mt: 1 }}
                  />
                  {upload.message && (
                    <Typography variant="caption" color="error" display="block">
                      {upload.message}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Search */}
      <Box mb={3}>
        <TextField
          fullWidth
          placeholder="Search documents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
        />
      </Box>

      {/* Documents Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Filename</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Upload Date</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDocuments.map((document) => (
              <TableRow key={document.id}>
                <TableCell>{document.title}</TableCell>
                <TableCell>{document.filename}</TableCell>
                <TableCell>
                  <Chip 
                    label={document.processing_status || 'completed'}
                    size="small"
                    color={getStatusColor(document.processing_status || 'completed') as any}
                  />
                </TableCell>
                <TableCell>
                  {new Date(document.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  {document.file_size ? `${Math.round(document.file_size / 1024)} KB` : 'N/A'}
                </TableCell>
                <TableCell>
                  <IconButton
                    onClick={(e) => handleMenuClick(e, document)}
                    size="small"
                  >
                    <MoreVert />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <Visibility sx={{ mr: 1 }} /> View Details
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <GetApp sx={{ mr: 1 }} /> Download
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Edit sx={{ mr: 1 }} /> Edit
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Refresh sx={{ mr: 1 }} /> Reprocess
        </MenuItem>
        <MenuItem onClick={handleMenuClose} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} /> Delete
        </MenuItem>
      </Menu>

      {/* Upload Dialog */}
      <Dialog 
        open={uploadDialogOpen} 
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload Documents</DialogTitle>
        <DialogContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'transparent',
            }}
          >
            <input {...getInputProps()} />
            <Upload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              or click to select files
            </Typography>
            <Typography variant="caption" display="block" mt={1}>
              Supported formats: PDF, DOCX, TXT, MD
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Notifications */}
      <Snackbar
        open={notificationOpen}
        autoHideDuration={4000}
        onClose={() => setNotificationOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setNotificationOpen(false)} 
          severity="success"
          sx={{ width: '100%' }}
        >
          {notifications[notifications.length - 1]}
        </Alert>
      </Snackbar>

      {/* Floating Notification Button */}
      {notifications.length > 0 && (
        <Fab
          color="primary"
          aria-label="notifications"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => setNotificationOpen(true)}
        >
          <Notifications />
        </Fab>
      )}
    </Container>
  );
};

export default DocumentManagement;