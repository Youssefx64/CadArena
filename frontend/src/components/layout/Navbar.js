import React, { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Menu, X, Home, Zap, BarChart3, Brain, Info, Users, MessageCircle, MessageSquare } from 'lucide-react';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const brandMarkSrc = `${process.env.PUBLIC_URL}/assets/cadarena-mark.svg`;

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Generate', href: '/generate', icon: Zap },
    { name: 'Studio', href: '/studio', icon: MessageSquare },
    { name: 'Community', href: '/community', icon: MessageCircle },
    { name: 'Models', href: '/models', icon: Brain },
    { name: 'Metrics', href: '/metrics', icon: BarChart3 },
    { name: 'About', href: '/about', icon: Info },
    { name: 'Developers', href: '/developers', icon: Users },
  ];

  const isActive = (path) => location.pathname === path;

  const close = useCallback(() => setIsOpen(false), []);

  useEffect(() => {
    close();
  }, [location.pathname, close]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [close]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const menuVariants = {
    hidden: { opacity: 0, y: -8, scaleY: 0.96 },
    visible: {
      opacity: 1, y: 0, scaleY: 1,
      transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] },
    },
    exit: {
      opacity: 0, y: -6, scaleY: 0.97,
      transition: { duration: 0.16, ease: 'easeIn' },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -8 },
    visible: (i) => ({
      opacity: 1, x: 0,
      transition: { delay: i * 0.04, duration: 0.18, ease: 'easeOut' },
    }),
  };

  return (
    <nav className="app-navbar sticky top-0 z-50" role="navigation" aria-label="Main navigation">
      <div className="app-shell">
        <div className="flex h-[72px] justify-between">
          <div className="flex items-center">
            <Link to="/" className="app-navbar-brand" aria-label="CadArena home">
              <img
                src={brandMarkSrc}
                alt=""
                aria-hidden="true"
                className="app-navbar-logo"
              />
              <div className="flex flex-col leading-none">
                <span className="text-lg font-bold tracking-tight text-slate-950 sm:text-xl">CadArena</span>
                <span className="hidden text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-500 sm:block">
                  AI Layout Workspace
                </span>
              </div>
            </Link>
          </div>

          <div className="hidden items-center gap-1 md:flex" role="list">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  role="listitem"
                  aria-current={active ? 'page' : undefined}
                  className={`app-nav-link px-2 ${active ? 'app-nav-link-active' : ''}`}
                >
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
            <Link
              to="/studio"
              className="app-button-primary app-button-compact ml-3"
              aria-label="Launch CadArena Studio"
            >
              <Zap className="h-4 w-4" aria-hidden="true" />
              Launch Studio
            </Link>
          </div>

          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen((v) => !v)}
              className="app-navbar-menu-button"
              aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={isOpen}
              aria-controls="mobile-menu"
            >
              <AnimatePresence mode="wait" initial={false}>
                {isOpen ? (
                  <motion.span
                    key="close"
                    initial={{ rotate: -45, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 45, opacity: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    <X className="w-5 h-5" aria-hidden="true" />
                  </motion.span>
                ) : (
                  <motion.span
                    key="open"
                    initial={{ rotate: 45, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: -45, opacity: 0 }}
                    transition={{ duration: 0.18 }}
                  >
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
          <motion.div
            id="mobile-menu"
            variants={menuVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="app-navbar-mobile md:hidden"
            style={{ transformOrigin: 'top center' }}
          >
            <div className="app-shell space-y-1 py-4">
              {navigation.map((item, i) => {
                const Icon = item.icon;
                const active = isActive(item.href);

                return (
                  <motion.div
                    key={item.name}
                    custom={i}
                    variants={itemVariants}
                    initial="hidden"
                    animate="visible"
                  >
                    <Link
                      to={item.href}
                      aria-current={active ? 'page' : undefined}
                      className={`app-nav-link app-nav-link-mobile ${active ? 'app-nav-link-active' : ''}`}
                    >
                      <Icon className="w-5 h-5" aria-hidden="true" />
                      <span>{item.name}</span>
                    </Link>
                  </motion.div>
                );
              })}
              <motion.div
                custom={navigation.length}
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                className="pt-2"
              >
                <Link
                  to="/studio"
                  className="app-button-primary w-full justify-center"
                  aria-label="Launch CadArena Studio"
                >
                  <Zap className="h-5 w-5" aria-hidden="true" />
                  Launch Studio
                </Link>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
