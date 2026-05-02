import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

function validate(fields) {
  const errs = {};
  if (!fields.email.trim()) errs.email = 'Email is required.';
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email)) errs.email = 'Enter a valid email address.';
  if (!fields.password) errs.password = 'Password is required.';
  return errs;
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  const [fields, setFields]         = useState({ email: '', password: '' });
  const [touched, setTouched]       = useState({});
  const [showPw, setShowPw]         = useState(false);
  const [isSubmitting, setSubmit]   = useState(false);
  const [apiError, setApiError]     = useState('');

  const errors = validate(fields);
  const visErr = Object.fromEntries(Object.entries(errors).filter(([k]) => touched[k]));

  const onChange = (e) => {
    setFields((f) => ({ ...f, [e.target.name]: e.target.value }));
    setApiError('');
  };
  const onBlur = (e) => setTouched((t) => ({ ...t, [e.target.name]: true }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setTouched({ email: true, password: true });
    if (Object.keys(errors).length) return;
    setSubmit(true);
    setApiError('');
    try {
      await login(fields.email.trim(), fields.password);
      navigate(from, { replace: true });
    } catch (err) {
      setApiError(err.message);
    } finally {
      setSubmit(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4.5rem)] items-center justify-center bg-gradient-to-b from-slate-50 to-white px-4 py-12 dark:from-[#060912] dark:to-[#0d1017]">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <div className="app-card app-card-strong p-8 sm:p-10">
          <div className="mb-8 text-center">
            <div className="app-icon-badge-lg mx-auto mb-5">
              <Lock className="h-7 w-7 text-white" aria-hidden="true" />
            </div>
            <h1 className="text-3xl font-black tracking-tight text-slate-950 dark:text-slate-50">Welcome back</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Sign in to your CadArena account</p>
          </div>

          <AnimatePresence>
            {apiError && (
              <motion.div
                initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                animate={{ opacity: 1, height: 'auto', marginBottom: 20 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                className="flex items-start gap-3 overflow-hidden rounded-2xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30"
                role="alert"
                aria-live="polite"
              >
                <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" aria-hidden="true" />
                <p className="text-sm font-semibold text-red-700 dark:text-red-400">{apiError}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={onSubmit} noValidate className="space-y-5">
            <div>
              <label htmlFor="login-email" className="mb-1.5 block text-sm font-semibold text-slate-950 dark:text-slate-100">
                Email address
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  id="login-email"
                  type="email"
                  name="email"
                  value={fields.email}
                  onChange={onChange}
                  onBlur={onBlur}
                  placeholder="you@example.com"
                  autoComplete="email"
                  className={`app-input pl-11${visErr.email ? ' border-red-400 focus:shadow-[0_0_0_4px_rgba(239,68,68,0.12)]' : ''}`}
                  aria-describedby={visErr.email ? 'login-email-err' : undefined}
                  aria-invalid={!!visErr.email}
                  disabled={isSubmitting}
                />
              </div>
              <AnimatePresence>
                {visErr.email && (
                  <motion.p id="login-email-err" initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className="mt-1.5 text-xs font-semibold text-red-600" role="alert">
                    {visErr.email}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label htmlFor="login-password" className="block text-sm font-semibold text-slate-950 dark:text-slate-100">
                  Password
                </label>
              </div>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input
                  id="login-password"
                  type={showPw ? 'text' : 'password'}
                  name="password"
                  value={fields.password}
                  onChange={onChange}
                  onBlur={onBlur}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className={`app-input pl-11 pr-12${visErr.password ? ' border-red-400 focus:shadow-[0_0_0_4px_rgba(239,68,68,0.12)]' : ''}`}
                  aria-describedby={visErr.password ? 'login-pw-err' : undefined}
                  aria-invalid={!!visErr.password}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                  aria-label={showPw ? 'Hide password' : 'Show password'}
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <AnimatePresence>
                {visErr.password && (
                  <motion.p id="login-pw-err" initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    className="mt-1.5 text-xs font-semibold text-red-600" role="alert">
                    {visErr.password}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            <motion.button
              type="submit"
              disabled={isSubmitting}
              whileHover={!isSubmitting ? { scale: 1.01 } : {}}
              whileTap={!isSubmitting ? { scale: 0.99 } : {}}
              className="app-button-primary w-full"
              aria-disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <motion.span className="block h-5 w-5 rounded-full border-2 border-white border-t-transparent"
                    animate={{ rotate: 360 }} transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }} aria-hidden="true" />
                  Signing in…
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="h-5 w-5" aria-hidden="true" />
                </>
              )}
            </motion.button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            Don&apos;t have an account?{' '}
            <Link to="/signup" className="font-semibold text-primary-700 underline-offset-2 hover:underline dark:text-violet-400">
              Create one free
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
