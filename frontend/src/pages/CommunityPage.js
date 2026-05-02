import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, CheckCircle2, Star, MessageCircle, Globe } from 'lucide-react';

const upcomingFeatures = [
  {
    icon: Star,
    title: 'Reputation System',
    description: 'Earn badges and build your professional profile as you contribute.',
  },
  {
    icon: MessageCircle,
    title: 'Q&A Forum',
    description: 'Ask questions and share knowledge with architects and engineers.',
  },
  {
    icon: Globe,
    title: 'Global Community',
    description: 'Connect with designers and engineers from around the world.',
  },
];

export default function CommunityPage() {
  const [email, setEmail] = React.useState('');
  const [subscribed, setSubscribed] = React.useState(false);

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setEmail('');
      setTimeout(() => setSubscribed(false), 4000);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
  };

  return (
    <div className="app-page bg-gradient-to-b from-slate-50 to-white dark:from-[#060912] dark:to-[#060912]">
      <div className="app-shell">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={containerVariants}
          className="flex min-h-[calc(100vh-200px)] flex-col items-center justify-center px-4 py-20"
        >
          <div className="w-full max-w-2xl">
            <motion.div
              variants={itemVariants}
              className="mb-10 flex justify-center"
              aria-hidden="true"
            >
              <div className="relative">
                <div className="absolute -inset-3 rounded-full bg-gradient-to-br from-primary-200/60 to-secondary-200/40 blur-xl" />
                <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-primary-100 to-secondary-50 border border-primary-200/50 shadow-medium">
                  <MessageCircle className="h-12 w-12 text-primary-600" strokeWidth={1.5} />
                </div>
              </div>
            </motion.div>

            <motion.div variants={itemVariants} className="mb-2 text-center">
              <span className="app-pill">
                Under Active Development
              </span>
            </motion.div>

            <motion.h1
              variants={itemVariants}
              className="mt-6 mb-4 text-center text-5xl font-black text-slate-950 dark:text-slate-50 md:text-6xl"
              style={{ letterSpacing: '-0.045em' }}
            >
              Coming Soon
            </motion.h1>

            <motion.p
              variants={itemVariants}
              className="mb-10 text-center text-lg leading-relaxed text-slate-600 dark:text-slate-400"
            >
              We&apos;re building a world-class engineering community platform for architects
              and designers. Be the first to know when we launch.
            </motion.p>

            <motion.form
              variants={itemVariants}
              onSubmit={handleSubscribe}
              className="mb-6 flex flex-col gap-3 sm:flex-row sm:justify-center"
              aria-label="Email notification signup"
            >
              <label htmlFor="notify-email" className="sr-only">Email address</label>
              <input
                id="notify-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                className="app-input flex-1 sm:max-w-xs"
                required
                autoComplete="email"
              />
              <button
                type="submit"
                className="app-button-primary whitespace-nowrap"
              >
                <Mail className="h-4 w-4" aria-hidden="true" />
                Notify Me
              </button>
            </motion.form>

            <AnimatePresence>
              {subscribed && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9, y: -8 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9, y: -4 }}
                  transition={{ duration: 0.2 }}
                  className="mb-10 flex items-center justify-center gap-2 rounded-full border border-green-200 bg-green-50 px-6 py-3 text-green-700 dark:border-green-900/40 dark:bg-green-950/30 dark:text-green-400"
                  role="status"
                  aria-live="polite"
                >
                  <CheckCircle2 className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                  <span className="font-semibold">You&apos;re on the list! We&apos;ll notify you when we launch.</span>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="mt-10 grid gap-5 sm:grid-cols-3"
            >
              {upcomingFeatures.map((feature) => {
                const Icon = feature.icon;
                return (
                  <motion.div
                    key={feature.title}
                    variants={itemVariants}
                    whileHover={{ y: -6, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } }}
                    className="app-card app-card-hover p-6 text-center"
                  >
                    <div className="app-icon-badge mx-auto mb-4" aria-hidden="true">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="mb-2 text-base font-bold text-slate-950 dark:text-slate-100">{feature.title}</h3>
                    <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400">{feature.description}</p>
                  </motion.div>
                );
              })}
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
