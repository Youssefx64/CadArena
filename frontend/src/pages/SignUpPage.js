import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, User, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

function passwordStrength(pw) {
  if (!pw) return { level: 0, label: '', cls: '' };
  const variety = [/[A-Z]/, /[a-z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(pw)).length;
  if (pw.length < 8) return { level: 1, label: 'Too short', cls: 'bg-red-400' };
  if (pw.length < 10 || variety < 2) return { level: 2, label: 'Weak', cls: 'bg-orange-400' };
  if (pw.length < 14 || variety < 3) return { level: 3, label: 'Fair', cls: 'bg-yellow-400' };
  return { level: 4, label: 'Strong', cls: 'bg-green-500' };
}

function validate(f) {
  const errs = {};
  if (!f.name.trim()) errs.name = 'Full name is required.';
  else if (f.name.trim().length < 2) errs.name = 'Name must be at least 2 characters.';
  if (!f.email.trim()) errs.email = 'Email is required.';
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) errs.email = 'Enter a valid email address.';
  if (!f.password) errs.password = 'Password is required.';
  else if (f.password.length < 8) errs.password = 'Password must be at least 8 characters.';
  if (!f.confirm) errs.confirm = 'Please confirm your password.';
  else if (f.confirm !== f.password) errs.confirm = 'Passwords do not match.';
  return errs;
}

