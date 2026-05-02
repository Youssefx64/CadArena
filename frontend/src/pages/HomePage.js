import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Zap, Brain, BarChart3, Sparkles, CheckCircle, Play } from 'lucide-react';
import { motion } from 'framer-motion';

function BlueprintPreview() {
  const rooms = [
    { id: 'living', label: 'Living Room', x: '8%', y: '8%', w: '52%', h: '36%', accent: true },
    { id: 'kitchen', label: 'Kitchen', x: '64%', y: '8%', w: '28%', h: '22%' },
    { id: 'dining', label: 'Dining', x: '64%', y: '34%', w: '28%', h: '10%' },
    { id: 'master', label: 'Master Bed', x: '8%', y: '50%', w: '36%', h: '34%', accent: true },
    { id: 'bed2', label: 'Bedroom 2', x: '48%', y: '50%', w: '26%', h: '34%' },
    { id: 'bath', label: 'Bath', x: '78%', y: '50%', w: '14%', h: '20%' },
    { id: 'hallway', label: '', x: '48%', y: '44%', w: '44%', h: '6%', muted: true },
  ];

  return (
    <div
      className="relative w-full overflow-hidden"
      style={{
        aspectRatio: '16 / 9',
        background: 'rgba(248, 250, 255, 0.9)',
        borderRadius: 16,
      }}
      aria-label="Animated floor plan preview"
      role="img"
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(37, 99, 235, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(124, 58, 237, 0.05) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
          opacity: 0.9,
        }}
      />

      {rooms.map((room, i) => (
        <motion.div
          key={room.id}
          initial={{ opacity: 0, scale: 0.88 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.25 + i * 0.1, duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
          style={{
            position: 'absolute',
            left: room.x,
            top: room.y,
            width: room.w,
            height: room.h,
            borderRadius: 8,
            border: room.muted
              ? '1px dashed rgba(99,102,241,0.22)'
              : room.accent
                ? '1.5px solid rgba(59,130,246,0.45)'
                : '1.5px solid rgba(99,102,241,0.28)',
            background: room.muted
              ? 'transparent'
              : room.accent
                ? 'rgba(239,246,255,0.75)'
                : 'rgba(255,255,255,0.72)',
            boxShadow: room.accent
              ? '0 2px 12px rgba(59,130,246,0.10), inset 0 1px 0 rgba(255,255,255,0.7)'
              : 'inset 0 1px 0 rgba(255,255,255,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {room.label && (
            <span
              style={{
                fontSize: 'clamp(0.55rem, 1vw, 0.72rem)',
                fontWeight: 700,
                color: room.accent ? '#1d4ed8' : '#64748b',
                letterSpacing: '0.02em',
                textAlign: 'center',
                padding: '0 4px',
                userSelect: 'none',
              }}
            >
              {room.label}
            </span>
          )}
        </motion.div>
      ))}

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.4 }}
        style={{
          position: 'absolute',
          bottom: '6%',
          right: '2%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          gap: 4,
        }}
      >
        <span
          style={{
            fontSize: '0.6rem',
            fontWeight: 800,
            color: '#3b82f6',
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
          }}
        >
          84.5% accuracy
        </span>
        <span
          style={{
            fontSize: '0.6rem',
            fontWeight: 600,
            color: '#94a3b8',
            letterSpacing: '0.08em',
          }}
        >
          2.3s · EBC 2023 ✓
        </span>
      </motion.div>

      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ delay: 1.4, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 3,
          background: 'linear-gradient(90deg, #3b82f6, #7c3aed)',
          transformOrigin: 'left center',
          borderBottomLeftRadius: 16,
          borderBottomRightRadius: 16,
        }}
      />
    </div>
  );
}

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
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { duration: 0.5 } },
  };

  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden py-20 sm:py-32">
        <div className="hero-premium-bg" aria-hidden="true" />
        <div className="absolute inset-0" aria-hidden="true">
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
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  AI-Powered Architecture • Live Demo Available
                </motion.span>
              </motion.div>

              <motion.h1 variants={itemVariants} className="app-hero-title hero-title-contrast">
                <motion.span
                  className="gradient-text hero-brand-mark inline-block"
                  animate={{ backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] }}
                  transition={{ duration: 5, repeat: Infinity, ease: 'linear' }}
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
                    <Zap className="h-5 w-5" aria-hidden="true" />
                    Try Generator
                    <ArrowRight className="h-5 w-5" aria-hidden="true" />
                  </Link>
                </motion.div>

                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Link to="/models" className="app-button-secondary w-full sm:w-auto">
                    <Play className="h-5 w-5" aria-hidden="true" />
                    View Models
                  </Link>
                </motion.div>
              </motion.div>
            </div>

            <motion.div variants={itemVariants} className="hero-preview-wrap">
              <div className="hero-preview-glass" aria-hidden="true" />
              <div className="hero-preview-card app-card app-card-strong mx-auto max-w-4xl p-6 sm:p-8">
                <div className="mb-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1.5" aria-hidden="true">
                      <div className="h-3 w-3 rounded-full bg-red-400" />
                      <div className="h-3 w-3 rounded-full bg-yellow-400" />
                      <div className="h-3 w-3 rounded-full bg-green-400" />
                    </div>
                    <span className="hidden text-xs font-semibold text-slate-400 sm:block">CadArena Studio</span>
                  </div>
                  <div className="flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1.5 text-xs font-semibold text-primary-700 border border-primary-100">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary-500 animate-pulse" aria-hidden="true" />
                    Live Preview
                  </div>
                </div>

                <div className="app-card-muted rounded-xl p-3 text-left">
                  <div className="mb-2 font-mono text-xs text-slate-500 flex items-center gap-2">
                    <span className="text-primary-600 font-bold">›</span>
                    <span>&quot;3-bedroom apartment with open kitchen and living room&quot;</span>
                  </div>
                  <BlueprintPreview />
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section className="py-16" aria-label="Key statistics">
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
                <div className="mb-2 text-3xl font-bold text-primary-700 lg:text-4xl" aria-label={`${stat.value} — ${stat.label}`}>
                  {stat.value}
                </div>
                <div className="mb-1 text-sm font-semibold text-slate-950">{stat.label}</div>
                <div className="text-xs text-slate-500">{stat.description}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="bg-white/50 py-20" aria-labelledby="features-heading">
        <div className="app-shell">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="mb-16 text-center"
          >
            <motion.h2 id="features-heading" variants={itemVariants} className="app-section-title mb-4">
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
                  <div className="app-icon-badge mb-6" aria-hidden="true">
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

      <section className="py-20" aria-labelledby="performance-heading">
        <div className="app-shell">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="mb-16 text-center"
          >
            <motion.h2 id="performance-heading" variants={itemVariants} className="app-section-title mb-4">
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
                <div className="space-y-4" role="list">
                  {[
                    { metric: 'FID Score Improvement', value: '-27.8 points', description: 'Better image quality' },
                    { metric: 'CLIP Score Improvement', value: '+0.13 points', description: 'Better text alignment' },
                    { metric: 'Adjacency Consistency', value: '+0.32 points', description: 'Spatial relationships' },
                    { metric: 'Overall Accuracy', value: '+13.2%', description: 'Generation quality' },
                  ].map((item) => (
                    <div key={item.metric} className="flex items-center gap-3" role="listitem">
                      <CheckCircle className="h-5 w-5 flex-shrink-0 text-primary-600" aria-hidden="true" />
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
                  <div
                    className="h-2 w-full rounded-full bg-primary-100"
                    role="progressbar"
                    aria-valuenow={84.5}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label="Overall accuracy: 84.5%"
                  >
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

      <section className="app-gradient-primary py-20" aria-labelledby="cta-heading">
        <div className="app-shell text-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={containerVariants}>
            <motion.h2 id="cta-heading" variants={itemVariants} className="app-section-title mb-4 text-white">
              Ready to Generate Floor Plans?
            </motion.h2>
            <motion.p variants={itemVariants} className="mx-auto mb-8 max-w-2xl text-xl leading-8 text-primary-100">
              Experience CadArena&apos;s conversational CAD workflow for moving from intent
              to architectural layouts and exportable design artifacts.
            </motion.p>
            <motion.div variants={itemVariants}>
              <Link to="/studio" className="app-button-secondary">
                <Zap className="h-5 w-5" aria-hidden="true" />
                Start Generating
                <ArrowRight className="h-5 w-5" aria-hidden="true" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
