import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { subscriptionService } from '../services/subscriptionService';
import { handleApiError } from '../utils/errorHandler';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  IconButton,
  Box,
  Avatar,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  CardMembership as PricingIcon,
  Logout as LogoutIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';

const drawerWidth = 280;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Pricing', icon: <PricingIcon />, path: '/pricing' }
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { darkMode, toggleTheme } = useTheme();
  const { user, logout, loadUser } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [canceling, setCanceling] = useState(false);

  const handleLogout = async () => {
    if (loggingOut) return; // Prevent double-click
    
    setLoggingOut(true);
    try {
      await logout();
      if (import.meta.env.DEV) {
        console.log('User logged out');
      }
      navigate('/login');
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('Logout failed:', error);
      }
      // Even if logout fails, redirect to login
      navigate('/login');
    } finally {
      setLoggingOut(false);
    }
  };

  const handleCancelSubscription = async () => {
    setCanceling(true);
    try {
      await subscriptionService.cancelSubscription();
      setCancelDialogOpen(false);
      // Reload user data to reflect changes
      await loadUser();
      // Show success (could add a snackbar here)
      alert('Your subscription has been canceled and your account has been downgraded to the free plan.');
    } catch (error) {
      alert(handleApiError(error, 'cancel subscription'));
    } finally {
      setCanceling(false);
    }
  };

  const hasActiveSubscription = user && user.subscription_tier !== 'free' && user.subscription_status === 'active';

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          p: 3,
        },
      }}
    >
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          📊 Stock Dashboard
        </Typography>
      </Box>

      {user && (
        <>
          <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              {user.username?.[0]?.toUpperCase() || 'U'}
            </Avatar>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                {String(user.username || '').substring(0, 150)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {String(user.subscription_tier || 'free').toLowerCase()} plan
              </Typography>
            </Box>
          </Box>
          <Divider sx={{ mb: 2 }} />
        </>
      )}
      
      <List sx={{ flexGrow: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 2,
                '&.Mui-selected': {
                  bgcolor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'white',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? 'white' : 'text.secondary' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: location.pathname === item.path ? 'bold' : 'medium',
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Box sx={{ mt: 'auto', pt: 2 }}>
        <IconButton
          onClick={toggleTheme}
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': {
              bgcolor: 'primary.dark',
            },
            width: '100%',
            borderRadius: 2,
            py: 1.5,
            mb: 2,
          }}
        >
          {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
          <Typography sx={{ ml: 1, fontWeight: 'medium' }}>
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </Typography>
        </IconButton>

        {hasActiveSubscription && (
          <Button
            fullWidth
            variant="outlined"
            color="warning"
            startIcon={<CancelIcon />}
            onClick={() => setCancelDialogOpen(true)}
            sx={{ mb: 2 }}
            aria-label="Cancel subscription"
          >
            Cancel Plan
          </Button>
        )}

        {user && (
          <Button
            fullWidth
            variant="outlined"
            startIcon={<LogoutIcon />}
            onClick={handleLogout}
            disabled={loggingOut}
            sx={{ mt: 'auto' }}
            aria-label="Logout from account"
          >
            {loggingOut ? 'Logging out...' : 'Logout'}
          </Button>
        )}
      </Box>

      <Dialog
        open={cancelDialogOpen}
        onClose={() => !canceling && setCancelDialogOpen(false)}
      >
        <DialogTitle>Cancel Subscription?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to cancel your subscription? Your account will be immediately downgraded to the free plan and you will lose access to premium features.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)} disabled={canceling}>
            Keep Subscription
          </Button>
          <Button onClick={handleCancelSubscription} color="warning" disabled={canceling}>
            {canceling ? 'Canceling...' : 'Yes, Cancel Now'}
          </Button>
        </DialogActions>
      </Dialog>
    </Drawer>
  );
}

export default Sidebar;
