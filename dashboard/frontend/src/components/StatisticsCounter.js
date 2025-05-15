// src/components/StatisticsCounter.js
import React, { useState, useEffect } from 'react';
import { connectToSSE } from '../services/eventSource';
import { Box } from '@mui/material';
import COLORS from '../utils/colors';
import '../styles/StatisticsCounter.css';

const StatisticsCounter = () => {
  const [stats, setStats] = useState({
    normal_count: 0,
    anomaly_count: 0,
    unidentified_count: 0,
    total_events: 0,
    normal_percent: 0,
    anomaly_percent: 0,
    unidentified_percent: 0
  });
  const [connectionError, setConnectionError] = useState(false);
  
  useEffect(() => {
    const handleError = (error) => {
      console.error('StatisticsCounter SSE error:', error);
      setConnectionError(true);
    };
    
    const eventSource = connectToSSE('/api/statistics/stream', handleError);
    
    if (eventSource) {
      eventSource.addEventListener('statistics', (event) => {
        try {
          if (!event.data) {
            console.warn('Received empty data in statistics event');
            return;
          }
          
          const statsData = JSON.parse(event.data);
          setStats(statsData);
        } catch (error) {
          console.error('Error parsing statistics data:', error);
        }
      });
      
      eventSource.addEventListener('ping', (event) => {
        try {
          const pingData = JSON.parse(event.data);
          setConnectionError(false);
        } catch (error) {
          console.error('Error parsing ping data:', error);
        }
      });
      
      return () => {
        console.log('Closing StatisticsCounter SSE connection');
        eventSource.close();
      };
    }
  }, []);
  
  // Create an array of classification data for rendering
  const classificationData = [
    {
      key: 'normal',
      label: 'Normal',
      count: stats.normal_count,
      percent: stats.normal_percent,
      color: COLORS.NORMAL
    },
    {
      key: 'anomaly',
      label: 'Anomaly',
      count: stats.anomaly_count,
      percent: stats.anomaly_percent,
      color: COLORS.ANOMALY
    },
    {
      key: 'unidentified',
      label: 'Unidentified',
      count: stats.unidentified_count,
      percent: stats.unidentified_percent,
      color: COLORS.UNIDENTIFIED
    }
  ];
  
  return (
    <div className="statistics-counter">
      {connectionError ? (
        <Box className="connection-error">
          Connection error. Trying to reconnect...
        </Box>
      ) : (
        <div className="pie-charts-container">
          {classificationData.map(({ key, label, count, percent, color }) => (
            <div key={key} className="pie-chart-wrapper">
              <div className="pie-chart">
                <div 
                  className="pie" 
                  style={{
                    background: `conic-gradient(${color} 0% ${percent}%, #f0f0f0 ${percent}% 100%)`
                  }}
                >
                  <div className="pie-center">
                    <div className="percent-value">{percent}%</div>
                    <div className="count-value">{count}</div>
                  </div>
                </div>
                <div className="label-badge" style={{ backgroundColor: color }}>
                  {label.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StatisticsCounter;