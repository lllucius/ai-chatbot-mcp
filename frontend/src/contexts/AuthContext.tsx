/**
 * Authentication Context for AI Chatbot Frontend
 * 
 * This context provides authentication state management throughout the application.
 * It handles user authentication, token management, and provides utilities for
 * protecting routes and accessing current user information.
 * 
 * Features:
 * - Current user state management
 * - Authentication status tracking
 * - Automatic token restoration on app load
 * - Protected route utilities
 * - Login/logout functionality
 * - Type-safe context with excellent developer experience
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import sdkService, { type User, type LoginRequest } from '../services/sdk-service';

// =============================================================================
// Authentication Context Types
// =============================================================================

/**
 * Authentication context value interface
 * Provides all authentication-related state and methods
 */
interface AuthContextValue {
  /** Current authenticated user, null if not logged in */
  user: User | null;
  /** Whether authentication status is currently being determined */
  isLoading: boolean;
  /** Whether user is currently authenticated */
  isAuthenticated: boolean;
  /** Login function that accepts credentials */
  login: (credentials: LoginRequest) => Promise<void>;
  /** Logout function that clears authentication */
  logout: () => Promise<void>;
  /** Error from authentication operations */
  error: string | null;
  /** Clear any authentication errors */
  clearError: () => void;
}

/**
 * Props for the AuthProvider component
 */
interface AuthProviderProps {
  /** Child components that will have access to auth context */
  children: ReactNode;
}

// =============================================================================
// Context Creation
// =============================================================================

/**
 * Create the authentication context with undefined default
 * This forces consumers to use the context within an AuthProvider
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Custom hook to access authentication context
 * Throws an error if used outside of AuthProvider
 * 
 * @returns Authentication context value
 * @throws Error if used outside AuthProvider
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// =============================================================================
// Authentication Provider Component
// =============================================================================

/**
 * Authentication Provider Component
 * 
 * This component wraps the entire application and provides authentication
 * state and methods to all child components. It automatically handles
 * token restoration, user fetching, and authentication state management.
 * 
 * @param props - Component props
 * @returns Provider component with authentication context
 */
export function AuthProvider({ children }: AuthProviderProps): React.ReactElement {
  // Local state
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Check if user is authenticated based on SDK state
  const isAuthenticated = sdkService.isAuthenticated() && user !== null;

  /**
   * Initialize authentication state
   */
  useEffect(() => {
    const initAuth = async () => {
      if (sdkService.isAuthenticated()) {
        try {
          const currentUser = await sdkService.getCurrentUser();
          setUser(currentUser);
        } catch (err) {
          console.error('Failed to get current user:', err);
          // Clear invalid token
          sdkService.getSdk().clearToken();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  /**
   * Listen for auth required events (global SDK error handling)
   */
  useEffect(() => {
    const handleAuthRequired = () => {
      setUser(null);
      setError('Authentication required. Please log in again.');
    };

    window.addEventListener('auth:required', handleAuthRequired);
    return () => window.removeEventListener('auth:required', handleAuthRequired);
  }, []);

  /**
   * Login function
   * Attempts to authenticate user with provided credentials
   * 
   * @param credentials - User login credentials
   * @throws Error if login fails
   */
  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);
      
      // Perform login via SDK
      await sdkService.login(credentials);
      
      // Get user data after successful login
      const currentUser = await sdkService.getCurrentUser();
      setUser(currentUser);
      
    } catch (err: any) {
      const errorMessage = err?.message || 'Login failed. Please check your credentials and try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout function
   * Clears authentication and user data
   */
  const logout = async (): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);
      
      await sdkService.logout();
      setUser(null);
      
    } catch (err: any) {
      // Logout errors are generally not critical, just log them
      console.error('Logout error:', err);
      // Still clear user state even if logout fails
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Clear authentication errors
   */
  const clearError = (): void => {
    setError(null);
  };

  // Context value object
  const contextValue: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    error,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// =============================================================================
// Authentication Utilities
// =============================================================================

/**
 * Higher-order component for protecting routes
 * Redirects to login page if user is not authenticated
 * 
 * @param WrappedComponent - Component to protect
 * @returns Protected component
 */
export function withAuthRequired<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.ComponentType<P> {
  const ProtectedComponent = (props: P) => {
    const { isAuthenticated, isLoading } = useAuth();

    // Show loading state while checking authentication
    if (isLoading) {
      return (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh' 
        }}>
          <div>Loading...</div>
        </div>
      );
    }

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      // In a real app, you'd use React Router's Navigate component
      window.location.href = '/login';
      return null;
    }

    return <WrappedComponent {...props} />;
  };

  ProtectedComponent.displayName = `withAuthRequired(${WrappedComponent.displayName || WrappedComponent.name})`;
  
  return ProtectedComponent;
}

/**
 * Hook to check if current user has admin privileges
 * 
 * @returns Object with admin status and loading state
 */
export function useIsAdmin(): { isAdmin: boolean; isLoading: boolean } {
  const { user, isLoading } = useAuth();
  
  return {
    isAdmin: !!user?.is_superuser,
    isLoading,
  };
}

/**
 * Component that only renders children if user is an admin
 * 
 * @param props - Component props
 * @returns Admin-only content or null
 */
export function AdminOnly({ children }: { children: ReactNode }): React.ReactElement | null {
  const { isAdmin } = useIsAdmin();
  
  return isAdmin ? <>{children}</> : null;
}

/**
 * Component that renders different content based on authentication status
 * 
 * @param props - Component props
 * @returns Appropriate content based on auth status
 */
export function AuthGuard({ 
  children, 
  fallback, 
  loading 
}: { 
  children: ReactNode; 
  fallback?: ReactNode; 
  loading?: ReactNode;
}): React.ReactElement {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <>{loading || <div>Loading...</div>}</>;
  }

  if (!isAuthenticated) {
    return <>{fallback || <div>Please log in to access this content.</div>}</>;
  }

  return <>{children}</>;
}