import React from 'react';
import { motion } from 'framer-motion';

/**
 * LoadingSkeleton Component - Placeholder while loading
 * @param {string} variant - Skeleton variant: 'text', 'card', 'avatar', 'custom'
 * @param {number} count - Number of skeleton items
 * @param {string} className - Additional classes
 */
export default function LoadingSkeleton({
  variant = 'text',
  count = 1,
  className = '',
  ...props
}) {
  const skeletonVariants = {
    hidden: { opacity: 0.6 },
    visible: { opacity: 1 },
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0.6 },
    visible: {
      opacity: 1,
      transition: {
        duration: 1.5,
        repeat: Infinity,
        repeatType: 'reverse',
      },
    },
  };

  const renderSkeleton = () => {
    switch (variant) {
      case 'text':
        return (
          <motion.div
            className="space-y-3"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {Array.from({ length: count }).map((_, i) => (
              <motion.div
                key={i}
                className="h-4 rounded-lg bg-slate-200"
                variants={itemVariants}
              />
            ))}
          </motion.div>
        );

      case 'card':
        return (
          <motion.div
            className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div className="h-6 rounded-lg bg-slate-200" variants={itemVariants} />
            <motion.div className="space-y-2" variants={containerVariants}>
              {Array.from({ length: 3 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="h-4 rounded-lg bg-slate-200"
                  variants={itemVariants}
                />
              ))}
            </Motion.div>
          </motion.div>
        );

      case 'avatar':
        return (
          <motion.div
            className="flex items-center gap-4"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div
              className="h-12 w-12 rounded-full bg-slate-200"
              variants={itemVariants}
            />
            <motion.div className="flex-1 space-y-2" variants={containerVariants}>
              <motion.div className="h-4 rounded-lg bg-slate-200" variants={itemVariants} />
              <Motion.div className="h-3 w-3/4 rounded-lg bg-slate-200" variants={itemVariants} />
            </motion.div>
          </motion.div>
        );

      default:
        return (
          <motion.div
            className={`h-12 rounded-lg bg-slate-200 ${className}`}
            variants={itemVariants}
            initial="hidden"
            animate="visible"
          />
        );
    }
  };

  return renderSkeleton();
}
