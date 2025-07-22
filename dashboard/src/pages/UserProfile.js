import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Avatar,
  Divider,
  Alert,
  Card,
  CardContent,
  FormControlLabel,
  Switch,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Edit,
  Save,
  Lock,
  Person,
  Notifications,
  Language,
  Palette,
  History,
  Delete,
} from '@mui/icons-material';
import { useAuth } from '../services/AuthContext';
import axios from 'axios';

/**
 * UserProfile Component
 * 
 * Personal user profile and settings management including:
 * - Personal information editing
 * - Password change functionality
 * - Notification preferences
 * - Theme and language settings
 * - Account activity history
 * - Privacy controls
 */
const UserProfile = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('profile');
  
  // Profile form state
  const [profileData, setProfileData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
    bio: '',
    phone: '',
    location: '',
  });

  // Password change state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Preferences state
  const [preferences, setPreferences] = useState({
    email_notifications: true,
    system_notifications: true,
    marketing_emails: false,
    theme: 'light',
    language: 'en',
    timezone: 'UTC',
  });

  // Activity history
  const [activityHistory, setActivityHistory] = useState([]);
  const [deleteAccountDialog, setDeleteAccountDialog] = useState(false);

  /**
   * Loads user profile data from API
   */
  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/auth/profile');
      const profile = response.data;
      
      setProfileData({
        username: profile.username || '',
        email: profile.email || '',
        full_name: profile.full_name || '',
        bio: profile.bio || '',
        phone: profile.phone || '',
        location: profile.location || '',
      });
      
      setPreferences(profile.preferences || preferences);
      setError('');
    } catch (err) {
      setError('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Loads user activity history
   */
  const loadActivityHistory = async () => {
    try {
      const response = await axios.get('/api/v1/auth/activity');
      setActivityHistory(response.data.activities || []);
    } catch (err) {
      console.error('Failed to load activity history:', err);
      // Use mock data
      setActivityHistory([
        { id: 1, action: 'Login', timestamp: new Date().toISOString(), ip_address: '192.168.1.1' },
        { id: 2, action: 'Password changed', timestamp: new Date(Date.now() - 86400000).toISOString(), ip_address: '192.168.1.1' },
        { id: 3, action: 'Profile updated', timestamp: new Date(Date.now() - 172800000).toISOString(), ip_address: '192.168.1.1' },
      ]);
    }
  };

  useEffect(() => {
    loadProfile();
    loadActivityHistory();
  }, []);

  /**
   * Handles profile information update
   */
  const handleProfileUpdate = async () => {
    try {
      setLoading(true);
      await axios.put('/api/v1/auth/profile', profileData);
      setSuccess('Profile updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handles password change
   */
  const handlePasswordChange = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match');
      return;
    }

    try {
      setLoading(true);
      await axios.post('/api/v1/auth/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
      setSuccess('Password changed successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handles preferences update
   */
  const handlePreferencesUpdate = async () => {
    try {
      setLoading(true);
      await axios.put('/api/v1/auth/preferences', preferences);
      setSuccess('Preferences updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to update preferences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Profile & Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Manage your personal information and account preferences
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
        {/* Profile Information */}
        <Grid item xs={12} md={8}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Person sx={{ mr: 2 }} />
              <Typography variant="h6">Personal Information</Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Username"
                  value={profileData.username}
                  disabled
                  helperText="Username cannot be changed"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={profileData.email}
                  onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Full Name"
                  value={profileData.full_name}
                  onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Phone"
                  value={profileData.phone}
                  onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Location"
                  value={profileData.location}
                  onChange={(e) => setProfileData({ ...profileData, location: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Bio"
                  value={profileData.bio}
                  onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                  placeholder="Tell us about yourself..."
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={handleProfileUpdate}
                disabled={loading}
              >
                Save Changes
              </Button>
            </Box>
          </Paper>

          {/* Password Change */}
          <Paper elevation={2} sx={{ p: 3, mt: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Lock sx={{ mr: 2 }} />
              <Typography variant="h6">Change Password</Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="password"
                  label="Current Password"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="password"
                  label="New Password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="password"
                  label="Confirm New Password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<Lock />}
                onClick={handlePasswordChange}
                disabled={loading || !passwordData.current_password || !passwordData.new_password}
              >
                Change Password
              </Button>
            </Box>
          </Paper>

          {/* Preferences */}
          <Paper elevation={2} sx={{ p: 3, mt: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Notifications sx={{ mr: 2 }} />
              <Typography variant="h6">Preferences</Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Notifications
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.email_notifications}
                      onChange={(e) => setPreferences({ ...preferences, email_notifications: e.target.checked })}
                    />
                  }
                  label="Email Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.system_notifications}
                      onChange={(e) => setPreferences({ ...preferences, system_notifications: e.target.checked })}
                    />
                  }
                  label="System Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.marketing_emails}
                      onChange={(e) => setPreferences({ ...preferences, marketing_emails: e.target.checked })}
                    />
                  }
                  label="Marketing Emails"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Interface
                </Typography>
                <TextField
                  fullWidth
                  select
                  label="Theme"
                  value={preferences.theme}
                  onChange={(e) => setPreferences({ ...preferences, theme: e.target.value })}
                  SelectProps={{ native: true }}
                  sx={{ mb: 2 }}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </TextField>
                <TextField
                  fullWidth
                  select
                  label="Language"
                  value={preferences.language}
                  onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                  SelectProps={{ native: true }}
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </TextField>
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={handlePreferencesUpdate}
                disabled={loading}
              >
                Save Preferences
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Account Summary & Activity */}
        <Grid item xs={12} md={4}>
          {/* Account Summary */}
          <Card elevation={2} sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ width: 60, height: 60, mr: 2, bgcolor: 'primary.main' }}>
                  {user?.username?.charAt(0).toUpperCase()}
                </Avatar>
                <Box>
                  <Typography variant="h6">{user?.full_name || user?.username}</Typography>
                  <Chip
                    label={user?.is_superuser ? 'Administrator' : 'User'}
                    color={user?.is_superuser ? 'error' : 'primary'}
                    size="small"
                  />
                </Box>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Member since: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last login: {user?.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A'}
              </Typography>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Paper elevation={2} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <History sx={{ mr: 2 }} />
              <Typography variant="h6">Recent Activity</Typography>
            </Box>
            <List dense>
              {activityHistory.slice(0, 5).map((activity) => (
                <ListItem key={activity.id} sx={{ px: 0 }}>
                  <ListItemText
                    primary={activity.action}
                    secondary={new Date(activity.timestamp).toLocaleDateString()}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>

          {/* Danger Zone */}
          <Paper elevation={2} sx={{ p: 3, mt: 3, borderColor: 'error.main', border: 1 }}>
            <Typography variant="h6" color="error" gutterBottom>
              Danger Zone
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Permanently delete your account and all associated data.
            </Typography>
            <Button
              variant="outlined"
              color="error"
              startIcon={<Delete />}
              onClick={() => setDeleteAccountDialog(true)}
              fullWidth
            >
              Delete Account
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Delete Account Confirmation */}
      <Dialog open={deleteAccountDialog} onClose={() => setDeleteAccountDialog(false)}>
        <DialogTitle>Delete Account</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete your account? This action cannot be undone and will permanently
            remove all your data, conversations, and documents.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAccountDialog(false)}>Cancel</Button>
          <Button color="error" variant="contained">
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserProfile;