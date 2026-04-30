/**
 * Validation Constants
 */

export const VALIDATION_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL: /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/,
  PHONE: /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/,
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  USERNAME: /^[a-zA-Z0-9_-]{3,16}$/,
  SLUG: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
  HEX_COLOR: /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/,
  CREDIT_CARD: /^[0-9]{13,19}$/,
};

export const VALIDATION_MESSAGES = {
  REQUIRED: 'This field is required',
  INVALID_EMAIL: 'Please enter a valid email address',
  INVALID_URL: 'Please enter a valid URL',
  INVALID_PHONE: 'Please enter a valid phone number',
  INVALID_PASSWORD: 'Password must contain uppercase, lowercase, number, and special character',
  MIN_LENGTH: (min) => `Minimum length is ${min} characters`,
  MAX_LENGTH: (max) => `Maximum length is ${max} characters`,
  INVALID_FILE_SIZE: (max) => `File size must be less than ${max}MB`,
  INVALID_FILE_TYPE: (types) => `File type must be one of: ${types.join(', ')}`,
};

export const FILE_TYPES = {
  IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  DOCUMENT: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  SPREADSHEET: ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
  VIDEO: ['video/mp4', 'video/mpeg', 'video/quicktime'],
};

export const FILE_SIZE_LIMITS = {
  IMAGE: 5, // MB
  DOCUMENT: 10, // MB
  VIDEO: 100, // MB
};

export default {
  VALIDATION_PATTERNS,
  VALIDATION_MESSAGES,
  FILE_TYPES,
  FILE_SIZE_LIMITS,
};
