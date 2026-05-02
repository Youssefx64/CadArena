import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Brain, Zap, Target, Code2, ArrowRight, CheckCircle,
  FileCode2, Layers, Cpu, Database,
} from 'lucide-react';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.09 } } };
const fadeUp  = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } } };

const AboutPage = () => {
  const PILLARS = [
    {
      icon: Brain,
      title: 'Constraint-Aware Diffusion',
      body: 'The core AI uses a modified Stable Diffusion 2.1 model with a custom spatial constraint loss that enforces room adjacency and structural relationships during the denoising process — not as a post-processing filter.',
    },
    {
      icon: Target,
      title: 'EBC 2023 Compliance',
      body: 'Generated layouts satisfy Egyptian Building Code 2023 standards for minimum room areas, ceiling heights, and spatial adjacency — making the output usable in real architectural practice, not just as visualizations.',
    },
    {
      icon: FileCode2,
      title: 'DXF-Ready Output',
      body: 'Every generated floor plan is automatically exported as a DXF file with per-room layers, room labels, and linear dimension entities — ready to open in AutoCAD, Revit, or any DXF-compatible tool.',
    },
    {
      icon: Zap,
      title: 'Conversational Workflow',
      body: 'The Studio provides a natural-language interface. Describe what you need in plain English or Arabic, and the AI handles spatial reasoning, constraint satisfaction, and CAD formatting automatically.',
    },
  ];

  const STACK = [
    {
      icon: Brain,
      category: 'AI & Machine Learning',
      items: [
        { name: 'PyTorch 2.0 + Diffusers 0.35', note: 'Diffusion model training and inference' },
        { name: 'Stable Diffusion 2.1', note: 'Foundation model (865M parameters)' },
        { name: 'CLIP + Transformers 4.57', note: 'Text encoder for prompt understanding' },
        { name: 'Custom constraint U-Net', note: 'Spatial attention + multi-loss training' },
      ],
    },
    {
      icon: Code2,
      category: 'Backend & API',
      items: [
        { name: 'FastAPI 0.128 + Uvicorn', note: 'High-performance async API server' },
        { name: 'Pydantic v2', note: 'Request/response validation' },
        { name: 'ezdxf', note: 'DXF generation and export pipeline' },
        { name: 'bcrypt + JWT cookies', note: 'Secure authentication system' },
      ],
    },
    {
      icon: Layers,
      category: 'Frontend & UI',
      items: [
        { name: 'React 18 + CRA', note: 'Code-split SPA with lazy loading' },
        { name: 'Tailwind CSS 3.3', note: 'Design system and utility styling' },
        { name: 'Framer Motion 10', note: 'Animations and micro-interactions' },
        { name: 'Lucide React + Recharts', note: 'Icons and data visualization' },
      ],
    },
    {
      icon: Database,
      category: 'Data & Infrastructure',
      items: [
        { name: 'CubiCasa5K dataset', note: '5,000+ annotated architectural floor plans' },
        { name: 'SQLite persistence', note: 'Workspace, profiles, and project storage' },
        { name: 'Google Colab A100', note: 'Training hardware (120+ GPU hours)' },
        { name: 'CUDA 11.8+', note: 'GPU-accelerated inference pipeline' },
      ],
    },
  ];

  const METRICS = [
    { label: 'Model Accuracy',  value: '84.5%', note: 'Constraint-Aware vs 71.3% baseline' },
    { label: 'FID Score',       value: '57.4',  note: 'Down from 85.2 baseline (lower = better)' },
    { label: 'CLIP Score',      value: '0.75',  note: 'Text-image alignment (up from 0.62)' },
    { label: 'Adjacency Score', value: '0.73',  note: '+78% over baseline' },
    { label: 'Generation Time', value: '2.3s',  note: 'Average on GPU hardware' },
    { label: 'Training Epochs', value: '5',     note: 'With early stopping and LR scheduling' },
  ];

  return (
    <div className="app-page">
      <div className="app-shell">

        {/* Header */}
        <motion.div initial="hidden" animate="visible" variants={stagger} className="app-page-header mb-16">
          <motion.div variants={fadeUp} className="mb-5">
            <span className="app-pill">
              <Brain className="h-4 w-4" aria-hidden="true" />
              About the Project
            </span>
          </motion.div>
          <motion.h1 variants={fadeUp} className="app-page-title mb-5">
            About <span className="gradient-text">CadArena</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="app-page-copy">
            CadArena is an AI-powered conversational CAD platform that transforms natural language intent
            into structured architectural layouts, EBC-compliant floor plans, and DXF-ready CAD exports.
          </motion.p>
        </motion.div>

        {/* Mission panel */}
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          className="app-cta-panel relative mb-16 overflow-hidden px-10 py-16 text-center">
          <div className="pointer-events-none absolute inset-0" aria-hidden="true">
            <div className="absolute -left-16 -top-16 h-64 w-64 rounded-full bg-white opacity-[0.06] blur-3xl" />
            <div className="absolute -bottom-16 -right-16 h-64 w-64 rounded-full bg-white opacity-[0.06] blur-3xl" />
          </div>
          <h2 className="mb-5 text-2xl font-black text-white">Mission</h2>
          <p className="mx-auto max-w-3xl text-lg leading-relaxed text-primary-100">
            To make architectural AI genuinely useful in practice — by combining conversational interfaces,
            reliable CAD outputs, and spatially-aware generative models that help architects and designers
            move faster from intent to execution, without sacrificing compliance or precision.
          </p>
        </motion.div>

        {/* Core pillars */}
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16">
          <motion.h2 variants={fadeUp} className="app-section-title mb-12 text-center">
            How it works
          </motion.h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {PILLARS.map((p) => {
              const Icon = p.icon;
              return (
                <motion.div key={p.title} variants={fadeUp} className="app-card app-card-hover p-8">
                  <div className="app-icon-badge-lg mb-5" aria-hidden="true">
                    <Icon className="h-7 w-7" />
                  </div>
                  <h3 className="app-card-title mb-3">{p.title}</h3>
                  <p className="app-body">{p.body}</p>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* By the numbers */}
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
          className="app-card mb-16 p-8 lg:p-12">
          <motion.h2 variants={fadeUp} className="app-section-title mb-10 text-center">
            By the numbers
          </motion.h2>
          <div className="grid grid-cols-2 gap-6 lg:grid-cols-3">
            {METRICS.map((m) => (
              <motion.div key={m.label} variants={fadeUp} className="text-center">
                <div
                  className="mb-1 text-4xl font-black tracking-tight lg:text-5xl"
                  style={{ backgroundImage: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}
                >
                  {m.value}
                </div>
                <div className="mb-1 font-semibold text-slate-950">{m.label}</div>
                <div className="text-xs text-slate-500">{m.note}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Key improvements */}
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
          className="app-card-muted mb-16 p-8 lg:p-12">
          <motion.h2 variants={fadeUp} className="app-section-title mb-8 text-center">
            Constraint-Aware vs Baseline
          </motion.h2>
          <div className="mx-auto max-w-2xl space-y-4">
            {[
              { metric: 'FID Score', improvement: '−27.8 pts', note: 'Lower is better — significant quality gain' },
              { metric: 'CLIP Score', improvement: '+0.13 pts', note: 'Better text-to-layout alignment' },
              { metric: 'Adjacency Consistency', improvement: '+0.32 pts', note: 'Rooms are now spatially coherent' },
              { metric: 'Overall Accuracy', improvement: '+13.2%', note: 'Measured across all evaluation metrics' },
            ].map(({ metric, improvement, note }) => (
              <motion.div key={metric} variants={fadeUp} className="flex items-start gap-3">
                <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary-600" aria-hidden="true" />
                <div className="flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold text-slate-950">{metric}</span>
                    <span className="font-black text-primary-700">{improvement}</span>
                  </div>
                  <p className="mt-0.5 text-sm text-slate-500">{note}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Technology stack */}
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16">
          <motion.h2 variants={fadeUp} className="app-section-title mb-12 text-center">
            Technology Stack
          </motion.h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {STACK.map((s) => {
              const Icon = s.icon;
              return (
                <motion.div key={s.category} variants={fadeUp} className="app-card p-7">
                  <div className="mb-5 flex items-center gap-3">
                    <div className="app-icon-badge" aria-hidden="true"><Icon className="h-5 w-5" /></div>
                    <h3 className="app-card-title">{s.category}</h3>
                  </div>
                  <div className="space-y-3">
                    {s.items.map((item) => (
                      <div key={item.name} className="flex items-start gap-3">
                        <div className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary-500" aria-hidden="true" />
                        <div>
                          <p className="text-sm font-semibold text-slate-950">{item.name}</p>
                          <p className="text-xs text-slate-500">{item.note}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Team */}
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16">
          <motion.h2 variants={fadeUp} className="app-section-title mb-8 text-center">
            Project Leadership
          </motion.h2>
          <motion.div variants={fadeUp} className="mx-auto max-w-lg">
            <div className="app-card app-card-hover p-8 text-center">
              <div className="app-icon-badge-lg mx-auto mb-5" aria-hidden="true">
                <Cpu className="h-8 w-8" />
              </div>
              <h3 className="mb-1 text-xl font-black text-slate-950">Youssef Taha Badawi</h3>
              <p className="mb-4 font-semibold text-primary-700">Founder · AI Engineer · Systems Architect</p>
              <p className="mb-6 text-sm leading-relaxed text-slate-600">
                AI Engineer specialising in GenAI, LLM systems, and agentic architectures. Built CadArena
                end-to-end — from dataset curation and model training to the frontend product and DXF export pipeline.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {['Conversational CAD', 'LLM & RAG Systems', 'Diffusion Models', 'FastAPI', 'React'].map((tag) => (
                  <span key={tag} className="app-pill-muted py-1 text-xs">{tag}</span>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* CTA */}
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          className="mb-8 flex flex-col items-center gap-4 text-center">
          <h2 className="app-section-title">Ready to try it?</h2>
          <p className="app-section-copy max-w-xl">
            Open the Studio and describe your first floor plan in plain language.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/studio" className="app-button-primary">
              Launch Studio <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link to="/docs" className="app-button-secondary">
              Read the Docs
            </Link>
            <Link to="/developers" className="app-button-ghost">
              Meet the Builder
            </Link>
          </div>
        </motion.div>

      </div>
    </div>
  );
};

export default AboutPage;
