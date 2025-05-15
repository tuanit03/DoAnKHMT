// src/utils/formatters.js
import { format, formatDistance, parseISO } from 'date-fns';

/**
 * Formats a timestamp as a time string (HH:MM:SS)
 * @param {string|number|Date} timestamp - Timestamp to format
 * @returns {string} Formatted time
 */
export const formatTime = (timestamp) => {
  if (!timestamp) return '';
  try {
    const date = typeof timestamp === 'string' ? parseISO(timestamp) : new Date(timestamp);
    return format(date, 'HH:mm:ss');
  } catch (error) {
    console.error('Error formatting time:', error);
    return '';
  }
};

/**
 * Formats a timestamp as a date and time string (YYYY-MM-DD HH:MM:SS)
 * @param {string|number|Date} timestamp - Timestamp to format
 * @returns {string} Formatted date and time
 */
export const formatDateTime = (timestamp) => {
  if (!timestamp) return '';
  try {
    const date = typeof timestamp === 'string' ? parseISO(timestamp) : new Date(timestamp);
    return format(date, 'yyyy-MM-dd HH:mm:ss');
  } catch (error) {
    console.error('Error formatting date time:', error);
    return '';
  }
};

/**
 * Formats a timestamp as relative time (e.g., "5 minutes ago")
 * @param {string|number|Date} timestamp - Timestamp to format
 * @returns {string} Formatted relative time
 */
export const formatRelativeTime = (timestamp) => {
  if (!timestamp) return '';
  try {
    const date = typeof timestamp === 'string' ? parseISO(timestamp) : new Date(timestamp);
    return formatDistance(date, new Date(), { addSuffix: true });
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return '';
  }
};

/**
 * Formats a number with commas as thousands separators
 * @param {number} number - Number to format
 * @returns {string} Formatted number
 */
export const formatNumber = (number) => {
  if (number === undefined || number === null) return '';
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
};

/**
 * Formats a percentage value with a specified number of decimal places
 * @param {number} value - Value to format as percentage
 * @param {number} [decimalPlaces=1] - Number of decimal places
 * @returns {string} Formatted percentage
 */
export const formatPercentage = (value, decimalPlaces = 1) => {
  if (value === undefined || value === null) return '';
  return `${parseFloat(value).toFixed(decimalPlaces)}%`;
};

/**
 * Truncates a string if it exceeds a certain length
 * @param {string} str - String to truncate
 * @param {number} [maxLength=100] - Maximum length
 * @returns {string} Truncated string
 */
export const truncateString = (str, maxLength = 100) => {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return `${str.substring(0, maxLength)}...`;
};