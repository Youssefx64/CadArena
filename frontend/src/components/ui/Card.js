import React from 'react';
import { motion } from 'framer-motion';

export default function Card({
  children,
  variant = 'default',
  interactive = false,
  className = '',
  ...props
}) {
  const variantClasses = {
    default:  'border border-slate-200 bg-white dark:border-white/10 dark:bg-zinc-900',
    hover:    'border border-slate-200 bg-white hover:border-primary-300 hover:shadow-md dark:border-white/10 dark:bg-zinc-900 dark:hover:border-violet-700',
    elevated: 'border border-slate-200 bg-white shadow-lg dark:border-white/10 dark:bg-zinc-900',
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
