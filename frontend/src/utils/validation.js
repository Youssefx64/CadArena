/**
 * Validation Utilities
 * Common validation functions for forms and inputs
 */

/**
 * Validate email
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate password strength
 */
export const validatePassword = (password) => {
  const minLength = password.length >= 8;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

  return {
    isValid: minLength && hasUpperCase && hasLowerCase && hasNumbers,
    strength: [minLength, hasUpperCase, hasLowerCase, hasNumbers, hasSpecialChar].filter(Boolean).length,
    requirements: {
      minLength,
      hasUpperCase,
      hasLowerCase,
      hasNumbers,
      hasSpecialChar,
    },
  };
};

/**
 * Validate URL
 */
export const validateURL = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * Validate phone number
 */
export const validatePhoneNumber = (phone) => {
  const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
  return phoneRegex.test(phone.replace(/\s/g, ''));
};

/**
 * Validate required field
 */
export const validateRequired = (value) => {
  if (typeof value === 'string') {
    return value.trim().length > 0;
  }
  return value !== null && value !== undefined;
};

/**
 * Validate min length
 */
export const validateMinLength = (value, minLength) => {
  return value.length >= minLength;
};

/**
 * Validate max length
 */
export const validateMaxLength = (value, maxLength) => {
  return value.length <= maxLength;
};

/**
 * Validate number range
 */
export const validateRange = (value, min, max) => {
  const num = Number(value);
  return num >= min && num <= max;
};

/**
 * Validate file size
 */
export const validateFileSize = (file, maxSizeMB) => {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
};

/**
 * Validate file type
 */
export const validateFileType = (file, allowedTypes) => {
  return allowedTypes.includes(file.type);
};

/**
 * Validate credit card
 */
export const validateCreditCard = (cardNumber) => {
  const sanitized = cardNumber.replace(/\s/g, '');
  if (!/^\d{13,19}$/.test(sanitized)) return false;

  // Luhn algorithm
  let sum = 0;
  let isEven = false;

  for (let i = sanitized.length - 1; i >= 0; i--) {
    let digit = parseInt(sanitized[i], 10);

    if (isEven) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }

    sum += digit;
    isEven = !isEven;
  }

  return sum % 10 === 0;
};

/**
 * Validate date
 */
export const validateDate = (dateString, format = 'YYYY-MM-DD') => {
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date);
};

/**
 * Validate form object
 */
export const validateForm = (formData, rules) => {
  const errors = {};

  Object.keys(rules).forEach((field) => {
    const value = formData[field];
    const fieldRules = rules[field];

    if (fieldRules.required && !validateRequired(value)) {
      errors[field] = `${field} is required`;
    }

    if (fieldRules.email && value && !validateEmail(value)) {
      errors[field] = 'Invalid email address';
    }

    if (fieldRules.minLength && value && !validateMinLength(value, fieldRules.minLength)) {
      errors[field] = `Minimum length is ${fieldRules.minLength}`;
    }

    if (fieldRules.maxLength && value && !validateMaxLength(value, fieldRules.maxLength)) {
      errors[field] = `Maximum length is ${fieldRules.maxLength}`;
    }

    if (fieldRules.pattern && value && !fieldRules.pattern.test(value)) {
      errors[field] = fieldRules.patternMessage || 'Invalid format';
    }

    if (fieldRules.custom && value) {
      const customError = fieldRules.custom(value);
      if (customError) {
        errors[field] = customError;
      }
    }
  });

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
};

export default {
  validateEmail,
  validatePassword,
  validateURL,
  validatePhoneNumber,
  validateRequired,
  validateMinLength,
  validateMaxLength,
  validateRange,
  validateFileSize,
  validateFileType,
  validateCreditCard,
  validateDate,
  validateForm,
};
