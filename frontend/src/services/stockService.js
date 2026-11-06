import api from './api';

export const stockService = {
  // Get all stocks (basic info)
  async getStocks() {
    const response = await api.get('/stocks/');
    return response.data;
  },

  // Get current scores (tier-based access)
  async getCurrentScores(symbol = null) {
    const params = symbol ? { stock__symbol: symbol } : {};
    const response = await api.get('/stocks/current-scores/', { params });
    return response.data;
  },

  // Get historic scores (requires Basic+ tier)
  async getHistoricScores(symbol = null, date = null) {
    const params = {};
    if (symbol) params.stock__symbol = symbol;
    if (date) params.date = date;
    const response = await api.get('/stocks/historic-scores/', { params });
    return response.data;
  },

  // Watchlist operations
  async getWatchlist() {
    const response = await api.get('/stocks/watchlist/');
    return response.data;
  },

  async addToWatchlist(stockId, notes = '') {
    const response = await api.post('/stocks/watchlist/', {
      stock_id: stockId,
      notes,
    });
    return response.data;
  },

  async removeFromWatchlist(watchlistId) {
    await api.delete(`/stocks/watchlist/${watchlistId}/`);
  },
};

// Named exports for convenience
export const getCurrentScores = stockService.getCurrentScores.bind(stockService);
export const getHistoricScores = stockService.getHistoricScores.bind(stockService);
export const getStocks = stockService.getStocks.bind(stockService);
