import React, { Suspense, lazy } from 'react';
import PropTypes from 'prop-types';
import { AnimatePresence, motion } from 'framer-motion';
import { BrowserRouter as Router, Routes, Route, Outlet, useLocation, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function RequireAuth({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return null;
  if (!isAuthenticated) {
    return <Navigate to={`/login?from=${encodeURIComponent(location.pathname)}`} replace />;
  }
  return children;
}
RequireAuth.propTypes = { children: PropTypes.node.isRequired };

const HomePage       = lazy(() => import('./pages/HomePage'));
const ArchVisionPage = lazy(() => import('./pages/ArchVisionPage'));
const AboutPage      = lazy(() => import('./pages/AboutPage'));
const DevelopersPage = lazy(() => import('./pages/DevelopersPage'));
const StudioPage     = lazy(() => import('./pages/StudioPage'));
const CommunityPage  = lazy(() => import('./pages/CommunityPage'));
const RAGChatPage    = lazy(() => import('./pages/RAGChatPage'));
const LoginPage      = lazy(() => import('./pages/LoginPage'));
const SignUpPage      = lazy(() => import('./pages/SignUpPage'));
const ProfilePage    = lazy(() => import('./pages/ProfilePage'));
const EditProfilePage = lazy(() => import('./pages/EditProfilePage'));
const DocsPage        = lazy(() => import('./pages/DocsPage'));
const ViewerPage      = lazy(() => import('./pages/ViewerPage'));

function PageLoader() {
  return (
    <div className="app-page">
      <div className="app-shell space-y-6">
        <div className="app-page-header">
          <span className="app-skeleton app-skeleton-pill mx-auto mb-4 block h-8 w-48" />
          <span className="app-skeleton mx-auto mb-3 block h-12 w-3/4" />
          <span className="app-skeleton mx-auto block h-6 w-1/2" />
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <span key={i} className="app-skeleton block h-48 w-full" style={{ borderRadius: 16 }} />
          ))}
        </div>
      </div>
    </div>
  );
}

function GlobalAmbientBg() {
  return (
    <>
      <div className="global-ambient-bg" aria-hidden="true">
        <div className="global-orb global-orb-1" />
        <div className="global-orb global-orb-2" />
        <div className="global-orb global-orb-3" />
      </div>
      <div className="global-grid-pattern" aria-hidden="true" />
    </>
  );
}

function FullscreenBackdrop({ children }) {
  return (
    <>
      <GlobalAmbientBg />
      <div className="relative z-[1] min-h-screen">
        <Suspense fallback={<PageLoader />}>
          {children}
        </Suspense>
      </div>
    </>
  );
}
FullscreenBackdrop.propTypes = { children: PropTypes.node.isRequired };

function MainLayout() {
  const location = useLocation();
  return (
    <>
      <GlobalAmbientBg />
      <div className="min-h-screen flex flex-col relative z-[1]">
        <Navbar />
        <AnimatePresence>
          <motion.main
            key={location.pathname}
            className="flex-1"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.14, ease: [0.22, 1, 0.36, 1] }}
            style={{ willChange: 'opacity, transform' }}
          >
            <Suspense fallback={<PageLoader />}>
              <Outlet />
            </Suspense>
          </motion.main>
        </AnimatePresence>
        <Footer />
      </div>
    </>
  );
}

function App() {
  const protectedElement = (element) => (
    <RequireAuth>
      {element}
    </RequireAuth>
  );

  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Routes>
            <Route
              path="/studio"
              element={
                <RequireAuth>
                  <FullscreenBackdrop>
                    <StudioPage />
                  </FullscreenBackdrop>
                </RequireAuth>
              }
            />
            <Route
              path="/rag-chat"
              element={
                <RequireAuth>
                  <FullscreenBackdrop>
                    <RAGChatPage />
                  </FullscreenBackdrop>
                </RequireAuth>
              }
            />
            <Route
              path="/viewer"
              element={
                <RequireAuth>
                  <FullscreenBackdrop>
                    <ViewerPage />
                  </FullscreenBackdrop>
                </RequireAuth>
              }
            />
            <Route element={<MainLayout />}>
              <Route path="/"              element={<HomePage />} />
              <Route path="/community"     element={protectedElement(<CommunityPage />)} />
              <Route path="/generate"      element={protectedElement(<ArchVisionPage />)} />
              <Route path="/about"         element={<AboutPage />} />
              <Route path="/developers"    element={<DevelopersPage />} />
              <Route path="/login"         element={<LoginPage />} />
              <Route path="/signup"        element={<SignUpPage />} />
              <Route path="/profile"       element={protectedElement(<ProfilePage />)} />
              <Route path="/profile/edit"  element={protectedElement(<EditProfilePage />)} />
              <Route path="/docs"          element={<DocsPage />} />
            </Route>
          </Routes>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'rgba(15, 23, 42, 0.96)',
                color: '#f8fafc',
                border: '1px solid rgba(96, 165, 250, 0.18)',
                borderRadius: '16px',
                boxShadow: '0 18px 40px rgba(15, 23, 42, 0.2)',
              },
              iconTheme: { primary: '#3b82f6', secondary: '#f8fafc' },
            }}
          />
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
