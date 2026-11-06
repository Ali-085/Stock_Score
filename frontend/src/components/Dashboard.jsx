import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getCurrentScores } from '../services/stockService';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  CircularProgress,
  Box,
  Chip,
  Alert,
  Button,
} from '@mui/material';

function Dashboard() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  // Combined effect with cleanup to prevent race conditions
  useEffect(() => {
    let isMounted = true;

    if (!user) {
      navigate('/login');
      return;
    }

    const getStocks = async () => {
      try {
        const data = await getCurrentScores();
        if (isMounted) {
          // Handle paginated response - extract results array
          const stocksArray = Array.isArray(data) ? data : (data.results || []);
          setStocks(stocksArray);
          setError('');
        }
      } catch (err) {
        if (!isMounted) return;
        
        // Only log in development
        if (import.meta.env.DEV) {
          console.error('Error fetching stocks:', err);
        }
        
        if (err.response?.status === 401) {
          navigate('/login');
        } else {
          setError('Failed to load stock data. Please try again.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    getStocks();

    return () => {
      isMounted = false;
    };
  }, [user, navigate]);

  const getSubscriptionDisplay = () => {
    if (!user) return null;
    
    const tier = user.subscription_tier || 'free';
    const status = user.subscription_status || 'active';
    
    const tierColors = {
      free: 'default',
      basic: 'info',
      pro: 'primary',
      elite: 'secondary',
    };
    
    return (
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Chip 
          label={`${tier.toUpperCase()} Plan`} 
          color={tierColors[tier]} 
          sx={{ fontWeight: 'bold' }}
        />
        {tier === 'free' && (
          <Button 
            variant="outlined" 
            size="small"
            onClick={() => navigate('/pricing')}
          >
            Upgrade
          </Button>
        )}
      </Box>
    );
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Box>
          <Typography 
            variant="h4" 
            component="h1" 
            gutterBottom 
            sx={{ 
              fontWeight: 'bold',
              mb: 1,
            }}
          >
            Stock Rankings
          </Typography>
          <Typography 
            variant="body1" 
            sx={{ 
              color: 'text.secondary',
              mb: 2,
            }}
          >
            View and analyze stock performance metrics
          </Typography>
        </Box>
      </Box>

      {getSubscriptionDisplay()}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
          <CircularProgress size={60} />
        </Box>
      ) : stocks.length === 0 ? (
        <Alert severity="info">
          No stock data available. {user?.subscription_tier === 'free' && 'Upgrade your plan to access more data.'}
        </Alert>
      ) : (
        <TableContainer 
          component={Paper} 
          elevation={0}
          sx={{ 
            borderRadius: 3,
            border: 1,
            borderColor: 'divider',
          }}
        >
          <Table sx={{ minWidth: 650 }} aria-label="stock table">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.95rem' }}>Symbol</TableCell>
                <TableCell sx={{ fontWeight: 'bold', fontSize: '0.95rem' }}>Company</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.95rem' }}>Score</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.95rem' }}>Momentum</TableCell>
                <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '0.95rem' }}>Volatility</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {stocks.map((stock) => (
                <TableRow
                  key={stock.id}
                  sx={{
                    '&:hover': { 
                      bgcolor: 'action.hover',
                    },
                    transition: 'background-color 0.2s',
                  }}
                >
                  <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                    {stock.stock?.symbol || 'N/A'}
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'medium' }}>
                    {stock.stock?.name || 'N/A'}
                  </TableCell>
                  <TableCell align="center">
                    <Chip 
                      label={stock.ml_rank || 'N/A'} 
                      color="success" 
                      size="small"
                      sx={{ 
                        fontWeight: 'bold',
                        minWidth: 60,
                      }}
                    />
                  </TableCell>
                  <TableCell align="center">
                    {stock.value_rank ? (
                      <Chip 
                        label={stock.value_rank} 
                        color="primary" 
                        size="small"
                        sx={{ fontWeight: 'bold', minWidth: 60 }}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">-</Typography>
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {stock.vol_rank ? (
                      <Chip 
                        label={stock.vol_rank} 
                        color="secondary" 
                        size="small"
                        sx={{ fontWeight: 'bold', minWidth: 60 }}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">-</Typography>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default Dashboard;
