/**
 * Documents Page Component
 * 
 * This page provides comprehensive document management functionality including:
 * - File upload with drag-and-drop support
 * - Document processing status tracking
 * - Document list with filtering and search
 * - Document preview and metadata viewing
 * - Bulk operations (delete, reprocess)
 * - Processing progress indicators
 * - File type validation and size limits
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Stack,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  FormControlLabel,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as DocumentIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreIcon,
  GetApp as DownloadIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  CheckBox as CheckBoxIcon,
  CheckBoxOutlineBlank as CheckBoxOutlineBlankIcon,
  InsertDriveFile as FileIcon,
  PictureAsPdf as PdfIcon,
  Article as DocIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

import { 
  PageHeader, 
  LoadingSpinner, 
  StatusChip, 
  ConfirmDialog,
  DataTable,
  EmptyState,
  type DataTableColumn,
} from '../components/common/CommonComponents';
import {
  useDocuments,
  useUploadDocument,
  useDeleteDocument,
  useReprocessDocument,
  useDocumentStatus,
} from '../hooks/api';
import type { Document, DocumentUpload } from '../types/api';

// =============================================================================
// File Upload Component
// =============================================================================

/**
 * Props for FileUpload component
 */
interface FileUploadProps {
  onUpload: (files: File[]) => void;
  disabled?: boolean;
}

/**
 * File upload component with drag-and-drop support
 */
