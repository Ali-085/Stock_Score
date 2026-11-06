import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { subscriptionService } from '../services/subscriptionService';
import { handleApiError } from '../utils/errorHandler';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Link as MuiLink,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

export default function Pricing() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingPlanId, setProcessingPlanId] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState({
    open: false,
    plan: null,
    preview: null,
    loading: false,
  });
  const { user, loadUser } = useAuth();

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const data = await subscriptionService.getPlans();
      // Handle paginated response - extract results array
      const plansArray = Array.isArray(data) ? data : (data.results || []);
      setPlans(plansArray);
    } catch (error) {
      // Only log in development
      if (import.meta.env.DEV) {
        console.error('Failed to load plans:', error);
      }
      setError('Failed to load subscription plans. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (plan) => {
    if (!user) {
      window.location.href = '/login';
      return;
    }

    const isCurrentPlan = user?.subscription_tier === plan.tier;
    
    if (isCurrentPlan) {
      setError('You are already on this plan. Use the "Cancel Plan" button in the sidebar to cancel your subscription.');
      return;
    }

    setProcessingPlanId(plan.id);
    setError('');

    try {
      // First, try to create checkout session (for new subscriptions or free users)
      const response = await subscriptionService.createCheckoutSession(plan.stripe_price_id);
      
      // If requires_confirmation is true, this is an upgrade/downgrade - preview it
      if (response.requires_confirmation) {
        // Get proration preview
        const preview = await subscriptionService.previewSubscriptionChange(plan.stripe_price_id);
        
        // Show confirmation dialog
        setConfirmDialog({
          open: true,
          plan: plan,
          preview: preview,
          loading: false,
        });
        setProcessingPlanId(null);
      } else {
        // New subscription - redirect to Stripe Checkout
        window.location.href = response.url;
      }
    } catch (error) {
      setError(handleApiError(error, 'checkout'));
      setProcessingPlanId(null);
    }
  };

  const handleConfirmChange = async () => {
    setConfirmDialog(prev => ({ ...prev, loading: true }));
    
    try {
      await subscriptionService.confirmSubscriptionChange(confirmDialog.plan.stripe_price_id);
      
      // Refresh user data
      await loadUser();
      
      // Close dialog and show success
      setConfirmDialog({ open: false, plan: null, preview: null, loading: false });
      setError('');
      
      // Optionally reload plans to update UI
      await loadPlans();
    } catch (error) {
      setError(handleApiError(error, 'subscription update'));
      setConfirmDialog({ open: false, plan: null, preview: null, loading: false });
    }
  };

  const handleCancelDialog = () => {
    setConfirmDialog({ open: false, plan: null, preview: null, loading: false });
  };

  const getTierColor = (tier) => {
    const colors = {
      free: 'default',
      basic: 'primary',
      pro: 'secondary',
      elite: 'error',
    };
    return colors[tier] || 'default';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 8 }}>
      <Typography variant="h3" component="h1" align="center" gutterBottom>
        Choose Your Plan
      </Typography>
      <Typography variant="h6" align="center" color="text.secondary" paragraph>
        Select the perfect plan for your stock analysis needs
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={4} sx={{ mt: 4 }}>
        {plans.map((plan) => {
          const isCurrentPlan = user?.subscription_tier === plan.tier;
          const isProcessing = processingPlanId === plan.id;

          return (
            <Grid item xs={12} sm={6} md={3} key={plan.id}>
              <Card
                elevation={isCurrentPlan ? 8 : 2}
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  border: isCurrentPlan ? 2 : 0,
                  borderColor: 'primary.main',
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h5" component="h2">
                      {plan.name}
                    </Typography>
                    {isCurrentPlan && (
                      <Chip
                        label="Current"
                        color="primary"
                        size="small"
                        icon={<CheckCircleIcon />}
                      />
                    )}
                  </Box>

                  <Typography variant="h4" color="primary" gutterBottom>
                    ${plan.price_per_month}
                    <Typography variant="subtitle1" component="span" color="text.secondary">
                      /month
                    </Typography>
                  </Typography>

                  <Box mt={3}>
                    {plan.features && typeof plan.features === 'object' && (
                      <>
                        {Object.values(plan.features).map((feature, index) => (
                          <Box key={index} display="flex" alignItems="center" mb={1}>
                            <CheckCircleIcon
                              color="success"
                              sx={{ mr: 1, fontSize: '1.2rem' }}
                            />
                            <Typography variant="body2">{feature}</Typography>
                          </Box>
                        ))}
                      </>
                    )}
                  </Box>
                </CardContent>

                <CardActions sx={{ p: 2 }}>
                  <Button
                    fullWidth
                    variant={isCurrentPlan ? 'outlined' : 'contained'}
                    color={getTierColor(plan.tier)}
                    size="large"
                    onClick={() => handleSubscribe(plan)}
                    disabled={isProcessing || !user}
                    aria-label={`Subscribe to ${plan.name} plan`}
                  >
                    {isProcessing
                      ? 'Processing...'
                      : isCurrentPlan
                      ? 'Current Plan'
                      : user
                      ? plan.tier === 'free' ? 'Free Plan' : 'Select Plan'
                      : 'Login to Subscribe'}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {!user && (
        <Alert severity="info" sx={{ mt: 4 }}>
          Please{' '}
          <MuiLink component={RouterLink} to="/login" underline="hover">
            login
          </MuiLink>
          {' '}or{' '}
          <MuiLink component={RouterLink} to="/register" underline="hover">
            create an account
          </MuiLink>
          {' '}to subscribe to a plan.
        </Alert>
      )}

      {/* Confirmation Dialog for Subscription Change */}
      <Dialog
        open={confirmDialog.open}
        onClose={handleCancelDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Confirm Subscription Change
        </DialogTitle>
        <DialogContent>
          {confirmDialog.preview && (
            <Box>
              <Typography variant="body1" gutterBottom>
                You are about to change your subscription:
              </Typography>
              
              <Box sx={{ my: 3 }}>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Current Plan
                    </Typography>
                    <Typography variant="h6">
                      {confirmDialog.preview.current_plan.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ${confirmDialog.preview.current_plan.price}/month
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      New Plan
                    </Typography>
                    <Typography variant="h6">
                      {confirmDialog.preview.new_plan.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ${confirmDialog.preview.new_plan.price}/month
                    </Typography>
                  </Grid>
                </Grid>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ my: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Billing Summary
                </Typography>
                
                {confirmDialog.preview.is_upgrade ? (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Upgrade Charge</strong>
                    </Typography>
                    <Typography variant="body2">
                      You will be charged <strong>${confirmDialog.preview.immediate_charge.toFixed(2)}</strong> now 
                      for the prorated difference until {new Date(confirmDialog.preview.period_end).toLocaleDateString()}.
                    </Typography>
                  </Alert>
                ) : (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Downgrade Credit</strong>
                    </Typography>
                    <Typography variant="body2">
                      A credit of <strong>${confirmDialog.preview.credit_applied.toFixed(2)}</strong> will be applied 
                      to your account for the unused time on your current plan.
                    </Typography>
                  </Alert>
                )}

                <Typography variant="body2" color="text.secondary">
                  Your next billing date: {new Date(confirmDialog.preview.period_end).toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={handleCancelDialog} 
            disabled={confirmDialog.loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirmChange}
            variant="contained"
            disabled={confirmDialog.loading}
            color={confirmDialog.preview?.is_upgrade ? 'primary' : 'secondary'}
          >
            {confirmDialog.loading ? 'Processing...' : 'Confirm Change'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
