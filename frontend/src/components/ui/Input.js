import React, { forwardRef } from 'react';
import { AlertCircle } from 'lucide-react';

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
          <label className="mb-2 block text-sm font-semibold text-slate-950 dark:text-slate-100">
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
          className={`w-full rounded-lg border px-4 py-2.5 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-55 ${
            hasError
              ? 'border-red-300 bg-red-50 text-red-900 placeholder-red-300 dark:border-red-700/60 dark:bg-red-950/30 dark:text-red-300 dark:placeholder-red-600'
              : 'border-slate-300 bg-white text-slate-950 placeholder-slate-400 hover:border-slate-400 dark:border-white/10 dark:bg-zinc-900 dark:text-slate-100 dark:placeholder-slate-500 dark:hover:border-white/20 dark:focus:ring-violet-500'
          } ${className}`}
          {...props}
        />

        {error && (
          <div id={`${label}-error`} className="mt-1 flex items-center gap-1 text-sm text-red-600 dark:text-red-400">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {hint && !error && (
          <p id={`${label}-hint`} className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
