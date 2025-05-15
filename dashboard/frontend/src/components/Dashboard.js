// src/components/Dashboard.js
import React from 'react';
import LogViewer from './LogViewer';
import StatisticsCounter from './StatisticsCounter';
import AnomalyList from './AnomalyList';
import TimeSeriesChart from './TimeSeriesChart';
import { Typography, Container, Paper } from '@mui/material';
import '../styles/Dashboard.css';

const Dashboard = () => {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <Typography variant="h4" component="h1" className="dashboard-title">
          Anomaly Detection Dashboard
        </Typography>
      </div>
      
      <Container maxWidth={false} className="dashboard-container">
        <div className="dashboard-grid">
          <Paper elevation={3} className="grid-item quadrant-1">
            <LogViewer />
          </Paper>
          
          <Paper elevation={3} className="grid-item quadrant-2">
            <StatisticsCounter />
          </Paper>
          
          <Paper elevation={3} className="grid-item quadrant-3">
            <AnomalyList />
          </Paper>
          
          <Paper elevation={3} className="grid-item quadrant-4">
            <TimeSeriesChart />
          </Paper>
        </div>
      </Container>
    </div>
  );
};

export default Dashboard;