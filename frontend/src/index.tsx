/**
 * Main entry point for the AI Chatbot React application
 * 
 * This file initializes the React application with proper error handling
 * and performance monitoring. It sets up the root component and configures
 * development tools for debugging and analytics.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Get the root element from the HTML
const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Failed to find the root element. Make sure you have <div id="root"></div> in your HTML.');
}

// Create the React root and render the application
const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Performance monitoring - logs performance metrics in development
// In production, you might want to send these to an analytics service
if (process.env.NODE_ENV === 'development') {
  reportWebVitals(console.log);
} else {
  // In production, you could send metrics to an analytics endpoint
  reportWebVitals();
}
