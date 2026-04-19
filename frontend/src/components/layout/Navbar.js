import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Home, Zap, BarChart3, Brain, Info, Users, MessageSquare } from 'lucide-react';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const brandMarkSrc = `${process.env.PUBLIC_URL}/studio-app/assets/cadarena-mark.svg`;

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Generate', href: '/generate', icon: Zap },
    { name: 'Studio', href: '/studio', icon: MessageSquare },
    { name: 'Models', href: '/models', icon: Brain },
    { name: 'Metrics', href: '/metrics', icon: BarChart3 },
    { name: 'About', href: '/about', icon: Info },
    { name: 'Developers', href: '/developers', icon: Users },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="app-navbar sticky top-0 z-50">
      <div className="app-shell">
        <div className="flex h-[72px] justify-between">
          <div className="flex items-center">
            <Link to="/" className="app-navbar-brand">
              <img
                src={brandMarkSrc}
                alt="CadArena"
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

          <div className="hidden items-center gap-6 md:flex">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  aria-current={active ? 'page' : undefined}
                  className={`app-nav-link ${active ? 'app-nav-link-active' : ''}`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>

          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="app-navbar-menu-button"
              aria-label={isOpen ? 'Close navigation' : 'Open navigation'}
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {isOpen && (
        <div className="app-navbar-mobile md:hidden">
          <div className="app-shell space-y-2 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsOpen(false)}
                  aria-current={active ? 'page' : undefined}
                  className={`app-nav-link app-nav-link-mobile ${active ? 'app-nav-link-active' : ''}`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
