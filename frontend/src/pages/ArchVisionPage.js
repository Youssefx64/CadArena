import React, { useState, useEffect } from 'react';
import { 
  Zap, Sparkles, Download, Share2, Maximize2, 
  Settings2, Layout, Image as ImageIcon, History,
  Info, ArrowRight, Loader2, Palette, Box, 
  Compass, Eraser
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

const STYLE_PRESETS = [
  { id: 'modern', name: 'Ultra-Modern', icon: Box, description: 'Sleek lines, glass facades, and contemporary materials.' },
  { id: 'minimalist', name: 'Minimalist', icon: Palette, description: 'Clean, simple, and functional architectural forms.' },
  { id: 'brutalist', name: 'Brutalist', icon: Box, description: 'Raw concrete, bold geometric shapes, and honesty in structure.' },
  { id: 'gothic', name: 'Neo-Gothic', icon: Compass, description: 'Pointed arches, intricate details, and dramatic silhouettes.' },
  { id: 'sketch', name: 'Hand Sketch', icon: Palette, description: 'Artistic charcoal and graphite architectural drafting.' },
  { id: 'render', name: '3D Photoreal', icon: ImageIcon, description: 'High-end cinematic rendering with realistic lighting.' },
];

const ArchVisionPage = () => {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedStyle, setSelectedStyle] = useState('modern');
  const [creativity, setCreativity] = useState(75);
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [history, setHistory] = useState([]);

  const handleGenerate = () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt to visualize your vision.');
      return;
    }

    setIsGenerating(true);
    // Simulate generation process
    setTimeout(() => {
      setIsGenerating(false);
      setGeneratedImage('/assets/archvision-sample.jpg');
      const newEntry = {
        id: Date.now(),
        image: '/assets/archvision-sample.jpg',
        prompt: prompt,
        style: selectedStyle,
        timestamp: new Date().toLocaleTimeString(),
      };
      setHistory(prev => [newEntry, ...prev].slice(0, 5));
      toast.success('ArchVision has brought your design to life!');
    }, 4000);
  };

  const clearPrompt = () => setPrompt('');

  return (
    <div className="app-page min-h-screen bg-[#f8faff] dark:bg-[#020617] transition-colors duration-500">
      <div className="app-shell py-12">
        {/* Header Section */}
        <header className="app-page-header mb-16 text-center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="app-eyebrow mb-4 block">Powered by CadArena AI</span>
            <h1 className="app-hero-title mb-6">
              <span className="gradient-text">ArchVision</span>
            </h1>
            <p className="app-page-copy text-slate-600 dark:text-slate-400">
              Transform your architectural concepts into stunning photorealistic renders or artistic sketches in seconds. 
              The future of spatial visualization is here.
            </p>
          </motion.div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Controls Sidebar */}
          <motion.div 
            className="lg:col-span-4 space-y-6"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {/* Prompt Input Card */}
            <div className="app-card-strong p-6 overflow-visible">
              <div className="flex items-center justify-between mb-4">
                <h3 className="app-card-title flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-blue-500" />
                  Your Vision
                </h3>
                <button 
                  onClick={clearPrompt}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-white/10 rounded-full transition-colors"
                  title="Clear Prompt"
                >
                  <Eraser className="w-4 h-4 text-slate-400" />
                </button>
              </div>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe a minimalist glass villa in a forest during sunset..."
                className="w-full h-32 bg-slate-50/50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-2xl p-4 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all resize-none"
              />
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400">Suggestions:</span>
                {['Modern Villa', 'Brutalist Museum', 'Sustainable Skyscraper'].map(s => (
                  <button 
                    key={s}
                    onClick={() => setPrompt(s)}
                    className="text-[11px] px-2 py-1 rounded-md bg-slate-100 dark:bg-white/5 hover:bg-blue-50 dark:hover:bg-blue-500/20 text-slate-600 dark:text-slate-400 transition-colors border border-transparent hover:border-blue-200"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Style Selector */}
            <div className="app-card p-6">
              <h3 className="app-card-title flex items-center gap-2 mb-6">
                <Palette className="w-5 h-5 text-purple-500" />
                Style Presets
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {STYLE_PRESETS.map((style) => {
                  const Icon = style.icon;
                  const isActive = selectedStyle === style.id;
                  return (
                    <button
                      key={style.id}
                      onClick={() => setSelectedStyle(style.id)}
                      className={`group relative flex flex-col items-center justify-center p-4 rounded-2xl border transition-all duration-300 ${
                        isActive 
                          ? 'bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-blue-400 shadow-md ring-1 ring-blue-400/50' 
                          : 'bg-white/50 dark:bg-white/5 border-slate-100 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/20'
                      }`}
                    >
                      <div className={`p-2 rounded-xl mb-2 transition-colors ${isActive ? 'bg-blue-500 text-white' : 'bg-slate-100 dark:bg-white/10 text-slate-500'}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className={`text-xs font-bold ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-400'}`}>
                        {style.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="app-card p-6">
              <h3 className="app-card-title flex items-center gap-2 mb-6">
                <Settings2 className="w-5 h-5 text-orange-500" />
                Parameters
              </h3>
              
              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Creativity Index</label>
                    <span className="text-xs font-mono font-bold bg-blue-50 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">{creativity}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="1" 
                    max="100" 
                    value={creativity}
                    onChange={(e) => setCreativity(e.target.value)}
                    className="w-full h-1.5 bg-slate-200 dark:bg-white/10 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                  <p className="text-[10px] text-slate-400 italic">Higher values lead to more experimental and artistic results.</p>
                </div>

                <div className="space-y-3">
                  <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Aspect Ratio</label>
                  <div className="flex gap-2">
                    {['1:1', '4:3', '16:9', '21:9'].map(ratio => (
                      <button
                        key={ratio}
                        onClick={() => setAspectRatio(ratio)}
                        className={`flex-1 py-2 text-xs font-bold rounded-xl border transition-all ${
                          aspectRatio === ratio 
                            ? 'bg-slate-950 text-white border-slate-950 dark:bg-white dark:text-slate-950' 
                            : 'bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-500 hover:border-slate-400'
                        }`}
                      >
                        {ratio}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full app-button-primary group overflow-hidden relative"
            >
              <AnimatePresence mode="wait">
                {isGenerating ? (
                  <motion.div 
                    key="loading"
                    initial={{ opacity: 0 }} 
                    animate={{ opacity: 1 }} 
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Conceptualizing...
                  </motion.div>
                ) : (
                  <motion.div 
                    key="idle"
                    initial={{ opacity: 0 }} 
                    animate={{ opacity: 1 }} 
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    <Zap className="w-5 h-5 group-hover:fill-current" />
                    Bring Vision to Life
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                  </motion.div>
                )}
              </AnimatePresence>
              
              {/* Shine effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-shine" />
            </button>
          </motion.div>

          {/* Result Area */}
          <motion.div 
            className="lg:col-span-8 space-y-8"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <div className="relative aspect-video rounded-[32px] overflow-hidden bg-slate-200 dark:bg-white/5 border border-slate-200 dark:border-white/10 shadow-strong group">
              <AnimatePresence mode="wait">
                {isGenerating ? (
                  <motion.div 
                    key="generating-state"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 flex flex-col items-center justify-center p-12 text-center"
                  >
                    <div className="relative mb-8">
                      <div className="absolute inset-0 bg-blue-500 blur-3xl opacity-20 animate-pulse" />
                      <Loader2 className="w-16 h-16 text-blue-500 animate-spin relative z-10" />
                    </div>
                    <h2 className="text-2xl font-bold mb-4 text-slate-800 dark:text-slate-100">ArchVision is Thinking</h2>
                    <p className="max-w-md text-slate-500 dark:text-slate-400 animate-pulse">
                      Synthesizing architectural patterns, material textures, and spatial constraints to match your prompt...
                    </p>
                    
                    {/* Fake progress steps */}
                    <div className="mt-12 w-full max-w-sm flex items-center gap-2">
                      {[0, 1, 2, 3].map(i => (
                        <div key={i} className="h-1.5 flex-1 bg-slate-300 dark:bg-white/10 rounded-full overflow-hidden">
                          <motion.div 
                            className="h-full bg-blue-500"
                            initial={{ width: 0 }}
                            animate={{ width: '100%' }}
                            transition={{ duration: 1, delay: i * 0.8, repeat: Infinity, repeatDelay: 0.5 }}
                          />
                        </div>
                      ))}
                    </div>
                  </motion.div>
                ) : generatedImage ? (
                  <motion.div 
                    key="result-state"
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="h-full w-full relative"
                  >
                    <img 
                      src={generatedImage} 
                      alt="Generated Architectural Vision" 
                      className="h-full w-full object-cover"
                    />
                    
                    {/* Image Actions Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end justify-between p-8">
                      <div className="space-y-1">
                        <p className="text-white font-bold text-lg">{selectedStyle.charAt(0).toUpperCase() + selectedStyle.slice(1)} Perspective</p>
                        <p className="text-slate-200 text-xs line-clamp-1 max-w-md">{prompt}</p>
                      </div>
                      <div className="flex gap-3">
                        <button className="p-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl text-white hover:bg-white/20 transition-all shadow-xl">
                          <Download className="w-5 h-5" />
                        </button>
                        <button className="p-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl text-white hover:bg-white/20 transition-all shadow-xl">
                          <Share2 className="w-5 h-5" />
                        </button>
                        <button className="p-3 bg-blue-600 border border-blue-500 rounded-2xl text-white hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/40">
                          <Maximize2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div 
                    key="empty-state"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 flex flex-col items-center justify-center text-center p-12"
                  >
                    <div className="w-24 h-24 bg-slate-100 dark:bg-white/5 rounded-full flex items-center justify-center mb-8 border border-slate-200 dark:border-white/10">
                      <ImageIcon className="w-10 h-10 text-slate-300 dark:text-slate-600" />
                    </div>
                    <h2 className="text-2xl font-bold mb-4 text-slate-400 dark:text-slate-600">Your Vision Starts Here</h2>
                    <p className="max-w-md text-slate-400 dark:text-slate-600">
                      Enter a detailed architectural description in the sidebar and select a style to begin generating.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Recent Creations (History) */}
            {history.length > 0 && (
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <History className="w-5 h-5 text-slate-400" />
                  <h3 className="app-section-title text-xl">Recent Creations</h3>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {history.map((item) => (
                    <motion.div 
                      key={item.id}
                      layoutId={`history-${item.id}`}
                      className="aspect-square rounded-2xl overflow-hidden border border-slate-200 dark:border-white/10 group cursor-pointer relative"
                      onClick={() => {
                        setGeneratedImage(item.image);
                        setPrompt(item.prompt);
                        setSelectedStyle(item.style);
                      }}
                      whileHover={{ scale: 1.05 }}
                    >
                      <img src={item.image} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110" />
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2">
                        <span className="text-[10px] text-white font-bold uppercase tracking-widest">{item.style}</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="app-card-muted p-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-blue-500/10 rounded-2xl">
                    <Info className="w-6 h-6 text-blue-500" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-2">Prompting Tips</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                      Be specific about materials (timber, concrete, marble), lighting (dusk, foggy, golden hour), and architectural style for the best results.
                    </p>
                  </div>
                </div>
              </div>
              <div className="app-card-muted p-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-purple-500/10 rounded-2xl">
                    <Zap className="w-6 h-6 text-purple-500" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-2">Architectural Accuracy</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                      ArchVision is trained on millions of architectural drawings to ensure structural logic and professional aesthetic standards.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ArchVisionPage;
