import {
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
} from './validation';

describe('Validation Utilities', () => {
  describe('validateEmail', () => {
    it('validates correct email', () => {
      expect(validateEmail('test@example.com')).toBe(true);
    });

    it('rejects invalid email', () => {
      expect(validateEmail('invalid-email')).toBe(false);
      expect(validateEmail('test@')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('validates strong password', () => {
      const result = validatePassword('SecurePass123!');
      expect(result.isValid).toBe(true);
      expect(result.strength).toBeGreaterThan(3);
    });

    it('rejects weak password', () => {
      const result = validatePassword('weak');
      expect(result.isValid).toBe(false);
    });

    it('checks password requirements', () => {
      const result = validatePassword('SecurePass123');
      expect(result.requirements.minLength).toBe(true);
      expect(result.requirements.hasUpperCase).toBe(true);
      expect(result.requirements.hasLowerCase).toBe(true);
      expect(result.requirements.hasNumbers).toBe(true);
    });
  });

  describe('validateURL', () => {
    it('validates correct URL', () => {
      expect(validateURL('https://example.com')).toBe(true);
      expect(validateURL('http://example.com')).toBe(true);
    });

    it('rejects invalid URL', () => {
      expect(validateURL('not a url')).toBe(false);
    });
  });

  describe('validatePhoneNumber', () => {
    it('validates correct phone number', () => {
      expect(validatePhoneNumber('123-456-7890')).toBe(true);
      expect(validatePhoneNumber('(123) 456-7890')).toBe(true);
    });

    it('rejects invalid phone number', () => {
      expect(validatePhoneNumber('123')).toBe(false);
    });
  });

  describe('validateRequired', () => {
    it('validates non-empty string', () => {
      expect(validateRequired('text')).toBe(true);
    });

    it('rejects empty string', () => {
      expect(validateRequired('')).toBe(false);
      expect(validateRequired('   ')).toBe(false);
    });

    it('rejects null and undefined', () => {
      expect(validateRequired(null)).toBe(false);
      expect(validateRequired(undefined)).toBe(false);
    });
  });

  describe('validateMinLength', () => {
    it('validates string with sufficient length', () => {
      expect(validateMinLength('hello', 3)).toBe(true);
    });

    it('rejects string with insufficient length', () => {
      expect(validateMinLength('hi', 3)).toBe(false);
    });
  });

  describe('validateMaxLength', () => {
    it('validates string within max length', () => {
      expect(validateMaxLength('hello', 10)).toBe(true);
    });

    it('rejects string exceeding max length', () => {
      expect(validateMaxLength('hello world', 5)).toBe(false);
    });
  });

  describe('validateRange', () => {
    it('validates number within range', () => {
      expect(validateRange('5', 1, 10)).toBe(true);
    });

    it('rejects number outside range', () => {
      expect(validateRange('15', 1, 10)).toBe(false);
    });
  });

  describe('validateFileSize', () => {
    it('validates file within size limit', () => {
      const file = new File(['content'], 'test.txt', { type: 'text/plain' });
      expect(validateFileSize(file, 1)).toBe(true);
    });
  });

  describe('validateFileType', () => {
    it('validates correct file type', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
      expect(validateFileType(file, ['image/jpeg', 'image/png'])).toBe(true);
    });

    it('rejects incorrect file type', () => {
      const file = new File(['content'], 'test.txt', { type: 'text/plain' });
      expect(validateFileType(file, ['image/jpeg', 'image/png'])).toBe(false);
    });
  });

  describe('validateCreditCard', () => {
    it('validates correct credit card number', () => {
      // Valid test credit card number
      expect(validateCreditCard('4532015112830366')).toBe(true);
    });

    it('rejects invalid credit card number', () => {
      expect(validateCreditCard('1234567890123456')).toBe(false);
    });
  });

  describe('validateDate', () => {
    it('validates correct date', () => {
      expect(validateDate('2024-01-01')).toBe(true);
    });

    it('rejects invalid date', () => {
      expect(validateDate('invalid-date')).toBe(false);
    });
  });

  describe('validateForm', () => {
    it('validates form with all valid data', () => {
      const formData = {
        email: 'test@example.com',
        password: 'SecurePass123',
      };

      const rules = {
        email: { required: true, email: true },
        password: { required: true, minLength: 8 },
      };

      const result = validateForm(formData, rules);
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    it('validates form with errors', () => {
      const formData = {
        email: 'invalid-email',
        password: 'weak',
      };

      const rules = {
        email: { required: true, email: true },
        password: { required: true, minLength: 8 },
      };

      const result = validateForm(formData, rules);
      expect(result.isValid).toBe(false);
      expect(Object.keys(result.errors).length).toBeGreaterThan(0);
    });
  });
});
