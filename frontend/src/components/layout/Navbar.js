import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Menu, X, Home, Zap, BarChart3, Brain, Info, Users,
  MessageCircle, MessageSquare, LogIn, UserPlus, LogOut,
  User, Settings, ChevronDown, BookOpen,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const NAV_LINKS = [
  { name: 'Home',       href: '/',           icon: Home },
  { name: 'Generate',   href: '/generate',   icon: Zap },
  { name: 'Community',  href: '/community',  icon: MessageCircle },
  { name: 'Models',     href: '/models',     icon: Brain },
  { name: 'Metrics',    href: '/metrics',    icon: BarChart3 },
  { name: 'About',      href: '/about',      icon: Info },
  { name: 'Developers', href: '/developers', icon: Users },
  { name: 'Docs',       href: '/docs',       icon: BookOpen },
];

function UserMenu({ user, profile, avatarTs, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const displayName = profile?.display_name || user?.name || 'Account';
  const initials = displayName.trim().split(/\s+/).map((w) => w[0]).join('').toUpperCase().slice(0, 2);

  useEffect(() => {
    if (!open) return;
    const onKey   = (e) => { if (e.key === 'Escape') setOpen(false); };
    const onClick  = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('keydown', onClick);
    document.addEventListener('mousedown', onClick);
    window.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onClick);
      document.removeEventListener('mousedown', onClick);
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const close = () => setOpen(false);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full border border-primary-100 bg-white/80 py-1.5 pl-1.5 pr-3 shadow-soft transition-colors hover:border-primary-200 hover:bg-primary-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Account menu"
      >
        <img
          key={avatarTs}
          src={`/api/v1/profile/me/avatar?t=${avatarTs}`}
          alt=""
          aria-hidden="true"
          className="h-7 w-7 rounded-full object-cover ring-2 ring-primary-100"
          onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextSibling.style.display = 'flex'; }}
        />
        <span
          aria-hidden="true"
          style={{ display: 'none' }}
          className="h-7 w-7 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white ring-2 ring-primary-100"
        >
          {initials}
        </span>
        <span className="hidden max-w-[9rem] truncate text-sm font-semibold text-slate-950 sm:block">
          {displayName}
        </span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.18 }}>
          <ChevronDown className="h-4 w-4 text-slate-500" aria-hidden="true" />
        </motion.span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            transition={{ duration: 0.16, ease: [0.22, 1, 0.36, 1] }}
            className="absolute right-0 top-full z-50 mt-2 w-52 origin-top-right overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-medium"
            role="menu"
            aria-label="Account menu"
          >
            <div className="border-b border-slate-50 px-4 py-3">
              <p className="truncate text-sm font-bold text-slate-950">{displayName}</p>
              <p className="truncate text-xs text-slate-500">{user?.email}</p>
            </div>
            <div className="py-1.5">
              <Link to="/profile" onClick={close} role="menuitem"
                className="flex items-center gap-3 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-primary-50 hover:text-primary-700">
                <User className="h-4 w-4" aria-hidden="true" /> My Profile
              </Link>
              <Link to="/profile/edit" onClick={close} role="menuitem"
                className="flex items-center gap-3 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-primary-50 hover:text-primary-700">
                <Settings className="h-4 w-4" aria-hidden="true" /> Edit Profile
              </Link>
            </div>
            <div className="border-t border-slate-100 py-1.5">
              <button onClick={() => { onLogout(); close(); }} role="menuitem"
                className="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-semibold text-red-600 transition-colors hover:bg-red-50">
                <LogOut className="h-4 w-4" aria-hidden="true" /> Sign Out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Navbar() {
  const [isOpen, setIsOpen]     = useState(false);
  const location                = useLocation();
  const navigate                = useNavigate();
  const { user, profile, isAuthenticated, isLoading, avatarTs, logout } = useAuth();
  const brandMarkSrc = `${process.env.PUBLIC_URL}/assets/cadarena-mark.svg`;

  const isActive = (path) => location.pathname === path;
  const close = useCallback(() => setIsOpen(false), []);

  useEffect(() => { close(); }, [location.pathname, close]);

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [close]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const menuVariants = {
    hidden: { opacity: 0, y: -8, scaleY: 0.96 },
    visible: { opacity: 1, y: 0, scaleY: 1, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } },
    exit:    { opacity: 0, y: -6, scaleY: 0.97, transition: { duration: 0.16, ease: 'easeIn' } },
  };

  const itemVariants = {
    hidden:  { opacity: 0, x: -8 },
    visible: (i) => ({ opacity: 1, x: 0, transition: { delay: i * 0.04, duration: 0.18 } }),
  };

  return (
    <nav className="app-navbar sticky top-0 z-50" role="navigation" aria-label="Main navigation">
      <div className="app-shell">
        <div className="flex h-[72px] items-center justify-between">
          <Link to="/" className="app-navbar-brand" aria-label="CadArena home">
            <img src={brandMarkSrc} alt="" aria-hidden="true" className="app-navbar-logo" />
            <div className="flex flex-col leading-none">
              <span className="text-lg font-bold tracking-tight text-slate-950 sm:text-xl">CadArena</span>
              <span className="hidden text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-500 sm:block">
                AI Layout Workspace
              </span>
            </div>
          </Link>

          <div className="hidden items-center gap-0.5 md:flex" role="list">
            {NAV_LINKS.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link key={item.name} to={item.href} role="listitem"
                  aria-current={active ? 'page' : undefined}
                  className={`app-nav-link px-2 ${active ? 'app-nav-link-active' : ''}`}>
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>

          <div className="hidden items-center gap-2 md:flex">
            {!isLoading && (
              isAuthenticated ? (
                <>
                  <Link to="/studio" className="app-button-primary app-button-compact"
                    aria-label="Launch CadArena Studio">
                    <MessageSquare className="h-4 w-4" aria-hidden="true" />
                    Studio
                  </Link>
                  <UserMenu user={user} profile={profile} avatarTs={avatarTs} onLogout={handleLogout} />
                </>
              ) : (
                <>
                  <Link to="/login" className="app-button-ghost app-button-compact">
                    <LogIn className="h-4 w-4" aria-hidden="true" />
                    Sign In
                  </Link>
                  <Link to="/signup" className="app-button-primary app-button-compact">
                    <UserPlus className="h-4 w-4" aria-hidden="true" />
                    Sign Up
                  </Link>
                </>
              )
            )}
            {isLoading && (
              <span className="h-8 w-8 rounded-full app-skeleton" aria-hidden="true" />
            )}
          </div>

          <div className="flex items-center gap-2 md:hidden">
            {!isLoading && !isAuthenticated && (
              <Link to="/login" className="app-button-ghost app-button-compact text-sm">
                <LogIn className="h-4 w-4" aria-hidden="true" />
                Sign In
              </Link>
            )}
            <button
              onClick={() => setIsOpen((v) => !v)}
              className="app-navbar-menu-button"
              aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={isOpen}
              aria-controls="mobile-menu"
            >
              <AnimatePresence mode="wait" initial={false}>
                {isOpen ? (
                  <motion.span key="close"
                    initial={{ rotate: -45, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 45, opacity: 0 }} transition={{ duration: 0.18 }}>
                    <X className="w-5 h-5" aria-hidden="true" />
                  </motion.span>
                ) : (
                  <motion.span key="open"
                    initial={{ rotate: 45, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: -45, opacity: 0 }} transition={{ duration: 0.18 }}>
                    <Menu className="w-5 h-5" aria-hidden="true" />
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div id="mobile-menu" variants={menuVariants} initial="hidden" animate="visible" exit="exit"
            className="app-navbar-mobile md:hidden" style={{ transformOrigin: 'top center' }}>
            <div className="app-shell space-y-1 py-4">
              {isAuthenticated && user && (
                <motion.div custom={0} variants={itemVariants} initial="hidden" animate="visible"
                  className="mb-3 flex items-center gap-3 rounded-2xl border border-primary-100 bg-primary-50/60 px-4 py-3">
                  <img key={avatarTs} src={`/api/v1/profile/me/avatar?t=${avatarTs}`} alt=""
                    aria-hidden="true" className="h-10 w-10 rounded-full object-cover ring-2 ring-primary-200" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold text-slate-950">
                      {profile?.display_name || user.name}
                    </p>
                    <p className="truncate text-xs text-slate-500">{user.email}</p>
                  </div>
                </motion.div>
              )}

              {NAV_LINKS.map((item, i) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <motion.div key={item.name} custom={i} variants={itemVariants} initial="hidden" animate="visible">
                    <Link to={item.href} aria-current={active ? 'page' : undefined}
                      className={`app-nav-link app-nav-link-mobile ${active ? 'app-nav-link-active' : ''}`}>
                      <Icon className="w-5 h-5" aria-hidden="true" />
                      <span>{item.name}</span>
                    </Link>
                  </motion.div>
                );
              })}

              <motion.div custom={NAV_LINKS.length} variants={itemVariants} initial="hidden" animate="visible" className="pt-2 space-y-2">
                <Link to="/studio" className="app-button-primary w-full justify-center"
                  aria-label="Launch CadArena Studio">
                  <MessageSquare className="h-5 w-5" aria-hidden="true" />
                  Launch Studio
                </Link>

                {isAuthenticated ? (
                  <div className="flex gap-2">
                    <Link to="/profile" className="app-button-secondary app-button-compact flex-1 justify-center">
                      <User className="h-4 w-4" aria-hidden="true" />
                      Profile
                    </Link>
                    <button onClick={handleLogout}
                      className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700 transition-colors hover:bg-red-100">
                      <LogOut className="h-4 w-4" aria-hidden="true" />
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <Link to="/signup" className="app-button-secondary w-full justify-center">
                    <UserPlus className="h-5 w-5" aria-hidden="true" />
                    Create Account
                  </Link>
                )}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
