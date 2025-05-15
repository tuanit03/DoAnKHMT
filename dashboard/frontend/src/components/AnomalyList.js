// src/components/AnomalyList.js
import React, { useState, useEffect } from 'react';
import { fetchAnomalyParams } from '../services/api';
import { Box, Tabs, Tab, CircularProgress, Button, Alert, Typography } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import COLORS from '../utils/colors';
import '../styles/AnomalyList.css';

const AnomalyList = () => {
  const [anomalyParams, setAnomalyParams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('anomaly'); // 'anomaly' or 'unidentified'
  const [retryCount, setRetryCount] = useState(0);
  
  const fetchData = async () => {
    try {
      setLoading(true);
      const params = { 
        classification_type: activeTab,
        limit: 20
      };
      const data = await fetchAnomalyParams(params);
      setAnomalyParams(data);
      setError(null);
      // Reset retry count on success
      setRetryCount(0);
    } catch (err) {
      console.error('Error fetching anomaly parameters:', err);
      setError('Failed to load parameters. Please try again.');
      setRetryCount(prevCount => prevCount + 1);
    } finally {
      setLoading(false);
    }
  };
  
  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [activeTab]);
  
  // Set up auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 10000);
    
    return () => clearInterval(interval);
  }, [activeTab]);
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  const handleRefresh = () => {
    fetchData();
  };
  
  return (
    <div className="anomaly-list">
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        variant="fullWidth"
        textColor="primary"
        indicatorColor="primary"
        sx={{
          '& .MuiTab-root': {
            fontWeight: 'bold',
          }
        }}
      >
        <Tab 
          value="anomaly" 
          label="Anomalies" 
          icon={<ReportProblemIcon />} 
          iconPosition="start"
          sx={{ color: COLORS.ANOMALY }}
        />
        <Tab 
          value="unidentified" 
          label="Unidentified" 
          icon={<HelpOutlineIcon />} 
          iconPosition="start"
          sx={{ color: COLORS.UNIDENTIFIED }}
        />
      </Tabs>
      
      {error && (
        <Alert 
          severity="error" 
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={handleRefresh}
              startIcon={<RefreshIcon />}
            >
              Retry
            </Button>
          }
          sx={{ my: 2 }}
        >
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box className="loading-box">
          <CircularProgress />
        </Box>
      ) : anomalyParams.length === 0 ? (
        <Box className="empty-list">
          <Typography variant="body1">No {activeTab} parameters found</Typography>
        </Box>
      ) : (
        <div className="params-container">
          {anomalyParams.map((param) => (
            <div 
              key={param.id} 
              className="param-item"
              style={{ 
                borderLeft: `4px solid ${activeTab === 'anomaly' ? COLORS.ANOMALY : COLORS.UNIDENTIFIED}`,
                backgroundColor: activeTab === 'anomaly' ? `${COLORS.ANOMALY}10` : `${COLORS.UNIDENTIFIED}10`
              }}
            >
              <div className="param-timestamp">
                {new Date(param.timestamp).toLocaleString()}
              </div>
              <div className="param-value">{param.param_value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AnomalyList;
