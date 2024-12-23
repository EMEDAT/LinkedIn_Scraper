import axios from 'axios';

// Create an Axios instance
const api = axios.create({
  baseURL: process.env.BACKEND_URL || 'http://localhost:5000', // Default to localhost if env is not set
  timeout: 120000, // Set timeout for 2 minutes requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add additional logic here if needed (e.g., add auth tokens)
    return config;
  },
  (error) => {
    // Handle request error
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data; // Return response data directly
  },
  (error) => {
    // Handle response error
    console.error('Response error:', error.response || error);
    return Promise.reject(error);
  }
);

export default api;