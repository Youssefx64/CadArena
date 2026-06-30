/* eslint-disable no-console */
import React from 'react';
import PropTypes from 'prop-types';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error('Enterprise Error Capture:', error, errorInfo);
    // In a real enterprise app, we would send this to Sentry or a backend sink.
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6 text-center dark:bg-slate-900">
          <div className="max-w-md space-y-4">
            <h1 className="text-4xl font-black text-slate-900 dark:text-slate-50">Something went wrong</h1>
            <p className="text-slate-600 dark:text-slate-400">
              An unexpected application error has occurred. Please reload the page or return to the dashboard.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={() => window.location.reload()}
                className="app-button-primary flex-1"
              >
                Reload Page
              </button>
              <button
                onClick={() => {
                  this.setState({ hasError: false, error: null, errorInfo: null });
                  window.location.href = '/';
                }}
                className="app-button-secondary flex-1"
              >
                Go to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node,
};

export default ErrorBoundary;
