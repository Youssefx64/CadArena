import React, { useMemo, useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, SlidersHorizontal, ArrowRight, Zap, MessageSquare, BookOpen,
  Filter, HelpCircle, Cancel as X, CheckCircle2, AlertTriangle, Clock
} from '../components/IconRegistry';
import FeaturesIllustration from '../components/illustrations/FeaturesIllustration';
import { features } from '../data/features';
import FeatureCard from '../components/ui/FeatureCard';

// ─── STAGE/THEME CONFIGS ──────────────────────────────────────────────────────
const CATEGORIES = [
  { id: 'all', label: 'All Categories' },
  { id: 'ai', label: 'AI Cognitive Engines' },
  { id: 'rag', label: 'RAG Retrieval Systems' },
  { id: 'cad', label: 'CAD & Geometry' },
  { id: 'workspace', label: 'Workspace Databases' },
  { id: 'export', label: 'Export Exporters' },
  { id: 'security', label: 'Security & Auth' },
  { id: 'performance', label: 'Performance & Workers' },
  { id: 'observability', label: 'Observability & Metrics' },
  { id: 'collaboration', label: 'Collaboration Hub' },
];

const COMPARISON_ROWS = [
  { key: 'ai_chat', label: 'Multi-turn Conversational AI', archchat: true, cadstudio: false, note: 'General query assistant' },
  { key: 'rag', label: 'Retrieval-Augmented Generation', archchat: true, cadstudio: false, note: 'Egyptian Building Code search' },
  { key: 'doc_upload', label: 'Document PDF & TXT Ingestion', archchat: true, cadstudio: false, note: 'Real-time vector indexing' },
  { key: 'citations', label: 'Interactive deep-link Citations', archchat: true, cadstudio: false, note: 'Cross-links code reference page' },
  { key: 'dxf_gen', label: 'Natural Language → DXF Generation', archchat: false, cadstudio: true, note: 'Deterministic spatial geometry' },
  { key: 'svg_viewer', label: 'High-performance CAD Visualizer', archchat: true, cadstudio: true, note: 'SVG canvas navigation & zoom' },
  { key: 'layers', label: 'CAD Layer Visibility Management', archchat: true, cadstudio: true, note: 'Toggles walls, columns, dims' },
  { key: 'compliance', label: 'EBC Code Compliance validation', archchat: true, cadstudio: true, note: 'Clearances and bottlenecks checks' },
  { key: 'exports', label: 'DXF, PNG, PDF document Export', archchat: false, cadstudio: true, note: 'Standard plotting export files' },
  { key: 'workspace', label: 'SQLite persistent Workspaces', archchat: true, cadstudio: true, note: 'Isolates project profiles' },
  { key: 'auth', label: 'Dual JWT OAuth Authentication', archchat: true, cadstudio: true, note: 'Google and email sessions' },
  { key: 'observability', label: 'cProfile Tracing & System Metrics', archchat: true, cadstudio: true, note: 'Uptime and requests monitors' },
];

// Motion variations
const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.02 } } };
const fadeUp  = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } } };

