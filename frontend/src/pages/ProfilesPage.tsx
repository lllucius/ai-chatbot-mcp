/**
 * LLM Profiles Page Component
 * 
 * Manages LLM parameter profiles for different conversation modes:
 * - View and edit existing profiles
 * - Create new custom profiles
 * - Set default profiles
 * - Parameter tuning (temperature, max tokens, etc.)
 * - Profile usage statistics
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
  Slider,
  FormControlLabel,
  Switch,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material';
import {
  Psychology as ProfileIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  MoreVert as MoreIcon,
  Tune as TuneIcon,
} from '@mui/icons-material';

import { 
  PageHeader, 
  LoadingSpinner, 
  StatusChip, 
  ConfirmDialog,
  EmptyState,
} from '../components/common/CommonComponents';
import {
  useLlmProfiles,
  useCreateLlmProfile,
  useUpdateLlmProfile,
  useDeleteLlmProfile,
  useSetDefaultLlmProfile,
} from '../hooks/api';
import type { LlmProfile, LlmParameters } from '../types/api';

/**
 * Profile form dialog component
 */
function ProfileFormDialog({
  open,
  onClose,
  profile,
  onSave,
}: {
  open: boolean;
  onClose: () => void;
  profile?: LlmProfile;
  onSave: (profile: Omit<LlmProfile, 'id' | 'created_at' | 'updated_at' | 'usage_count'>) => void;
}): JSX.Element {
  const [formData, setFormData] = useState({
    name: profile?.name || '',
    title: profile?.title || '',
    description: profile?.description || '',
    parameters: {
      temperature: profile?.parameters.temperature || 0.7,
      max_tokens: profile?.parameters.max_tokens || 2000,
      top_p: profile?.parameters.top_p || 1.0,
      frequency_penalty: profile?.parameters.frequency_penalty || 0,
      presence_penalty: profile?.parameters.presence_penalty || 0,
    },
    is_default: profile?.is_default || false,
    is_active: profile?.is_active ?? true,
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

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validateForm()) {
      onSave(formData);
    }
  };

  const handleParameterChange = (param: keyof LlmParameters, value: number) => {
    setFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [param]: value,
      },
    }));
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {profile ? 'Edit Profile' : 'Create New Profile'}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            fullWidth
            label="Profile Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            error={!!errors.name}
            helperText={errors.name || 'Unique identifier for the profile'}
            disabled={!!profile} // Can't change name of existing profile
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
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            multiline
            rows={2}
            helperText="Optional description of when to use this profile"
          />

          {/* Temperature */}
          <Box>
            <Typography gutterBottom>
              Temperature: {formData.parameters.temperature}
            </Typography>
            <Slider
              value={formData.parameters.temperature}
              onChange={(_, value) => handleParameterChange('temperature', value as number)}
              min={0}
              max={2}
              step={0.1}
              marks={[
                { value: 0, label: '0 (Focused)' },
                { value: 1, label: '1 (Balanced)' },
                { value: 2, label: '2 (Creative)' },
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              Controls randomness. Higher values make output more creative but less focused.
            </Typography>
          </Box>

          {/* Max Tokens */}
          <Box>
            <Typography gutterBottom>
              Max Tokens: {formData.parameters.max_tokens}
            </Typography>
            <Slider
              value={formData.parameters.max_tokens}
              onChange={(_, value) => handleParameterChange('max_tokens', value as number)}
              min={100}
              max={4000}
              step={100}
              marks={[
                { value: 500, label: '500' },
                { value: 2000, label: '2000' },
                { value: 4000, label: '4000' },
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              Maximum number of tokens to generate in the response.
            </Typography>
          </Box>

          {/* Top P */}
          <Box>
            <Typography gutterBottom>
              Top P: {formData.parameters.top_p}
            </Typography>
            <Slider
              value={formData.parameters.top_p}
              onChange={(_, value) => handleParameterChange('top_p', value as number)}
              min={0.1}
              max={1.0}
              step={0.1}
              marks={[
                { value: 0.1, label: '0.1' },
                { value: 0.5, label: '0.5' },
                { value: 1.0, label: '1.0' },
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              Controls diversity via nucleus sampling. Lower values are more focused.
            </Typography>
          </Box>

          {/* Advanced Parameters */}
          <Box>
            <Typography gutterBottom>
              Frequency Penalty: {formData.parameters.frequency_penalty}
            </Typography>
            <Slider
              value={formData.parameters.frequency_penalty}
              onChange={(_, value) => handleParameterChange('frequency_penalty', value as number)}
              min={-2}
              max={2}
              step={0.1}
              marks={[
                { value: -2, label: '-2' },
                { value: 0, label: '0' },
                { value: 2, label: '2' },
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              Reduces repetition based on frequency. Positive values discourage repetition.
            </Typography>
          </Box>

          <Box>
            <Typography gutterBottom>
              Presence Penalty: {formData.parameters.presence_penalty}
            </Typography>
            <Slider
              value={formData.parameters.presence_penalty}
              onChange={(_, value) => handleParameterChange('presence_penalty', value as number)}
              min={-2}
              max={2}
              step={0.1}
              marks={[
                { value: -2, label: '-2' },
                { value: 0, label: '0' },
                { value: 2, label: '2' },
              ]}
              valueLabelDisplay="auto"
            />
            <Typography variant="caption" color="text.secondary">
              Reduces repetition based on presence. Positive values encourage new topics.
            </Typography>
          </Box>

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
          {profile ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/**
 * Profile card component
 */
function ProfileCard({ 
  profile, 
  onEdit, 
  onDelete, 
  onSetDefault 
}: {
  profile: LlmProfile;
  onEdit: (profile: LlmProfile) => void;
  onDelete: (profileName: string) => void;
  onSetDefault: (profileName: string) => void;
}): JSX.Element {
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

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          {/* Header */}
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1}>
              <ProfileIcon color="primary" />
              <Typography variant="h6">{profile.title}</Typography>
              {profile.is_default && (
                <StarIcon color="warning" />
              )}
            </Stack>
            <IconButton onClick={handleMenuClick}>
              <MoreIcon />
            </IconButton>
          </Stack>

          {/* Description */}
          {profile.description && (
            <Typography variant="body2" color="text.secondary">
              {profile.description}
            </Typography>
          )}

          {/* Parameters */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Parameters
            </Typography>
            <Grid container spacing={1}>
              <Grid item xs={6}>
                <Chip 
                  label={`Temp: ${profile.parameters.temperature}`}
                  size="small"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={6}>
                <Chip 
                  label={`Max: ${profile.parameters.max_tokens}`}
                  size="small"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={6}>
                <Chip 
                  label={`Top-P: ${profile.parameters.top_p}`}
                  size="small"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={6}>
                <Chip 
                  label={`Used: ${profile.usage_count}`}
                  size="small"
                  variant="outlined"
                  color="primary"
                />
              </Grid>
            </Grid>
          </Box>

          {/* Status */}
          <Stack direction="row" spacing={1}>
            <StatusChip
              status={profile.is_active ? 'success' : 'default'}
              label={profile.is_active ? 'Active' : 'Inactive'}
            />
            {profile.is_default && (
              <StatusChip
                status="warning"
                label="Default"
                showIcon={false}
              />
            )}
          </Stack>

          {/* Footer */}
          <Typography variant="caption" color="text.secondary">
            Created: {new Date(profile.created_at).toLocaleDateString()}
          </Typography>
        </Stack>

        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
          <MenuItem onClick={() => handleAction(() => onEdit(profile))}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
          
          {!profile.is_default && (
            <MenuItem onClick={() => handleAction(() => onSetDefault(profile.name))}>
              <ListItemIcon>
                <StarBorderIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Set as Default</ListItemText>
            </MenuItem>
          )}
          
          <MenuItem 
            onClick={() => handleAction(() => onDelete(profile.name))}
            disabled={profile.is_default}
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
 * Main profiles page component
 */
export default function ProfilesPage(): JSX.Element {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<LlmProfile | undefined>(undefined);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [profileToDelete, setProfileToDelete] = useState<string | null>(null);

  // API hooks
  const { data: profiles = [], isLoading, refetch } = useLlmProfiles();
  const createMutation = useCreateLlmProfile();
  const updateMutation = useUpdateLlmProfile();
  const deleteMutation = useDeleteLlmProfile();
  const setDefaultMutation = useSetDefaultLlmProfile();

  const handleCreateProfile = async (profileData: Omit<LlmProfile, 'id' | 'created_at' | 'updated_at' | 'usage_count'>) => {
    try {
      await createMutation.mutateAsync(profileData);
      setDialogOpen(false);
      setEditingProfile(undefined);
    } catch (error) {
      console.error('Failed to create profile:', error);
    }
  };

  const handleEditProfile = async (profileData: Omit<LlmProfile, 'id' | 'created_at' | 'updated_at' | 'usage_count'>) => {
    if (!editingProfile) return;

    try {
      await updateMutation.mutateAsync({
        profileName: editingProfile.name,
        updates: profileData,
      });
      setDialogOpen(false);
      setEditingProfile(undefined);
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  };

  const handleDeleteProfile = async () => {
    if (!profileToDelete) return;

    try {
      await deleteMutation.mutateAsync(profileToDelete);
      setDeleteDialogOpen(false);
      setProfileToDelete(null);
    } catch (error) {
      console.error('Failed to delete profile:', error);
    }
  };

  const handleSetDefault = async (profileName: string) => {
    try {
      await setDefaultMutation.mutateAsync(profileName);
    } catch (error) {
      console.error('Failed to set default profile:', error);
    }
  };

  const openEditDialog = (profile: LlmProfile) => {
    setEditingProfile(profile);
    setDialogOpen(true);
  };

  const openCreateDialog = () => {
    setEditingProfile(undefined);
    setDialogOpen(true);
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading LLM profiles..." />;
  }

  return (
    <Box>
      <PageHeader
        title="LLM Profiles"
        subtitle="Manage parameter profiles for different conversation modes and use cases"
        actions={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={openCreateDialog}
          >
            Create Profile
          </Button>
        }
      />

      {profiles.length === 0 ? (
        <EmptyState
          icon={<TuneIcon sx={{ fontSize: 64 }} />}
          title="No LLM Profiles"
          description="Create your first LLM profile to customize AI behavior for different use cases."
          action={
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={openCreateDialog}
            >
              Create First Profile
            </Button>
          }
        />
      ) : (
        <Grid container spacing={3}>
          {profiles.map((profile) => (
            <Grid item xs={12} md={6} lg={4} key={profile.id}>
              <ProfileCard
                profile={profile}
                onEdit={openEditDialog}
                onDelete={(name) => {
                  setProfileToDelete(name);
                  setDeleteDialogOpen(true);
                }}
                onSetDefault={handleSetDefault}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Profile Form Dialog */}
      <ProfileFormDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setEditingProfile(undefined);
        }}
        profile={editingProfile}
        onSave={editingProfile ? handleEditProfile : handleCreateProfile}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Profile"
        message="Are you sure you want to delete this profile? This action cannot be undone."
        confirmText="Delete"
        confirmColor="error"
        loading={deleteMutation.isPending}
        onConfirm={handleDeleteProfile}
        onCancel={() => {
          setDeleteDialogOpen(false);
          setProfileToDelete(null);
        }}
      />
    </Box>
  );
}