import axios from 'axios';

export const fetchData = async () => {
  try {
    const response = await axios.get('http://localhost:3000/Stocks');
    return response.data;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
}