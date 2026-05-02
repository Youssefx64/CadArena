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
const GeneratorPage  = lazy(() => import('./pages/GeneratorPage'));
const ModelsPage     = lazy(() => import('./pages/ModelsPage'));
const MetricsPage    = lazy(() => import('./pages/MetricsPage'));
const AboutPage      = lazy(() => import('./pages/AboutPage'));
const DevelopersPage = lazy(() => import('./pages/DevelopersPage'));
const StudioPage     = lazy(() => import('./pages/StudioPage'));
const CommunityPage  = lazy(() => import('./pages/CommunityPage'));
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

function MainLayout() {
  const location = useLocation();
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <AnimatePresence mode="wait">
        <motion.main
          key={location.pathname}
          className="flex-1"
          initial={{ opacity: 0, y: 22, scale: 0.982, filter: 'blur(6px)' }}
          animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: -12, scale: 1.01, filter: 'blur(4px)' }}
          transition={{ duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
          style={{ willChange: 'transform, opacity' }}
        >
          <Suspense fallback={<PageLoader />}>
            <Outlet />
          </Suspense>
        </motion.main>
      </AnimatePresence>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Routes>
            <Route
              path="/studio"
              element={
                <RequireAuth>
                  <Suspense fallback={<PageLoader />}>
                    <StudioPage />
                  </Suspense>
                </RequireAuth>
              }
            />
            <Route
              path="/viewer"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ViewerPage />
                </Suspense>
              }
            />
            <Route element={<MainLayout />}>
              <Route path="/"              element={<HomePage />} />
              <Route path="/community"     element={<CommunityPage />} />
              <Route path="/generate"      element={<GeneratorPage />} />
              <Route path="/models"        element={<ModelsPage />} />
              <Route path="/metrics"       element={<MetricsPage />} />
              <Route path="/about"         element={<AboutPage />} />
              <Route path="/developers"    element={<DevelopersPage />} />
              <Route path="/login"         element={<LoginPage />} />
              <Route path="/signup"        element={<SignUpPage />} />
              <Route path="/profile"       element={<ProfilePage />} />
              <Route path="/profile/edit"  element={<EditProfilePage />} />
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
