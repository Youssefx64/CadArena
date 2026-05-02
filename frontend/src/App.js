import React, { Suspense, lazy } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { BrowserRouter as Router, Routes, Route, Outlet, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';

const HomePage = lazy(() => import('./pages/HomePage'));
const GeneratorPage = lazy(() => import('./pages/GeneratorPage'));
const ModelsPage = lazy(() => import('./pages/ModelsPage'));
const MetricsPage = lazy(() => import('./pages/MetricsPage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const DevelopersPage = lazy(() => import('./pages/DevelopersPage'));
const StudioPage = lazy(() => import('./pages/StudioPage'));
const CommunityPage = lazy(() => import('./pages/CommunityPage'));

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
          initial={{ opacity: 0, y: 14, filter: 'blur(4px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: -10, filter: 'blur(3px)' }}
          transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
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
      <Router>
        <Routes>
          <Route
            path="/studio"
            element={
              <Suspense fallback={<PageLoader />}>
                <StudioPage />
              </Suspense>
            }
          />
          <Route element={<MainLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/community" element={<CommunityPage />} />
            <Route path="/generate" element={<GeneratorPage />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/metrics" element={<MetricsPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/developers" element={<DevelopersPage />} />
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
            iconTheme: {
              primary: '#3b82f6',
              secondary: '#f8fafc',
            },
          }}
        />
      </Router>
    </ErrorBoundary>
  );
}

export default App;
