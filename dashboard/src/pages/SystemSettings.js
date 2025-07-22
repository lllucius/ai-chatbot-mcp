import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Save,
  Refresh,
  Security,
  Storage,
  Notifications,
  Api,
  Speed,
  ExpandMore,
  Edit,
  Delete,
  Add,
  Backup,
  RestoreFromTrash,
} from '@mui/icons-material';
import axios from 'axios';

/**
 * SystemSettings Component
 * 
 * Comprehensive system configuration interface providing:
 * - General application settings and preferences
 * - Security configuration and authentication settings
 * - API rate limits and performance tuning
 * - Storage and file upload configuration
 * - Notification and email settings
 * - Database backup and maintenance tools
 * - Environment variable management
 */
const SystemSettings = () => {
  // State management for settings
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null, title: '', message: '' });
  
  // Settings categories
  const [generalSettings, setGeneralSettings] = useState({
    app_name: 'AI Chatbot Platform',
    app_description: 'Enterprise-grade AI chatbot with document processing',
    maintenance_mode: false,
    debug_mode: false,
    default_language: 'en',
    timezone: 'UTC',
  });

  const [securitySettings, setSecuritySettings] = useState({
    jwt_expiry_hours: 24,
    max_login_attempts: 5,
    password_min_length: 8,
    require_special_chars: true,
    session_timeout_minutes: 30,
    two_factor_enabled: false,
  });

  const [apiSettings, setApiSettings] = useState({
    rate_limit_per_minute: 100,
    max_file_size_mb: 10,
    allowed_file_types: 'pdf,docx,txt,md,rtf',
    openai_model: 'gpt-4',
    embedding_model: 'text-embedding-3-small',
    max_tokens: 1000,
    temperature: 0.7,
  });

  const [storageSettings, setStorageSettings] = useState({
    upload_path: '/uploads',
    backup_path: '/backups',
    cleanup_old_files: true,
    cleanup_days: 30,
    compression_enabled: true,
    auto_backup: true,
    backup_frequency: 'daily',
  });

  const [notificationSettings, setNotificationSettings] = useState({
    email_notifications: true,
    system_alerts: true,
    user_registration_notify: true,
    error_notifications: true,
    smtp_server: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    from_email: '',
  });

  /**
   * Loads settings from the API
   */
  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/admin/settings');
      const settings = response.data;
      
      setGeneralSettings(settings.general || generalSettings);
      setSecuritySettings(settings.security || securitySettings);
      setApiSettings(settings.api || apiSettings);
      setStorageSettings(settings.storage || storageSettings);
      setNotificationSettings(settings.notifications || notificationSettings);
      
      setError('');
    } catch (err) {
      setError('Failed to load system settings');
      console.error('Error loading settings:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  /**
   * Saves settings to the API
   */
  const saveSettings = async (category, settings) => {
    try {
      setSaving(true);
      await axios.put('/api/v1/admin/settings', {
        category,
        settings,
      });
      
      setSuccess(`${category} settings saved successfully`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(`Failed to save ${category} settings`);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Handles system backup
   */
  const handleBackup = async () => {
    try {
      setSaving(true);
      const response = await axios.post('/api/v1/admin/backup');
      setSuccess('System backup completed successfully');
      
      // Download backup file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backup_${new Date().toISOString().split('T')[0]}.sql`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to create backup');
    } finally {
      setSaving(false);
    }
  };

  /**
   * Handles cache clearing
   */
  const handleClearCache = async () => {
    try {
      setSaving(true);
      await axios.post('/api/v1/admin/clear-cache');
      setSuccess('Cache cleared successfully');
    } catch (err) {
      setError('Failed to clear cache');
    } finally {
      setSaving(false);
    }
  };

  /**
   * Shows confirmation dialog for dangerous actions
   */
  const showConfirmDialog = (action, title, message) => {
    setConfirmDialog({
      open: true,
      action,
      title,
      message,
    });
  };

  /**
   * Handles confirmed actions
   */
  const handleConfirmedAction = () => {
    const { action } = confirmDialog;
    setConfirmDialog({ open: false, action: null, title: '', message: '' });
    
    switch (action) {
      case 'backup':
        handleBackup();
        break;
      case 'clearCache':
        handleClearCache();
        break;
      default:
        break;
    }
  };

  /**
   * Settings section component
   */
  const SettingsSection = ({ title, icon, children, onSave, settings, category }) => (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1 }}>
            {title}
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ width: '100%' }}>
          {children}
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={() => onSave(category, settings)}
              disabled={saving}
            >
              Save {title}
            </Button>
          </Box>
        </Box>
      </AccordionDetails>
    </Accordion>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Configure system-wide settings, security, and performance parameters
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

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* General Settings */}
          <Grid item xs={12}>
            <Paper elevation={2}>
              <SettingsSection
                title="General Settings"
                icon={<Speed />}
                onSave={saveSettings}
                settings={generalSettings}
                category="general"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Application Name"
                      value={generalSettings.app_name}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, app_name: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Default Language</InputLabel>
                      <Select
                        value={generalSettings.default_language}
                        label="Default Language"
                        onChange={(e) => setGeneralSettings({ ...generalSettings, default_language: e.target.value })}
                      >
                        <MenuItem value="en">English</MenuItem>
                        <MenuItem value="es">Spanish</MenuItem>
                        <MenuItem value="fr">French</MenuItem>
                        <MenuItem value="de">German</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      label="Application Description"
                      value={generalSettings.app_description}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, app_description: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.maintenance_mode}
                          onChange={(e) => setGeneralSettings({ ...generalSettings, maintenance_mode: e.target.checked })}
                        />
                      }
                      label="Maintenance Mode"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.debug_mode}
                          onChange={(e) => setGeneralSettings({ ...generalSettings, debug_mode: e.target.checked })}
                        />
                      }
                      label="Debug Mode"
                    />
                  </Grid>
                </Grid>
              </SettingsSection>
            </Paper>
          </Grid>

          {/* Security Settings */}
          <Grid item xs={12}>
            <Paper elevation={2}>
              <SettingsSection
                title="Security Settings"
                icon={<Security />}
                onSave={saveSettings}
                settings={securitySettings}
                category="security"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="JWT Expiry (hours)"
                      value={securitySettings.jwt_expiry_hours}
                      onChange={(e) => setSecuritySettings({ ...securitySettings, jwt_expiry_hours: parseInt(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Login Attempts"
                      value={securitySettings.max_login_attempts}
                      onChange={(e) => setSecuritySettings({ ...securitySettings, max_login_attempts: parseInt(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Password Min Length"
                      value={securitySettings.password_min_length}
                      onChange={(e) => setSecuritySettings({ ...securitySettings, password_min_length: parseInt(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Session Timeout (minutes)"
                      value={securitySettings.session_timeout_minutes}
                      onChange={(e) => setSecuritySettings({ ...securitySettings, session_timeout_minutes: parseInt(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={securitySettings.require_special_chars}
                          onChange={(e) => setSecuritySettings({ ...securitySettings, require_special_chars: e.target.checked })}
                        />
                      }
                      label="Require Special Characters"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={securitySettings.two_factor_enabled}
                          onChange={(e) => setSecuritySettings({ ...securitySettings, two_factor_enabled: e.target.checked })}
                        />
                      }
                      label="Two-Factor Authentication"
                    />
                  </Grid>
                </Grid>
              </SettingsSection>
            </Paper>
          </Grid>

          {/* API Settings */}
          <Grid item xs={12}>
            <Paper elevation={2}>
              <SettingsSection
                title="API Configuration"
                icon={<Api />}
                onSave={saveSettings}
                settings={apiSettings}
                category="api"
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Rate Limit (per minute)"
                      value={apiSettings.rate_limit_per_minute}
                      onChange={(e) => setApiSettings({ ...apiSettings, rate_limit_per_minute: parseInt(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Max File Size (MB)"
                      value={apiSettings.max_file_size_mb}
                      onChange={(e) => setApiSettings({ ...apiSettings, max_file_size_mb: parseInt(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="OpenAI Model"
                      value={apiSettings.openai_model}
                      onChange={(e) => setApiSettings({ ...apiSettings, openai_model: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Embedding Model"
                      value={apiSettings.embedding_model}
                      onChange={(e) => setApiSettings({ ...apiSettings, embedding_model: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Tokens"
                      value={apiSettings.max_tokens}
                      onChange={(e) => setApiSettings({ ...apiSettings, max_tokens: parseInt(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Temperature"
                      inputProps={{ step: 0.1, min: 0, max: 2 }}
                      value={apiSettings.temperature}
                      onChange={(e) => setApiSettings({ ...apiSettings, temperature: parseFloat(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Allowed File Types (comma-separated)"
                      value={apiSettings.allowed_file_types}
                      onChange={(e) => setApiSettings({ ...apiSettings, allowed_file_types: e.target.value })}
                    />
                  </Grid>
                </Grid>
              </SettingsSection>
            </Paper>
          </Grid>

          {/* System Maintenance */}
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Backup sx={{ mr: 1 }} />
                System Maintenance
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Database Backup
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Create a complete backup of the database
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<Backup />}
                        onClick={() => showConfirmDialog('backup', 'Create Backup', 'Are you sure you want to create a database backup?')}
                        disabled={saving}
                      >
                        Create Backup
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Clear Cache
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Clear all application caches
                      </Typography>
                      <Button
                        variant="outlined"
                        startIcon={<RestoreFromTrash />}
                        onClick={() => showConfirmDialog('clearCache', 'Clear Cache', 'Are you sure you want to clear all caches?')}
                        disabled={saving}
                      >
                        Clear Cache
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ ...confirmDialog, open: false })}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <Typography>{confirmDialog.message}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ ...confirmDialog, open: false })}>
            Cancel
          </Button>
          <Button onClick={handleConfirmedAction} variant="contained" color="primary">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SystemSettings;