/**
 * Error handling and reporting utilities
 * Production-ready error management for CadArena frontend
 */

export class AppError extends Error {
  constructor(message, code = 'UNKNOWN_ERROR', statusCode = 500, details = {}) {
    super(message);
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.timestamp = new Date().toISOString();
    Object.setPrototypeOf(this, AppError.prototype);
  }

  toJSON() {
    return {
      code: this.code,
      message: this.message,
      statusCode: this.statusCode,
      timestamp: this.timestamp,
      details: this.details,
    };
  }
}

/**
 * Error messages for common scenarios
 */
export const ERROR_MESSAGES = {
  // Network errors
  NETWORK_ERROR: 'Unable to connect to the server. Please check your internet connection.',
  TIMEOUT_ERROR: 'Request timed out. The operation took too long. Please try again.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  BAD_REQUEST: 'Invalid request. Please check your input and try again.',
  NOT_FOUND: 'The requested resource was not found.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied.',

  // Validation errors
  VALIDATION_ERROR: 'Please check your input and try again.',
  REQUIRED_FIELD: 'This field is required.',
  INVALID_FORMAT: 'Invalid format. Please check your input.',
  INVALID_EMAIL: 'Please enter a valid email address.',

  // File errors
  FILE_TOO_LARGE: 'File size exceeds the maximum limit.',
  INVALID_FILE_TYPE: 'Invalid file type. Please upload the correct format.',
  FILE_UPLOAD_ERROR: 'Failed to upload file. Please try again.',

  // Generation errors
  GENERATION_FAILED: 'Floor plan generation failed. Please try again.',
  MODEL_NOT_LOADED: 'Model is not loaded. Please wait and try again.',
  INVALID_PROMPT: 'Invalid prompt. Please provide a valid floor plan description.',

  // Project errors
  PROJECT_NOT_FOUND: 'Project not found.',
  PROJECT_CREATION_FAILED: 'Failed to create project. Please try again.',
  PROJECT_DELETION_FAILED: 'Failed to delete project. Please try again.',
};

/**
 * Detailed error resolution guide
 */
export const ERROR_SOLUTIONS = {
  NETWORK_ERROR: {
    title: 'Network Connection Issue',
    steps: [
      'Check your internet connection',
      'Try refreshing the page',
      'Verify the backend server is running (port 8000)',
      'Check your firewall settings',
    ],
    contactSupport: true,
  },
  TIMEOUT_ERROR: {
    title: 'Operation Timeout',
    steps: [
      'Check your internet speed',
      'Try a simpler operation first',
      'Reduce input complexity',
      'Increase timeout setting if possible',
    ],
    contactSupport: false,
  },
  SERVER_ERROR: {
    title: 'Server Error',
    steps: [
      'Wait a few moments and try again',
      'Refresh the page',
      'Check server status',
      'Try a different operation',
    ],
    contactSupport: true,
  },
};

/**
 * Handle API errors and return user-friendly message
 */
