/**
 * Common UI Components for AI Chatbot Frontend
 * 
 * This module provides reusable UI components that are used throughout
 * the application. These components are built on top of Material-UI
 * and provide consistent styling, behavior, and functionality.
 * 
 * Components included:
 * - LoadingSpinner: Centralized loading indicator
 * - ErrorBoundary: Error handling component
 * - PageHeader: Consistent page titles and actions
 * - DataTable: Enhanced table with sorting, filtering, and pagination
 * - ConfirmDialog: Reusable confirmation dialogs
 * - StatusChip: Status indicators with consistent styling
 * - EmptyState: Placeholder for empty data states
 */

import React, { useState, ReactNode } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  AlertTitle,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  TextField,
  InputAdornment,
  Paper,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  ErrorOutline as ErrorIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// =============================================================================
// Loading Spinner Component
// =============================================================================

/**
 * Props for LoadingSpinner component
 */
interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: number;
  /** Loading message to display */
  message?: string;
  /** Whether to center the spinner */
  centered?: boolean;
}

/**
 * Reusable loading spinner component with optional message
 * 
 * @param props - Component props
 * @returns Loading spinner component
 */
export function LoadingSpinner({ 
  size = 40, 
  message = 'Loading...', 
  centered = true 
}: LoadingSpinnerProps): JSX.Element {
  const content = (
    <Stack 
      direction="column" 
      alignItems="center" 
      spacing={2}
      sx={{ p: 2 }}
    >
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Stack>
  );

  if (centered) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="200px"
      >
        {content}
      </Box>
    );
  }

  return content;
}

// =============================================================================
// Error Boundary Component
// =============================================================================

/**
 * Props for ErrorBoundary component
 */
interface ErrorBoundaryProps {
  /** Child components to wrap */
  children: ReactNode;
  /** Custom error message */
  fallback?: ReactNode;
}

/**
 * State for ErrorBoundary component
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary component that catches JavaScript errors anywhere in the child tree
 * 
 * This component implements React's error boundary pattern to gracefully handle
 * JavaScript errors and prevent the entire app from crashing.
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="error">
            <AlertTitle>Something went wrong</AlertTitle>
            An unexpected error occurred. Please try refreshing the page.
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Box component="pre" sx={{ mt: 2, fontSize: '0.75rem', overflow: 'auto' }}>
                {this.state.error.toString()}
              </Box>
            )}
          </Alert>
          <Button 
            onClick={() => window.location.reload()} 
            variant="outlined" 
            sx={{ mt: 2 }}
          >
            Refresh Page
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

// =============================================================================
// Page Header Component
// =============================================================================

/**
 * Props for PageHeader component
 */
interface PageHeaderProps {
  /** Page title */
  title: string;
  /** Optional subtitle */
  subtitle?: string;
  /** Action buttons to display */
  actions?: ReactNode;
  /** Whether to show a refresh button */
  showRefresh?: boolean;
  /** Refresh handler function */
  onRefresh?: () => void;
}

/**
 * Consistent page header with title, subtitle, and actions
 * 
 * @param props - Component props
 * @returns Page header component
 */
export function PageHeader({
  title,
  subtitle,
  actions,
  showRefresh = false,
  onRefresh,
}: PageHeaderProps): JSX.Element {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        mb: 3,
        pb: 2,
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body1" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>
      <Stack direction="row" spacing={1}>
        {showRefresh && onRefresh && (
          <Tooltip title="Refresh">
            <IconButton onClick={onRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        )}
        {actions}
      </Stack>
    </Box>
  );
}

// =============================================================================
// Status Chip Component
// =============================================================================

/**
 * Status types for status chip
 */
export type StatusType = 'success' | 'error' | 'warning' | 'info' | 'default';

/**
 * Props for StatusChip component
 */
interface StatusChipProps {
  /** Status type determining color and icon */
  status: StatusType;
  /** Status label to display */
  label: string;
  /** Whether to show an icon */
  showIcon?: boolean;
  /** Custom icon to display */
  icon?: ReactNode;
}

/**
 * Status chip component with consistent styling for different states
 * 
 * @param props - Component props
 * @returns Status chip component
 */
export function StatusChip({ 
  status, 
  label, 
  showIcon = true, 
  icon 
}: StatusChipProps): JSX.Element {
  // Map status types to colors and default icons
  const statusConfig = {
    success: { color: 'success' as const, icon: <SuccessIcon /> },
    error: { color: 'error' as const, icon: <ErrorIcon /> },
    warning: { color: 'warning' as const, icon: <WarningIcon /> },
    info: { color: 'info' as const, icon: <InfoIcon /> },
    default: { color: 'default' as const, icon: null },
  };

  const config = statusConfig[status];
  const chipIcon = icon || (showIcon ? config.icon : undefined);

  return (
    <Chip
      label={label}
      color={config.color}
      size="small"
      icon={chipIcon}
      variant="outlined"
    />
  );
}

// =============================================================================
// Confirmation Dialog Component
// =============================================================================

/**
 * Props for ConfirmDialog component
 */
interface ConfirmDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Dialog title */
  title: string;
  /** Dialog message/content */
  message: string;
  /** Confirm button text */
  confirmText?: string;
  /** Cancel button text */
  cancelText?: string;
  /** Confirm button color */
  confirmColor?: 'error' | 'warning' | 'primary';
  /** Whether the action is loading */
  loading?: boolean;
  /** Function called when user confirms */
  onConfirm: () => void;
  /** Function called when user cancels or closes dialog */
  onCancel: () => void;
}

