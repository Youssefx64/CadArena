import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Zap, Settings, Download, Sparkles, AlertCircle, Info } from 'lucide-react';
import toast from 'react-hot-toast';
import cadArenaAPI from '../services/api';

function BlueprintPlaceholder() {
  return (
    <div
      className="generator-placeholder-shell"
      aria-hidden="true"
    >
      <div className="generator-blueprint-frame">
        <div className="generator-placeholder-grid" />
        <div className="generator-room generator-room-a" />
        <div className="generator-room generator-room-b" />
        <div className="generator-room generator-room-c" />
        <div className="generator-room generator-room-d" />
        <div className="generator-room generator-room-e" />
        <div className="generator-room generator-room-f" />
      </div>
      <p className="mt-4 text-center text-sm font-semibold text-slate-500 tracking-wide">
        Your floor plan will appear here
      </p>
      <p className="mt-1 text-center text-xs text-slate-400">
        Describe a layout and click Generate
      </p>
    </div>
  );
}

const GeneratorPage = () => {
  const location = useLocation();
  const promptRef = useRef(null);
  const [prompt, setPrompt] = useState('');
  const [modelType, setModelType] = useState('baseline');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [generationMetrics, setGenerationMetrics] = useState(null);
  const [style, setStyle] = useState('modern');
  const [apiStatus, setApiStatus] = useState('idle');
  const [modelInfo, setModelInfo] = useState(null);
  const [presets, setPresets] = useState(null);
  const [modelLoaded, setModelLoaded] = useState(false);

  const resizePromptField = (field = promptRef.current) => {
    if (!field) return;
    field.style.height = '0px';
    field.style.height = `${Math.min(field.scrollHeight, 360)}px`;
  };

  useEffect(() => {
    const prefill = location.state?.prefillPrompt;
    if (prefill) {
      setPrompt(prefill);
      setTimeout(() => resizePromptField(), 16);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const checkStatus = useCallback(async () => {
    setApiStatus('checking');
    try {
      await cadArenaAPI.checkHealth();
      setApiStatus('online');

      try {
        const info = await cadArenaAPI.getModelInfo();
        setModelInfo(info.model_info);
        setModelLoaded(info.model_info?.is_loaded || false);
      } catch (_) {}

      try {
        const presetsData = await cadArenaAPI.getPresets();
        setPresets(presetsData.presets);
      } catch (_) {}
    } catch (_) {
      setApiStatus('offline');
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  useEffect(() => {
    resizePromptField();
  }, [prompt]);

  const samplePrompts = presets?.residential || [
    '3-bedroom apartment with open kitchen and living room',
    'Small studio with bathroom and kitchenette',
    '2-story house with 4 bedrooms and 2 bathrooms',
    'Modern loft with master bedroom and walk-in closet',
    'Family home with garage and dining room',
    'Office space with conference room and reception area',
  ];

  const generationPhases = [
    { title: 'Parsing your brief', detail: 'Understanding rooms, counts, and adjacency intent.' },
    { title: 'Balancing the layout', detail: 'Shaping circulation and room proportions.' },
    { title: 'Rendering the preview', detail: 'Preparing a floor plan image you can inspect.' },
  ];

  const promptWordCount = prompt.trim() ? prompt.trim().split(/\s+/).length : 0;
  const isInitializing = apiStatus === 'checking';
  const showPresetSkeletons = isInitializing && !presets;
  const showModelInfoSkeleton = isInitializing && !modelInfo;

  const handleLoadModel = async () => {
    if (apiStatus !== 'online') {
      toast.error('Backend server is not available');
      return;
    }
    setApiStatus('loading_model');
    try {
      toast.loading('Loading CadArena AI model…', { duration: 2000 });
      const result = await cadArenaAPI.loadModel();
      if (result.status === 'success') {
        setModelLoaded(true);
        setModelInfo(result.model_info);
        toast.success('CadArena AI model loaded successfully!');
      } else {
        throw new Error(result.error || 'Failed to load model');
      }
    } catch (error) {
      toast.error(`Failed to load model: ${error.message}`);
      setModelLoaded(false);
    } finally {
      setApiStatus('online');
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a description for your floor plan');
      return;
    }
    if (apiStatus !== 'online') {
      toast.error('CadArena AI is not available. Please check the backend server.');
      return;
    }
    if (!modelLoaded) {
      toast.error('Please load the CadArena AI model first.');
      return;
    }

    setIsGenerating(true);
    setGenerationMetrics(null);
    const startTime = Date.now();

    try {
      const result = await cadArenaAPI.generateFloorPlan({
        description: prompt,
        model: modelType,
        style,
        width: 512,
        height: 512,
        steps: 20,
        guidance: 7.5,
        save: true,
      });

      if (result.success) {
        setGeneratedImage(result.image);
        setGenerationMetrics({
          generation_time: (Date.now() - startTime) / 1000,
          metadata: result.metadata,
        });
        toast.success('Floor plan generated successfully!');
      } else {
        throw new Error('Generation failed');
      }
    } catch (error) {
      toast.error(`Generation failed: ${error.message}`);
      setGeneratedImage(null);
      setGenerationMetrics(null);
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePromptChange = (event) => {
    setPrompt(event.target.value);
    resizePromptField(event.target);
  };

  const handleSamplePrompt = (samplePrompt) => {
    setPrompt(samplePrompt);
    requestAnimationFrame(() => {
      if (promptRef.current) {
        promptRef.current.focus();
        const len = samplePrompt.length;
        promptRef.current.setSelectionRange(len, len);
      }
    });
  };

  const handleDownload = async () => {
    if (!generatedImage) return;
    try {
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      await cadArenaAPI.downloadImage(generatedImage, `cadarena_layout_${timestamp}.png`);
      toast.success('Floor plan downloaded successfully!');
    } catch (_) {
      toast.error('Download failed. Please try again.');
    }
  };

  const statusConfig = (() => {
    if (apiStatus === 'offline')
      return { label: 'Backend Offline', classes: 'border-red-200 bg-red-50 text-red-700', dot: 'bg-red-500' };
    if (apiStatus === 'loading_model')
      return { label: 'Loading AI Model…', classes: 'border-secondary-200 bg-secondary-50 text-secondary-700', dot: 'bg-secondary-500 animate-pulse' };
    if (apiStatus === 'checking')
      return { label: 'Connecting…', classes: 'border-primary-200 bg-primary-50 text-primary-700', dot: 'bg-primary-500 animate-pulse' };
    if (modelLoaded)
      return { label: 'AI Ready', classes: 'border-green-200 bg-green-50 text-green-700', dot: 'bg-green-500' };
    return { label: 'Model Not Loaded', classes: 'border-secondary-200 bg-secondary-50 text-secondary-700', dot: 'bg-secondary-500' };
  })();

  const previewCopy = isGenerating
    ? 'CadArena is translating your brief into a polished floor plan preview.'
    : generatedImage
      ? 'Review the rendered output, inspect the result, and download when you are ready.'
      : 'Describe the plan you want and your generated concept will appear here.';

  const canGenerate = !isGenerating && prompt.trim() && modelLoaded && apiStatus === 'online';

  return (
    <div className="app-page">
      <div className="app-shell">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-page-header">
          <h1 className="app-page-title mb-4">
            <span className="gradient-text">CadArena AI</span> Layout Generator
          </h1>
          <p className="app-page-copy">
            Transform your ideas into detailed architectural floor plans using your trained AI model.
          </p>

          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <div
              className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold shadow-soft ${statusConfig.classes}`}
              role="status"
              aria-live="polite"
              aria-label={`AI status: ${statusConfig.label}`}
            >
              <span className={`app-status-dot ${statusConfig.dot}`} aria-hidden="true" />
              {statusConfig.label}
            </div>

            {apiStatus === 'offline' && (
              <button
                onClick={checkStatus}
                className="app-button-secondary app-button-compact"
                aria-label="Retry connection"
              >
                <AlertCircle className="h-4 w-4" aria-hidden="true" />
                Retry Connection
              </button>
            )}

            {apiStatus === 'online' && !modelLoaded && (
              <button
                onClick={handleLoadModel}
                className="app-button-primary app-button-compact"
                aria-label="Load AI model"
              >
                <Zap className="h-4 w-4" aria-hidden="true" />
                Load AI Model
              </button>
            )}
          </div>
        </motion.div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)] xl:gap-10">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="app-card p-6 lg:p-7">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <label
                    htmlFor="floor-plan-prompt"
                    className="block text-sm font-semibold text-slate-950"
                  >
                    Describe Your Floor Plan
                  </label>
                  <p className="mt-1 text-sm text-slate-600" id="prompt-hint">
                    Include room count, desired adjacencies, special spaces, and overall style direction.
                  </p>
                </div>
                <span className="app-pill-muted shrink-0" aria-hidden="true">Auto-expands</span>
              </div>

              <div className="generator-prompt-shell">
                <textarea
                  id="floor-plan-prompt"
                  ref={promptRef}
                  value={prompt}
                  onChange={handlePromptChange}
                  placeholder="e.g. 3-bedroom apartment with open kitchen, large living area, and two bathrooms…"
                  className="app-textarea generator-prompt-input"
                  rows={8}
                  disabled={isGenerating}
                  aria-describedby="prompt-hint prompt-meta"
                  aria-label="Floor plan description"
                />
              </div>

              <div className="generator-prompt-meta" id="prompt-meta">
                <p className="app-caption">Detailed prompts produce cleaner room relationships.</p>
                <span className="app-pill-muted" aria-label={`${promptWordCount} words`}>
                  {promptWordCount} {promptWordCount === 1 ? 'word' : 'words'}
                </span>
              </div>

              <div className="mt-4">
                <p className="mb-3 text-sm font-semibold text-slate-700" id="samples-label">
                  Example prompts:
                </p>
                <div
                  className="flex flex-wrap gap-2"
                  role="list"
                  aria-labelledby="samples-label"
                >
                  {showPresetSkeletons
                    ? [0, 1, 2].map((item) => (
                      <span key={item} className="app-skeleton app-skeleton-pill h-11 w-40" aria-hidden="true" />
                    ))
                    : samplePrompts.slice(0, 3).map((sample) => (
                      <button
                        key={sample}
                        role="listitem"
                        onClick={() => handleSamplePrompt(sample)}
                        className="app-button-ghost app-button-compact text-xs"
                        disabled={isGenerating}
                        aria-label={`Use example: ${sample}`}
                      >
                        {sample}
                      </button>
                    ))}
                </div>
              </div>
            </div>

            <div className="app-card p-6 lg:p-7">
              <p className="mb-3 block text-sm font-semibold text-slate-950" id="model-label">
                <Settings className="mr-2 inline h-4 w-4" aria-hidden="true" />
                Model Selection
              </p>
              <div className="space-y-3" role="radiogroup" aria-labelledby="model-label">
                <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-primary-100/70 bg-white/80 p-4 shadow-soft transition-colors hover:border-primary-200">
                  <input
                    type="radio"
                    name="model"
                    value="baseline"
                    checked={modelType === 'baseline'}
                    onChange={(e) => setModelType(e.target.value)}
                    className="text-primary-600 focus:ring-primary-500"
                    disabled={isGenerating}
                    aria-describedby="baseline-desc"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-slate-950 flex items-center gap-2 flex-wrap">
                      CadArena Baseline Model
                      {apiStatus === 'online' && (
                        <span className="rounded-full border border-primary-200 bg-primary-50 px-2 py-0.5 text-xs font-semibold text-primary-700">
                          Ready
                        </span>
                      )}
                    </div>
                    <div id="baseline-desc" className="text-sm text-slate-600">
                      Fine-tuned Stable Diffusion model (Recommended)
                    </div>
                    {modelInfo && (
                      <div className="mt-1 text-xs text-slate-500">
                        {modelInfo.resolution || '512×512'} · {modelInfo.device || 'Auto'}
                      </div>
                    )}
                    {showModelInfoSkeleton && (
                      <div className="mt-2 flex gap-2" aria-hidden="true">
                        <span className="app-skeleton h-3 w-24" />
                        <span className="app-skeleton h-3 w-20" />
                      </div>
                    )}
                  </div>
                  <span className="shrink-0 rounded-full border border-secondary-200 bg-secondary-50 px-3 py-1 text-xs font-semibold text-secondary-700">
                    71.7%
                  </span>
                </label>

                <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200 bg-white/60 p-4 opacity-60 shadow-soft">
                  <input
                    type="radio"
                    name="model"
                    value="constraint_aware"
                    checked={modelType === 'constraint_aware'}
                    onChange={(e) => setModelType(e.target.value)}
                    className="text-primary-600 focus:ring-primary-500"
                    disabled
                    aria-describedby="constraint-desc"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-slate-950 flex items-center gap-2">
                      Constraint-Aware Model
                      <Info className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
                    </div>
                    <div id="constraint-desc" className="text-sm text-slate-600">
                      Advanced spatial consistency model
                    </div>
                  </div>
                  <span className="shrink-0 rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
                    Coming Soon
                  </span>
                </label>
              </div>
            </div>

            <div className="app-card p-6 lg:p-7">
              <p className="mb-3 block text-sm font-semibold text-slate-950" id="style-label">
                <Sparkles className="mr-2 inline h-4 w-4" aria-hidden="true" />
                Architectural Style
              </p>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                disabled={isGenerating}
                className="app-select"
                aria-labelledby="style-label"
              >
                <option value="modern">Modern</option>
                <option value="contemporary">Contemporary</option>
                <option value="traditional">Traditional</option>
                <option value="minimalist">Minimalist</option>
                <option value="industrial">Industrial</option>
                <option value="scandinavian">Scandinavian</option>
              </select>
            </div>

            <motion.button
              onClick={handleGenerate}
              disabled={!canGenerate}
              whileHover={canGenerate ? { scale: 1.01 } : {}}
              whileTap={canGenerate ? { scale: 0.99 } : {}}
              className="app-button-primary w-full"
              aria-label={isGenerating ? 'Generating floor plan…' : 'Generate floor plan'}
              aria-disabled={!canGenerate}
            >
              {isGenerating ? (
                <span className="flex items-center justify-center gap-2">
                  <motion.span
                    className="block h-5 w-5 rounded-full border-2 border-white border-t-transparent"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    aria-hidden="true"
                  />
                  Generating…
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <Zap className="h-5 w-5" aria-hidden="true" />
                  Generate Floor Plan
                </span>
              )}
            </motion.button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="app-card p-6 lg:p-7">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <h2 className="app-card-title">Generated Floor Plan</h2>
                  <p className="mt-1 text-sm text-slate-600">{previewCopy}</p>
                </div>
                {generatedImage && !isGenerating && (
                  <button
                    onClick={handleDownload}
                    className="app-button-secondary app-button-compact shrink-0"
                    aria-label="Download generated floor plan as PNG"
                  >
                    <Download className="h-4 w-4" aria-hidden="true" />
                    <span>Download</span>
                  </button>
                )}
              </div>

              <div
                className={`generator-preview-stage app-card-muted ${isGenerating ? 'generator-preview-stage-loading' : ''}`}
                aria-live="polite"
                aria-label={isGenerating ? 'Generating floor plan' : generatedImage ? 'Generated floor plan image' : 'Floor plan preview area'}
              >
                <AnimatePresence mode="wait">
                  {isGenerating ? (
                    <motion.div
                      key="loading"
                      initial={{ opacity: 0, y: 16, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -12, scale: 0.98 }}
                      transition={{ duration: 0.3, ease: 'easeOut' }}
                      className="generator-state-shell"
                    >
                      <div className="generator-loading-orb" aria-hidden="true">
                        <motion.div
                          className="generator-loading-ring"
                          animate={{ scale: [0.92, 1.08, 0.92], opacity: [0.28, 0.7, 0.28] }}
                          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                        />
                        <motion.div
                          className="generator-loading-ring generator-loading-ring-secondary"
                          animate={{ scale: [1.06, 0.94, 1.06], opacity: [0.18, 0.52, 0.18] }}
                          transition={{ duration: 3.6, repeat: Infinity, ease: 'easeInOut' }}
                        />
                        <motion.div
                          className="generator-loading-core"
                          animate={{ scale: [1, 1.08, 1], rotate: [0, 90, 180] }}
                          transition={{ duration: 4.2, repeat: Infinity, ease: 'easeInOut' }}
                        >
                          <Sparkles className="h-9 w-9" />
                        </motion.div>
                      </div>

                      <div className="mb-6 text-center">
                        <span className="generator-state-badge">Generating Preview</span>
                        <h3 className="mt-4 text-2xl font-bold text-slate-950">
                          Composing your floor plan
                        </h3>
                        <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-600">
                          Translating your prompt into rooms, adjacency logic, and a polished layout.
                        </p>
                      </div>

                      <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-3" aria-hidden="true">
                        {generationPhases.map((phase, index) => (
                          <motion.div
                            key={phase.title}
                            className="generator-phase-card"
                            animate={{ y: [0, -6, 0], opacity: [0.72, 1, 0.72] }}
                            transition={{
                              duration: 2.4,
                              delay: index * 0.2,
                              repeat: Infinity,
                              ease: 'easeInOut',
                            }}
                          >
                            <span className="generator-phase-index">0{index + 1}</span>
                            <div className="mt-3 font-semibold text-slate-950">{phase.title}</div>
                            <p className="mt-2 text-sm leading-6 text-slate-600">{phase.detail}</p>
                          </motion.div>
                        ))}
                      </div>

                      <div className="mt-6 w-full max-w-md" aria-hidden="true">
                        <div className="flex items-center justify-between text-[0.7rem] font-semibold uppercase tracking-[0.2em] text-slate-500">
                          <span>Render Progress</span>
                          <span>Live</span>
                        </div>
                        <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/70">
                          <motion.div
                            className="app-gradient-primary h-full w-1/2 rounded-full"
                            animate={{ x: ['-100%', '200%'] }}
                            transition={{ duration: 1.7, repeat: Infinity, ease: 'easeInOut' }}
                          />
                        </div>
                      </div>
                    </motion.div>
                  ) : generatedImage ? (
                    <motion.div
                      key="generated"
                      initial={{ opacity: 0, scale: 0.96 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{ duration: 0.32, ease: 'easeOut' }}
                      className="relative z-10 flex min-h-[26rem] w-full items-center justify-center overflow-hidden rounded-[24px] border border-white/50 bg-white/[0.84] shadow-strong backdrop-blur-sm"
                    >
                      <img
                        src={generatedImage}
                        alt="Generated architectural floor plan"
                        className="h-full w-full bg-white object-contain"
                      />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.25 }}
                    >
                      <BlueprintPlaceholder />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {generationMetrics && !isGenerating && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="app-card p-6"
                role="region"
                aria-label="Generation metrics"
              >
                <h3 className="mb-4 text-sm font-bold uppercase tracking-widest text-slate-500">
                  Generation Metrics
                </h3>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {[
                    { label: 'Time', value: `${generationMetrics.generation_time.toFixed(1)}s` },
                    { label: 'CLIP Score', value: generationMetrics.metadata?.clip_score?.toFixed(2) ?? '—' },
                    { label: 'Adjacency', value: generationMetrics.metadata?.adjacency_score?.toFixed(2) ?? '—' },
                    { label: 'Accuracy', value: generationMetrics.metadata?.accuracy ? `${generationMetrics.metadata.accuracy.toFixed(1)}%` : '—' },
                  ].map((m) => (
                    <div key={m.label} className="app-card-muted p-3 text-center">
                      <div className="text-lg font-bold text-primary-700">{m.value}</div>
                      <div className="text-xs text-slate-500">{m.label}</div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default GeneratorPage;
