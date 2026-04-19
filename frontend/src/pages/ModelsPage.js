import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, BarChart3, CheckCircle, ArrowRight, Settings, Cpu, Clock, Target } from 'lucide-react';

const ModelsPage = () => {
  const [selectedModel, setSelectedModel] = useState('constraint_aware');

  const models = [
    {
      id: 'baseline',
      name: 'Baseline Stable Diffusion',
      description: 'Fine-tuned Stable Diffusion 2.1 model on architectural datasets.',
      type: 'Foundation Model',
      status: 'Active',
      accuracy: 71.3,
      fidScore: 85.2,
      clipScore: 0.62,
      adjacencyScore: 0.41,
      trainingTime: '4.2 hours',
      parameters: '865M',
      features: [
        'Standard diffusion architecture',
        'Fine-tuned on floor plan data',
        'Text-to-image generation',
        'Basic spatial understanding',
      ],
      useCases: [
        'Quick prototyping',
        'Basic floor plan generation',
        'Educational purposes',
        'Baseline comparisons',
      ],
    },
    {
      id: 'constraint_aware',
      name: 'Constraint-Aware Diffusion',
      description: 'Enhanced model with spatial consistency and adjacency constraint loss.',
      type: 'Advanced Model',
      status: 'Recommended',
      accuracy: 84.5,
      fidScore: 57.4,
      clipScore: 0.75,
      adjacencyScore: 0.73,
      trainingTime: '6.8 hours',
      parameters: '865M + Constraints',
      features: [
        'Spatial constraint enforcement',
        'Adjacency relationship modeling',
        'Enhanced architectural understanding',
        'Multi-loss optimization',
      ],
      useCases: [
        'Professional floor plans',
        'Architectural design',
        'Real estate visualization',
        'Production applications',
      ],
    },
  ];

  const architectureDetails = {
    baseline: {
      components: [
        { name: 'Text Encoder', description: 'CLIP text encoder for prompt understanding' },
        { name: 'U-Net', description: 'Denoising network for image generation' },
        { name: 'VAE Decoder', description: 'Variational autoencoder for final image output' },
        { name: 'Scheduler', description: 'DDPM scheduler for noise management' },
      ],
      trainingProcess: [
        'Dataset preprocessing and augmentation',
        'Text-image pair alignment',
        'Standard diffusion loss optimization',
        'Fine-tuning on architectural data',
      ],
    },
    constraint_aware: {
      components: [
        { name: 'Text Encoder', description: 'Enhanced CLIP encoder with architectural tokens' },
        { name: 'Constraint U-Net', description: 'Modified U-Net with spatial attention layers' },
        { name: 'Adjacency Module', description: 'Custom module for spatial relationship modeling' },
        { name: 'Multi-Loss VAE', description: 'Enhanced decoder with constraint awareness' },
      ],
      trainingProcess: [
        'Spatial relationship annotation',
        'Multi-objective loss function design',
        'Constraint-aware fine-tuning',
        'Adjacency consistency optimization',
      ],
    },
  };

  const selectedCard = models.find((model) => model.id === selectedModel);

  return (
    <div className="app-page">
      <div className="app-shell">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-page-header">
          <h1 className="app-page-title mb-4">
            <span className="gradient-text">AI Models</span> Overview
          </h1>
          <p className="app-page-copy">
            Explore our advanced diffusion models designed for architectural floor plan generation.
          </p>
        </motion.div>

        <div className="mb-12 grid grid-cols-1 gap-8 lg:grid-cols-2">
          {models.map((model, index) => (
            <motion.div
              key={model.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`app-card app-card-hover cursor-pointer p-8 ${
                selectedModel === model.id ? 'border-primary-200 shadow-lg' : ''
              }`}
              onClick={() => setSelectedModel(model.id)}
            >
              <div className="mb-6 flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="app-icon-badge">
                    <Brain className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="app-card-title">{model.name}</h3>
                    <p className="text-sm text-slate-600">{model.type}</p>
                  </div>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    model.status === 'Recommended'
                      ? 'border border-secondary-200 bg-secondary-50 text-secondary-700'
                      : 'border border-primary-200 bg-primary-50 text-primary-700'
                  }`}
                >
                  {model.status}
                </span>
              </div>

              <p className="mb-6 text-slate-600">{model.description}</p>

              <div className="mb-6 grid grid-cols-2 gap-4">
                <div className="app-card-muted p-4 text-center">
                  <div className="text-2xl font-bold text-slate-950">{model.accuracy}%</div>
                  <div className="text-xs text-slate-600">Accuracy</div>
                </div>
                <div className="app-card-muted p-4 text-center">
                  <div className="text-2xl font-bold text-slate-950">{model.fidScore}</div>
                  <div className="text-xs text-slate-600">FID Score</div>
                </div>
                <div className="app-card-muted p-4 text-center">
                  <div className="text-2xl font-bold text-slate-950">{model.clipScore}</div>
                  <div className="text-xs text-slate-600">CLIP Score</div>
                </div>
                <div className="app-card-muted p-4 text-center">
                  <div className="text-2xl font-bold text-slate-950">{model.adjacencyScore}</div>
                  <div className="text-xs text-slate-600">Adjacency</div>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
                  Key Features
                </h4>
                <div className="space-y-2">
                  {model.features.slice(0, 3).map((feature) => (
                    <div key={feature} className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 flex-shrink-0 text-primary-600" />
                      <span className="text-sm text-slate-600">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button className="app-button-primary w-full">
                <span>View Details</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </motion.div>
          ))}
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-card p-8">
          <div className="mb-8 flex items-center gap-3">
            <Settings className="h-6 w-6 text-primary-600" />
            <h2 className="app-section-title text-2xl">{selectedCard?.name} Architecture</h2>
          </div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <div>
              <h3 className="mb-4 text-lg font-semibold text-slate-950">
                <Cpu className="mr-2 inline h-5 w-5" />
                Model Specifications
              </h3>
              <div className="space-y-4">
                {[
                  { label: 'Parameters', value: selectedCard?.parameters, icon: Target },
                  { label: 'Training Time', value: selectedCard?.trainingTime, icon: Clock },
                  { label: 'Architecture', value: 'Diffusion Transformer', icon: Brain },
                  { label: 'Input Resolution', value: '512x512', icon: Settings },
                ].map((spec) => {
                  const Icon = spec.icon;
                  return (
                    <div key={spec.label} className="app-card-muted flex items-center justify-between p-4">
                      <div className="flex items-center gap-3">
                        <Icon className="h-4 w-4 text-primary-600" />
                        <span className="font-medium text-slate-950">{spec.label}</span>
                      </div>
                      <span className="text-slate-600">{spec.value}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <h3 className="mb-4 text-lg font-semibold text-slate-950">
                <Brain className="mr-2 inline h-5 w-5" />
                Architecture Components
              </h3>
              <div className="space-y-3">
                {architectureDetails[selectedModel]?.components.map((component) => (
                  <div key={component.name} className="app-card-muted p-4">
                    <div className="mb-1 font-medium text-slate-950">{component.name}</div>
                    <div className="text-sm text-slate-600">{component.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-8">
            <h3 className="mb-4 text-lg font-semibold text-slate-950">
              <BarChart3 className="mr-2 inline h-5 w-5" />
              Training Process
            </h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              {architectureDetails[selectedModel]?.trainingProcess.map((step, index) => (
                <div key={step} className="text-center">
                  <div className="app-gradient-primary mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold text-white shadow-soft">
                    {index + 1}
                  </div>
                  <div className="mb-1 text-sm font-medium text-slate-950">Step {index + 1}</div>
                  <div className="text-xs text-slate-600">{step}</div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="app-card-muted mt-8 p-8">
          <h2 className="app-section-title mb-6 text-center text-2xl">Performance Comparison</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
            {[
              { metric: 'Accuracy', baseline: 71.3, constraint: 84.5, unit: '%', better: 'higher' },
              { metric: 'FID Score', baseline: 85.2, constraint: 57.4, unit: '', better: 'lower' },
              { metric: 'CLIP Score', baseline: 0.62, constraint: 0.75, unit: '', better: 'higher' },
              { metric: 'Adjacency', baseline: 0.41, constraint: 0.73, unit: '', better: 'higher' },
            ].map((metric) => {
              const improvement =
                metric.better === 'higher'
                  ? ((metric.constraint - metric.baseline) / metric.baseline) * 100
                  : ((metric.baseline - metric.constraint) / metric.baseline) * 100;

              return (
                <div key={metric.metric} className="app-card app-card-hover p-6 text-center">
                  <h3 className="mb-4 font-semibold text-slate-950">{metric.metric}</h3>
                  <div className="mb-4 space-y-2">
                    <div className="text-sm text-slate-600">
                      Baseline: <span className="font-medium">{metric.baseline}{metric.unit}</span>
                    </div>
                    <div className="text-sm text-slate-600">
                      Constraint: <span className="font-medium text-primary-700">{metric.constraint}{metric.unit}</span>
                    </div>
                  </div>
                  <div className={`text-lg font-bold ${improvement > 0 ? 'text-primary-700' : 'text-red-600'}`}>
                    {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
                  </div>
                  <div className="text-xs text-slate-500">improvement</div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ModelsPage;