export default function SignUpPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fields, setFields]       = useState({ name: '', email: '', password: '', confirm: '' });
  const [touched, setTouched]     = useState({});
  const [showPw, setShowPw]       = useState(false);
  const [showCf, setShowCf]       = useState(false);
  const [isSubmitting, setSubmit] = useState(false);
  const [apiError, setApiError]   = useState('');

  const errors = validate(fields);
  const visErr = Object.fromEntries(Object.entries(errors).filter(([k]) => touched[k]));
  const strength = passwordStrength(fields.password);

  const onChange = (e) => { setFields((f) => ({ ...f, [e.target.name]: e.target.value })); setApiError(''); };
  const onBlur = (e) => setTouched((t) => ({ ...t, [e.target.name]: true }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setTouched({ name: true, email: true, password: true, confirm: true });
    if (Object.keys(errors).length) return;
    setSubmit(true);
    setApiError('');
    try {
      await register(fields.name.trim(), fields.email.trim(), fields.password);
      navigate('/', { replace: true });
    } catch (err) {
      setApiError(err.message);
    } finally {
      setSubmit(false);
    }
  };

  const inputCls = (key) =>
    `app-input pl-11${visErr[key] ? ' border-red-400 focus:shadow-[0_0_0_4px_rgba(239,68,68,0.12)]' : ''}`;

  const FieldError = ({ id, msg }) =>
    msg ? (
      <motion.p id={id} initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
        className="mt-1.5 text-xs font-semibold text-red-600" role="alert">{msg}</motion.p>
    ) : null;

  FieldError.propTypes = {
    id:  PropTypes.string,
    msg: PropTypes.string,
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
              <User className="h-7 w-7 text-white" aria-hidden="true" />
            </div>
            <h1 className="text-3xl font-black tracking-tight text-slate-950 dark:text-slate-50">Create account</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Join CadArena to start designing</p>
          </div>

          <AnimatePresence>
            {apiError && (
              <motion.div
                initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                animate={{ opacity: 1, height: 'auto', marginBottom: 20 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                className="flex items-start gap-3 overflow-hidden rounded-2xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30"
                role="alert" aria-live="polite"
              >
                <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" aria-hidden="true" />
                <p className="text-sm font-semibold text-red-700 dark:text-red-400">{apiError}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={onSubmit} noValidate className="space-y-5">
            <div>
              <label htmlFor="su-name" className="mb-1.5 block text-sm font-semibold text-slate-950 dark:text-slate-100">Full name</label>
              <div className="relative">
                <User className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input id="su-name" type="text" name="name" value={fields.name} onChange={onChange} onBlur={onBlur}
                  placeholder="Alex Johnson" autoComplete="name" className={inputCls('name')}
                  aria-describedby={visErr.name ? 'su-name-err' : undefined} aria-invalid={!!visErr.name} disabled={isSubmitting} />
              </div>
              <AnimatePresence><FieldError id="su-name-err" msg={visErr.name} /></AnimatePresence>
            </div>

            <div>
              <label htmlFor="su-email" className="mb-1.5 block text-sm font-semibold text-slate-950 dark:text-slate-100">Email address</label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input id="su-email" type="email" name="email" value={fields.email} onChange={onChange} onBlur={onBlur}
                  placeholder="you@example.com" autoComplete="email" className={inputCls('email')}
                  aria-describedby={visErr.email ? 'su-email-err' : undefined} aria-invalid={!!visErr.email} disabled={isSubmitting} />
              </div>
              <AnimatePresence><FieldError id="su-email-err" msg={visErr.email} /></AnimatePresence>
            </div>

            <div>
              <label htmlFor="su-password" className="mb-1.5 block text-sm font-semibold text-slate-950 dark:text-slate-100">Password</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input id="su-password" type={showPw ? 'text' : 'password'} name="password" value={fields.password}
                  onChange={onChange} onBlur={onBlur} placeholder="Min. 8 characters" autoComplete="new-password"
                  className={`${inputCls('password')} pr-12`}
                  aria-describedby="su-pw-strength" aria-invalid={!!visErr.password} disabled={isSubmitting} />
                <button type="button" onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-400 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                  aria-label={showPw ? 'Hide password' : 'Show password'}>
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {fields.password && (
                <div id="su-pw-strength" className="mt-2" aria-label={`Password strength: ${strength.label}`}>
                  <div className="flex gap-1" aria-hidden="true">
                    {[1, 2, 3, 4].map((l) => (
                      <div key={l} className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${l <= strength.level ? strength.cls : 'bg-slate-200 dark:bg-slate-700'}`} />
                    ))}
                  </div>
                  <p className={`mt-1 text-xs font-semibold ${
                    strength.level <= 1 ? 'text-red-600' : strength.level === 2 ? 'text-orange-600' :
                    strength.level === 3 ? 'text-yellow-600' : 'text-green-600'}`}>
                    {strength.label}
                  </p>
                </div>
              )}
              <AnimatePresence><FieldError id="su-pw-err" msg={visErr.password} /></AnimatePresence>
            </div>

            <div>
              <label htmlFor="su-confirm" className="mb-1.5 block text-sm font-semibold text-slate-950 dark:text-slate-100">Confirm password</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                <input id="su-confirm" type={showCf ? 'text' : 'password'} name="confirm" value={fields.confirm}
                  onChange={onChange} onBlur={onBlur} placeholder="Re-enter password" autoComplete="new-password"
                  className={`${inputCls('confirm')} pr-20${fields.confirm && fields.confirm === fields.password ? ' border-green-400' : ''}`}
                  aria-describedby={visErr.confirm ? 'su-cf-err' : undefined} aria-invalid={!!visErr.confirm} disabled={isSubmitting} />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {fields.confirm && fields.confirm === fields.password && (
                    <CheckCircle2 className="h-4 w-4 text-green-500" aria-hidden="true" />
                  )}
                  <button type="button" onClick={() => setShowCf((v) => !v)}
                    className="rounded-lg p-1.5 text-slate-400 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                    aria-label={showCf ? 'Hide password' : 'Show password'}>
                    {showCf ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <AnimatePresence><FieldError id="su-cf-err" msg={visErr.confirm} /></AnimatePresence>
            </div>

            <motion.button type="submit" disabled={isSubmitting}
              whileHover={!isSubmitting ? { scale: 1.01 } : {}} whileTap={!isSubmitting ? { scale: 0.99 } : {}}
              className="app-button-primary w-full" aria-disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <motion.span className="block h-5 w-5 rounded-full border-2 border-white border-t-transparent"
                    animate={{ rotate: 360 }} transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }} aria-hidden="true" />
                  Creating account…
                </>
              ) : (
                <>Create Account <ArrowRight className="h-5 w-5" aria-hidden="true" /></>
              )}
            </motion.button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-primary-700 underline-offset-2 hover:underline dark:text-violet-400">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
