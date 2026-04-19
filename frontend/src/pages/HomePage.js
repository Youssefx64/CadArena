import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Zap, Brain, BarChart3, Sparkles, CheckCircle, Play } from 'lucide-react';
import { motion } from 'framer-motion';

const HomePage = () => {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Generation',
      description: 'Advanced diffusion models fine-tuned on architectural datasets for precise floor plan generation.',
    },
    {
      icon: Zap,
      title: 'Constraint-Aware Design',
      description: 'Ensures spatial consistency and adjacency relationships for realistic architectural layouts.',
    },
    {
      icon: BarChart3,
      title: 'Performance Metrics',
      description: 'Comprehensive evaluation using FID, CLIP-Score, and adjacency consistency metrics.',
    },
    {
      icon: Sparkles,
      title: 'Real-time Generation',
      description: 'Fast inference with optimized models for quick floor plan generation from text prompts.',
    },
  ];

  const stats = [
    { label: 'Accuracy Improvement', value: '+13.2%', description: 'Over baseline models' },
    { label: 'FID Score', value: '57.4', description: 'Industry-leading quality' },
    { label: 'CLIP Score', value: '0.75', description: 'Text-image alignment' },
    { label: 'Generation Time', value: '2.3s', description: 'Average processing time' },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5,
      },
    },
  };

  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden py-20 sm:py-32">
        <div className="hero-premium-bg" />
        <div className="absolute inset-0">
          <div className="absolute left-10 top-20 h-72 w-72 rounded-full bg-primary-200 opacity-25 blur-3xl" />
          <div
            className="absolute right-10 top-40 h-72 w-72 rounded-full bg-secondary-200 opacity-25 blur-3xl"
            style={{ animationDelay: '2s' }}
          />
          <div
            className="absolute -bottom-8 left-20 h-72 w-72 rounded-full bg-primary-100 opacity-24 blur-3xl"
            style={{ animationDelay: '4s' }}
          />
        </div>

        <div className="app-shell relative">
          <motion.div initial="hidden" animate="visible" variants={containerVariants} className="text-center">
            <div className="hero-copy-stack">
              <motion.div variants={itemVariants}>
                <motion.span className="app-pill" whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Sparkles className="h-4 w-4" />
                  AI-Powered Architecture • Live Demo Available
                </motion.span>
              </motion.div>

              <motion.h1 variants={itemVariants} className="app-hero-title hero-title-contrast">
                <motion.span
                  className="gradient-text hero-brand-mark inline-block"
                  animate={{
                    backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
                  }}
                  transition={{
                    duration: 5,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                >
                  CadArena
                </motion.span>
                <span className="hero-title-subline">Conversational CAD Studio</span>
              </motion.h1>

              <motion.p variants={itemVariants} className="hero-subtitle">
                Transform natural language descriptions into structured architectural layouts,
                DXF-ready outputs, and scalable AI-assisted CAD workflows.
              </motion.p>

              <motion.div variants={itemVariants} className="hero-actions">
                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Link to="/studio" className="app-button-primary hero-cta-button w-full sm:w-auto">
                    <Zap className="h-5 w-5" />
                    Try Generator
                    <ArrowRight className="h-5 w-5" />
                  </Link>
                </motion.div>

                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Link to="/models" className="app-button-secondary w-full sm:w-auto">
                    <Play className="h-5 w-5" />
                    View Models
                  </Link>
                </motion.div>
              </motion.div>
            </div>

            <motion.div variants={itemVariants} className="hero-preview-wrap">
              <div className="hero-preview-glass" />
              <div className="hero-preview-card app-card app-card-strong mx-auto max-w-4xl p-8">
                <div className="mb-6 flex items-center justify-center gap-4">
                  <div className="flex gap-2">
                    <div className="h-3 w-3 rounded-full bg-primary-400" />
                    <div className="h-3 w-3 rounded-full bg-secondary-400" />
                    <div className="h-3 w-3 rounded-full bg-primary-200" />
                  </div>
                  <span className="text-sm font-medium text-slate-500">CadArena Studio</span>
                </div>
                <div className="app-card-muted rounded-2xl p-4 text-left">
                  <div className="mb-2 text-sm font-medium text-slate-500">Input:</div>
                  <div className="mb-4 font-mono text-sm text-slate-800">
                    &quot;3-bedroom apartment with open kitchen and living room&quot;
                  </div>
                  <div className="mb-2 text-sm font-medium text-slate-500">Output:</div>
                  <div className="rounded-2xl bg-primary-50/70 p-6 text-center">
                    <div className="mb-2 text-4xl">🏠</div>
                    <div className="text-sm text-slate-600">Generated Floor Plan</div>
                    <div className="mt-1 text-xs font-semibold text-primary-700">
                      84.5% Accuracy • 2.3s Generation Time
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section className="py-16">
        <div className="app-shell">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="grid grid-cols-2 gap-8 lg:grid-cols-4"
          >
            {stats.map((stat) => (
              <motion.div key={stat.label} variants={itemVariants} className="text-center">
                <div className="mb-2 text-3xl font-bold text-primary-700 lg:text-4xl">{stat.value}</div>
                <div className="mb-1 text-sm font-semibold text-slate-950">{stat.label}</div>
                <div className="text-xs text-slate-500">{stat.description}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="bg-white/50 py-20">
        <div className="app-shell">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="mb-16 text-center"
          >
            <motion.h2 variants={itemVariants} className="app-section-title mb-4">
              Powerful AI Features
            </motion.h2>
            <motion.p variants={itemVariants} className="app-section-copy mx-auto max-w-3xl">
              Built with cutting-edge machine learning techniques and architectural expertise.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4"
          >
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <motion.div key={feature.title} variants={itemVariants} className="app-card app-card-hover p-8">
                  <div className="app-icon-badge mb-6">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="app-card-title mb-3">{feature.title}</h3>
                  <p className="app-body">{feature.description}</p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      <section className="py-20">
        <div className="app-shell">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="mb-16 text-center"
          >
            <motion.h2 variants={itemVariants} className="app-section-title mb-4">
              Model Performance
            </motion.h2>
            <motion.p variants={itemVariants} className="app-section-copy mx-auto max-w-3xl">
              Constraint-aware diffusion significantly outperforms baseline models.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="app-card-muted p-8 lg:p-12"
          >
            <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
              <motion.div variants={itemVariants}>
                <h3 className="app-card-title mb-6 text-2xl">Key Improvements</h3>
                <div className="space-y-4">
                  {[
                    { metric: 'FID Score Improvement', value: '-27.8 points', description: 'Better image quality' },
                    { metric: 'CLIP Score Improvement', value: '+0.13 points', description: 'Better text alignment' },
                    { metric: 'Adjacency Consistency', value: '+0.32 points', description: 'Spatial relationships' },
                    { metric: 'Overall Accuracy', value: '+13.2%', description: 'Generation quality' },
                  ].map((item) => (
                    <div key={item.metric} className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 flex-shrink-0 text-primary-600" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-4">
                          <span className="font-medium text-slate-950">{item.metric}</span>
                          <span className="font-bold text-primary-700">{item.value}</span>
                        </div>
                        <p className="text-sm text-slate-600">{item.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              <motion.div variants={itemVariants} className="text-center">
                <div className="app-card app-card-strong app-card-hover p-8 shadow-lg">
                  <h4 className="app-card-title mb-4">Constraint-Aware Model</h4>
                  <div className="mb-2 text-4xl font-bold text-primary-700">84.5%</div>
                  <div className="mb-4 text-sm text-slate-600">Overall Accuracy</div>
                  <div className="h-2 w-full rounded-full bg-primary-100">
                    <div
                      className="app-gradient-primary h-2 rounded-full"
                      style={{ width: '84.5%' }}
                    />
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="app-gradient-primary py-20">
        <div className="app-shell text-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={containerVariants}>
            <motion.h2 variants={itemVariants} className="app-section-title mb-4 text-white">
              Ready to Generate Floor Plans?
            </motion.h2>
            <motion.p variants={itemVariants} className="mx-auto mb-8 max-w-2xl text-xl leading-8 text-primary-100">
              Experience CadArena&apos;s conversational CAD workflow for moving from intent
              to architectural layouts and exportable design artifacts.
            </motion.p>
            <motion.div variants={itemVariants}>
              <Link to="/studio" className="app-button-secondary">
                <Zap className="h-5 w-5" />
                Start Generating
                <ArrowRight className="h-5 w-5" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
