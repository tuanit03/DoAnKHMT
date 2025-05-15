// src/services/api.js
import axios from 'axios';

// Use environment variable with fallback for local development
// In React, browser environment variables must be prefixed with REACT_APP_
const BASE_URL = process.env.REACT_APP_BACKEND_URL;

console.log('API connecting to:', BASE_URL); // Debug log to help troubleshoot

// Remove trailing slash from BASE_URL if present to avoid double slash issues
const normalizedBaseUrl = BASE_URL.endsWith('/') ? BASE_URL.slice(0, -1) : BASE_URL;

const api = axios.create({
  baseURL: normalizedBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  // Add timeout and handle proxy redirects properly
  timeout: 10000,
  maxRedirects: 5,
});

// Add response interceptor to handle errors consistently
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.message, error.response?.status);
    return Promise.reject(error);
  }
);

/**
 * Fetch logs with optional filtering parameters
 * @param {Object} params - Query parameters
 * @returns {Promise} API response
 */
export const fetchLogs = async (params) => {
  const response = await api.get('/api/logs', { params });
  return response.data;
};

/**
 * Fetch classification statistics
 * @param {Object} params - Query parameters (e.g. time range)
 * @returns {Promise} API response
 */
export const fetchClassifications = async (params) => {
  const response = await api.get('/api/statistics/classifications', { params });
  return response.data;
};

/**
 * Fetch anomaly parameters list
 * @param {Object} params - Query parameters (e.g. classification_type, limit)
 * @returns {Promise} API response
 */
export const fetchAnomalyParams = async (params) => {
  const response = await api.get('/api/anomalies/', { params });
  return response.data;
};

/**
 * Fetch time series data for charting
 * @param {Object} params - Query parameters (e.g. hours, interval_minutes)
 * @returns {Promise} API response
 */
export const fetchTimeSeriesData = async (params) => {
  const response = await api.get('/api/statistics/time-series', { params });
  return response.data;
};

/**
 * Fetch summary statistics
 * @param {Object} params - Query parameters
 * @returns {Promise} API response
 */
export const fetchSummaryStatistics = async (params) => {
  const response = await api.get('/api/statistics/summary', { params });
  return response.data;
};

export default api;