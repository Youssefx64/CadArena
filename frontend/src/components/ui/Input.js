import React, { forwardRef } from 'react';
import { AlertCircle } from 'lucide-react';

/**
 * Input Component - Reusable form input
 * @param {string} label - Input label
 * @param {string} error - Error message
 * @param {string} hint - Helper text
 * @param {boolean} required - Mark as required
 * @param {string} type - Input type
 * @param {string} placeholder - Placeholder text
 * @param {string} value - Input value
 * @param {function} onChange - Change handler
 * @param {boolean} disabled - Disable input
 */
const Input = forwardRef(
  (
    {
      label,
      error,
      hint,
      required = false,
      type = 'text',
      placeholder,
      value,
      onChange,
      disabled = false,
      className = '',
      ...props
    },
    ref
  ) => {
    const hasError = !!error;

    return (
      <div className="w-full">
        {label && (
          <label className="mb-2 block text-sm font-semibold text-slate-950">
            {label}
            {required && <span className="ml-1 text-red-500">*</span>}
          </label>
        )}

        <input
          ref={ref}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          aria-invalid={hasError}
          aria-describedby={error ? `${label}-error` : hint ? `${label}-hint` : undefined}
          className={`w-full rounded-lg border px-4 py-2.5 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100 disabled:text-slate-500 ${
            hasError
              ? 'border-red-300 bg-red-50 text-red-900 placeholder-red-300'
              : 'border-slate-300 bg-white text-slate-950 placeholder-slate-400 hover:border-slate-400'
          } ${className}`}
          {...props}
        />

        {error && (
          <div id={`${label}-error`} className="mt-1 flex items-center gap-1 text-sm text-red-600">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {hint && !error && (
          <p id={`${label}-hint`} className="mt-1 text-sm text-slate-500">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