export function handleApiError(error) {
  if (error instanceof AppError) {
    return error;
  }

  if (error.response) {
    const { status, data } = error.response;
    let code = 'UNKNOWN_ERROR';
    let message = ERROR_MESSAGES.SERVER_ERROR;
    let details = {};

    switch (status) {
      case 400:
        code = 'BAD_REQUEST';
        message = data?.message || data?.error || ERROR_MESSAGES.BAD_REQUEST;
        details = data?.details || {};
        break;
      case 401:
        code = 'UNAUTHORIZED';
        message = ERROR_MESSAGES.UNAUTHORIZED;
        break;
      case 403:
        code = 'FORBIDDEN';
        message = ERROR_MESSAGES.FORBIDDEN;
        break;
      case 404:
        code = 'NOT_FOUND';
        message = data?.message || ERROR_MESSAGES.NOT_FOUND;
        break;
      case 422:
        code = 'VALIDATION_ERROR';
        message = data?.message || ERROR_MESSAGES.VALIDATION_ERROR;
        details = data?.details || {};
        break;
      case 429:
        code = 'RATE_LIMITED';
        message = 'Too many requests. Please wait a moment and try again.';
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        code = 'SERVER_ERROR';
        message = data?.message || ERROR_MESSAGES.SERVER_ERROR;
        break;
      default:
        message = data?.message || ERROR_MESSAGES.SERVER_ERROR;
    }

    return new AppError(message, code, status, details);
  }

  if (error.code === 'ECONNABORTED') {
    return new AppError(ERROR_MESSAGES.TIMEOUT_ERROR, 'TIMEOUT_ERROR', 408);
  }

  if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
    return new AppError(ERROR_MESSAGES.NETWORK_ERROR, 'NETWORK_ERROR', 503);
  }

  if (error.message?.includes('Unexpected end of JSON')) {
    return new AppError('Invalid response from server. Please try again.', 'INVALID_RESPONSE', 502);
  }

  return new AppError(
    error.message || ERROR_MESSAGES.SERVER_ERROR,
    'UNKNOWN_ERROR',
    500,
    { originalError: error.message }
  );
}

/**
 * Log error with context for debugging
 */
export function logError(error, context = {}) {
  const timestamp = new Date().toISOString();
  const errorInfo = {
    timestamp,
    ...context,
    error: error instanceof AppError ? error.toJSON() : {
      message: error.message,
      stack: error.stack,
      type: error.name,
    },
  };

  if (process.env.NODE_ENV === 'development') {
    console.error('[Error]', errorInfo);
  } else {
    // In production, send to error tracking service (Sentry, etc.)
    // Example: Sentry.captureException(error, { extra: errorInfo });
    console.error('[Error]', errorInfo);
  }

  return errorInfo;
}

/**
 * Validate form data
 */
export function validateForm(data, schema) {
  const errors = {};

  for (const [field, rules] of Object.entries(schema)) {
    const value = data[field];

    for (const rule of rules) {
      const error = rule(value, field);
      if (error) {
        errors[field] = error;
        break;
      }
    }
  }

  return Object.keys(errors).length === 0 ? null : errors;
}

/**
 * Common validation rules
 */
export const ValidationRules = {
  required: (msg = 'This field is required') => (value) => {
    return !value || (typeof value === 'string' && !value.trim()) ? msg : null;
  },

  email: () => (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return value && !emailRegex.test(value) ? ERROR_MESSAGES.INVALID_EMAIL : null;
  },

  minLength: (min, msg) => (value) => {
    return value && value.length < min ? msg || `Minimum ${min} characters required` : null;
  },

  maxLength: (max, msg) => (value) => {
    return value && value.length > max ? msg || `Maximum ${max} characters allowed` : null;
  },

  pattern: (regex, msg = 'Invalid format') => (value) => {
    return value && !regex.test(value) ? msg : null;
  },

  match: (otherValue, msg = 'Values do not match') => (value) => {
    return value !== otherValue ? msg : null;
  },
};

/**
 * Retry logic with exponential backoff
 */
export async function retryWithBackoff(
  fn,
  maxRetries = 3,
  initialDelay = 1000,
  backoffMultiplier = 2
) {
  let lastError;
  let delay = initialDelay;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay *= backoffMultiplier;
      }
    }
  }

  throw lastError;
}

/**
 * Timeout wrapper for promises
 */
export function promiseWithTimeout(promise, timeoutMs, timeoutMessage = 'Operation timed out') {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new AppError(timeoutMessage, 'TIMEOUT_ERROR', 408)), timeoutMs)
    ),
  ]);
}

export default {
  AppError,
  ERROR_MESSAGES,
  ERROR_SOLUTIONS,
  handleApiError,
  logError,
  validateForm,
  ValidationRules,
  retryWithBackoff,
  promiseWithTimeout,
};
