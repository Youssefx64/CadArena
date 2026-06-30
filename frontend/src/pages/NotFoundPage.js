import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Compass, ArrowRight } from '../components/IconRegistry';

export default function NotFoundPage() {
  useEffect(() => {
    document.title = 'Page Not Found — CadArena';
  }, []);

  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-6 py-12 text-center relative overflow-hidden">
      {/* Background design grids */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-40 dark:opacity-20" style={{ backgroundImage: 'linear-gradient(var(--line-soft) 1px,transparent 1px),linear-gradient(90deg,var(--line-soft) 1px,transparent 1px)', backgroundSize: '32px 32px' }} />
      
      <div className="relative z-10 max-w-md space-y-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto w-16 h-16 rounded-full bg-primary-50 dark:bg-violet-950/30 flex items-center justify-center border border-primary-200/50 dark:border-violet-900/30 text-primary-600 dark:text-violet-400 mb-2"
        >
          <Compass className="w-8 h-8" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.45 }}
          className="space-y-2"
        >
          <span className="text-xs font-black uppercase tracking-widest text-primary-600 dark:text-violet-400">Error 404</span>
          <h1 className="text-3xl font-black text-slate-900 dark:text-slate-50 tracking-tight">
            Page not found
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            The coordinate path you requested does not exist in the layout database. It may have been moved, renamed, or deleted.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.45 }}
          className="flex flex-col sm:flex-row gap-3 justify-center pt-2"
        >
          <Link to="/" className="app-button-primary app-button-compact">
            Return Home
          </Link>
          <Link to="/docs" className="app-button-secondary app-button-compact flex items-center justify-center gap-1.5">
            <span>Read Docs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
