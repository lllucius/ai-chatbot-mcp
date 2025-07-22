import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Alert,
  CircularProgress,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  Upload,
  Download,
  Delete,
  Search,
  Visibility,
  CloudUpload,
  Description,
  PictureAsPdf,
  TextSnippet,
  InsertDriveFile,
  Add,
  Refresh,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

/**
 * UserDocuments Component
 * 
 * Personal document management interface providing:
 * - File upload with drag & drop support
 * - Personal document library with search and filtering
 * - Document processing status monitoring
 * - Download and delete capabilities for own documents
 * - File type and size management
 * - Real-time processing updates
 */
const UserDocuments = () => {
  // State management for documents and UI interactions
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});

  // Document statistics
  const [stats, setStats] = useState({
    total: 0,
    processing: 0,
    completed: 0,
    failed: 0,
    totalSize: 0,
  });

  /**
   * Fetches user's documents from the API
   */
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/documents/');
      const docs = response.data.documents || [];
      setDocuments(docs);
      
      // Calculate statistics
      const totalSize = docs.reduce((acc, doc) => acc + (doc.file_size || 0), 0);
      setStats({
        total: docs.length,
        processing: docs.filter(d => d.status === 'processing').length,
        completed: docs.filter(d => d.status === 'completed').length,
        failed: docs.filter(d => d.status === 'failed').length,
        totalSize,
      });
      
      setError('');
    } catch (err) {
      setError('Failed to load documents. Please try again.');
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load documents on component mount
  useEffect(() => {
    fetchDocuments();
    
    // Set up polling for processing documents
    const interval = setInterval(() => {
      fetchDocuments();
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, []);

  /**
   * Returns appropriate icon for file type
   */
  const getFileIcon = (fileType) => {
    switch (fileType?.toLowerCase()) {
      case 'pdf':
        return <PictureAsPdf sx={{ color: '#f44336' }} />;
      case 'docx':
      case 'doc':
        return <Description sx={{ color: '#2196f3' }} />;
      case 'txt':
      case 'md':
        return <TextSnippet sx={{ color: '#4caf50' }} />;
      default:
        return <InsertDriveFile sx={{ color: '#757575' }} />;
    }
  };

  /**
   * Formats file size for display
   */
  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  /**
   * Handles file upload with progress tracking
   */
  const handleFileUpload = async (files) => {
    setUploading(true);
    setError('');
    setSuccess('');

    const uploadPromises = files.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.split('.')[0]);

      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
        
        const response = await axios.post('/api/v1/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
          },
        });

        return { success: true, fileName: file.name, data: response.data };
      } catch (err) {
        console.error(`Upload failed for ${file.name}:`, err);
        return { 
          success: false, 
          fileName: file.name, 
          error: err.response?.data?.detail || 'Upload failed' 
        };
      }
    });

    try {
      const results = await Promise.all(uploadPromises);
      const failed = results.filter(r => !r.success);
      const succeeded = results.filter(r => r.success);
      
      if (failed.length > 0) {
        setError(`Failed to upload ${failed.length} file(s): ${failed.map(f => f.fileName).join(', ')}`);
      }
      
      if (succeeded.length > 0) {
        setSuccess(`Successfully uploaded ${succeeded.length} file(s)`);
        setTimeout(() => setSuccess(''), 5000);
      }
      
      await fetchDocuments(); // Refresh the documents list
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress({});
    }
  };

  /**
   * Handles document deletion
   */
  const handleDeleteDocument = async () => {
    try {
      await axios.delete(`/api/v1/documents/${documentToDelete.id}`);
      await fetchDocuments(); // Refresh the documents list
      setDeleteConfirmOpen(false);
      setDocumentToDelete(null);
      setSuccess('Document deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete document');
    }
  };

  /**
   * Handles document download
   */
  const handleDownloadDocument = async (document) => {
    try {
      const response = await axios.get(`/api/v1/documents/${document.id}/download`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', document.filename || `${document.title}.${document.file_type}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download document');
    }
  };

  /**
   * Opens delete confirmation dialog
   */
  const handleOpenDeleteConfirm = (document) => {
    setDocumentToDelete(document);
    setDeleteConfirmOpen(true);
  };

  // Configure dropzone for file uploads
  const onDrop = useCallback((acceptedFiles) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const validFiles = acceptedFiles.filter(file => file.size <= maxSize);
    const oversizedFiles = acceptedFiles.filter(file => file.size > maxSize);
    
    if (oversizedFiles.length > 0) {
      setError(`Some files are too large. Maximum size is 10MB. Skipped: ${oversizedFiles.map(f => f.name).join(', ')}`);
    }
    
    if (validFiles.length > 0) {
      handleFileUpload(validFiles);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/rtf': ['.rtf'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true,
  });

  // Filter documents based on search term and filters
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.filename?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
    const matchesType = typeFilter === 'all' || doc.file_type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  // Paginated documents for display
  const paginatedDocuments = filteredDocuments.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Get unique file types for filter
  const fileTypes = [...new Set(documents.map(doc => doc.file_type).filter(Boolean))];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            My Documents
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Upload, manage, and organize your personal documents
          </Typography>
        </div>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchDocuments}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="overline">
                Total Documents
              </Typography>
              <Typography variant="h4">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="overline">
                Processing
              </Typography>
              <Typography variant="h4" color="warning.main">{stats.processing}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="overline">
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">{stats.completed}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="overline">
                Total Size
              </Typography>
              <Typography variant="h4">{formatFileSize(stats.totalSize)}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* File Upload Area */}
      <Paper 
        elevation={1} 
        sx={{ 
          p: 3, 
          mb: 3, 
          border: isDragActive ? '2px dashed #2196f3' : '2px dashed #ccc',
          backgroundColor: isDragActive ? '#f3f8ff' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
        }}
        {...getRootProps()}
      >
        <input {...getInputProps()} />
        <Box sx={{ textAlign: 'center' }}>
          <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop files here' : 'Drag & drop files here, or click to select'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Supported formats: PDF, DOCX, DOC, TXT, MD, RTF (max 10MB each)
          </Typography>
          {uploading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="primary">
                Uploading files...
              </Typography>
              {Object.entries(uploadProgress).map(([fileName, progress]) => (
                <Box key={fileName} sx={{ mt: 1 }}>
                  <Typography variant="caption">{fileName}</Typography>
                  <LinearProgress variant="determinate" value={progress} />
                </Box>
              ))}
            </Box>
          )}
        </Box>
      </Paper>

      {/* Search and Filter Bar */}
      <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              placeholder="Search documents..."
              variant="outlined"
              size="small"
              fullWidth
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>File Type</InputLabel>
              <Select
                value={typeFilter}
                label="File Type"
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                {fileTypes.map(type => (
                  <MenuItem key={type} value={type}>{type.toUpperCase()}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Documents Table */}
      <Paper elevation={2}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Document</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : paginatedDocuments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      {searchTerm || statusFilter !== 'all' || typeFilter !== 'all' 
                        ? 'No documents found matching your criteria' 
                        : 'No documents uploaded yet. Upload your first document above!'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedDocuments.map((document) => (
                  <TableRow key={document.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getFileIcon(document.file_type)}
                        <Box sx={{ ml: 2 }}>
                          <Typography variant="subtitle2">
                            {document.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {document.filename}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={document.file_type?.toUpperCase() || 'Unknown'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{formatFileSize(document.file_size)}</TableCell>
                    <TableCell>
                      <Chip
                        label={document.status || 'Unknown'}
                        color={
                          document.status === 'completed' ? 'success' :
                          document.status === 'processing' ? 'warning' :
                          document.status === 'failed' ? 'error' : 'default'
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {document.created_at 
                        ? new Date(document.created_at).toLocaleDateString()
                        : 'N/A'
                      }
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Download">
                        <IconButton
                          size="small"
                          onClick={() => handleDownloadDocument(document)}
                          disabled={document.status !== 'completed'}
                        >
                          <Download />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleOpenDeleteConfirm(document)}
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredDocuments.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(event, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the document "{documentToDelete?.title}"? 
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteDocument} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserDocuments;