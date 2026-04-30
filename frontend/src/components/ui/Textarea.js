import React, { forwardRef } from 'react';
import { AlertCircle } from 'lucide-react';

/**
 * Textarea Component - Reusable form textarea
 * @param {string} label - Textarea label
 * @param {string} error - Error message
 * @param {string} hint - Helper text
 * @param {boolean} required - Mark as required
 * @param {number} rows - Number of rows
 * @param {string} placeholder - Placeholder text
 * @param {string} value - Textarea value
 * @param {function} onChange - Change handler
 * @param {boolean} disabled - Disable textarea
 * @param {number} maxLength - Max character length
 */
const Textarea = forwardRef(
  (
    {
      label,
      error,
      hint,
      required = false,
      rows = 4,
      placeholder,
      value,
      onChange,
      disabled = false,
      maxLength,
      className = '',
      ...props
    },
    ref
  ) => {
    const hasError = !!error;
    const charCount = value?.length || 0;

    return (
      <div className="w-full">
        {label && (
          <label className="mb-2 block text-sm font-semibold text-slate-950">
            {label}
            {required && <span className="ml-1 text-red-500">*</span>}
          </label>
        )}

        <textarea
          ref={ref}
          rows={rows}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          maxLength={maxLength}
          aria-invalid={hasError}
          aria-describedby={error ? `${label}-error` : hint ? `${label}-hint` : undefined}
          className={`w-full rounded-lg border px-4 py-2.5 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100 disabled:text-slate-500 resize-none ${
            hasError
              ? 'border-red-300 bg-red-50 text-red-900 placeholder-red-300'
              : 'border-slate-300 bg-white text-slate-950 placeholder-slate-400 hover:border-slate-400'
          } ${className}`}
          {...props}
        />

        <div className="mt-1 flex items-center justify-between">
          <div>
            {error && (
              <div id={`${label}-error`} className="flex items-center gap-1 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}

            {hint && !error && (
              <p id={`${label}-hint`} className="text-sm text-slate-500">
                {hint}
              </p>
            )}
          </div>

          {maxLength && (
            <span className={`text-xs ${charCount > maxLength * 0.9 ? 'text-orange-600' : 'text-slate-500'}`}>
              {charCount}/{maxLength}
            </span>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export default Textarea;
