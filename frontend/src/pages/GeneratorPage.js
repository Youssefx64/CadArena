import React, { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Zap, Settings, Download, Sparkles, Image as ImageIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import cadArenaAPI from '../services/api';

const GeneratorPage = () => {
  const promptRef = useRef(null);
  const [prompt, setPrompt] = useState('');
  const [modelType, setModelType] = useState('baseline');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [generationMetrics, setGenerationMetrics] = useState(null);
  const [style, setStyle] = useState('modern');
  const [apiStatus, setApiStatus] = useState('checking');
  const [modelInfo, setModelInfo] = useState(null);
  const [presets, setPresets] = useState(null);
  const [modelLoaded, setModelLoaded] = useState(false);

  const resizePromptField = (field = promptRef.current) => {
    if (!field) {
      return;
    }

    field.style.height = '0px';
    field.style.height = `${Math.min(field.scrollHeight, 360)}px`;
  };

  useEffect(() => {
    const initializeAPI = async () => {
      try {
        await cadArenaAPI.checkHealth();
        setApiStatus('online');
        toast.success('CadArena AI is ready!');

        try {
          const info = await cadArenaAPI.getModelInfo();
          setModelInfo(info.model_info);
          setModelLoaded(info.model_info?.is_loaded || false);
        } catch (error) {
          console.warn('Could not load model info:', error);
        }

        try {
          const presetsData = await cadArenaAPI.getPresets();
          setPresets(presetsData.presets);
        } catch (error) {
          console.warn('Could not load presets:', error);
        }
      } catch (error) {
        setApiStatus('offline');
        toast.error('CadArena AI is offline. Please start the backend server.');
        console.error('API initialization failed:', error);
      }
    };

    initializeAPI();
  }, []);

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
    {
      title: 'Parsing your brief',
      detail: 'Understanding rooms, counts, and adjacency intent.',
    },
    {
      title: 'Balancing the layout',
      detail: 'Shaping circulation and room proportions.',
    },
    {
      title: 'Rendering the preview',
      detail: 'Preparing a floor plan image you can inspect.',
    },
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
      toast.loading('Loading CadArena AI model...', { duration: 2000 });

      const result = await cadArenaAPI.loadModel();

      if (result.status === 'success') {
        setModelLoaded(true);
        setModelInfo(result.model_info);
        toast.success('🎉 CadArena AI model loaded successfully!');
      } else {
        throw new Error(result.error || 'Failed to load model');
      }
    } catch (error) {
      console.error('Model loading error:', error);
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

        toast.success('🎉 Floor plan generated successfully!');
      } else {
        throw new Error('Generation failed');
      }
    } catch (error) {
      console.error('Generation error:', error);
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
        const promptLength = samplePrompt.length;
        promptRef.current.setSelectionRange(promptLength, promptLength);
      }
    });
  };

  const handleDownload = async () => {
    if (generatedImage) {
      try {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `cadarena_layout_${timestamp}.png`;

        await cadArenaAPI.downloadImage(generatedImage, filename);
        toast.success('🎉 Floor plan downloaded successfully!');
      } catch (error) {
        console.error('Download error:', error);
        toast.error('Download failed. Please try again.');
      }
    }
  };

  const statusConfig = (() => {
    if (apiStatus === 'offline') {
      return {
        label: 'CadArena AI Offline',
        classes: 'border-red-200 bg-red-50 text-red-700',
        dot: 'bg-red-500',
      };
    }

    if (apiStatus === 'loading_model') {
      return {
        label: 'Loading AI Model...',
        classes: 'border-secondary-200 bg-secondary-50 text-secondary-700',
        dot: 'bg-secondary-500 animate-pulse',
      };
    }

    if (apiStatus === 'checking') {
      return {
        label: 'Connecting to CadArena AI...',
        classes: 'border-primary-200 bg-primary-50 text-primary-700',
        dot: 'bg-primary-500 animate-pulse',
      };
    }

    if (modelLoaded) {
      return {
        label: 'CadArena AI Ready',
        classes: 'border-primary-200 bg-primary-50 text-primary-700',
        dot: 'bg-primary-600',
      };
    }

    return {
      label: 'Model Not Loaded',
      classes: 'border-secondary-200 bg-secondary-50 text-secondary-700',
      dot: 'bg-secondary-500',
    };
  })();

  const previewCopy = isGenerating
    ? 'CadArena is translating your brief into a polished floor plan preview.'
    : generatedImage
      ? 'Review the rendered output, inspect the result, and download when you are ready.'
      : 'Describe the plan you want and your generated concept will appear here.';

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

          <div className="mt-6 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <div className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold shadow-soft ${statusConfig.classes}`}>
              <span className={`app-status-dot ${statusConfig.dot}`} />
              {statusConfig.label}
            </div>

            {apiStatus === 'online' && !modelLoaded && (
              <button onClick={handleLoadModel} className="app-button-primary app-button-compact">
                <Zap className="h-4 w-4" />
                Load AI Model
              </button>
            )}
          </div>
        </motion.div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)] xl:gap-10">
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
            <div className="app-card p-6 lg:p-7">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <label className="block text-sm font-semibold text-slate-950">Describe Your Floor Plan</label>
                  <p className="mt-1 text-sm text-slate-600">
                    Include room count, desired adjacencies, special spaces, and overall style direction.
                  </p>
                </div>
                <span className="app-pill-muted">Auto-expands as you write</span>
              </div>

              <div className="generator-prompt-shell">
                <textarea
                  ref={promptRef}
                  value={prompt}
                  onChange={handlePromptChange}
                  placeholder="Enter a detailed description of your desired floor plan..."
                  className="app-textarea generator-prompt-input"
                  rows={8}
                  disabled={isGenerating}
                />
              </div>

              <div className="generator-prompt-meta">
                <p className="app-caption">Detailed prompts usually produce cleaner room relationships and flow.</p>
                <span className="app-pill-muted">{promptWordCount} {promptWordCount === 1 ? 'word' : 'words'}</span>
              </div>

              <div className="mt-4">
                <p className="mb-3 text-sm font-semibold text-slate-700">Try these examples:</p>
                <div className="flex flex-wrap gap-2">
                  {showPresetSkeletons
                    ? [0, 1, 2].map((item) => (
                      <span key={item} className="app-skeleton app-skeleton-pill h-11 w-40" />
                    ))
                    : samplePrompts.slice(0, 3).map((sample) => (
                      <button
                        key={sample}
                        onClick={() => handleSamplePrompt(sample)}
                        className="app-button-ghost app-button-compact text-xs"
                        disabled={isGenerating}
                      >
                        {sample}
                      </button>
                    ))}
                </div>
              </div>
            </div>

            <div className="app-card p-6 lg:p-7">
              <label className="mb-3 block text-sm font-semibold text-slate-950">
                <Settings className="mr-2 inline h-4 w-4" />
                Model Selection
              </label>
              <div className="space-y-3">
                <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-primary-100/70 bg-white/80 p-4 shadow-soft transition-colors hover:border-primary-200">
                  <input
                    type="radio"
                    name="model"
                    value="baseline"
                    checked={modelType === 'baseline'}
                    onChange={(e) => setModelType(e.target.value)}
                    className="text-primary-600 focus:ring-primary-500"
                    disabled={isGenerating}
                  />
                  <div className="flex-1">
                    <div className="font-medium text-slate-950">
                      CadArena Baseline Model
                      {apiStatus === 'online' && (
                        <span className="ml-2 rounded-full border border-primary-200 bg-primary-50 px-2 py-1 text-xs font-semibold text-primary-700">
                          Ready
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-600">
                      Your trained Stable Diffusion model (Recommended)
                    </div>
                    {modelInfo && (
                      <div className="mt-1 text-xs text-slate-500">
                        Resolution: {modelInfo.resolution || '512x512'} • Device: {modelInfo.device || 'Auto'}
                      </div>
                    )}
                    {showModelInfoSkeleton && (
                      <div className="mt-2 flex gap-2">
                        <span className="app-skeleton h-3 w-24" />
                        <span className="app-skeleton h-3 w-20" />
                      </div>
                    )}
                  </div>
                  <div className="rounded-full border border-secondary-200 bg-secondary-50 px-3 py-1 text-xs font-semibold text-secondary-700">
                    71.7% Accuracy
                  </div>
                </label>

                <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-slate-200 bg-white/60 p-4 opacity-70 shadow-soft">
                  <input
                    type="radio"
                    name="model"
                    value="constraint_aware"
                    checked={modelType === 'constraint_aware'}
                    onChange={(e) => setModelType(e.target.value)}
                    className="text-primary-600 focus:ring-primary-500"
                    disabled
                  />
                  <div className="flex-1">
                    <div className="font-medium text-slate-950">Constraint-Aware Model</div>
                    <div className="text-sm text-slate-600">
                      Advanced model with spatial consistency (Coming Soon)
                    </div>
                  </div>
                  <div className="rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                    In Development
                  </div>
                </label>
              </div>
            </div>

            <div className="app-card p-6 lg:p-7">
              <label className="mb-3 block text-sm font-semibold text-slate-950">
                <Sparkles className="mr-2 inline h-4 w-4" />
                Advanced Options
              </label>

              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">
                    Architectural Style
                  </label>
                  <select
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    disabled={isGenerating}
                    className="app-select"
                  >
                    <option value="modern">Modern</option>
                    <option value="contemporary">Contemporary</option>
                    <option value="traditional">Traditional</option>
                    <option value="minimalist">Minimalist</option>
                    <option value="industrial">Industrial</option>
                    <option value="scandinavian">Scandinavian</option>
                  </select>
                </div>
              </div>
            </div>

            <motion.button
              onClick={handleGenerate}
              disabled={isGenerating || !prompt.trim() || !modelLoaded || apiStatus !== 'online'}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className="app-button-primary w-full"
            >
              {isGenerating ? (
                <div className="flex items-center justify-center gap-2">
                  <motion.div
                    className="h-5 w-5 rounded-full border-2 border-white border-t-transparent"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                  <span>Generating Floor Plan...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2">
                  <Zap className="h-5 w-5" />
                  <span>Generate Floor Plan</span>
                </div>
              )}
            </motion.button>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
            <div className="app-card p-6 lg:p-7">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <h3 className="app-card-title">Generated Floor Plan</h3>
                  <p className="mt-1 text-sm text-slate-600">{previewCopy}</p>
                </div>
                {generatedImage && !isGenerating && (
                  <button onClick={handleDownload} className="app-button-secondary app-button-compact">
                    <Download className="h-4 w-4" />
                    <span>Download</span>
                  </button>
                )}
              </div>

              <div className={`generator-preview-stage app-card-muted ${isGenerating ? 'generator-preview-stage-loading' : ''}`}>
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
                      <div className="generator-loading-orb">
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
                        <h4 className="mt-4 text-2xl font-bold text-slate-950">
                          CadArena is composing your floor plan
                        </h4>
                        <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-600">
                          We&apos;re translating your prompt into rooms, adjacency logic, and a polished layout image.
                        </p>
                      </div>

                      <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-3">
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

                      <div className="mt-6 w-full max-w-md">
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
                        alt="Generated Floor Plan"
                        className="h-full w-full bg-white object-contain"
                        onError={(e) => {
                          console.error('Image load error:', e);
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'flex';
                        }}
                      />

                      <div className="absolute left-0 top-0 hidden h-full w-full items-center justify-center rounded-[24px] bg-primary-50/80">
                        <div className="text-center text-slate-600">
                          <ImageIcon className="mx-auto mb-4 h-20 w-20 text-primary-500" />
                          <p className="text-lg font-semibold">Floor Plan Generated</p>
                          <p className="mt-1 text-sm font-medium text-primary-700">Image ready for download</p>
                        </div>
                      </div>

                      <div className="absolute left-4 top-4 inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/[0.88] px-3 py-2 text-xs font-semibold text-primary-700 shadow-soft backdrop-blur-sm">
                        <span className="app-status-dot bg-primary-500" />
                        Preview Ready
                      </div>

                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: [0, 1.2, 1] }}
                        transition={{ delay: 0.45, duration: 0.5 }}
                        className="app-gradient-primary absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-full shadow-lg"
                      >
                        <span className="text-sm text-white">✓</span>
                      </motion.div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0, y: 16, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -12, scale: 0.98 }}
                      transition={{ duration: 0.3, ease: 'easeOut' }}
                      className="generator-state-shell"
                    >
                      <motion.div
                        className="generator-placeholder-shell"
                        animate={{ y: [0, -8, 0] }}
                        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                      >
                        <div className="generator-blueprint-frame">
                          <div className="generator-placeholder-grid" />
                          <div className="generator-room generator-room-a" />
                          <div className="generator-room generator-room-b" />
                          <div className="generator-room generator-room-c" />
                          <div className="generator-room generator-room-d" />
                          <div className="generator-room generator-room-e" />
                          <div className="generator-room generator-room-f" />

                          <div className="absolute inset-x-6 bottom-5 flex items-center justify-between rounded-full border border-white/[0.65] bg-white/[0.82] px-4 py-2 text-xs shadow-soft backdrop-blur-sm">
                            <span className="font-semibold uppercase tracking-[0.18em] text-primary-700">Live Preview</span>
                            <span className="text-slate-500">Awaiting input</span>
                          </div>
                        </div>

                        <div className="text-center">
                          <div className="app-gradient-primary mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl text-white shadow-medium">
                            <ImageIcon className="h-6 w-6" />
                          </div>
                          <h4 className="text-xl font-bold text-slate-950">Ready for your next concept</h4>
                          <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-600">
                            Describe the rooms you want, how they should connect, and the style you&apos;re after.
                            Your generated floor plan will appear here.
                          </p>
                        </div>

                        <div className="mt-5 flex flex-wrap justify-center gap-2">
                          <span className="app-pill-muted">Room count</span>
                          <span className="app-pill-muted">Adjacency rules</span>
                          <span className="app-pill-muted">Architectural style</span>
                        </div>
                      </motion.div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {isGenerating && (
              <motion.div
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                className="app-card p-6"
              >
                <div className="mb-4 flex items-center justify-between gap-4">
                  <span className="app-skeleton h-5 w-40" />
                  <span className="app-skeleton app-skeleton-pill h-8 w-24" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {[0, 1, 2, 3].map((item) => (
                    <div key={item} className="app-card-muted p-4 text-center">
                      <span className="app-skeleton mx-auto mb-3 h-8 w-16" />
                      <span className="app-skeleton mx-auto h-3 w-20" />
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {generationMetrics && !isGenerating && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-card p-6">
                <h3 className="app-card-title mb-4">Generation Metrics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="app-card-muted p-4 text-center">
                    <div className="text-2xl font-bold text-primary-700">
                      {generationMetrics.metadata.clip_score.toFixed(2)}
                    </div>
                    <div className="text-sm text-slate-600">CLIP Score</div>
                  </div>
                  <div className="app-card-muted p-4 text-center">
                    <div className="text-2xl font-bold text-secondary-700">
                      {generationMetrics.metadata.adjacency_score.toFixed(2)}
                    </div>
                    <div className="text-sm text-slate-600">Adjacency</div>
                  </div>
                  <div className="app-card-muted p-4 text-center">
                    <div className="text-2xl font-bold text-primary-700">
                      {generationMetrics.metadata.accuracy.toFixed(1)}%
                    </div>
                    <div className="text-sm text-slate-600">Accuracy</div>
                  </div>
                  <div className="app-card-muted p-4 text-center">
                    <div className="text-2xl font-bold text-secondary-700">
                      {generationMetrics.generation_time.toFixed(1)}s
                    </div>
                    <div className="text-sm text-slate-600">Gen Time</div>
                  </div>
                </div>
              </motion.div>
            )}

            <div className="app-card-muted p-6">
              <h3 className="app-card-title mb-3">
                <Sparkles className="mr-2 inline h-5 w-5" />
                Pro Tips
              </h3>
              <ul className="space-y-2 text-sm text-slate-700">
                <li>• Be specific about room types and their relationships.</li>
                <li>• Mention desired adjacencies such as &quot;kitchen next to dining room.&quot;</li>
                <li>• Include approximate sizes or room counts for better results.</li>
                <li>• Use architectural terms for more precise layouts.</li>
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default GeneratorPage;
