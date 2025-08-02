/**
 * Settings Page Component
 * 
 * This page provides user settings and profile management including:
 * - User profile editing (name, email)
 * - Password change functionality
 * - Account preferences and settings
 * - Security settings
 * - Notification preferences
 * - Data export and privacy controls
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Divider,
  Alert,
  Button,
  Stack,
  Switch,
  FormControlLabel,
  FormGroup,
} from '@mui/material';
import {
  Person as PersonIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Storage as DataIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

import { PageHeader, LoadingSpinner } from '../components/common/CommonComponents';
import { ProfileForm, PasswordChangeForm } from '../components/auth/AuthComponents';
import { useAuth } from '../contexts/AuthContext';

// =============================================================================
// Tab Panel Component
// =============================================================================

/**
 * Props for TabPanel component
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * Tab panel component for organizing settings sections
 */
function TabPanel({ children, value, index }: TabPanelProps): JSX.Element {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

// =============================================================================
// Profile Settings Tab Component
// =============================================================================

/**
 * Profile settings tab component
 */
function ProfileSettingsTab(): JSX.Element {
  const { user } = useAuth();
  const [updateSuccess, setUpdateSuccess] = useState(false);

  const handleUpdateSuccess = () => {
    setUpdateSuccess(true);
    setTimeout(() => setUpdateSuccess(false), 5000);
  };

  if (!user) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  return (
    <Stack spacing={3}>
      {updateSuccess && (
        <Alert severity="success">
          Profile updated successfully!
        </Alert>
      )}

      <ProfileForm user={user} onUpdateSuccess={handleUpdateSuccess} />

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Account Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Username
              </Typography>
              <Typography variant="body1">{user.username}</Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Account Type
              </Typography>
              <Typography variant="body1">
                {user.is_superuser ? 'Administrator' : 'Standard User'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Account Status
              </Typography>
              <Typography variant="body1" color={user.is_active ? 'success.main' : 'error.main'}>
                {user.is_active ? 'Active' : 'Inactive'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Member Since
              </Typography>
              <Typography variant="body1">
                {new Date(user.created_at).toLocaleDateString()}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Stack>
  );
}

// =============================================================================
// Security Settings Tab Component
// =============================================================================

/**
 * Security settings tab component
 */
function SecuritySettingsTab(): JSX.Element {
  const [passwordChangeSuccess, setPasswordChangeSuccess] = useState(false);

  const handlePasswordChangeSuccess = () => {
    setPasswordChangeSuccess(true);
    setTimeout(() => setPasswordChangeSuccess(false), 5000);
  };

  return (
    <Stack spacing={3}>
      {passwordChangeSuccess && (
        <Alert severity="success">
          Password changed successfully!
        </Alert>
      )}

      <PasswordChangeForm onChangeSuccess={handlePasswordChangeSuccess} />

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Security Preferences
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Require password confirmation for sensitive actions"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Log out from all devices when password is changed"
            />
            <FormControlLabel
              control={<Switch />}
              label="Send email notifications for login attempts"
            />
          </FormGroup>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Session Management
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Manage your active sessions and logged-in devices.
          </Typography>
          <Button variant="outlined" color="warning">
            Log Out All Devices
          </Button>
        </CardContent>
      </Card>
    </Stack>
  );
}

// =============================================================================
// Notifications Settings Tab Component
// =============================================================================

/**
 * Notifications settings tab component
 */
function NotificationsSettingsTab(): JSX.Element {
  return (
    <Stack spacing={3}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Email Notifications
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Document processing completion"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="System maintenance notifications"
            />
            <FormControlLabel
              control={<Switch />}
              label="Weekly usage reports"
            />
            <FormControlLabel
              control={<Switch />}
              label="New feature announcements"
            />
          </FormGroup>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            In-App Notifications
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Real-time chat notifications"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Processing status updates"
            />
            <FormControlLabel
              control={<Switch />}
              label="System alerts and warnings"
            />
          </FormGroup>
        </CardContent>
      </Card>
    </Stack>
  );
}

// =============================================================================
// Data & Privacy Settings Tab Component
// =============================================================================

/**
 * Data and privacy settings tab component
 */
function DataPrivacySettingsTab(): JSX.Element {
  const handleExportData = () => {
    // This would typically call an API endpoint to export user data
    console.log('Exporting user data...');
  };

  const handleDeleteAccount = () => {
    // This would show a confirmation dialog and call delete API
    console.log('Account deletion requested...');
  };

  return (
    <Stack spacing={3}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Data Export
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Download a copy of your data including conversations, documents, and settings.
          </Typography>
          <Button variant="outlined" onClick={handleExportData}>
            Request Data Export
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Privacy Preferences
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Allow usage analytics collection"
            />
            <FormControlLabel
              control={<Switch />}
              label="Share anonymous usage data for improvements"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Store conversation history"
            />
          </FormGroup>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Data Retention
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Configure how long your data is stored in the system.
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Auto-delete conversations older than 1 year"
            />
            <FormControlLabel
              control={<Switch />}
              label="Auto-delete processed documents after 6 months"
            />
          </FormGroup>
        </CardContent>
      </Card>

      <Divider />

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom color="error">
            Danger Zone
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            These actions are irreversible. Please proceed with caution.
          </Typography>
          <Stack spacing={2}>
            <Button variant="outlined" color="warning">
              Delete All Conversations
            </Button>
            <Button variant="outlined" color="warning">
              Delete All Documents
            </Button>
            <Button variant="outlined" color="error" onClick={handleDeleteAccount}>
              Delete Account
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

// =============================================================================
// Application Settings Tab Component
// =============================================================================

/**
 * Application settings tab component
 */
function ApplicationSettingsTab(): JSX.Element {
  return (
    <Stack spacing={3}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Interface Preferences
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Enable dark mode"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Show typing indicators in chat"
            />
            <FormControlLabel
              control={<Switch />}
              label="Auto-scroll to new messages"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Show message timestamps"
            />
          </FormGroup>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Default Settings
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Enable RAG by default in new conversations"
            />
            <FormControlLabel
              control={<Switch />}
              label="Auto-save conversation titles"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Show document sources in AI responses"
            />
          </FormGroup>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Performance
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Enable response caching"
            />
            <FormControlLabel
              control={<Switch />}
              label="Preload conversation history"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Compress uploaded documents"
            />
          </FormGroup>
        </CardContent>
      </Card>
    </Stack>
  );
}

// =============================================================================
// Main Settings Page Component
// =============================================================================

/**
 * Main settings page component
 */
export default function SettingsPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState(0);
  const { user } = useAuth();

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const tabs = [
    { label: 'Profile', icon: <PersonIcon />, component: ProfileSettingsTab },
    { label: 'Security', icon: <SecurityIcon />, component: SecuritySettingsTab },
    { label: 'Notifications', icon: <NotificationsIcon />, component: NotificationsSettingsTab },
    { label: 'Data & Privacy', icon: <DataIcon />, component: DataPrivacySettingsTab },
    { label: 'Application', icon: <SettingsIcon />, component: ApplicationSettingsTab },
  ];

  if (!user) {
    return <LoadingSpinner message="Loading settings..." />;
  }

  return (
    <Box>
      <PageHeader
        title="Settings"
        subtitle="Manage your account, security, and preferences"
      />

      <Grid container spacing={3}>
        {/* Settings Navigation */}
        <Grid item xs={12} md={3}>
          <Card>
            <Tabs
              orientation="vertical"
              value={activeTab}
              onChange={handleTabChange}
              sx={{
                borderRight: 1,
                borderColor: 'divider',
                '& .MuiTab-root': {
                  alignItems: 'flex-start',
                  textAlign: 'left',
                  minHeight: 48,
                },
              }}
            >
              {tabs.map((tab, index) => (
                <Tab
                  key={index}
                  icon={tab.icon}
                  iconPosition="start"
                  label={tab.label}
                  id={`settings-tab-${index}`}
                  aria-controls={`settings-tabpanel-${index}`}
                  sx={{
                    justifyContent: 'flex-start',
                    '& .MuiTab-iconWrapper': {
                      marginRight: 1,
                      marginBottom: 0,
                    },
                  }}
                />
              ))}
            </Tabs>
          </Card>
        </Grid>

        {/* Settings Content */}
        <Grid item xs={12} md={9}>
          {tabs.map((tab, index) => (
            <TabPanel key={index} value={activeTab} index={index}>
              <tab.component />
            </TabPanel>
          ))}
        </Grid>
      </Grid>
    </Box>
  );
}