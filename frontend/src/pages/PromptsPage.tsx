/**
 * Prompts Page Component
 * 
 * Manages prompt templates for consistent AI behavior:
 * - View and edit existing prompts
 * - Create new custom prompts
 * - Organize prompts by categories and tags
 * - Set default prompts
 * - Prompt usage statistics
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Autocomplete,
} from '@mui/material';
import {
  Article as PromptIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  MoreVert as MoreIcon,
  Category as CategoryIcon,
  Tag as TagIcon,
} from '@mui/icons-material';

import { 
  PageHeader, 
  LoadingSpinner, 
  StatusChip, 
  ConfirmDialog,
  EmptyState,
} from '../components/common/CommonComponents';
import {
  usePromptTemplates,
  useCreatePromptTemplate,
  useUpdatePromptTemplate,
  useDeletePromptTemplate,
  useSetDefaultPromptTemplate,
} from '../hooks/api';
import type { PromptTemplate } from '../types/api';

// Default categories and tags for new prompts
const DEFAULT_CATEGORIES = [
  'general',
  'technical',
  'creative',
  'analytical',
  'educational',
  'business',
  'research',
];

const DEFAULT_TAGS = [
  'assistant',
  'helpful',
  'expert',
  'creative',
  'analytical',
  'educational',
  'formal',
  'casual',
  'technical',
  'business',
];

/**
 * Prompt form dialog component
 */
