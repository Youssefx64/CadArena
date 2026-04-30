import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Mail, CheckCircle2 } from 'lucide-react';

export default function CommunityPage() {
  const [email, setEmail] = React.useState('');
  const [subscribed, setSubscribed] = React.useState(false);

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
      setEmail('');
      setTimeout(() => setSubscribed(false), 3000);
    }
  };

  return (
    <div className="app-page bg-gradient-to-b from-slate-50 to-white">
      <div className="app-shell">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="flex min-h-[calc(100vh-200px)] flex-col items-center justify-center px-4 py-20"
        >
          {/* Main Content Container */}
          <div className="w-full max-w-2xl">
            {/* Icon */}
            <motion.div
              animate={{ y: [0, -12, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="mb-12 flex justify-center"
            >
              <div className="rounded-full bg-gradient-to-br from-primary-100 to-primary-50 p-8">
                <Zap className="h-16 w-16 text-primary-600" strokeWidth={1.5} />
              </div>
            </motion.div>

            {/* Title */}
            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              className="mb-4 text-center text-5xl font-black text-slate-950 md:text-6xl"
            >
              Coming Soon
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
              className="mb-12 text-center text-lg text-slate-600"
            >
              We're building an amazing engineering community platform.
              <br />
              Get notified when we launch!
            </motion.p>

            {/* Email Subscription */}
            <motion.form
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
              onSubmit={handleSubscribe}
              className="mb-16 flex flex-col gap-3 sm:flex-row sm:justify-center"
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="app-input flex-1 sm:max-w-xs"
                required
              />
              <button
                type="submit"
                className="app-button-primary whitespace-nowrap"
              >
                <Mail className="h-4 w-4" />
                Notify Me
              </button>
            </motion.form>

            {/* Success Message */}
            {subscribed && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="mb-16 flex items-center justify-center gap-2 rounded-full border border-green-200 bg-green-50 px-6 py-3 text-green-700"
              >
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-semibold">Thanks! We'll notify you when we launch.</span>
              </motion.div>
            )}

            {/* Features Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              className="grid gap-6 sm:grid-cols-3"
            >
              {/* Feature 1 - Reputation */}
              <motion.div
                whileHover={{ y: -8, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}
                className="group rounded-2xl border border-slate-200 bg-white p-8 text-center transition-all duration-300"
              >
                <div className="mb-4 flex justify-center">
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/1995/1995467.png"
                    alt="Reputation"
                    className="h-16 w-16 object-contain"
                  />
                </div>
                <h3 className="mb-2 text-lg font-bold text-slate-950">Reputation System</h3>
                <p className="text-sm text-slate-600">Earn badges and build your professional profile</p>
              </motion.div>

              {/* Feature 2 - Q&A */}
              <motion.div
                whileHover={{ y: -8, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}
                className="group rounded-2xl border border-slate-200 bg-white p-8 text-center transition-all duration-300"
              >
                <div className="mb-4 flex justify-center">
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/3556/3556098.png"
                    alt="Q&A Forum"
                    className="h-16 w-16 object-contain"
                  />
                </div>
                <h3 className="mb-2 text-lg font-bold text-slate-950">Q&A Forum</h3>
                <p className="text-sm text-slate-600">Ask questions and share knowledge with experts</p>
              </motion.div>

              {/* Feature 3 - Global Community */}
              <motion.div
                whileHover={{ y: -8, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}
                className="group rounded-2xl border border-slate-200 bg-white p-8 text-center transition-all duration-300"
              >
                <div className="mb-4 flex justify-center">
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/747/747376.png"
                    alt="Global Community"
                    className="h-16 w-16 object-contain"
                  />
                </div>
                <h3 className="mb-2 text-lg font-bold text-slate-950">Global Community</h3>
                <p className="text-sm text-slate-600">Connect with engineers worldwide</p>
              </motion.div>
            </motion.div>

            {/* Bottom Text */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.6 }}
              className="mt-16 text-center"
            >
              <div className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-4 py-2 text-sm font-semibold text-primary-700">
                <span className="h-2 w-2 rounded-full bg-primary-600 animate-pulse" />
                Under Development
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
