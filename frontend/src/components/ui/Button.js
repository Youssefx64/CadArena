import React, { forwardRef } from 'react';
import { motion } from 'framer-motion';

/**
 * Button Component - Reusable button
 * @param {string} variant - Button variant: 'primary', 'secondary', 'danger', 'ghost'
 * @param {string} size - Button size: 'sm', 'md', 'lg'
 * @param {boolean} disabled - Disable button
 * @param {boolean} loading - Show loading state
 * @param {React.ReactNode} children - Button content
 * @param {string} className - Additional classes
 */
const Button = forwardRef(
  (
    {
      variant = 'primary',
      size = 'md',
      disabled = false,
      loading = false,
      children,
      className = '',
      ...props
    },
    ref
  ) => {
    const variantClasses = {
      primary: 'bg-primary-600 text-white hover:bg-primary-700 disabled:bg-primary-400',
      secondary: 'bg-slate-200 text-slate-950 hover:bg-slate-300 disabled:bg-slate-100',
      danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-red-400',
      ghost: 'bg-transparent text-primary-600 hover:bg-primary-50 disabled:text-primary-400',
    };

    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2.5 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    return (
      <motion.button
        ref={ref}
        disabled={disabled || loading}
        whileHover={!disabled && !loading ? { scale: 1.02 } : {}}
        whileTap={!disabled && !loading ? { scale: 0.98 } : {}}
        className={`
          rounded-lg font-semibold transition-colors
          ${variantClasses[variant]}
          ${sizeClasses[size]}
          disabled:cursor-not-allowed
          ${className}
        `}
        {...props}
      >
        {loading ? 'Loading...' : children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
