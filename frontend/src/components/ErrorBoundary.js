import React from 'react';

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
              An unexpected error has occurred. Our engineers have been notified.
            </p>
            <div className="rounded-lg bg-red-50 p-4 text-left font-mono text-xs text-red-800 dark:bg-red-900/30 dark:text-red-400">
              {this.state.error?.toString()}
            </div>
            <button
              onClick={() => window.location.reload()}
              className="app-button-primary w-full"
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
