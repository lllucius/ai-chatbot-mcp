import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Fab,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { DocumentService } from '../services';
import { Document, DocumentUploadResponse } from '../types';

interface FileUpload {
  file: File;
  title: string;
  uploading: boolean;
  progress: number;
  error?: string;
}

const UserDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [pendingUploads, setPendingUploads] = useState<FileUpload[]>([]);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await DocumentService.listDocuments({ page: 1, size: 100 });
      if (response.success && response.data) {
        setDocuments(response.data.items);
      } else {
        setError('Failed to load documents');
      }
    } catch (error: any) {
      console.error('Failed to load documents:', error);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      const response = await DocumentService.deleteDocument(documentId);
      if (response.success) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      } else {
        setError('Failed to delete document');
      }
    } catch (error: any) {
      console.error('Failed to delete document:', error);
      setError('Failed to delete document');
    }
  };

  const handleDownloadDocument = async (documentId: string, filename: string) => {
    try {
      const response = await DocumentService.downloadDocument(documentId);
      if (response instanceof Blob) {
        const url = window.URL.createObjectURL(response);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
      } else {
        setError('Failed to download document');
      }
    } catch (error: any) {
      console.error('Failed to download document:', error);
      setError('Failed to download document');
    }
  };

  const onDrop = (acceptedFiles: File[]) => {
    const newUploads: FileUpload[] = acceptedFiles.map(file => ({
      file,
      title: file.name.replace(/\.[^/.]+$/, ''), // Remove file extension
      uploading: false,
      progress: 0,
    }));
    
    setPendingUploads(prev => [...prev, ...newUploads]);
    setUploadDialogOpen(true);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/rtf': ['.rtf'],
    },
    multiple: true,
  });

  const uploadFiles = async () => {
    for (let i = 0; i < pendingUploads.length; i++) {
      const upload = pendingUploads[i];
      if (upload.uploading) continue;

      // Update upload status
      setPendingUploads(prev => 
        prev.map((u, index) => 
          index === i ? { ...u, uploading: true, progress: 0 } : u
        )
      );

      try {
        const response = await DocumentService.uploadDocument(
          upload.file,
          upload.title,
          true, // auto-process
          5 // default priority
        );

        if (response.success && response.data) {
          // Update progress to complete
          setPendingUploads(prev => 
            prev.map((u, index) => 
              index === i ? { ...u, uploading: false, progress: 100 } : u
            )
          );

          // Add to documents list
          setDocuments(prev => [response.data!.document, ...prev]);
        } else {
          setPendingUploads(prev => 
            prev.map((u, index) => 
              index === i ? { 
                ...u, 
                uploading: false, 
                error: 'Upload failed' 
              } : u
            )
          );
        }
      } catch (error: any) {
        setPendingUploads(prev => 
          prev.map((u, index) => 
            index === i ? { 
              ...u, 
              uploading: false, 
              error: error.message || 'Upload failed' 
            } : u
          )
        );
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      case 'pending':
        return 'info';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          My Documents
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadDocuments}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
          >
            Upload Documents
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <DocumentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4">{documents.length}</Typography>
              <Typography variant="body2" color="text.secondary">Total Documents</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CircularProgress 
                variant="determinate" 
                value={75} 
                sx={{ fontSize: 40, mb: 1 }} 
                color="success"
              />
              <Typography variant="h4">
                {documents.filter(doc => doc.processing_status === 'completed').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">Processed</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <CircularProgress 
                variant="determinate" 
                value={25} 
                sx={{ fontSize: 40, mb: 1 }} 
                color="warning"
              />
              <Typography variant="h4">
                {documents.filter(doc => doc.processing_status === 'processing').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">Processing</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="text.secondary">
                {documents.reduce((sum, doc) => sum + doc.chunk_count, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">Total Chunks</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Documents Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>File Type</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Chunks</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    No documents uploaded yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Click "Upload Documents" to get started
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              documents.map((document) => (
                <TableRow key={document.id}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {document.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {document.filename}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={document.file_type.toUpperCase()} 
                      size="small" 
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{formatFileSize(document.file_size)}</TableCell>
                  <TableCell>
                    <Chip 
                      label={document.processing_status} 
                      size="small" 
                      color={getStatusColor(document.processing_status) as any}
                    />
                  </TableCell>
                  <TableCell>{document.chunk_count}</TableCell>
                  <TableCell>{formatDate(document.created_at)}</TableCell>
                  <TableCell>
                    <IconButton 
                      size="small" 
                      onClick={() => handleDownloadDocument(document.id, document.filename)}
                      title="Download"
                    >
                      <DownloadIcon />
                    </IconButton>
                    <IconButton 
                      size="small" 
                      onClick={() => handleDeleteDocument(document.id)}
                      title="Delete"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Upload FAB for mobile */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16, display: { xs: 'flex', sm: 'none' } }}
        onClick={() => setUploadDialogOpen(true)}
      >
        <AddIcon />
      </Fab>

      {/* Upload Dialog */}
      <Dialog 
        open={uploadDialogOpen} 
        onClose={() => !pendingUploads.some(u => u.uploading) && setUploadDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Upload Documents</DialogTitle>
        <DialogContent>
          {pendingUploads.length === 0 ? (
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
                transition: 'all 0.2s',
              }}
            >
              <input {...getInputProps()} />
              <UploadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                or click to select files
              </Typography>
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Supported: PDF, DOCX, TXT, MD, RTF
              </Typography>
            </Box>
          ) : (
            <Box>
              {pendingUploads.map((upload, index) => (
                <Box key={index} sx={{ mb: 2, p: 2, border: 1, borderColor: 'grey.200', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body2">{upload.file.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatFileSize(upload.file.size)}
                    </Typography>
                  </Box>
                  
                  <TextField
                    fullWidth
                    label="Document Title"
                    value={upload.title}
                    onChange={(e) => {
                      setPendingUploads(prev =>
                        prev.map((u, i) => i === index ? { ...u, title: e.target.value } : u)
                      );
                    }}
                    size="small"
                    sx={{ mb: 1 }}
                    disabled={upload.uploading}
                  />
                  
                  {upload.uploading && (
                    <LinearProgress 
                      variant="indeterminate" 
                      sx={{ mb: 1 }}
                    />
                  )}
                  
                  {upload.error && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      {upload.error}
                    </Alert>
                  )}
                </Box>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setUploadDialogOpen(false)}
            disabled={pendingUploads.some(u => u.uploading)}
          >
            Cancel
          </Button>
          {pendingUploads.length > 0 && (
            <Button 
              onClick={uploadFiles}
              variant="contained"
              disabled={pendingUploads.some(u => u.uploading)}
            >
              Upload {pendingUploads.length} File{pendingUploads.length > 1 ? 's' : ''}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserDocuments;