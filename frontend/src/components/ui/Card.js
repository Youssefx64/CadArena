import React from 'react';
import { motion } from 'framer-motion';

/**
 * Card Component - Reusable card container
 * @param {React.ReactNode} children - Card content
 * @param {string} variant - Card variant: 'default', 'hover', 'elevated'
 * @param {boolean} interactive - Add hover effects
 * @param {string} className - Additional classes
 */
export default function Card({
  children,
  variant = 'default',
  interactive = false,
  className = '',
  ...props
}) {
  const variantClasses = {
    default: 'border border-slate-200 bg-white',
    hover: 'border border-slate-200 bg-white hover:border-primary-300 hover:shadow-md',
    elevated: 'border border-slate-200 bg-white shadow-lg',
  };

  const Component = interactive ? motion.div : 'div';
  const motionProps = interactive
    ? {
        whileHover: { y: -4, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' },
        transition: { duration: 0.2 },
      }
    : {};

  return (
    <Component
      className={`rounded-2xl p-6 transition-all ${variantClasses[variant]} ${className}`}
      {...motionProps}
      {...props}
    >
      {children}
    </Component>
  );
}
