// src/components/LogViewer.js
import React, { useState, useEffect, useRef } from 'react';
import { connectToSSE } from '../services/eventSource';
import { Chip, Tooltip, Box, IconButton } from '@mui/material';
import FilterAltIcon from '@mui/icons-material/FilterAlt';
import COLORS from '../utils/colors';
import '../styles/LogViewer.css';

const LogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('');
  const [connectionError, setConnectionError] = useState(false);
  const logContainerRef = useRef(null);
  
  useEffect(() => {
    const handleError = (error) => {
      console.error('LogViewer SSE error:', error);
      setConnectionError(true);
    };
    
    const eventSource = connectToSSE('/api/logs/stream', handleError);
    
    if (eventSource) {
      // Handle main log events
      eventSource.addEventListener('log', (event) => {
        try {
          if (!event.data) {
            console.warn('Received empty data in log event');
            return;
          }
          
          const logData = JSON.parse(event.data);
          
          // Add the new log to the state
          setLogs(prevLogs => {
            // Keep only the latest 100 logs to prevent performance issues
            const newLogs = [...prevLogs, logData].slice(-100);
            return newLogs;
          });
        } catch (error) {
          console.error('Error parsing log event data:', error);
        }
      });
      
      // Handle keepalive ping events
      eventSource.addEventListener('ping', (event) => {
        try {
          const pingData = JSON.parse(event.data);
          setConnectionError(false); // Connection is working
          console.log('Received ping:', pingData);
        } catch (error) {
          console.error('Error parsing ping data:', error);
        }
      });
      
      // Cleanup on unmount
      return () => {
        console.log('Closing LogViewer SSE connection');
        eventSource.close();
      };
    }
  }, []);
  
  // Auto-scroll to the bottom when new logs arrive
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);
  
  // Handle filter change
  const handleFilterChange = (e) => {
    setFilter(e.target.value);
  };
  
  // Parse and format HDFS log messages
  const parseHdfsLog = (logMessage) => {
    try {
      // Expected format: "YYMMDD HHMMSS [Thread ID] INFO [HDFS Component]: [Detailed message containing block ID]"
      const match = logMessage.match(/^(\d{6}) (\d{6}) \[(\d+)\] (\w+) \[([^\]]+)\]: (.+)$/);
      
      if (!match) {
        return {
          dateTime: '',
          threadId: '',
          logLevel: '',
          component: '',
          message: logMessage // Return the original message if parsing fails
        };
      }
      
      const [_, date, time, threadId, logLevel, component, message] = match;
      
      // Highlight block IDs in the message
      const highlightedMessage = message.replace(/(blk_[-]?\d{10,19})/g, '<span class="block-id">$1</span>');
      
      return {
        dateTime: `${date} ${time}`,
        threadId,
        logLevel,
        component,
        message: highlightedMessage
      };
    } catch (error) {
      console.error('Error parsing HDFS log:', error);
      return {
        dateTime: '',
        threadId: '',
        logLevel: '',
        component: '',
        message: logMessage // Return the original message if parsing fails
      };
    }
  };
  
  // Get color for log level
  const getLogLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'error': return COLORS.ERROR;
      case 'warn': return COLORS.WARNING;
      case 'info': return COLORS.INFO;
      case 'debug': return COLORS.DEBUG;
      case 'trace': return COLORS.TRACE;
      default: return COLORS.DEFAULT;
    }
  };
  
  return (
    <div className="log-viewer">
      <div 
        ref={logContainerRef}
        className="logs-container"
      >
        {connectionError && (
          <div className="connection-error">
            Connection error. Trying to reconnect...
          </div>
        )}
        
        {logs.length === 0 && !connectionError && (
          <div className="no-logs">
            Waiting for logs...
          </div>
        )}
        
        {logs.filter(log => {
          if (!filter) return true;
          return JSON.stringify(log).toLowerCase().includes(filter.toLowerCase());
        }).map((log, index) => {
          const parsedLog = parseHdfsLog(log.message);
          return (
            <div key={`${log.timestamp}-${index}`} className="log-entry">
              <Tooltip title={new Date(log.timestamp).toLocaleString()}>
                <div className="log-timestamp">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </div>
              </Tooltip>
              <Chip
                label={log.log_level}
                size="small"
                className="log-level"
                sx={{ 
                  backgroundColor: getLogLevelColor(log.log_level) + '20',
                  color: getLogLevelColor(log.log_level),
                  fontWeight: 'bold'
                }}
              />
              <div 
                className="log-message"
              >
                <span className="log-component">[{parsedLog.component}]:</span>
                <span dangerouslySetInnerHTML={{ __html: parsedLog.message }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default LogViewer;