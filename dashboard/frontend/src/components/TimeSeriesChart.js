// src/components/TimeSeriesChart.js
import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart
} from 'recharts';
import { fetchTimeSeriesData } from '../services/api';
import { format } from 'date-fns';
import { Box, ToggleButtonGroup, ToggleButton, CircularProgress, Alert } from '@mui/material';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import COLORS from '../utils/colors';
import '../styles/TimeSeriesChart.css';

const TimeSeriesChart = () => {
  const TIME_OPTIONS = [
    { label: '5M', hours: 1, interval: 1 }, // Use minimum 1 hour for backend compatibility but set interval to 1 min
    { label: '1H', hours: 1, interval: 5 },
    { label: '6H', hours: 6, interval: 15 },
    { label: '12H', hours: 12, interval: 30 },
  ];
  
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeOption, setTimeOption] = useState(TIME_OPTIONS[1].label); // Default to 1H
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // Function to fetch time series data
  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Find the selected time option
      const selectedOption = TIME_OPTIONS.find(option => option.label === timeOption);
      
      // Get the hours and interval
      const hours = selectedOption ? selectedOption.hours : 1;
      const interval = selectedOption ? selectedOption.interval : 5;
      
      // Call the API
      const data = await fetchTimeSeriesData({ hours, interval });
      
      // Process the data for the chart
      const processedData = data.map(item => ({
        ...item,
        timestamp: new Date(item.timestamp),
        formattedTime: format(new Date(item.timestamp), 'HH:mm')
      }));
      
      setTimeSeriesData(processedData);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching time series data:', err);
      setError('Failed to load time series data');
    } finally {
      setLoading(false);
    }
  };
  
  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [timeOption]);
  
  // Set up an auto-refresh based on the selected time option
  useEffect(() => {
    const selectedOption = TIME_OPTIONS.find(option => option.label === timeOption);
    const refreshInterval = selectedOption.label === '5M' ? 60000 : 3600000; // 1 minute for 5M, 1 hour for others
    
    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [timeOption]);
  
  // Handle time option change
  const handleTimeChange = (event, newTimeOption) => {
    if (newTimeOption !== null) {
      setTimeOption(newTimeOption);
    }
  };
  
  return (
    <div className="time-series-chart">
      <div className="chart-options">
        <ToggleButtonGroup
          value={timeOption}
          exclusive
          onChange={handleTimeChange}
          aria-label="time range"
          size="small"
        >
          {TIME_OPTIONS.map(option => (
            <ToggleButton key={option.label} value={option.label}>
              {option.label}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </div>
      
      {error && (
        <Alert severity="error" sx={{ my: 2 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box className="loading-box">
          <CircularProgress />
        </Box>
      ) : (
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={timeSeriesData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.5} />
              <XAxis 
                dataKey="formattedTime" 
                tick={{ fontSize: 12 }}
                tickMargin={10}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickMargin={10}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  border: 'none',
                  borderRadius: '4px',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
                }}
                formatter={(value, name) => [value, name]}
                labelFormatter={(label) => `Time: ${label}`}
              />
              <Legend verticalAlign="top" height={36} />
              <Area 
                type="monotone" 
                dataKey="normal_count" 
                name="Normal" 
                fill={COLORS.NORMAL} 
                stroke={COLORS.NORMAL}
                fillOpacity={0.2}
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="anomaly_count" 
                name="Anomaly" 
                stroke={COLORS.ANOMALY} 
                strokeWidth={2}
                dot={{ r: 2, fill: COLORS.ANOMALY }}
                activeDot={{ r: 6 }}
              />
              <Line 
                type="monotone" 
                dataKey="unidentified_count" 
                name="Unidentified" 
                stroke={COLORS.UNIDENTIFIED} 
                strokeWidth={2}
                dot={{ r: 2, fill: COLORS.UNIDENTIFIED }}
                activeDot={{ r: 6 }}
              />
              <ReferenceLine y={0} stroke="#000" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default TimeSeriesChart;
