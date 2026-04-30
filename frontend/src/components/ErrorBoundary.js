import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

/**
 * Error Boundary - Catches React errors and displays fallback UI
 * Logs errors to console and can be extended to send to error tracking service
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('Error caught by boundary:', error);
    console.error('Error info:', errorInfo);

    // Update state with error details
    this.setState((prevState) => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // TODO: Send error to error tracking service (Sentry, LogRocket, etc.)
    // Example: Sentry.captureException(error, { contexts: { react: errorInfo } });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4"
        >
          <div className="max-w-md rounded-2xl border border-red-200 bg-white p-8 shadow-lg">
            {/* Icon */}
            <div className="mb-4 flex justify-center">
              <div className="rounded-full bg-red-100 p-4">
                <AlertCircle className="h-8 w-8 text-red-600" />
              </div>
            </div>

            {/* Title */}
            <h1 className="mb-2 text-center text-2xl font-bold text-slate-950">
              Oops! Something went wrong
            </h1>

            {/* Message */}
            <p className="mb-6 text-center text-slate-600">
              We encountered an unexpected error. Please try refreshing the page or contact support if the problem persists.
            </p>

            {/* Error Details (Development only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-6 rounded-lg bg-slate-50 p-4">
                <summary className="cursor-pointer font-semibold text-slate-950">
                  Error Details
                </summary>
                <pre className="mt-2 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                  {this.state.error.toString()}
                  {'\n\n'}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={this.handleReset}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 font-semibold text-white transition-colors hover:bg-primary-700"
              >
                <RefreshCw className="h-4 w-4" />
                Try Again
              </button>
              <button
                onClick={() => (window.location.href = '/')}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-slate-200 px-4 py-2.5 font-semibold text-slate-950 transition-colors hover:bg-slate-300"
              >
                Go Home
              </button>
            </div>

            {/* Error Count */}
            {this.state.errorCount > 2 && (
              <p className="mt-4 text-center text-sm text-orange-600">
                Multiple errors detected. Please refresh the page.
              </p>
            )}
          </div>
        </motion.div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
