/**
 * Application Router Component
 * 
 * This component handles all routing and navigation for the AI Chatbot frontend.
 * It includes route protection, lazy loading of components, and a responsive
 * navigation layout with sidebar and main content areas.
 * 
 * Features:
 * - Protected routes that require authentication
 * - Admin-only routes for system management
 * - Responsive sidebar navigation
 * - Lazy loading for better performance
 * - Breadcrumb navigation
 * - Mobile-friendly design
 */

import React, { useState, Suspense } from 'react';
import {
  Routes,
  Route,
  Navigate,
  useLocation,
  Link as RouterLink,
  useNavigate,
} from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Breadcrumbs,
  Link,
  useTheme,
  useMediaQuery,
  Chip,
  Badge,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Chat as ChatIcon,
  Description as DocumentIcon,
  Search as SearchIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  People as PeopleIcon,
  Build as ToolsIcon,
  Psychology as ProfilesIcon,
  Article as PromptsIcon,
  AdminPanelSettings as AdminIcon,
  AccountCircle,
  Logout,
  ChevronRight,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';

import { useAuth, AdminOnly } from '../contexts/AuthContext';
import { LoadingSpinner } from './common/CommonComponents';

// =============================================================================
// Lazy Loading of Page Components
// =============================================================================

// Authentication pages
const LoginPage = React.lazy(() => import('../pages/LoginPage'));
const RegisterPage = React.lazy(() => import('../pages/RegisterPage'));

// Main application pages
const DashboardPage = React.lazy(() => import('../pages/DashboardPage'));
const ChatPage = React.lazy(() => import('../pages/ChatPage'));
const DocumentsPage = React.lazy(() => import('../pages/DocumentsPage'));
const SearchPage = React.lazy(() => import('../pages/SearchPage'));
const AnalyticsPage = React.lazy(() => import('../pages/AnalyticsPage'));
const ProfilesPage = React.lazy(() => import('../pages/ProfilesPage'));
const PromptsPage = React.lazy(() => import('../pages/PromptsPage'));
const ToolsPage = React.lazy(() => import('../pages/ToolsPage'));
const SettingsPage = React.lazy(() => import('../pages/SettingsPage'));

// Admin pages
const AdminUsersPage = React.lazy(() => import('../pages/admin/AdminUsersPage'));
const AdminSystemPage = React.lazy(() => import('../pages/admin/AdminSystemPage'));
const AdminHealthPage = React.lazy(() => import('../pages/admin/AdminHealthPage'));

// =============================================================================
// Navigation Configuration
// =============================================================================

/**
 * Navigation item interface
 */
interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  adminOnly?: boolean;
  badge?: string | number;
}

/**
 * Main navigation items
 */
const navigationItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    id: 'chat',
    label: 'Chat',
    icon: <ChatIcon />,
    path: '/chat',
  },
  {
    id: 'documents',
    label: 'Documents',
    icon: <DocumentIcon />,
    path: '/documents',
  },
  {
    id: 'search',
    label: 'Search',
    icon: <SearchIcon />,
    path: '/search',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: <AnalyticsIcon />,
    path: '/analytics',
  },
  {
    id: 'profiles',
    label: 'LLM Profiles',
    icon: <ProfilesIcon />,
    path: '/profiles',
  },
  {
    id: 'prompts',
    label: 'Prompts',
    icon: <PromptsIcon />,
    path: '/prompts',
  },
  {
    id: 'tools',
    label: 'MCP Tools',
    icon: <ToolsIcon />,
    path: '/tools',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <SettingsIcon />,
    path: '/settings',
  },
];

/**
 * Admin-only navigation items
 */
const adminNavigationItems: NavItem[] = [
  {
    id: 'admin-users',
    label: 'User Management',
    icon: <PeopleIcon />,
    path: '/admin/users',
    adminOnly: true,
  },
  {
    id: 'admin-system',
    label: 'System Settings',
    icon: <AdminIcon />,
    path: '/admin/system',
    adminOnly: true,
  },
  {
    id: 'admin-health',
    label: 'System Health',
    icon: <NotificationsIcon />,
    path: '/admin/health',
    adminOnly: true,
  },
];

// =============================================================================
// Sidebar Width Configuration
// =============================================================================

const DRAWER_WIDTH = 280;

// =============================================================================
// Protected Route Component
// =============================================================================

/**
 * Component that protects routes requiring authentication
 */