export default function FeaturesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeDetailsFeature, setActiveDetailsFeature] = useState(null);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // SEO
  useEffect(() => {
    document.title = 'Platform Capabilities — CadArena';
  }, []);
  
  // Ref to track last focused element before opening modal
  const triggerRef = useRef(null);
  const modalRef = useRef(null);
  const searchInputRef = useRef(null);

  // Read URL states
  const productFilter = searchParams.get('product') || 'all';
  const categoryFilter = searchParams.get('category') || 'all';
  const statusFilter = searchParams.get('status') || 'all';
  const searchQuery = searchParams.get('search') || '';

  // Simulate loading screen on mount to ensure smooth client-side experience
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsDataLoading(false);
    }, 450);
    return () => clearTimeout(timer);
  }, []);

  // Update specific URL search parameters helper
  const updateParams = useCallback((key, value) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (!value || value === 'all') {
        next.delete(key);
      } else {
        next.set(key, value);
      }
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  // Fast debounced-like search input callback (instant search satisfies typing specs)
  const handleSearchChange = (e) => {
    updateParams('search', e.target.value);
  };

  const handleClearFilters = useCallback(() => {
    setSearchParams(new URLSearchParams());
    if (searchInputRef.current) searchInputRef.current.focus();
  }, [setSearchParams]);

  // Memoized filter and search implementation
  const filteredFeatures = useMemo(() => {
    if (isDataLoading || hasError) return [];
    return features.filter((feat) => {
      // 1. Product Filter (exclude coming soon from general search if not in roadmap category)
      if (productFilter !== 'all' && feat.product !== productFilter) {
        return false;
      }
      // If showing roadmap/coming-soon category, status filters bypass general implemented-only grid
      if (statusFilter !== 'all' && feat.status !== statusFilter) {
        return false;
      }
      if (statusFilter === 'all' && categoryFilter !== 'roadmap' && feat.status === 'coming-soon') {
        return false;
      }
      
      // 2. Category Filter
      if (categoryFilter !== 'all') {
        if (categoryFilter === 'roadmap') {
          if (feat.status !== 'coming-soon') return false;
        } else if (feat.category !== categoryFilter) {
          return false;
        }
      }

      // 3. Search text matching
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = feat.title.toLowerCase().includes(q);
        const matchesDesc = feat.description.toLowerCase().includes(q);
        const matchesTags = feat.tags && feat.tags.some((t) => t.toLowerCase().includes(q));
        const matchesCat = feat.category.toLowerCase().includes(q);
        const matchesProd = feat.product.toLowerCase().includes(q);

        return matchesTitle || matchesDesc || matchesTags || matchesCat || matchesProd;
      }

      return true;
    });
  }, [productFilter, categoryFilter, statusFilter, searchQuery, isDataLoading, hasError]);

  // Compute category counts dynamically based on active product/search filter (ensures real feedback)
  const categoryCounts = useMemo(() => {
    const counts = { all: 0, roadmap: 0 };
    CATEGORIES.forEach((cat) => {
      if (cat.id !== 'all') counts[cat.id] = 0;
    });

    features.forEach((feat) => {
      // Apply search and product constraints to the counts so filters reflect search subset
      if (productFilter !== 'all' && feat.product !== productFilter) return;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = feat.title.toLowerCase().includes(q);
        const matchesDesc = feat.description.toLowerCase().includes(q);
        const matchesTags = feat.tags && feat.tags.some((t) => t.toLowerCase().includes(q));
        const matchesCat = feat.category.toLowerCase().includes(q);
        const matchesProd = feat.product.toLowerCase().includes(q);
        if (!(matchesTitle || matchesDesc || matchesTags || matchesCat || matchesProd)) return;
      }

      counts.all++;
      if (feat.status === 'coming-soon') {
        counts.roadmap++;
      } else {
        counts[feat.category] = (counts[feat.category] || 0) + 1;
      }
    });

    return counts;
  }, [productFilter, searchQuery]);

  // Feature details modal handlers
  const handleOpenDetails = useCallback((feature) => {
    triggerRef.current = document.activeElement;
    setActiveDetailsFeature(feature);
  }, []);

  const handleCloseDetails = useCallback(() => {
    setActiveDetailsFeature(null);
    if (triggerRef.current) {
      triggerRef.current.focus();
    }
  }, []);

  // Modal accessibility focus trap & key listeners
  useEffect(() => {
    if (!activeDetailsFeature) return;

    const modalElement = modalRef.current;
    if (!modalElement) return;

    const focusableSelector = 'button, a, input, [tabindex="0"]';
    const focusables = modalElement.querySelectorAll(focusableSelector);
    if (focusables.length === 0) return;

    const firstFocusable = focusables[0];
    const lastFocusable = focusables[focusables.length - 1];

    // Automatically focus the first element (the close button)
    firstFocusable.focus();

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        handleCloseDetails();
      } else if (e.key === 'Tab') {
        if (e.shiftKey) { // Shift + Tab: wrap to end
          if (document.activeElement === firstFocusable) {
            e.preventDefault();
            lastFocusable.focus();
          }
        } else { // Tab: wrap to start
          if (document.activeElement === lastFocusable) {
            e.preventDefault();
            firstFocusable.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [activeDetailsFeature, handleCloseDetails]);

  // Roadmap timeline features
  const roadmapFeatures = useMemo(() => {
    const items = features.filter((feat) => feat.status === 'coming-soon');
    const stages = {
      'In Progress': [],
      'Planned': [],
      'Future Vision': [],
    };
    items.forEach((item) => {
      if (stages[item.stage]) {
        stages[item.stage].push(item);
      }
    });
    return stages;
  }, []);

  // Focus trap / click outside mobile drawer
  const closeDrawer = () => setMobileDrawerOpen(false);

  return (
    <div className="min-h-screen relative pb-16 pt-10">
      
      {/* ═══ HERO SECTION ════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24">
        <div className="hero-grid-pattern" aria-hidden="true" />
        <div className="app-shell relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <motion.div 
              initial="hidden" 
              animate="visible" 
              variants={stagger} 
              className="lg:col-span-7 text-center lg:text-left space-y-6"
            >
              <motion.div variants={fadeUp} className="flex justify-center lg:justify-start">
                <span className="app-pill">
                  <Zap className="h-3.5 w-3.5" aria-hidden="true" />
                  Verified Platform Capabilities
                </span>
              </motion.div>
              
              <motion.h1 variants={fadeUp} className="app-hero-title leading-tight text-4xl sm:text-5xl lg:text-6xl font-black mb-6">
                Everything the platform
                <br />
                <span className="gradient-text-animated">ships today</span>
              </motion.h1>

              <motion.p variants={fadeUp} className="app-page-copy mx-auto lg:mx-0 mb-10 max-w-2xl text-slate-500 dark:text-slate-400">
                A complete index of implemented features across ArchChat and CadStudio.
                Filter by product, category, or keyword — every entry reflects code that is deployed and running.
              </motion.p>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="lg:col-span-5 flex justify-center w-full"
            >
              <FeaturesIllustration />
            </motion.div>
          </div>

            {/* Statistics counters derived from implementation */}
            <motion.div 
              variants={stagger}
              className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 max-w-5xl mx-auto"
            >
              {[
                { label: 'Verified geometry ops', value: '12+' },
                { label: 'Vector architecture', value: 'Qdrant' },
                { label: 'Avg. response time', value: '<200 ms' },
                { label: 'Supported formats', value: '5 types' },
                { label: 'Auth standards', value: 'OAuth/JWT' },
                { label: 'Deployment sync', value: '6 h' },
              ].map((stat, i) => (
                <motion.div 
                  key={i}
                  variants={fadeUp}
                  className="app-card border border-slate-100 bg-white/70 dark:border-white/5 dark:bg-zinc-900/60 p-4 rounded-2xl flex flex-col justify-center"
                >
                  <span className="text-lg font-black text-primary-600 dark:text-violet-400 leading-tight">
                    {stat.value}
                  </span>
                  <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 mt-1 uppercase tracking-wide leading-tight">
                    {stat.label}
                  </span>
                </motion.div>
              ))}
            </motion.div>
        </div>
      </section>

      {/* ═══ ERROR STATE FALLBACK ═══════════════════════════════════════════ */}
      {hasError && (
        <div className="app-shell py-12 flex justify-center">
          <div className="app-card max-w-md p-8 text-center border-red-500/25 bg-red-500/5">
            <AlertTriangle className="h-10 w-10 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">Sync Error</h3>
            <p className="text-sm text-slate-500 mb-6">Unable to connect to the feature registry. Check network permissions.</p>
            <button 
              onClick={() => setHasError(false)}
              className="app-button-primary app-button-compact"
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}

      {!hasError && (
        <section className="app-shell relative z-20">
          
          {/* ═══ FILTER BAR (TABS) ═══════════════════════════════════════════ */}
          <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 dark:border-white/5 pb-6">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mr-2">
                Products:
              </span>
              {[
                { id: 'all', label: 'All Platform' },
                { id: 'archchat', label: 'ArchChat (RAG)' },
                { id: 'cadstudio', label: 'CadStudio (CAD)' },
                { id: 'platform', label: 'Platform Core' },
              ].map((prod) => (
                <button
                  key={prod.id}
                  onClick={() => updateParams('product', prod.id)}
                  className={`px-4 py-2 text-xs font-bold rounded-xl border transition-colors ${
                    productFilter === prod.id
                      ? 'border-primary-500 bg-primary-500 text-white dark:border-violet-600 dark:bg-violet-600'
                      : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-zinc-900 dark:text-slate-300 dark:hover:bg-zinc-800'
                  }`}
                >
                  {prod.label}
                </button>
              ))}
            </div>

            {/* Status Filter Dropdown */}
            <div className="flex items-center gap-2">
              <label htmlFor="status-select" className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                Status:
              </label>
              <select
                id="status-select"
                value={statusFilter}
                onChange={(e) => updateParams('status', e.target.value)}
                className="bg-white dark:bg-zinc-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs font-bold text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="all">All States</option>
                <option value="implemented">Implemented</option>
                <option value="beta">Beta</option>
                <option value="experimental">Experimental</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* ═══ DESKTOP CATEGORY SIDEBAR ══════════════════════════════════ */}
            <aside className="hidden lg:block lg:col-span-3 sticky top-24">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="h-4 w-4 text-slate-400" />
                <h3 className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                  Categories
                </h3>
              </div>
              <nav className="space-y-1" aria-label="Feature categories filter list">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => updateParams('category', cat.id)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 text-xs font-bold rounded-xl transition-all ${
                      categoryFilter === cat.id
                        ? 'bg-primary-50 text-primary-700 dark:bg-violet-950/30 dark:text-violet-300 border border-primary-200/50 dark:border-violet-900/40'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <span>{cat.label}</span>
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                      categoryFilter === cat.id 
                        ? 'bg-primary-200/50 text-primary-800 dark:bg-violet-900/40 dark:text-violet-300' 
                        : 'bg-slate-100 dark:bg-white/5 text-slate-400'
                    }`}>
                      {categoryCounts[cat.id]}
                    </span>
                  </button>
                ))}
                
                {/* Roadmap Category Selector */}
                <button
                  onClick={() => updateParams('category', 'roadmap')}
                  className={`w-full flex items-center justify-between px-3 py-2.5 text-xs font-bold rounded-xl transition-all border ${
                    categoryFilter === 'roadmap'
                      ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-300 border-amber-200/50 dark:border-amber-900/40'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 border-transparent'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5" />
                    Roadmap & Coming Soon
                  </span>
                  <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                    categoryFilter === 'roadmap' 
                      ? 'bg-amber-200/50 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300' 
                      : 'bg-slate-100 dark:bg-white/5 text-slate-400'
                  }`}>
                    {categoryCounts.roadmap}
                  </span>
                </button>
              </nav>
            </aside>

            {/* ═══ MOBILE CATEGORY TRIGGER ═══════════════════════════════════ */}
            <div className="lg:hidden flex justify-between items-center gap-4 bg-slate-50 dark:bg-zinc-900/60 p-4 border border-slate-200/60 dark:border-white/5 rounded-2xl mb-2">
              <button 
                onClick={() => setMobileDrawerOpen(true)}
                className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-300"
              >
                <SlidersHorizontal className="h-4 w-4" />
                <span>Filter Categories ({categoryFilter === 'all' ? 'All' : categoryFilter})</span>
              </button>
              <span className="text-xs font-bold text-slate-400">
                {filteredFeatures.length} matching
              </span>
            </div>

            {/* ═══ MAIN FEATURE LIST & SEARCH ════════════════════════════════ */}
            <div className="lg:col-span-9 space-y-6">
              
              {/* Search bar */}
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4" aria-hidden="true">
                  <Search className="h-5 w-5 text-slate-400 dark:text-slate-500" />
                </div>
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={handleSearchChange}
                  placeholder="Query by feature, capability, or technical tag..."
                  className="w-full bg-white dark:bg-zinc-900 border border-slate-200 dark:border-slate-800 rounded-2xl py-3.5 pl-12 pr-10 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-primary-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-shadow hover:shadow-soft"
                />
                {searchQuery && (
                  <button 
                    onClick={() => updateParams('search', '')}
                    className="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    aria-label="Clear search"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
              </div>

              {/* SKELETON LOADER STATE */}
              {isDataLoading && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[0, 1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="app-card border border-slate-100 bg-white p-6 rounded-2xl space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="app-skeleton h-8 w-8 rounded-lg" />
                        <span className="app-skeleton h-5 w-20 rounded-full" />
                      </div>
                      <span className="app-skeleton block h-6 w-3/4" />
                      <span className="app-skeleton block h-14 w-full" />
                      <div className="flex gap-1">
                        <span className="app-skeleton h-5 w-12 rounded-lg" />
                        <span className="app-skeleton h-5 w-12 rounded-lg" />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* EMPTY STATE */}
              {!isDataLoading && filteredFeatures.length === 0 && (
                <div className="app-card p-12 text-center border-dashed border-slate-200 dark:border-white/5 bg-transparent rounded-2xl">
                  <HelpCircle className="h-10 w-10 text-slate-400 dark:text-slate-500 mx-auto mb-4" />
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-2">No matching capabilities</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 max-w-sm mx-auto">
                    Your current parameters return no results. Clear active filters or broaden your query.
                  </p>
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    <button 
                      onClick={handleClearFilters}
                      className="app-button-primary app-button-compact"
                    >
                      Reset All
                    </button>
                    <button 
                      onClick={() => updateParams('category', 'all')}
                      className="app-button-secondary app-button-compact text-xs"
                    >
                      Show All
                    </button>
                  </div>
                </div>
              )}

              {/* DYNAMIC FEATURE CARDS GRID */}
              {!isDataLoading && filteredFeatures.length > 0 && (
                <motion.div 
                  initial="hidden"
                  animate="visible"
                  variants={stagger}
                  className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                >
                  {filteredFeatures.map((feat) => (
                    <FeatureCard
                      key={feat.id}
                      feature={feat}
                      onOpenDetails={handleOpenDetails}
                      searchTerm={searchQuery}
                    />
                  ))}
                </motion.div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ═══ MOBILE BOTTOM DRAWER DIALOG ═════════════════════════════════════ */}
      <AnimatePresence>
        {mobileDrawerOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              onClick={closeDrawer}
              className="fixed inset-0 z-40 bg-black md:hidden"
            />
            <motion.div 
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 250 }}
              className="fixed inset-x-0 bottom-0 z-50 bg-white dark:bg-zinc-900 border-t border-slate-200 dark:border-white/10 rounded-t-3xl max-h-[85vh] overflow-y-auto p-6 md:hidden shadow-2xl"
              role="dialog"
              aria-modal="true"
              aria-label="Choose Category Filter"
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-widest">
                  Categories List
                </h3>
                <button onClick={closeDrawer} className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-white/5">
                  <X className="h-5 w-5 text-slate-500" />
                </button>
              </div>
              <div className="space-y-1">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => { updateParams('category', cat.id); closeDrawer(); }}
                    className={`w-full flex items-center justify-between px-3 py-3 text-xs font-bold rounded-xl transition-all ${
                      categoryFilter === cat.id
                        ? 'bg-primary-50 text-primary-700 dark:bg-violet-950/30 dark:text-violet-300'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5'
                    }`}
                  >
                    <span>{cat.label}</span>
                    <span className="bg-slate-100 dark:bg-white/5 text-slate-500 px-2 py-0.5 rounded-full text-[10px]">
                      {categoryCounts[cat.id]}
                    </span>
                  </button>
                ))}
                
                {/* Roadmap mobile link */}
                <button
                  onClick={() => { updateParams('category', 'roadmap'); closeDrawer(); }}
                  className={`w-full flex items-center justify-between px-3 py-3 text-xs font-bold rounded-xl transition-all border ${
                    categoryFilter === 'roadmap'
                      ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-300 border-amber-200/50'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 border-transparent'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5" />
                    Roadmap & Coming Soon
                  </span>
                  <span className="bg-slate-100 dark:bg-white/5 text-slate-500 px-2 py-0.5 rounded-full text-[10px]">
                    {categoryCounts.roadmap}
                  </span>
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ═══ INTERACTIVE DETAILED MODAL DIALOG ═══════════════════════════════ */}
      <AnimatePresence>
        {activeDetailsFeature && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              onClick={handleCloseDetails}
              className="absolute inset-0 bg-black"
            />
            {/* Modal Box */}
            <motion.div
              ref={modalRef}
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
              className="relative w-full max-w-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-white/10 rounded-3xl shadow-2xl p-6 md:p-8 max-h-[90vh] overflow-y-auto focus-visible:outline-none"
              role="dialog"
              aria-modal="true"
              aria-labelledby="modal-title"
              aria-describedby="modal-desc"
            >
              {/* Close buttons */}
              <button
                onClick={handleCloseDetails}
                className="absolute right-4 top-4 p-2 rounded-full text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-600 dark:hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                aria-label="Close modal dialog"
              >
                <X className="h-5 w-5" />
              </button>

              <div className="mb-6">
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="text-[10px] font-bold uppercase bg-primary-100 text-primary-700 dark:bg-violet-950/40 dark:text-violet-300 border border-primary-200 dark:border-violet-900/40 px-2.5 py-0.5 rounded-full">
                    {activeDetailsFeature.product === 'archchat' ? 'ArchChat' : activeDetailsFeature.product === 'cadstudio' ? 'CadStudio' : 'Platform'}
                  </span>
                  <span className="text-[10px] font-bold uppercase bg-slate-100 border border-slate-200 dark:bg-white/5 dark:border-white/5 text-slate-500 dark:text-slate-400 px-2.5 py-0.5 rounded-full">
                    {activeDetailsFeature.status}
                  </span>
                </div>
                <h2 id="modal-title" className="text-xl md:text-2xl font-black text-slate-950 dark:text-slate-50">
                  {activeDetailsFeature.title}
                </h2>
              </div>

              {/* Body details */}
              <div className="space-y-6">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Description</h4>
                  <p id="modal-desc" className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                    {activeDetailsFeature.fullDescription || activeDetailsFeature.description}
                  </p>
                </div>

                {/* Workflow section */}
                {activeDetailsFeature.workflows && activeDetailsFeature.workflows.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Verified Workflows</h4>
                    <ul className="space-y-2">
                      {activeDetailsFeature.workflows.map((flow, idx) => (
                        <li key={idx} className="flex items-start gap-3">
                          <span className="flex-shrink-0 mt-1 flex h-4 w-4 items-center justify-center rounded-full bg-green-100 text-[10px] font-bold text-green-700 dark:bg-green-950/20 dark:text-green-400" aria-hidden="true">
                            {idx + 1}
                          </span>
                          <span className="text-xs text-slate-600 dark:text-slate-300">{flow}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Meta details list */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-100 dark:border-white/5 pt-6">
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Capability Tags</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {activeDetailsFeature.tags?.map((t) => (
                        <span key={t} className="text-[10px] font-semibold bg-slate-50 border border-slate-200/50 dark:bg-white/5 dark:border-white/5 px-2 py-0.5 rounded text-slate-500 dark:text-slate-400">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Dependencies</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {activeDetailsFeature.dependencies?.map((dep) => (
                        <span key={dep} className="text-[10px] font-semibold bg-slate-50 border border-slate-200/50 dark:bg-white/5 dark:border-white/5 px-2 py-0.5 rounded text-slate-500 dark:text-slate-400">
                          {dep}
                        </span>
                      )) || <span className="text-xs text-slate-400">None</span>}
                    </div>
                  </div>
                </div>

                {/* Contextual actions linking to verified routes */}
                <div className="border-t border-slate-100 dark:border-white/5 pt-6 flex justify-end gap-3">
                  <button 
                    onClick={handleCloseDetails}
                    className="app-button-secondary app-button-compact text-xs"
                  >
                    Close Window
                  </button>
                  {activeDetailsFeature.product === 'archchat' && (
                    <Link 
                      to="/rag-chat" 
                      className="app-button-primary app-button-compact text-xs flex items-center gap-1.5"
                    >
                      Launch ArchChat
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                    </Link>
                  )}
                  {activeDetailsFeature.product === 'cadstudio' && (
                    <Link 
                      to="/studio" 
                      className="app-button-primary app-button-compact text-xs flex items-center gap-1.5"
                    >
                      Open CAD Studio
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                    </Link>
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ═══ INTERACTIVE PRODUCT COMPARISON TABLE ═══════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 mt-20 pt-16" aria-labelledby="comp-heading">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">System Matrix</p>
          <h2 id="comp-heading" className="app-section-title mb-4">Functional Differentiation</h2>
          <p className="app-section-copy mx-auto max-w-xl">
            Comparing ArchChat (AI/Retrieval) and CadStudio (CAD/Geometry). 
            Independent scopes unified into a single, cohesive engineering environment.
          </p>
        </div>

        <div className="app-card border border-slate-200/70 dark:border-white/5 overflow-x-auto p-2 rounded-3xl bg-white/40 dark:bg-zinc-900/40">
          <table className="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr className="border-b border-slate-200/50 dark:border-white/5 text-xs font-bold text-slate-400 uppercase">
                <th className="p-4 pl-6">Core Capability</th>
                <th className="p-4 text-center">ArchChat</th>
                <th className="p-4 text-center">CadStudio</th>
                <th className="p-4">Technical Note</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr 
                  key={row.key} 
                  className="border-b border-slate-100 dark:border-white/5 hover:bg-slate-50/50 dark:hover:bg-white/5 transition-colors text-xs font-semibold"
                >
                  <td className="p-4 pl-6 font-bold text-slate-800 dark:text-slate-200">
                    {row.label}
                  </td>
                  <td className="p-4 text-center">
                    {row.archchat ? (
                      <CheckCircle2 className="h-5 w-5 text-primary-600 dark:text-violet-400 mx-auto" />
                    ) : (
                      <span className="text-slate-300 dark:text-slate-700">—</span>
                    )}
                  </td>
                  <td className="p-4 text-center">
                    {row.cadstudio ? (
                      <CheckCircle2 className="h-5 w-5 text-primary-600 dark:text-violet-400 mx-auto" />
                    ) : (
                      <span className="text-slate-300 dark:text-slate-700">—</span>
                    )}
                  </td>
                  <td className="p-4 text-slate-500 dark:text-slate-400">
                    {row.note}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ═══ ROADMAP TIMELINE SECTION ═══════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 mt-20 pt-16" aria-labelledby="roadmap-heading">
        <div className="text-center mb-16">
          <p className="app-eyebrow mb-3">Planned Features</p>
          <h2 id="roadmap-heading" className="app-section-title mb-4">Roadmap & Future Timeline</h2>
          <p className="app-section-copy mx-auto max-w-xl">
            A transparent visual roadmap separating verified implemented code from future milestones.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Connector line for roadmap timeline */}
          <div className="absolute top-1/2 left-[15%] right-[15%] h-px bg-slate-200 dark:bg-white/10 hidden md:block z-0" aria-hidden="true" />
          
          {Object.entries(roadmapFeatures).map(([stage, items]) => (
            <div key={stage} className="relative z-10 space-y-6">
              {/* Stage Header */}
              <div className="flex items-center gap-3 border-b border-slate-100 dark:border-white/5 pb-3">
                <span className={`h-2.5 w-2.5 rounded-full ${
                  stage === 'In Progress' ? 'bg-indigo-500 animate-pulse' : stage === 'Planned' ? 'bg-primary-500' : 'bg-slate-400'
                }`} />
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  {stage}
                </h3>
              </div>

              {/* Stage Items Grid */}
              <div className="space-y-4">
                {items.map((item) => (
                  <div 
                    key={item.id}
                    className="app-card border border-slate-200/50 bg-white/70 dark:border-white/5 dark:bg-zinc-900/60 p-5 rounded-2xl flex flex-col hover:border-amber-500/20 dark:hover:border-amber-500/10 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                        {item.title}
                      </span>
                      <span className="text-[9px] font-bold uppercase bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Clock className="h-2.5 w-2.5" />
                        {item.stage}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal flex-1">
                      {item.description}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-1">
                      {item.tags?.map((t) => (
                        <span key={t} className="text-[9px] font-semibold bg-slate-100 dark:bg-white/5 border border-slate-200/30 px-2 py-0.5 rounded text-slate-400">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ PREMIUM CALL-TO-ACTION (CTA) SECTION ══════════════════════════ */}
      <section className="app-shell mt-24" aria-labelledby="cta-heading">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeUp}
          className="app-cta-panel relative overflow-hidden px-8 py-16 text-center sm:px-14 sm:py-20 rounded-3xl"
        >
          <div className="pointer-events-none absolute inset-0" aria-hidden="true">
            <div className="absolute -left-20 -top-20 h-80 w-80 rounded-full bg-white opacity-[0.05] blur-3xl" />
            <div className="absolute -bottom-20 -right-20 h-80 w-80 rounded-full bg-white opacity-[0.05] blur-3xl" />
            <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent" />
            <div className="absolute left-1/2 top-0 h-px w-2/3 -translate-x-1/2 bg-white opacity-20" />
          </div>

          <p className="mb-4 text-xs font-bold uppercase tracking-widest text-primary-200">
            Ready to build
          </p>
          <h2 id="cta-heading" className="mb-4 text-2xl font-black tracking-tight text-white sm:text-3xl">
            Start working with the platform
          </h2>
          <p className="mx-auto mb-10 max-w-lg text-sm leading-relaxed text-primary-100">
            Query the Egyptian Building Code, generate a DXF floor plan from a text prompt,
            or review the system documentation — all without any setup.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link to="/studio" className="app-button-primary bg-white text-slate-950 hover:bg-slate-100 flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Open CAD Studio
            </Link>
            <Link to="/rag-chat" className="app-button-secondary border-white/20 text-white hover:bg-white/10 flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Open ArchChat
            </Link>
            <Link to="/docs" className="app-button-secondary border-white/20 text-white hover:bg-white/10 flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Read System Docs
            </Link>
          </div>
        </motion.div>
      </section>

    </div>
  );
}
