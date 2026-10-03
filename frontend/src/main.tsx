import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './index.css';

// Set theme synchronously before React renders to prevent flash
const savedTheme = localStorage.getItem('ui.theme');
if (savedTheme === 'day') {
  document.documentElement.setAttribute('data-theme', 'day');
} else {
  document.documentElement.setAttribute('data-theme', 'night');
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
