// src/services/hdfsApi.js
import api from './api';

// Fetch HDFS block statistics
export const fetchBlockStats = async (params = {}) => {
  const { limit = 100, minLogs = 1, hours = 24 } = params;
  try {
    const response = await api.get('/hdfs/blocks', {
      params: { limit, min_logs: minLogs, hours }
    });
    
    // Ensure we always return an array
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error fetching HDFS block stats:', error);
    // Return empty array on error
    return [];
  }
};

// Fetch HDFS component activity
export const fetchComponentActivity = async (params = {}) => {
  const { hours = 24, components = [] } = params;
  try {
    const response = await api.get('/hdfs/components', {
      params: { hours, components }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching HDFS component activity:', error);
    throw error;
  }
};

// Fetch logs for a specific block ID
export const fetchBlockLogs = async (blockId, limit = 100) => {
  try {
    const response = await api.get(`/hdfs/logs/${blockId}`, {
      params: { limit }
    });
    return response.data;
  } catch (error) {
    console.error(`Error fetching logs for block ${blockId}:`, error);
    throw error;
  }
};
