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

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {error: any}> {
  constructor(props: any) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error: any) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 20, color: 'red', fontFamily: 'monospace', backgroundColor: 'white', minHeight: '100vh' }}>
          <h1>Runtime Crash!</h1>
          <pre>{this.state.error.toString()}</pre>
          <pre>{this.state.error.stack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
