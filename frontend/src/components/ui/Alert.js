import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Alert Component - Reusable alert/notification
 * @param {string} type - Alert type: 'success', 'error', 'warning', 'info'
 * @param {string} title - Alert title
 * @param {string} message - Alert message
 * @param {boolean} dismissible - Show close button
 * @param {function} onDismiss - Callback when dismissed
 */
export default function Alert({
  type = 'info',
  title,
  message,
  dismissible = true,
  onDismiss,
  className = '',
}) {
  const [isVisible, setIsVisible] = React.useState(true);

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  const typeConfig = {
    success: {
      icon: CheckCircle2,
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-900',
      titleColor: 'text-green-950',
      iconColor: 'text-green-600',
    },
    error: {
      icon: AlertCircle,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-900',
      titleColor: 'text-red-950',
      iconColor: 'text-red-600',
    },
    warning: {
      icon: AlertTriangle,
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-900',
      titleColor: 'text-yellow-950',
      iconColor: 'text-yellow-600',
    },
    info: {
      icon: Info,
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-900',
      titleColor: 'text-blue-950',
      iconColor: 'text-blue-600',
    },
  };

  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className={`rounded-lg border ${config.bgColor} ${config.borderColor} p-4 ${className}`}
          role="alert"
          aria-live="polite"
        >
          <div className="flex gap-3">
            <Icon className={`h-5 w-5 flex-shrink-0 ${config.iconColor}`} />
            <div className="flex-1">
              {title && <h3 className={`font-semibold ${config.titleColor}`}>{title}</h3>}
              {message && <p className={`text-sm ${config.textColor}`}>{message}</p>}
            </div>
            {dismissible && (
              <button
                onClick={handleDismiss}
                className={`flex-shrink-0 rounded p-1 transition-colors hover:bg-white/50 ${config.textColor}`}
                aria-label="Dismiss alert"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
