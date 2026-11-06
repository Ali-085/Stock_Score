import React from 'react';
import PropTypes from 'prop-types';
import { Box, Typography, Button, Paper } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
    this.errorRef = React.createRef();
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log error only in development
    if (import.meta.env.DEV) {
      console.error('Error boundary caught:', error, errorInfo);
    }
    
    // Focus error message for accessibility
    setTimeout(() => {
      if (this.errorRef.current) {
        this.errorRef.current.focus();
      }
    }, 100);
    
    // In production, you could send to error tracking service
    // Example: Sentry.captureException(error);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    // Use full reload to reset app state
    window.location.assign('/dashboard');
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          ref={this.errorRef}
          tabIndex={-1}
          role="alert"
          aria-live="assertive"
          sx={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'background.default',
            p: 2,
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              maxWidth: 500,
              textAlign: 'center',
            }}
          >
            <ErrorOutlineIcon
              sx={{
                fontSize: 80,
                color: 'error.main',
                mb: 2,
              }}
            />
            <Typography variant="h4" component="h1" gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              We're sorry, but something unexpected happened. Please try again.
            </Typography>
            
            {/* Only show error details in development */}
            {import.meta.env.DEV && this.state.error && (
              <Box
                sx={{
                  mt: 2,
                  p: 2,
                  bgcolor: 'grey.100',
                  borderRadius: 1,
                  textAlign: 'left',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  overflow: 'auto',
                  maxHeight: 200,
                }}
              >
                {this.state.error.toString()}
              </Box>
            )}

            <Button
              variant="contained"
              size="large"
              onClick={this.handleReset}
              sx={{ mt: 3 }}
            >
              Go to Dashboard
            </Button>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ErrorBoundary;
