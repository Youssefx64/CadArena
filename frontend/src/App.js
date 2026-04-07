import React from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import HomePage from './pages/HomePage';
import GeneratorPage from './pages/GeneratorPage';
import ModelsPage from './pages/ModelsPage';
import MetricsPage from './pages/MetricsPage';
import AboutPage from './pages/AboutPage';
import DevelopersPage from './pages/DevelopersPage';
import StudioPage from './pages/StudioPage';

function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/studio" element={<StudioPage />} />
        <Route element={<MainLayout />}>
          <Route path="/" element={<HomePage />} />
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
            background: '#1f2937',
            color: '#f9fafb',
          },
        }}
      />
    </Router>
  );
}

export default App;