function ProtectedRoute({ children }: { children: React.ReactNode }): JSX.Element {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner message="Checking authentication..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// =============================================================================
// Breadcrumb Component
// =============================================================================

/**
 * Generate breadcrumb items based on current path
 */
function AppBreadcrumbs(): JSX.Element {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Map path segments to display names
  const pathDisplayNames: Record<string, string> = {
    dashboard: 'Dashboard',
    chat: 'Chat',
    documents: 'Documents',
    search: 'Search',
    analytics: 'Analytics',
    profiles: 'LLM Profiles',
    prompts: 'Prompts',
    tools: 'MCP Tools',
    settings: 'Settings',
    admin: 'Admin',
    users: 'Users',
    system: 'System',
    health: 'Health',
  };

  if (pathnames.length === 0) {
    return <div />;
  }

  return (
    <Breadcrumbs separator={<ChevronRight fontSize="small" />} sx={{ mb: 2 }}>
      <Link component={RouterLink} to="/dashboard" color="inherit">
        Home
      </Link>
      {pathnames.map((pathname, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const displayName = pathDisplayNames[pathname] || pathname;

        return isLast ? (
          <Typography key={pathname} color="text.primary">
            {displayName}
          </Typography>
        ) : (
          <Link key={pathname} component={RouterLink} to={routeTo} color="inherit">
            {displayName}
          </Link>
        );
      })}
    </Breadcrumbs>
  );
}

// =============================================================================
// User Menu Component
// =============================================================================

/**
 * User menu in the top app bar
 */
function UserMenu(): JSX.Element {
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleMenuClose();
    await logout();
    navigate('/login');
  };

  const handleProfileClick = () => {
    handleMenuClose();
    navigate('/settings');
  };

  if (!user) {
    return <div />;
  }

  return (
    <>
      <IconButton onClick={handleMenuOpen} sx={{ ml: 2 }}>
        <Avatar sx={{ width: 32, height: 32 }}>
          {user.full_name.charAt(0).toUpperCase()}
        </Avatar>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem disabled>
          <Box>
            <Typography variant="subtitle2">{user.full_name}</Typography>
            <Typography variant="caption" color="text.secondary">
              {user.email}
            </Typography>
            {user.is_superuser && (
              <Chip label="Admin" size="small" color="primary" sx={{ mt: 0.5 }} />
            )}
          </Box>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleProfileClick}>
          <ListItemIcon>
            <AccountCircle fontSize="small" />
          </ListItemIcon>
          Profile & Settings
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>
    </>
  );
}

// =============================================================================
// Main Layout Component
// =============================================================================

/**
 * Main application layout with sidebar and content area
 */
function AppLayout({ children }: { children: React.ReactNode }): JSX.Element {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { user } = useAuth();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // Get all navigation items (including admin items for admins)
  const allNavItems = user?.is_superuser 
    ? [...navigationItems, ...adminNavigationItems]
    : navigationItems;

  /**
   * Sidebar content
   */
  const drawerContent = (
    <Box sx={{ overflow: 'auto', height: '100%' }}>
      {/* App title */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" noWrap component="div">
          AI Chatbot
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Advanced AI Assistant
        </Typography>
      </Box>

      {/* Main navigation */}
      <List>
        {allNavItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <ListItem key={item.id} disablePadding>
              <ListItemButton
                component={RouterLink}
                to={item.path}
                selected={isActive}
                onClick={isMobile ? handleDrawerToggle : undefined}
                sx={{
                  mx: 1,
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: theme.palette.primary.main,
                    color: 'white',
                    '&:hover': {
                      backgroundColor: theme.palette.primary.dark,
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'white',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? 'white' : theme.palette.text.secondary,
                  }}
                >
                  {item.badge ? (
                    <Badge badgeContent={item.badge} color="error">
                      {item.icon}
                    </Badge>
                  ) : (
                    item.icon
                  )}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  sx={{
                    '& .MuiTypography-root': {
                      fontWeight: isActive ? 600 : 400,
                    },
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Admin section */}
      {user?.is_superuser && (
        <>
          <Divider sx={{ my: 1 }} />
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="overline" color="text.secondary">
              Administration
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          zIndex: theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {/* Page title could be dynamic based on route */}
          </Typography>

          {/* Notifications */}
          <IconButton color="inherit">
            <Badge badgeContent={0} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          {/* User menu */}
          <UserMenu />
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
        >
          {drawerContent}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          overflow: 'auto',
        }}
      >
        <Toolbar /> {/* Spacer for app bar */}
        <Box sx={{ p: 3 }}>
          <AppBreadcrumbs />
          {children}
        </Box>
      </Box>
    </Box>
  );
}

// =============================================================================
// Main App Router Component
// =============================================================================

/**
 * Main application router component
 * Handles all routing, authentication, and layout
 */
export function AppRouter(): JSX.Element {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return <LoadingSpinner message="Initializing application..." />;
  }

  return (
    <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
          }
        />

        {/* Protected routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/chat/:conversationId" element={<ChatPage />} />
                  <Route path="/documents" element={<DocumentsPage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/profiles" element={<ProfilesPage />} />
                  <Route path="/prompts" element={<PromptsPage />} />
                  <Route path="/tools" element={<ToolsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />

                  {/* Admin routes */}
                  <Route
                    path="/admin/users"
                    element={
                      <AdminOnly>
                        <AdminUsersPage />
                      </AdminOnly>
                    }
                  />
                  <Route
                    path="/admin/system"
                    element={
                      <AdminOnly>
                        <AdminSystemPage />
                      </AdminOnly>
                    }
                  />
                  <Route
                    path="/admin/health"
                    element={
                      <AdminOnly>
                        <AdminHealthPage />
                      </AdminOnly>
                    }
                  />

                  {/* 404 route */}
                  <Route
                    path="*"
                    element={
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <Typography variant="h4" gutterBottom>
                          Page Not Found
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                          The page you're looking for doesn't exist.
                        </Typography>
                      </Box>
                    }
                  />
                </Routes>
              </AppLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  );
}