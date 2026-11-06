import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { handleRegistrationError } from '../utils/errorHandler';
import { Box, Button, TextField, Typography, Paper, Alert, Link as MuiLink } from '@mui/material';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (!formData.username.trim() || !formData.email.trim() || !formData.password) {
      setError('Please fill in all required fields.');
      return;
    }

    // Validate username format
    if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      setError('Username can only contain letters, numbers, and underscores.');
      return;
    }

    // Validate email format
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Please enter a valid email address.');
      return;
    }

    // Validate password match
    if (formData.password !== formData.password2) {
      setError('Passwords do not match.');
      return;
    }

    // Validate password strength
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);

    try {
      await register(formData);
      navigate('/login?registered=true');
    } catch (err) {
      setError(handleRegistrationError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        p: 2,
      }}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: 500, width: '100%' }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Create Account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2, whiteSpace: 'pre-line' }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            fullWidth
            margin="normal"
            required
            label="Username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            autoComplete="username"
            inputProps={{ maxLength: 150 }}
            helperText="Letters, numbers, and underscores only"
          />

          <TextField
            fullWidth
            margin="normal"
            required
            label="Email Address"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            autoComplete="email"
            inputProps={{ maxLength: 254 }}
          />

          <TextField
            fullWidth
            margin="normal"
            label="First Name"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            autoComplete="given-name"
            inputProps={{ maxLength: 150 }}
          />

          <TextField
            fullWidth
            margin="normal"
            label="Last Name"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            autoComplete="family-name"
            inputProps={{ maxLength: 150 }}
          />

          <TextField
            fullWidth
            margin="normal"
            required
            label="Password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            autoComplete="new-password"
          />

          <TextField
            fullWidth
            margin="normal"
            required
            label="Confirm Password"
            name="password2"
            type="password"
            value={formData.password2}
            onChange={handleChange}
            autoComplete="new-password"
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading}
            sx={{ mt: 3, mb: 2 }}
          >
            {loading ? 'Creating Account...' : 'Register'}
          </Button>

          <Box textAlign="center">
            <Typography variant="body2">
              Already have an account?{' '}
              <MuiLink component={RouterLink} to="/login" underline="hover">
                Sign In
              </MuiLink>
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