function FileUpload({ onUpload, disabled = false }: FileUploadProps): JSX.Element {
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  // Supported file types
  const supportedTypes = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md'],
    'application/rtf': ['.rtf'],
  };

  const { getRootProps, getInputProps, isDragActive, acceptedFiles, fileRejections } = useDropzone({
    accept: supportedTypes,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled,
    onDrop: (files) => {
      if (files.length > 0) {
        onUpload(files);
        setUploadDialogOpen(false);
      }
    },
  });

  return (
    <>
      <Button
        variant="contained"
        startIcon={<UploadIcon />}
        onClick={() => setUploadDialogOpen(true)}
        disabled={disabled}
      >
        Upload Documents
      </Button>

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
              border: 2,
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderStyle: 'dashed',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: disabled ? 'not-allowed' : 'pointer',
              bgcolor: isDragActive ? 'primary.50' : 'grey.50',
              transition: 'all 0.2s ease',
              '&:hover': {
                borderColor: disabled ? 'grey.300' : 'primary.main',
                bgcolor: disabled ? 'grey.50' : 'primary.50',
              },
            }}
          >
            <input {...getInputProps()} />
            <UploadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              or click to select files
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Supported formats: PDF, DOCX, DOC, TXT, MD, RTF (max 10MB each)
            </Typography>
          </Box>

          {fileRejections.length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Some files were rejected:
              <ul>
                {fileRejections.map((rejection, index) => (
                  <li key={index}>
                    {rejection.file.name}: {rejection.errors.map(e => e.message).join(', ')}
                  </li>
                ))}
              </ul>
            </Alert>
          )}

          {acceptedFiles.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Files ready for upload:
              </Typography>
              {acceptedFiles.map((file, index) => (
                <Chip
                  key={index}
                  label={`${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`}
                  variant="outlined"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => {
              if (acceptedFiles.length > 0) {
                onUpload(acceptedFiles);
                setUploadDialogOpen(false);
              }
            }}
            disabled={acceptedFiles.length === 0}
          >
            Upload {acceptedFiles.length} file(s)
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

// =============================================================================
// Document Actions Menu Component
// =============================================================================

/**
 * Props for DocumentActions component
 */
interface DocumentActionsProps {
  document: Document;
  onDelete: (id: string) => void;
  onReprocess: (id: string) => void;
  onView: (document: Document) => void;
}

/**
 * Document actions menu component
 */
function DocumentActions({ document, onDelete, onReprocess, onView }: DocumentActionsProps): JSX.Element {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleAction = (action: () => void) => {
    action();
    handleClose();
  };

  return (
    <>
      <IconButton onClick={handleClick}>
        <MoreIcon />
      </IconButton>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleClose}>
        <MenuItem onClick={() => handleAction(() => onView(document))}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        {document.status === 'failed' && (
          <MenuItem onClick={() => handleAction(() => onReprocess(document.id))}>
            <ListItemIcon>
              <RefreshIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Reprocess</ListItemText>
          </MenuItem>
        )}
        
        <MenuItem onClick={() => handleAction(() => onDelete(document.id))}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
}

// =============================================================================
// Document Details Dialog Component
// =============================================================================

/**
 * Props for DocumentDetails component
 */
interface DocumentDetailsProps {
  document: Document | null;
  open: boolean;
  onClose: () => void;
}

/**
 * Document details dialog component
 */
function DocumentDetails({ document, open, onClose }: DocumentDetailsProps): JSX.Element {
  if (!document) return <div />;

  const getFileIcon = (contentType: string) => {
    if (contentType.includes('pdf')) return <PdfIcon />;
    if (contentType.includes('word') || contentType.includes('document')) return <DocIcon />;
    return <FileIcon />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={1}>
          {getFileIcon(document.content_type)}
          <Typography variant="h6">Document Details</Typography>
        </Stack>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Title</Typography>
            <Typography>{document.title}</Typography>
          </Box>
          
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Filename</Typography>
            <Typography>{document.filename}</Typography>
          </Box>
          
          <Box>
            <Typography variant="subtitle2" color="text.secondary">File Size</Typography>
            <Typography>{formatFileSize(document.file_size)}</Typography>
          </Box>
          
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Content Type</Typography>
            <Typography>{document.content_type}</Typography>
          </Box>
          
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Status</Typography>
            <StatusChip
              status={
                document.status === 'completed' ? 'success' :
                document.status === 'failed' ? 'error' :
                document.status === 'processing' ? 'warning' : 'default'
              }
              label={document.status.toUpperCase()}
            />
          </Box>
          
          {document.status === 'processing' && document.processing_progress !== undefined && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Processing Progress</Typography>
              <LinearProgress 
                variant="determinate" 
                value={document.processing_progress} 
                sx={{ mt: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {document.processing_progress}% complete
              </Typography>
            </Box>
          )}
          
          {document.chunk_count !== undefined && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Text Chunks</Typography>
              <Typography>{document.chunk_count} chunks extracted</Typography>
            </Box>
          )}
          
          {document.error_message && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Error Message</Typography>
              <Alert severity="error">{document.error_message}</Alert>
            </Box>
          )}
          
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Upload Date</Typography>
            <Typography>{new Date(document.created_at).toLocaleString()}</Typography>
          </Box>
          
          {document.processed_at && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Processing Completed</Typography>
              <Typography>{new Date(document.processed_at).toLocaleString()}</Typography>
            </Box>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

// =============================================================================
// Main Documents Page Component
// =============================================================================

/**
 * Main documents page component
 */
export default function DocumentsPage(): JSX.Element {
  // State management
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<string | null>(null);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

  // API hooks
  const { 
    data: documentsData, 
    isLoading, 
    refetch 
  } = useDocuments(page + 1, rowsPerPage);
  
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();
  const reprocessMutation = useReprocessDocument();

  /**
   * Handle file upload
   */
  const handleUpload = useCallback(async (files: File[]) => {
    for (const file of files) {
      try {
        const upload: DocumentUpload = {
          file,
          title: file.name.replace(/\.[^/.]+$/, ''), // Remove extension
          process_immediately: true,
        };

        await uploadMutation.mutateAsync({
          upload,
          onProgress: (progress) => {
            setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
          },
        });

        // Clear progress after upload
        setUploadProgress(prev => {
          const updated = { ...prev };
          delete updated[file.name];
          return updated;
        });
      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }
  }, [uploadMutation]);

  /**
   * Handle document deletion
   */
  const handleDelete = useCallback(async (documentId: string) => {
    try {
      await deleteMutation.mutateAsync(documentId);
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  }, [deleteMutation]);

  /**
   * Handle document reprocessing
   */
  const handleReprocess = useCallback(async (documentId: string) => {
    try {
      await reprocessMutation.mutateAsync(documentId);
    } catch (error) {
      console.error('Failed to reprocess document:', error);
    }
  }, [reprocessMutation]);

  /**
   * Handle viewing document details
   */
  const handleViewDocument = useCallback((document: Document) => {
    setSelectedDocument(document);
    setDetailsDialogOpen(true);
  }, []);

  /**
   * Get file type icon
   */
  const getFileIcon = (contentType: string) => {
    if (contentType.includes('pdf')) return <PdfIcon color="error" />;
    if (contentType.includes('word') || contentType.includes('document')) return <DocIcon color="primary" />;
    return <FileIcon color="action" />;
  };

  /**
   * Format file size
   */
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Define table columns
  const columns: DataTableColumn<Document>[] = [
    {
      id: 'title',
      label: 'Document',
      sortable: true,
      render: (_, document) => (
        <Stack direction="row" alignItems="center" spacing={1}>
          {getFileIcon(document.content_type)}
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {document.title}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {document.filename} • {formatFileSize(document.file_size)}
            </Typography>
          </Box>
        </Stack>
      ),
    },
    {
      id: 'status',
      label: 'Status',
      sortable: true,
      render: (_, document) => (
        <Box>
          <StatusChip
            status={
              document.status === 'completed' ? 'success' :
              document.status === 'failed' ? 'error' :
              document.status === 'processing' ? 'warning' : 'default'
            }
            label={document.status.toUpperCase()}
          />
          {document.status === 'processing' && document.processing_progress !== undefined && (
            <LinearProgress 
              variant="determinate" 
              value={document.processing_progress} 
              sx={{ mt: 1, width: 100 }}
            />
          )}
        </Box>
      ),
    },
    {
      id: 'chunk_count',
      label: 'Chunks',
      sortable: true,
      render: (_, document) => document.chunk_count || 0,
    },
    {
      id: 'created_at',
      label: 'Uploaded',
      sortable: true,
      render: (_, document) => new Date(document.created_at).toLocaleDateString(),
    },
    {
      id: 'actions',
      label: 'Actions',
      render: (_, document) => (
        <DocumentActions
          document={document}
          onDelete={(id) => {
            setDocumentToDelete(id);
            setDeleteDialogOpen(true);
          }}
          onReprocess={handleReprocess}
          onView={handleViewDocument}
        />
      ),
    },
  ];

  const documents = documentsData?.items || [];
  const totalCount = documentsData?.pagination.total || 0;

  return (
    <Box>
      <PageHeader
        title="Documents"
        subtitle="Upload and manage documents for AI-powered search and analysis"
        actions={
          <Stack direction="row" spacing={1}>
            <FileUpload 
              onUpload={handleUpload} 
              disabled={uploadMutation.isPending} 
            />
            <Tooltip title="Refresh">
              <IconButton onClick={() => refetch()}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        }
      />

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Uploading Files
            </Typography>
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <Box key={filename} sx={{ mb: 1 }}>
                <Typography variant="body2">{filename}</Typography>
                <LinearProgress variant="determinate" value={progress} sx={{ mt: 0.5 }} />
                <Typography variant="caption" color="text.secondary">
                  {progress}% complete
                </Typography>
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Documents Table */}
      <DataTable
        columns={columns}
        data={documents}
        loading={isLoading}
        totalCount={totalCount}
        page={page}
        rowsPerPage={rowsPerPage}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        searchable
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search documents..."
        emptyState={{
          title: 'No documents uploaded',
          description: 'Upload your first document to get started with AI-powered search and analysis.',
          icon: <DocumentIcon sx={{ fontSize: 64 }} />,
        }}
      />

      {/* Document Details Dialog */}
      <DocumentDetails
        document={selectedDocument}
        open={detailsDialogOpen}
        onClose={() => {
          setDetailsDialogOpen(false);
          setSelectedDocument(null);
        }}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Document"
        message="Are you sure you want to delete this document? This action cannot be undone and will remove all associated text chunks."
        confirmText="Delete"
        confirmColor="error"
        loading={deleteMutation.isPending}
        onConfirm={() => documentToDelete && handleDelete(documentToDelete)}
        onCancel={() => {
          setDeleteDialogOpen(false);
          setDocumentToDelete(null);
        }}
      />
    </Box>
  );
}