function PromptFormDialog({
  open,
  onClose,
  prompt,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  prompt?: PromptTemplate;
  onSave: (prompt: Omit<PromptTemplate, 'id' | 'created_at' | 'updated_at' | 'usage_count'>) => void;
}): React.ReactElement {
  const [formData, setFormData] = useState({
    name: prompt?.name || '',
    title: prompt?.title || '',
    content: prompt?.content || '',
    description: prompt?.description || '',
    category: prompt?.category || 'general',
    tags: prompt?.tags || [],
    is_default: prompt?.is_default || false,
    is_active: prompt?.is_active ?? true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.name)) {
      newErrors.name = 'Name can only contain letters, numbers, underscore, and hyphen';
    }

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.content.trim()) {
      newErrors.content = 'Content is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validateForm()) {
      onSave(formData);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {prompt ? 'Edit Prompt' : 'Create New Prompt'}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            fullWidth
            label="Prompt Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            error={!!errors.name}
            helperText={errors.name || 'Unique identifier for the prompt'}
            disabled={!!prompt} // Can't change name of existing prompt
          />

          <TextField
            fullWidth
            label="Display Title"
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            error={!!errors.title}
            helperText={errors.title}
          />

          <TextField
            fullWidth
            label="Content"
            value={formData.content}
            onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
            error={!!errors.content}
            helperText={errors.content || 'The actual prompt text that will be sent to the AI'}
            multiline
            rows={6}
            placeholder="You are a helpful assistant that..."
          />

          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            multiline
            rows={2}
            helperText="Optional description of when to use this prompt"
          />

          <Autocomplete
            freeSolo
            value={formData.category}
            onChange={(_, value) => setFormData(prev => ({ ...prev, category: value || 'general' }))}
            options={DEFAULT_CATEGORIES}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Category"
                helperText="Choose or create a category for organization"
              />
            )}
          />

          <Autocomplete
            multiple
            freeSolo
            value={formData.tags}
            onChange={(_, value) => setFormData(prev => ({ ...prev, tags: value }))}
            options={DEFAULT_TAGS}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip variant="outlined" label={option} {...getTagProps({ index })} />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Tags"
                helperText="Add tags to help categorize and find this prompt"
              />
            )}
          />

          <Stack direction="row" spacing={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                />
              }
              label="Active"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_default}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_default: e.target.checked }))}
                />
              }
              label="Set as Default"
            />
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>
          {prompt ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * Prompt card component
 */
function PromptCard({ 
  prompt, 
  onEdit, 
  onDelete, 
  onSetDefault 
}: {
  prompt: PromptTemplate;
  onEdit: (prompt: PromptTemplate) => void;
  onDelete: (promptName: string) => void;
  onSetDefault: (promptName: string) => void;
}): React.ReactElement {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleAction = (action: () => void) => {
    action();
    handleMenuClose();
  };

  // Truncate content for display
  const truncatedContent = prompt.content.length > 200 
    ? prompt.content.substring(0, 200) + '...'
    : prompt.content;

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          {/* Header */}
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1}>
              <PromptIcon color="primary" />
              <Typography variant="h6">{prompt.title}</Typography>
              {prompt.is_default && (
                <StarIcon color="warning" />
              )}
            </Stack>
            <IconButton onClick={handleMenuClick}>
              <MoreIcon />
            </IconButton>
          </Stack>

          {/* Description */}
          {prompt.description && (
            <Typography variant="body2" color="text.secondary">
              {prompt.description}
            </Typography>
          )}

          {/* Content Preview */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Content Preview
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                bgcolor: 'grey.50',
                p: 1,
                borderRadius: 1,
                border: 1,
                borderColor: 'grey.200',
              }}
            >
              {truncatedContent}
            </Typography>
          </Box>

          {/* Category and Tags */}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <CategoryIcon fontSize="small" />
              <Chip 
                label={prompt.category}
                size="small"
                variant="outlined"
                color="primary"
              />
            </Stack>
            {prompt.tags.length > 0 && (
              <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="wrap">
                <TagIcon fontSize="small" />
                {prompt.tags.map((tag, index) => (
                  <Chip 
                    key={index}
                    label={tag}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Stack>
            )}
          </Box>

          {/* Status and Usage */}
          <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
            <Stack direction="row" spacing={1}>
              <StatusChip
                status={prompt.is_active ? 'success' : 'default'}
                label={prompt.is_active ? 'Active' : 'Inactive'}
              />
              {prompt.is_default && (
                <StatusChip
                  status="warning"
                  label="Default"
                  showIcon={false}
                />
              )}
            </Stack>
            <Chip 
              label={`Used ${prompt.usage_count} times`}
              size="small"
              variant="outlined"
            />
          </Stack>

          {/* Footer */}
          <Typography variant="caption" color="text.secondary">
            Created: {new Date(prompt.created_at).toLocaleDateString()}
          </Typography>
        </Stack>

        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItem onClick={() => handleAction(() => onEdit(prompt))}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
          
          {!prompt.is_default && (
            <MenuItem onClick={() => handleAction(() => onSetDefault(prompt.name))}>
              <ListItemIcon>
                <StarBorderIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Set as Default</ListItemText>
            </MenuItem>
          )}
          
          <MenuItem 
            onClick={() => handleAction(() => onDelete(prompt.name))}
            disabled={prompt.is_default}
          >
            <ListItemIcon>
              <DeleteIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        </Menu>
      </CardContent>
    </Card>
  );
}

/**
 * Main prompts page component
 */
export default function PromptsPage(): React.ReactElement {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<PromptTemplate | undefined>(undefined);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [promptToDelete, setPromptToDelete] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('');

  // API hooks
  const { data: prompts = [], isLoading } = usePromptTemplates();
  const createMutation = useCreatePromptTemplate();
  const updateMutation = useUpdatePromptTemplate();
  const deleteMutation = useDeletePromptTemplate();
  const setDefaultMutation = useSetDefaultPromptTemplate();

  const handleCreatePrompt = async (promptData: Omit<PromptTemplate, 'id' | 'created_at' | 'updated_at' | 'usage_count'>) => {
    try {
      await createMutation.mutateAsync(promptData);
      setDialogOpen(false);
      setEditingPrompt(undefined);
    } catch (error) {
      console.error('Failed to create prompt:', error);
    }
  };

  const handleEditPrompt = async (promptData: Omit<PromptTemplate, 'id' | 'created_at' | 'updated_at' | 'usage_count'>) => {
    if (!editingPrompt) return;

    try {
      await updateMutation.mutateAsync({
        promptName: editingPrompt.name,
        updates: promptData,
      });
      setDialogOpen(false);
      setEditingPrompt(undefined);
    } catch (error) {
      console.error('Failed to update prompt:', error);
    }
  };

  const handleDeletePrompt = async () => {
    if (!promptToDelete) return;

    try {
      await deleteMutation.mutateAsync(promptToDelete);
      setDeleteDialogOpen(false);
      setPromptToDelete(null);
    } catch (error) {
      console.error('Failed to delete prompt:', error);
    }
  };

  const handleSetDefault = async (promptName: string) => {
    try {
      await setDefaultMutation.mutateAsync(promptName);
    } catch (error) {
      console.error('Failed to set default prompt:', error);
    }
  };

  const openEditDialog = (prompt: PromptTemplate) => {
    setEditingPrompt(prompt);
    setDialogOpen(true);
  };

  const openCreateDialog = () => {
    setEditingPrompt(undefined);
    setDialogOpen(true);
  };

  // Filter prompts by category
  const filteredPrompts = categoryFilter 
    ? prompts.filter(prompt => prompt.category === categoryFilter)
    : prompts;

  // Get unique categories
  const categories = Array.from(new Set(prompts.map(p => p.category))).sort();

  if (isLoading) {
    return <LoadingSpinner message="Loading prompts..." />;
  }

  return (
    <Box>
      <PageHeader
        title="Prompt Templates"
        subtitle="Manage prompt templates for consistent AI behavior and specialized tasks"
        actions={
          <Stack direction="row" spacing={1}>
            <Autocomplete
              value={categoryFilter}
              onChange={(_, value) => setCategoryFilter(value || '')}
              options={['', ...categories]}
              getOptionLabel={(option) => option || 'All Categories'}
              renderInput={(params) => (
                <TextField
                  {...params}
                  size="small"
                  sx={{ minWidth: 150 }}
                  placeholder="Filter by category"
                />
              )}
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={openCreateDialog}
            >
              Create Prompt
            </Button>
          </Stack>
        }
      />

      {prompts.length === 0 ? (
        <EmptyState
          icon={<PromptIcon sx={{ fontSize: 64 }} />}
          title="No Prompt Templates"
          description="Create your first prompt template to standardize AI behavior for different tasks."
          action={
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={openCreateDialog}
            >
              Create First Prompt
            </Button>
          }
        />
      ) : (
        <>
          {/* Category Summary */}
          {categories.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Categories ({categories.length})
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {categories.map((category) => {
                    const count = prompts.filter(p => p.category === category).length;
                    return (
                      <Chip
                        key={category}
                        label={`${category} (${count})`}
                        clickable
                        variant={categoryFilter === category ? 'filled' : 'outlined'}
                        onClick={() => setCategoryFilter(categoryFilter === category ? '' : category)}
                      />
                    );
                  })}
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* Prompts Grid */}
          <Grid container spacing={3}>
            {filteredPrompts.map((prompt) => (
              <Grid item xs={12} lg={6} key={prompt.id}>
                <PromptCard
                  prompt={prompt}
                  onEdit={openEditDialog}
                  onDelete={(name) => {
                    setPromptToDelete(name);
                    setDeleteDialogOpen(true);
                  }}
                  onSetDefault={handleSetDefault}
                />
              </Grid>
            ))}
          </Grid>

          {filteredPrompts.length === 0 && categoryFilter && (
            <EmptyState
              icon={<CategoryIcon sx={{ fontSize: 64 }} />}
              title={`No prompts in "${categoryFilter}" category`}
              description="Try selecting a different category or clear the filter."
            />
          )}
        </>
      )}

      {/* Prompt Form Dialog */}
      <PromptFormDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setEditingPrompt(undefined);
        }}
        prompt={editingPrompt}
        onSave={editingPrompt ? handleEditPrompt : handleCreatePrompt}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Prompt"
        message="Are you sure you want to delete this prompt template? This action cannot be undone."
        confirmText="Delete"
        confirmColor="error"
        loading={deleteMutation.isPending}
        onConfirm={handleDeletePrompt}
        onCancel={() => {
          setDeleteDialogOpen(false);
          setPromptToDelete(null);
        }}
      />
    </Box>
  );
}