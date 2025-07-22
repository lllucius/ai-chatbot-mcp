import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Avatar,
  Divider,
  Alert,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Save as SaveIcon,
  Edit as EditIcon,
  Check as CheckIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { UserService } from '../services';
import { useAuth } from '../services/AuthContext';
import { User, UserUpdate, UserPasswordUpdate } from '../types';

const UserProfile: React.FC = () => {
  const { user: authUser, logout } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Profile editing
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState<UserUpdate>({});
  
  // Password change
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [passwordData, setPasswordData] = useState<UserPasswordUpdate>({
    current_password: '',
    new_password: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await UserService.getMyProfile();
      if (response.success && response.data) {
        setUser(response.data);
        setProfileData({
          email: response.data.email,
          full_name: response.data.full_name,
        });
      } else {
        setError('Failed to load user profile');
      }
    } catch (error: any) {
      console.error('Failed to load user profile:', error);
      setError('Failed to load user profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setError(null);
    setSuccess(null);

    try {
      const response = await UserService.updateMyProfile(profileData);
      if (response.success && response.data) {
        setUser(response.data);
        setEditingProfile(false);
        setSuccess('Profile updated successfully');
      } else {
        setError('Failed to update profile');
      }
    } catch (error: any) {
      console.error('Failed to update profile:', error);
      setError('Failed to update profile');
    }
  };

  const handleChangePassword = async () => {
    setError(null);
    setSuccess(null);

    if (passwordData.new_password !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }

    try {
      const response = await UserService.changePassword(passwordData);
      if (response.success) {
        setPasswordDialogOpen(false);
        setPasswordData({ current_password: '', new_password: '' });
        setConfirmPassword('');
        setSuccess('Password changed successfully');
      } else {
        setError('Failed to change password');
      }
    } catch (error: any) {
      console.error('Failed to change password:', error);
      setError('Failed to change password');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getInitials = (name?: string) => {
    if (!name) return authUser?.username?.charAt(0).toUpperCase() || 'U';
    return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase();
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
      <Typography variant="h4" gutterBottom>
        Profile & Settings
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Profile Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar
                  sx={{ 
                    width: 80, 
                    height: 80, 
                    mr: 2, 
                    bgcolor: 'primary.main',
                    fontSize: '2rem',
                  }}
                >
                  {getInitials(user?.full_name)}
                </Avatar>
                <Box>
                  <Typography variant="h5">
                    {user?.full_name || user?.username}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    @{user?.username}
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                    <Chip 
                      label={user?.is_active ? 'Active' : 'Inactive'} 
                      size="small" 
                      color={user?.is_active ? 'success' : 'default'} 
                    />
                    {user?.is_superuser && (
                      <Chip label="Administrator" size="small" color="primary" />
                    )}
                  </Box>
                </Box>
              </Box>

              <Divider sx={{ mb: 2 }} />

              {editingProfile ? (
                <Box>
                  <TextField
                    fullWidth
                    label="Full Name"
                    value={profileData.full_name || ''}
                    onChange={(e) => setProfileData(prev => ({ ...prev, full_name: e.target.value }))}
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={profileData.email || ''}
                    onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                    sx={{ mb: 2 }}
                  />
                </Box>
              ) : (
                <Box>
                  <List>
                    <ListItem>
                      <ListItemIcon>
                        <PersonIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Full Name"
                        secondary={user?.full_name || 'Not set'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <EmailIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Email"
                        secondary={user?.email}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <TimeIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Member Since"
                        secondary={user ? formatDate(user.created_at) : '—'}
                      />
                    </ListItem>
                  </List>
                </Box>
              )}
            </CardContent>
            <CardActions>
              {editingProfile ? (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveProfile}
                  >
                    Save Changes
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setEditingProfile(false);
                      setProfileData({
                        email: user?.email,
                        full_name: user?.full_name,
                      });
                    }}
                  >
                    Cancel
                  </Button>
                </Box>
              ) : (
                <Button
                  startIcon={<EditIcon />}
                  onClick={() => setEditingProfile(true)}
                >
                  Edit Profile
                </Button>
              )}
            </CardActions>
          </Card>
        </Grid>

        {/* Account Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Account Security
              </Typography>
              
              <Typography variant="body2" color="text.secondary" paragraph>
                Manage your account security settings and password.
              </Typography>

              <Button
                variant="outlined"
                fullWidth
                startIcon={<SecurityIcon />}
                onClick={() => setPasswordDialogOpen(true)}
                sx={{ mb: 2 }}
              >
                Change Password
              </Button>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Account Information
              </Typography>

              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Account ID"
                    secondary={user?.id}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Created"
                    secondary={user ? formatDateTime(user.created_at) : '—'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Last Updated"
                    secondary={user ? formatDateTime(user.updated_at) : '—'}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Account Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom color="error">
                Danger Zone
              </Typography>
              
              <Typography variant="body2" color="text.secondary" paragraph>
                These actions cannot be undone. Please be careful.
              </Typography>

              <Button
                variant="outlined"
                color="error"
                onClick={logout}
              >
                Sign Out of All Devices
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Change Password Dialog */}
      <Dialog 
        open={passwordDialogOpen} 
        onClose={() => setPasswordDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Current Password"
            type="password"
            value={passwordData.current_password}
            onChange={(e) => setPasswordData(prev => ({ ...prev, current_password: e.target.value }))}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            fullWidth
            label="New Password"
            type="password"
            value={passwordData.new_password}
            onChange={(e) => setPasswordData(prev => ({ ...prev, new_password: e.target.value }))}
            sx={{ mb: 2 }}
            helperText="Password must be at least 8 characters long"
          />
          <TextField
            fullWidth
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={confirmPassword !== '' && passwordData.new_password !== confirmPassword}
            helperText={
              confirmPassword !== '' && passwordData.new_password !== confirmPassword
                ? 'Passwords do not match'
                : ''
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleChangePassword}
            variant="contained"
            disabled={
              !passwordData.current_password ||
              !passwordData.new_password ||
              passwordData.new_password !== confirmPassword ||
              passwordData.new_password.length < 8
            }
          >
            Change Password
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserProfile;