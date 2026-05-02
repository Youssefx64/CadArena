import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Construction } from 'lucide-react';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.08 } } };
const fadeUp  = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.48, ease: [0.22, 1, 0.36, 1] } } };

function ComingSoon({
  icon: Icon = Construction,
  title,
  subtitle,
  features = [],
  ctaLabel  = 'Open Studio',
  ctaTo     = '/studio',
  secondaryLabel,
  secondaryTo,
}) {
  return (
    <div className="app-page">
      <div className="app-shell flex min-h-[68vh] items-center justify-center py-20">
        <motion.div
          className="w-full max-w-2xl text-center"
          initial="hidden"
          animate="visible"
          variants={stagger}
        >
          {/* Status badge */}
          <motion.div variants={fadeUp} className="mb-8 inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 dark:border-violet-800/40 dark:bg-violet-950/30 dark:text-violet-300">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            In Development
          </motion.div>

          {/* Icon */}
          <motion.div variants={fadeUp} className="app-icon-badge-lg mx-auto mb-8" aria-hidden="true">
            <Icon className="h-8 w-8" />
          </motion.div>

          {/* Heading */}
          <motion.h1 variants={fadeUp} className="app-section-title mb-4">
            {title}
          </motion.h1>
          <motion.p variants={fadeUp} className="app-section-copy mx-auto mb-10 max-w-xl">
            {subtitle}
          </motion.p>

          {/* What's coming */}
          {features.length > 0 && (
            <motion.div variants={fadeUp} className="app-card mb-10 p-8 text-left">
              <p className="mb-5 text-xs font-bold uppercase tracking-widest text-slate-400">
                What&apos;s coming
              </p>
              <ul className="space-y-3">
                {features.map((f) => (
                  <li key={f} className="flex items-start gap-3">
                    <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-primary-500" aria-hidden="true" />
                    <span className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">{f}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* CTAs */}
          <motion.div variants={fadeUp} className="flex flex-wrap items-center justify-center gap-3">
            <Link to={ctaTo} className="app-button-primary">
              {ctaLabel}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            {secondaryLabel && secondaryTo && (
              <Link to={secondaryTo} className="app-button-secondary">
                {secondaryLabel}
              </Link>
            )}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default ComingSoon;