/**
 * Reusable confirmation dialog for destructive or important actions
 * 
 * @param props - Component props
 * @returns Confirmation dialog component
 */
export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmColor = 'primary',
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps): JSX.Element {
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <DialogTitle id="confirm-dialog-title">
        {title}
      </DialogTitle>
      <DialogContent>
        <DialogContentText id="confirm-dialog-description">
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={loading}>
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          color={confirmColor}
          variant="contained"
          disabled={loading}
          autoFocus
        >
          {loading ? 'Processing...' : confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// =============================================================================
// Empty State Component
// =============================================================================

/**
 * Props for EmptyState component
 */
interface EmptyStateProps {
  /** Icon to display */
  icon?: ReactNode;
  /** Title text */
  title: string;
  /** Description text */
  description?: string;
  /** Action button */
  action?: ReactNode;
}

/**
 * Empty state component for when there's no data to display
 * 
 * @param props - Component props
 * @returns Empty state component
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
}: EmptyStateProps): JSX.Element {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 200,
        p: 3,
        textAlign: 'center',
      }}
    >
      {icon && (
        <Box sx={{ mb: 2, color: 'text.secondary' }}>
          {icon}
        </Box>
      )}
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {description}
        </Typography>
      )}
      {action}
    </Box>
  );
}

// =============================================================================
// Enhanced Data Table Component
// =============================================================================

/**
 * Column definition for DataTable
 */
export interface DataTableColumn<T = any> {
  /** Column identifier */
  id: string;
  /** Column header label */
  label: string;
  /** Whether column is sortable */
  sortable?: boolean;
  /** Custom render function for cell content */
  render?: (value: any, row: T) => ReactNode;
  /** Column alignment */
  align?: 'left' | 'center' | 'right';
  /** Column width */
  width?: string | number;
}

/**
 * Props for DataTable component
 */
interface DataTableProps<T = any> {
  /** Table columns configuration */
  columns: DataTableColumn<T>[];
  /** Table data rows */
  data: T[];
  /** Whether data is loading */
  loading?: boolean;
  /** Total number of items (for pagination) */
  totalCount?: number;
  /** Current page (0-based) */
  page?: number;
  /** Items per page */
  rowsPerPage?: number;
  /** Pagination change handler */
  onPageChange?: (page: number) => void;
  /** Rows per page change handler */
  onRowsPerPageChange?: (rowsPerPage: number) => void;
  /** Sort change handler */
  onSortChange?: (column: string, direction: 'asc' | 'desc') => void;
  /** Current sort column */
  sortColumn?: string;
  /** Current sort direction */
  sortDirection?: 'asc' | 'desc';
  /** Search functionality */
  searchable?: boolean;
  /** Search value */
  searchValue?: string;
  /** Search change handler */
  onSearchChange?: (value: string) => void;
  /** Search placeholder */
  searchPlaceholder?: string;
  /** Empty state configuration */
  emptyState?: {
    title: string;
    description?: string;
    icon?: ReactNode;
  };
}

/**
 * Enhanced data table with sorting, pagination, and search
 * 
 * @param props - Component props
 * @returns Data table component
 */
export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  totalCount,
  page = 0,
  rowsPerPage = 10,
  onPageChange,
  onRowsPerPageChange,
  onSortChange,
  sortColumn,
  sortDirection = 'asc',
  searchable = false,
  searchValue = '',
  onSearchChange,
  searchPlaceholder = 'Search...',
  emptyState,
}: DataTableProps<T>): JSX.Element {
  const [localSearchValue, setLocalSearchValue] = useState(searchValue);

  // Handle search input change with debouncing
  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (onSearchChange && localSearchValue !== searchValue) {
        onSearchChange(localSearchValue);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [localSearchValue, onSearchChange, searchValue]);

  // Handle sort click
  const handleSortClick = (columnId: string) => {
    if (!onSortChange) return;
    
    const newDirection = sortColumn === columnId && sortDirection === 'asc' ? 'desc' : 'asc';
    onSortChange(columnId, newDirection);
  };

  // Handle pagination change
  const handlePageChange = (_: unknown, newPage: number) => {
    onPageChange?.(newPage);
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onRowsPerPageChange?.(parseInt(event.target.value, 10));
  };

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      {/* Search bar */}
      {searchable && (
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <TextField
            fullWidth
            placeholder={searchPlaceholder}
            value={localSearchValue}
            onChange={(e) => setLocalSearchValue(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>
      )}

      {/* Table */}
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align || 'left'}
                  style={{ width: column.width }}
                  sortDirection={sortColumn === column.id ? sortDirection : false}
                >
                  {column.sortable && onSortChange ? (
                    <TableSortLabel
                      active={sortColumn === column.id}
                      direction={sortColumn === column.id ? sortDirection : 'asc'}
                      onClick={() => handleSortClick(column.id)}
                    >
                      {column.label}
                    </TableSortLabel>
                  ) : (
                    column.label
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center">
                  <LoadingSpinner message="Loading data..." centered={false} />
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} align="center">
                  <EmptyState
                    icon={emptyState?.icon}
                    title={emptyState?.title || 'No data available'}
                    description={emptyState?.description}
                  />
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, index) => (
                <TableRow key={index} hover>
                  {columns.map((column) => {
                    const value = row[column.id];
                    const content = column.render ? column.render(value, row) : value;
                    
                    return (
                      <TableCell key={column.id} align={column.align || 'left'}>
                        {content}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {(totalCount !== undefined || data.length > 0) && (
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={totalCount || data.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handlePageChange}
          onRowsPerPageChange={handleRowsPerPageChange}
        />
      )}
    </Paper>
  );
}