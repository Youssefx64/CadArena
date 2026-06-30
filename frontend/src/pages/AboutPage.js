import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Brain, Target, CheckCircle2, Layers, Cpu, Shield, MessageSquare, BookOpen, Zap
} from '../components/IconRegistry';
import AboutIllustration from '../components/illustrations/AboutIllustration';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.06, delayChildren: 0.02 } } };
const fadeUp  = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] } } };

export default function AboutPage() {
  useEffect(() => { document.title = 'About — CadArena'; }, []);

  const CORE_PRINCIPLES = [
    {
      icon: Shield,
      title: 'Secure by Default',
      desc: 'User sessions, auth tokens, and generated plans are stored in local SQLite databases. Session cookies are HTTP-only. No sensitive data is transmitted to third-party services.',
    },
    {
      icon: Cpu,
      title: 'Local-First AI Inference',
      desc: 'CadArena supports Ollama-hosted models (Llama, Qwen, Gemma), allowing engineers to run the full retrieval and generation pipeline entirely offline without external API calls.',
    },
    {
      icon: Target,
      title: 'Geometry Over Guesswork',
      desc: 'Spatial layout — topology scoring, corridor zoning, room origin placement — is computed by deterministic planners. LLMs handle intent extraction; they never generate raw coordinates.',
    },
    {
      icon: CheckCircle2,
      title: 'Compliance-Aware Output',
      desc: 'Every generated layout passes through an automated EBC validation gate that checks setbacks, corridor clearances, and egress widths against the Egyptian Building Code before export.',
    },
  ];

  const TIMELINE_STEPS = [
    { stage: 'Problem', title: 'The Coordinate Hallucination Problem', body: 'AI layout models that generate raw coordinates directly from LLM output produce physically impossible drawings. Walls overlap. Dimensions are wrong. The output cannot be used.' },
    { stage: 'Research', title: 'Building Code Formalisation', body: 'Egyptian Building Code regulations were formalised into computable rule sets: setback distances, corridor widths, egress clearances. CubiCasa5K dataset structures were analysed for spatial priors.' },
    { stage: 'Architecture', title: 'Dual-Engine Design', body: 'LLMs handle natural language parsing and design intent extraction. A separate deterministic spatial planner resolves room placement, topology scoring, and boundary constraints geometrically.' },
    { stage: 'Development', title: 'FastAPI + React Integration', body: 'FastAPI endpoints, Qdrant vector retrieval, ezdxf rendering, and the interactive React CAD canvas were built and integrated into a single cohesive workspace.' },
    { stage: 'Current', title: 'Integrated Engineering Workspace', body: 'CadArena is live with iterative floor plan prompting, visual compliance warnings, cProfile observability telemetry, and DXF / PNG / PDF export.' },
    { stage: 'Roadmap', title: 'WebSockets & 3D Visualisation', body: 'Planned: real-time co-authoring via WebSockets, Three.js 3D walkthrough rendering, DWG import support, and AI-assisted cost estimation from material catalogs.' },
  ];

  const TECH_STACK = [
    {
      category: 'Frontend Suite',
      items: [
        { name: 'React 18 & React Router 6', desc: 'SPA architecture with code-split lazy loading' },
        { name: 'Framer Motion 10', desc: 'Premium micro-interactions and modal transitions' },
        { name: 'Vanilla CSS System', desc: 'Curated dark/light variables and animations' }
      ]
    },
    {
      category: 'Backend Services',
      items: [
        { name: 'FastAPI & Uvicorn', desc: 'High-performance asynchronous API router' },
        { name: 'ezdxf Library', desc: 'Generates CAD-compatible drawing sheets' },
        { name: 'Pydantic v2', desc: 'Strict validation schemas for architectural payloads' }
      ]
    },
    {
      category: 'Cognitive & Vector Engines',
      items: [
        { name: 'Local Ollama & Cloud APIs', desc: 'Dynamic model switching for layout parsing' },
        { name: 'Qdrant Vector Store', desc: 'Embedded collection matching for regulatory RAG queries' },
        { name: 'PyMuPDF Parser', desc: 'In-memory text extraction for uploaded reference guides' }
      ]
    },
    {
      category: 'Infrastructure & Data',
      items: [
        { name: 'SQLite Persistence', desc: 'Isolates project directories and message threads' },
        { name: 'JWT Secure Cookie Auth', desc: 'Stateless session authentication for user profiles' },
        { name: 'Docker Orchestration', desc: 'Multi-container setups for backend and RAG services' }
      ]
    }
  ];

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
                  <Brain className="h-3.5 w-3.5" aria-hidden="true" />
                  Platform Overview
                </span>
              </motion.div>
              
              <motion.h1 variants={fadeUp} className="app-hero-title leading-tight text-4xl sm:text-5xl lg:text-6xl font-black mb-6">
                Engineering-grade AI
                <br />
                <span className="gradient-text-animated">for architectural design</span>
              </motion.h1>

              <motion.p variants={fadeUp} className="app-page-copy mx-auto lg:mx-0 mb-10 max-w-2xl text-slate-500 dark:text-slate-400">
                CadArena combines conversational AI with a deterministic spatial planner to produce
                structurally valid floor plans — not approximations. Design intent goes in; compliant DXF comes out.
              </motion.p>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="lg:col-span-5 flex justify-center w-full"
            >
              <AboutIllustration />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ═══ PLATFORM OVERVIEW (ARCHCHAT vs CADSTUDIO) ═══════════════════════ */}
      <section className="app-shell mb-20 relative z-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* ArchChat Card */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="app-card border border-slate-200/60 dark:border-white/5 p-8 flex flex-col hover:shadow-medium"
          >
            <div className="app-icon-badge mb-6" aria-hidden="true">
              <MessageSquare className="h-6 w-6 text-violet-600 dark:text-violet-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-3">
              ArchChat
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed flex-1 mb-6">
              A conversational AI interface backed by Qdrant vector retrieval. Upload PDF or CSV reference
              documents and query them with natural language. Responses include inline citations that
              deep-link to the relevant passage in the source document.
            </p>
            <div className="flex gap-2 flex-wrap">
              {['Qdrant RAG', 'PDF Ingestion', 'Citation Links', 'Multi-turn Context'].map((t) => (
                <span key={t} className="text-[10px] font-bold bg-slate-100 dark:bg-white/5 border border-slate-200/50 dark:border-white/5 px-2 py-0.5 rounded text-slate-500 dark:text-slate-400">
                  {t}
                </span>
              ))}
            </div>
          </motion.div>

          {/* CadStudio Card */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="app-card border border-slate-200/60 dark:border-white/5 p-8 flex flex-col hover:shadow-medium"
          >
            <div className="app-icon-badge mb-6" aria-hidden="true">
              <Layers className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-3">
              CadStudio
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed flex-1 mb-6">
              A DXF generation workspace. Accepts natural language design parameters, computes room
              placement and boundary constraints with a deterministic spatial planner, and renders
              the result on an interactive multi-layer canvas. Exports to DXF, PNG, and PDF.
            </p>
            <div className="flex gap-2 flex-wrap">
              {['Deterministic Planner', 'EBC Validation', 'ezdxf Export', 'Layer Controls'].map((t) => (
                <span key={t} className="text-[10px] font-bold bg-slate-100 dark:bg-white/5 border border-slate-200/50 dark:border-white/5 px-2 py-0.5 rounded text-slate-500 dark:text-slate-400">
                  {t}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ═══ PRODUCT JOURNEY TIMELINE ═══════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-label="Project story timeline">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">Development History</p>
          <h2 className="app-section-title mb-4">How it was built</h2>
          <p className="app-section-copy mx-auto max-w-xl">
            From problem definition through architecture decisions to a deployed engineering workspace.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative">
          {TIMELINE_STEPS.map((step, idx) => (
            <div 
              key={idx}
              className="app-card border border-slate-100 dark:border-white/5 p-6 rounded-2xl flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4 border-b border-slate-100 dark:border-white/5 pb-3">
                  <span className="text-[10px] font-black uppercase text-primary-600 dark:text-violet-400 tracking-wider">
                    {step.stage}
                  </span>
                  <span className="text-xs font-bold text-slate-400">
                    Step {String(idx + 1).padStart(2, '0')}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-2">
                  {step.title}
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  {step.body}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ CORE PRINCIPLES ════════════════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-labelledby="principles-heading">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">Engineering Philosophy</p>
          <h2 id="principles-heading" className="app-section-title mb-4">Design Decisions</h2>
          <p className="app-section-copy mx-auto max-w-xl">
            Every architectural decision in CadArena is a consequence of one constraint: produced drawings must be geometrically correct and code-compliant.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {CORE_PRINCIPLES.map((pr, idx) => {
            const Icon = pr.icon;
            return (
              <div 
                key={idx}
                className="app-card border border-slate-100 dark:border-white/5 p-6 rounded-2xl flex items-start gap-4"
              >
                <div className="app-icon-badge flex-shrink-0" aria-hidden="true">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-2">
                    {pr.title}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    {pr.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ═══ ARCHITECTURE DIAGRAM ═══════════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-labelledby="arch-heading">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">System Architecture</p>
          <h2 id="arch-heading" className="app-section-title mb-4">Component Map</h2>
          <p className="app-section-copy mx-auto max-w-xl">
            A high-level view of how the FastAPI gateway, retrieval engine, spatial planner, and rendering pipeline are connected.
          </p>
        </div>

        <div className="max-w-3xl mx-auto border border-slate-850 bg-slate-950 p-6 rounded-3xl font-mono text-xs text-slate-300 overflow-x-auto shadow-medium">
          <div className="border-b border-slate-800 pb-3 mb-4 flex items-center gap-1.5" aria-hidden="true">
            <span className="h-3 w-3 rounded-full bg-red-500/70" />
            <span className="h-3 w-3 rounded-full bg-yellow-500/70" />
            <span className="h-3 w-3 rounded-full bg-green-500/70" />
            <span className="ml-2 text-[10px] text-slate-500">cadarena_system_tree</span>
          </div>
          <pre className="leading-relaxed">
{`CadArena (FastAPI Gateway)
├── ArchChat (AI + RAG Controller)
│   ├── RAG Engine
│   │   ├── Vector Store (Local Qdrant Collection)
│   │   └── Document Loader (PDF / CSV / JSON Text Parser)
│   ├── Conversational Storage (SQLite Memory)
│   └── AI reasoner (Inference router to Ollama/Cohere/OpenAI)
│
└── CadStudio (DXF Generation Studio)
    ├── Deterministic spatial Planner
    │   ├── Boundary setbacks solver
    │   └── Corridor & openings zoning
    ├── Compliance Gate (EBC 2023 Ruleset Validator)
    ├── ezdxf Canvas Rendering Pipeline
    └── Export Exporter (DXF / PNG / PDF plots)`}
          </pre>
        </div>
      </section>

      {/* ═══ DYNAMIC TECH STACK ═════════════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-labelledby="tech-heading">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">Implementation</p>
          <h2 id="tech-heading" className="app-section-title mb-4">Technology Stack</h2>
          <p className="app-section-copy mx-auto max-w-xl">
            Every library and framework listed here is actively used in the production codebase. Nothing is aspirational.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {TECH_STACK.map((group, idx) => (
            <div 
              key={idx}
              className="app-card border border-slate-100 dark:border-white/5 p-6 rounded-2xl flex flex-col justify-between"
            >
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 dark:border-white/5 pb-2 mb-4">
                  {group.category}
                </h4>
                <div className="space-y-4">
                  {group.items.map((item, idy) => (
                    <div key={idy}>
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200 block">
                        {item.name}
                      </span>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed block mt-0.5">
                        {item.desc}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ CTA SECTION ════════════════════════════════════════════════════ */}
      <section className="app-shell" aria-label="Get started CTA">
        <div className="app-cta-panel relative overflow-hidden px-8 py-16 text-center sm:px-14 sm:py-20 rounded-3xl">
          <div className="pointer-events-none absolute inset-0" aria-hidden="true">
            <div className="absolute -left-20 -top-20 h-80 w-80 bg-white opacity-[0.05] blur-3xl" />
            <div className="absolute -bottom-20 -right-20 h-80 w-80 bg-white opacity-[0.05] blur-3xl" />
          </div>

          <h2 className="mb-4 text-2xl font-black text-white">
            Start working with the platform
          </h2>
          <p className="mx-auto mb-10 max-w-lg text-sm text-primary-100">
            Generate a DXF floor plan, query the Egyptian Building Code with ArchChat,
            or read the full system documentation — no installation required.
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
            <Link to="/features" className="app-button-ghost text-white">
              Explore Features
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
