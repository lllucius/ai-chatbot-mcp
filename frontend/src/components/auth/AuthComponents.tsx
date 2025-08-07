/**
 * Authentication Components for AI Chatbot Frontend
 * 
 * This module provides authentication-related components including:
 * - LoginForm: User login interface
 * - RegisterForm: User registration interface
 * - ProfileForm: User profile editing
 * - PasswordChangeForm: Password change interface
 * 
 * All components use Material-UI for consistent styling and include
 * comprehensive form validation, error handling, and loading states.
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  Link,
  Paper,
  Stack,
  IconButton,
  InputAdornment,
  CircularProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Person as PersonIcon,
  Email as EmailIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useRegister, useUpdateProfile, useChangePassword } from '../../hooks/api';
import { LoadingSpinner } from '../common/CommonComponents';
import type { User, UserRegistration } from '../../types/api';

// =============================================================================
// Login Form Component
// =============================================================================

/**
 * Props for LoginForm component
 */
interface LoginFormProps {
  /** Callback when user wants to switch to registration */
  onSwitchToRegister?: () => void;
  /** Callback when login is successful */
  onLoginSuccess?: () => void;
}

/**
 * User login form with validation and error handling
 * 
 * @param props - Component props
 * @returns Login form component
 */
export function LoginForm({ onSwitchToRegister, onLoginSuccess }: LoginFormProps): React.ReactElement {
  const { login, error, clearError, isLoading } = useAuth();
  
  // Form state
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  /**
   * Validate form data
   * @returns Whether form is valid
   */
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.username.trim()) {
      errors.username = 'Username or email is required';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) return;

    try {
      clearError();
      await login(formData);
      onLoginSuccess?.();
    } catch (error) {
      // Error is handled by the auth context
      console.error('Login failed:', error);
    }
  };

  /**
   * Handle input changes
   */
  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    
    // Clear field error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 400, mx: 'auto' }}>
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h4" component="h1" align="center" gutterBottom>
          Sign In
        </Typography>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
          Welcome back! Please sign in to your account.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Username or Email"
            variant="outlined"
            value={formData.username}
            onChange={handleInputChange('username')}
            error={!!formErrors.username}
            helperText={formErrors.username}
            disabled={isLoading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <PersonIcon />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            variant="outlined"
            value={formData.password}
            onChange={handleInputChange('password')}
            error={!!formErrors.password}
            helperText={formErrors.password}
            disabled={isLoading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isLoading}
            sx={{ mt: 2 }}
          >
            {isLoading ? <CircularProgress size={24} /> : 'Sign In'}
          </Button>
        </Stack>

        {onSwitchToRegister && (
          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Typography variant="body2">
              Don't have an account?{' '}
              <Link
                component="button"
                type="button"
                onClick={onSwitchToRegister}
                disabled={isLoading}
              >
                Sign up
              </Link>
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}

// =============================================================================
// Registration Form Component
// =============================================================================

/**
 * Props for RegisterForm component
 */
interface RegisterFormProps {
  /** Callback when user wants to switch to login */
  onSwitchToLogin?: () => void;
  /** Callback when registration is successful */
  onRegisterSuccess?: () => void;
}

/**
 * User registration form with comprehensive validation
 * 
 * @param props - Component props
 * @returns Registration form component
 */
export function RegisterForm({ onSwitchToLogin, onRegisterSuccess }: RegisterFormProps): React.ReactElement {
  const registerMutation = useRegister();
  
  // Form state
  const [formData, setFormData] = useState<UserRegistration>({
    username: '',
    email: '',
    password: '',
    full_name: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  /**
   * Validate form data
   * @returns Whether form is valid
   */
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Username validation
    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      errors.username = 'Username can only contain letters, numbers, underscore, and hyphen';
    }

    // Email validation
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    // Full name validation
    if (!formData.full_name.trim()) {
      errors.full_name = 'Full name is required';
    }

    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      errors.password = 'Password must contain uppercase, lowercase, and number';
    }

    // Confirm password validation
    if (formData.password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) return;

    try {
      await registerMutation.mutateAsync(formData);
      onRegisterSuccess?.();
    } catch (error) {
      // Error is handled by the mutation
      console.error('Registration failed:', error);
    }
  };

  /**
   * Handle input changes
   */
  const handleInputChange = (field: keyof UserRegistration) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    
    // Clear field error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleConfirmPasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(event.target.value);
    
    if (formErrors.confirmPassword) {
      setFormErrors(prev => ({
        ...prev,
        confirmPassword: '',
      }));
    }
  };

  const isLoading = registerMutation.isPending;

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 400, mx: 'auto' }}>
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h4" component="h1" align="center" gutterBottom>
          Sign Up
        </Typography>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
          Create your account to get started.
        </Typography>

        {registerMutation.error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {(registerMutation.error as any)?.message || 'Registration failed'}
          </Alert>
        )}

        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Full Name"
            variant="outlined"
            value={formData.full_name}
            onChange={handleInputChange('full_name')}
            error={!!formErrors.full_name}
            helperText={formErrors.full_name}
            disabled={isLoading}
          />

          <TextField
            fullWidth
            label="Username"
            variant="outlined"
            value={formData.username}
            onChange={handleInputChange('username')}
            error={!!formErrors.username}
            helperText={formErrors.username || 'Letters, numbers, underscore, and hyphen only'}
            disabled={isLoading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <PersonIcon />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Email"
            type="email"
            variant="outlined"
            value={formData.email}
            onChange={handleInputChange('email')}
            error={!!formErrors.email}
            helperText={formErrors.email}
            disabled={isLoading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <EmailIcon />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            variant="outlined"
            value={formData.password}
            onChange={handleInputChange('password')}
            error={!!formErrors.password}
            helperText={formErrors.password || 'Min 8 characters with uppercase, lowercase, and number'}
            disabled={isLoading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Confirm Password"
            type={showConfirmPassword ? 'text' : 'password'}
            variant="outlined"
            value={confirmPassword}
            onChange={handleConfirmPasswordChange}
            error={!!formErrors.confirmPassword}
            helperText={formErrors.confirmPassword}
            disabled={isLoading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isLoading}
            sx={{ mt: 2 }}
          >
            {isLoading ? <CircularProgress size={24} /> : 'Sign Up'}
          </Button>
        </Stack>

        {onSwitchToLogin && (
          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Typography variant="body2">
              Already have an account?{' '}
              <Link
                component="button"
                type="button"
                onClick={onSwitchToLogin}
                disabled={isLoading}
              >
                Sign in
              </Link>
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}

// =============================================================================
// Profile Form Component
// =============================================================================

/**
 * Props for ProfileForm component
 */
interface ProfileFormProps {
  /** Current user data */
  user: User;
  /** Callback when profile is updated successfully */
  onUpdateSuccess?: () => void;
}

/**
 * User profile editing form
 * 
 * @param props - Component props
 * @returns Profile form component
 */
export function ProfileForm({ user, onUpdateSuccess }: ProfileFormProps): React.ReactElement {
  const updateProfileMutation = useUpdateProfile();
  
  // Form state - initialize with current user data
  const [formData, setFormData] = useState({
    full_name: user.full_name,
    email: user.email,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  /**
   * Validate form data
   * @returns Whether form is valid
   */
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.full_name.trim()) {
      errors.full_name = 'Full name is required';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) return;

    try {
      await updateProfileMutation.mutateAsync(formData);
      onUpdateSuccess?.();
    } catch (error) {
      console.error('Profile update failed:', error);
    }
  };

  /**
   * Handle input changes
   */
  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    
    // Clear field error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const isLoading = updateProfileMutation.isPending;
  const hasChanges = formData.full_name !== user.full_name || formData.email !== user.email;

  return (
    <Paper elevation={1} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Profile Information
      </Typography>

      {updateProfileMutation.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {(updateProfileMutation.error as any)?.message || 'Profile update failed'}
        </Alert>
      )}

      {updateProfileMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Profile updated successfully!
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Username"
            variant="outlined"
            value={user.username}
            disabled
            helperText="Username cannot be changed"
          />

          <TextField
            fullWidth
            label="Full Name"
            variant="outlined"
            value={formData.full_name}
            onChange={handleInputChange('full_name')}
            error={!!formErrors.full_name}
            helperText={formErrors.full_name}
            disabled={isLoading}
          />

          <TextField
            fullWidth
            label="Email"
            type="email"
            variant="outlined"
            value={formData.email}
            onChange={handleInputChange('email')}
            error={!!formErrors.email}
            helperText={formErrors.email}
            disabled={isLoading}
          />

          <Box>
            <Button
              type="submit"
              variant="contained"
              disabled={isLoading || !hasChanges}
            >
              {isLoading ? <CircularProgress size={20} /> : 'Update Profile'}
            </Button>
          </Box>
        </Stack>
      </Box>
    </Paper>
  );
}

// =============================================================================
// Password Change Form Component
// =============================================================================

/**
 * Props for PasswordChangeForm component
 */
interface PasswordChangeFormProps {
  /** Callback when password is changed successfully */
  onChangeSuccess?: () => void;
}

/**
 * Password change form with validation
 * 
 * @param props - Component props
 * @returns Password change form component
 */
export function PasswordChangeForm({ onChangeSuccess }: PasswordChangeFormProps): React.ReactElement {
  const changePasswordMutation = useChangePassword();
  
  // Form state
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  /**
   * Validate form data
   * @returns Whether form is valid
   */
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.currentPassword) {
      errors.currentPassword = 'Current password is required';
    }

    if (!formData.newPassword) {
      errors.newPassword = 'New password is required';
    } else if (formData.newPassword.length < 8) {
      errors.newPassword = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.newPassword)) {
      errors.newPassword = 'Password must contain uppercase, lowercase, and number';
    }

    if (formData.newPassword !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (formData.currentPassword === formData.newPassword) {
      errors.newPassword = 'New password must be different from current password';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) return;

    try {
      await changePasswordMutation.mutateAsync({
        current_password: formData.currentPassword,
        new_password: formData.newPassword,
      });
      
      // Reset form on success
      setFormData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
      
      onChangeSuccess?.();
    } catch (error) {
      console.error('Password change failed:', error);
    }
  };

  /**
   * Handle input changes
   */
  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    
    // Clear field error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  /**
   * Toggle password visibility
   */
  const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm') => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  const isLoading = changePasswordMutation.isPending;

  return (
    <Paper elevation={1} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Change Password
      </Typography>

      {changePasswordMutation.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {(changePasswordMutation.error as any)?.message || 'Password change failed'}
        </Alert>
      )}

      {changePasswordMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Password changed successfully!
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <TextField
            fullWidth
            label="Current Password"
            type={showPasswords.current ? 'text' : 'password'}
            variant="outlined"
            value={formData.currentPassword}
            onChange={handleInputChange('currentPassword')}
            error={!!formErrors.currentPassword}
            helperText={formErrors.currentPassword}
            disabled={isLoading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => togglePasswordVisibility('current')}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showPasswords.current ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="New Password"
            type={showPasswords.new ? 'text' : 'password'}
            variant="outlined"
            value={formData.newPassword}
            onChange={handleInputChange('newPassword')}
            error={!!formErrors.newPassword}
            helperText={formErrors.newPassword || 'Min 8 characters with uppercase, lowercase, and number'}
            disabled={isLoading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => togglePasswordVisibility('new')}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showPasswords.new ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Confirm New Password"
            type={showPasswords.confirm ? 'text' : 'password'}
            variant="outlined"
            value={formData.confirmPassword}
            onChange={handleInputChange('confirmPassword')}
            error={!!formErrors.confirmPassword}
            helperText={formErrors.confirmPassword}
            disabled={isLoading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => togglePasswordVisibility('confirm')}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showPasswords.confirm ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Box>
            <Button
              type="submit"
              variant="contained"
              disabled={isLoading}
            >
              {isLoading ? <CircularProgress size={20} /> : 'Change Password'}
            </Button>
          </Box>
        </Stack>
      </Box>
    </Paper>
  );
}