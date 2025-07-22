import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Toolbar,
  Divider,
  Typography,
  Box,
} from '@mui/material';
import {
  Chat,
  Dashboard,
  People,
  Description,
  Analytics,
  Settings,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const DRAWER_WIDTH = 240;

interface MenuItem {
  id: string;
  label: string;
  icon: React.ReactElement;
  path: string;
}

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  currentView: string;
  onViewChange: (view: string) => void;
  isAdmin: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, currentView, onViewChange, isAdmin }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const adminMenuItems: MenuItem[] = [
    { id: 'admin', label: 'Overview', icon: <Dashboard />, path: '/admin' },
    { id: 'chat', label: 'Chat Testing', icon: <Chat />, path: '/admin/chat' },
    { id: 'users', label: 'User Management', icon: <People />, path: '/admin/users' },
    { id: 'documents', label: 'Document Management', icon: <Description />, path: '/admin/documents' },
    { id: 'analytics', label: 'Analytics', icon: <Analytics />, path: '/admin/analytics' },
    { id: 'settings', label: 'System Settings', icon: <Settings />, path: '/admin/settings' },
  ];

  const handleItemClick = (item: MenuItem): void => {
    navigate(item.path);
    onViewChange(item.id);
  };

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Admin Controls
        </Typography>
      </Toolbar>
      <Divider />
      
      {/* Admin Section */}
      <Box sx={{ px: 2, py: 1 }}>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
          ADMINISTRATION
        </Typography>
        <List dense>
          {adminMenuItems.map((item) => (
            <ListItem key={item.id} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => handleItemClick(item)}
                sx={{
                  borderRadius: 1,
                  mb: 0.5,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.light',
                    color: 'primary.contrastText',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  primaryTypographyProps={{ fontSize: '0.875rem' }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </div>
  );

  return (
    <Drawer
      variant="permanent"
      open={open}
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
        },
      }}
    >
      {drawer}
    </Drawer>
  );
};

export default Sidebar;