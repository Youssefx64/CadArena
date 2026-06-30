import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Brain, Target, Code as Code2, GitHub as Github, LinkedIn as Linkedin, Mail,
  Cpu, Layers, Shield, Compass, CheckCircle2, Sliders,
  X as Twitter, Globe
} from '../components/IconRegistry';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.02 } } };
const fadeUp  = { hidden: { y: 15, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } } };

export default function DevelopersPage() {
  useEffect(() => { document.title = 'Developers — CadArena'; }, []);

  const EXPERTISE = [
    { icon: Brain, title: 'Large Language Models', body: 'Designing prompt schemas, intent extraction parsers, and multi-turn context management for architectural generation tasks.' },
    { icon: Cpu, title: 'Retrieval-Augmented Generation', body: 'Configuring Qdrant vector collections, document chunking pipelines, and similarity search for regulatory retrieval.' },
    { icon: Target, title: 'CAD & DXF Automation', body: 'Converting spatial planning outputs to structured multi-layer DXF drawings via ezdxf with geometric precision.' },
    { icon: Code2, title: 'Backend Engineering', body: 'Building async FastAPI endpoints, HTTP-only JWT authentication, and background worker lifecycle management.' },
    { icon: Layers, title: 'Frontend Systems', body: 'Developing interactive canvas viewports, coordinate-aware SVG layers, and Framer Motion transitions.' },
    { icon: Shield, title: 'Offline AI Infrastructure', body: 'Deploying Ollama model nodes for local inference, enabling full generation pipelines without external API dependencies.' }
  ];

  const SKILLS = [
    { category: 'Programming Languages', items: ['Python', 'JavaScript (ES6+)', 'SQL', 'HTML5 & CSS3'] },
    { category: 'AI & ML Frameworks', items: ['LangChain', 'HuggingFace Diffusers', 'PyTorch 2.0+', 'Ollama Integration'] },
    { category: 'Backend Suite', items: ['FastAPI', 'Uvicorn', 'Pydantic v2', 'SQLAlchemy ORM'] },
    { category: 'Frontend Stack', items: ['React 18', 'TailwindCSS 3.3', 'Framer Motion 10', 'Recharts'] },
    { category: 'Databases & Vectors', items: ['SQLite (Persistence)', 'Qdrant (Vector Collections)', 'PostgreSQL'] },
    { category: 'CAD & Render Tools', items: ['ezdxf drawing database', 'Matplotlib (raster export)', 'SVG rendering layer'] }
  ];

  const JOURNEY = [
    { phase: 'Phase 1', title: 'Problem Definition', date: 'Idea Validation', desc: 'Identified that LLM-generated coordinates produce geometrically invalid drawings. Defined the need for a deterministic layout layer separate from the AI reasoning layer.' },
    { phase: 'Phase 2', title: 'Code Formalisation', date: 'Building Regulations', desc: 'Egyptian Building Code setback rules, corridor widths, and egress requirements were encoded as computable constraint formulas.' },
    { phase: 'Phase 3', title: 'Dual-Engine Architecture', date: 'System Design', desc: 'Designed the core split: LLM handles intent parsing, deterministic planner handles spatial computation and room placement.' },
    { phase: 'Phase 4', title: 'RAG Integration', date: 'Knowledge Retrieval', desc: 'Configured Qdrant vector collections with Egyptian Building Code documents for real-time compliance context injection.' },
    { phase: 'Phase 5', title: 'DXF Rendering Pipeline', date: 'CAD Output', desc: 'Implemented ezdxf room loop generators, layer management, and annotation systems for AutoCAD-compatible output.' },
    { phase: 'Phase 6', title: 'Platform Release', date: 'React App', desc: 'Shipped user authentication, SQLite workspaces, resizable canvas panels, and the full public release.' }
  ];

  const PRINCIPLES = [
    { title: 'Secure by Default', desc: 'User history, message logs, and uploaded documents remain isolated in local data stores. No sensitive data leaves the deployment environment.' },
    { title: 'Offline-First AI', desc: 'The generation pipeline runs on locally hosted Ollama models. Cloud API calls are optional, not required.' },
    { title: 'Deterministic Geometry', desc: 'Spatial coordinates are computed by constraint solvers, not sampled from language model distributions.' },
    { title: 'Engineer-Centred Design', desc: 'Every interface decision is evaluated against whether it reduces friction for working architects and structural engineers.' }
  ];

  return (
    <div className="min-h-screen relative pb-16 pt-10">
      
      {/* ═══ HERO SECTION ════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24">
        <div className="hero-grid-pattern" aria-hidden="true" />
        <div className="app-shell relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center max-w-5xl mx-auto">
            
            {/* Avatar / Portrait Placeholder */}
            <div className="lg:col-span-4 flex justify-center">
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.45 }}
                className="relative group cursor-pointer"
              >
                <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500 opacity-20 group-hover:opacity-30 blur transition" />
                <div className="relative h-44 w-44 rounded-full bg-white dark:bg-zinc-900 border border-slate-200 dark:border-white/10 flex items-center justify-center shadow-lg overflow-hidden">
                  <img 
                    src="/youssef_pic.png" 
                    alt="Youssef Taha"
                    className="h-full w-full object-cover"
                    onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextSibling.style.display = 'flex'; }}
                  />
                  <div 
                    style={{ display: 'none' }}
                    className="h-full w-full items-center justify-center bg-gradient-to-tr from-primary-600 to-indigo-600 text-white text-5xl font-black"
                  >
                    YT
                  </div>
                </div>
              </motion.div>
            </div>

            {/* Profile Intro Info */}
            <div className="lg:col-span-8 text-center lg:text-left space-y-5">
              <motion.div initial="hidden" animate="visible" variants={stagger}>
                <motion.span variants={fadeUp} className="app-pill inline-flex mb-3">
                  <Sliders className="h-3.5 w-3.5" aria-hidden="true" />
                  Creator Profile
                </motion.span>
                <motion.h1 variants={fadeUp} className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-900 dark:text-slate-50 tracking-tight leading-none mb-2">
                  Youssef Taha
                </motion.h1>
                <motion.p variants={fadeUp} className="text-sm font-bold text-primary-600 dark:text-violet-400">
                  AI Engineer & Founder of CadArena
                </motion.p>
                <motion.p variants={fadeUp} className="app-body text-xs text-slate-500 dark:text-slate-400 max-w-xl mt-4 leading-relaxed">
                  AI Engineer specialising in LLM systems, retrieval-augmented generation, and AI-assisted CAD automation. Built CadArena from the ground up — from EBC rule formalisation and Qdrant collection design through to the React canvas and DXF export pipeline.
                </motion.p>
                <motion.div variants={fadeUp} className="pt-4 flex flex-wrap justify-center lg:justify-start gap-2.5">
                  <a href="#contact" className="app-button-primary app-button-compact text-xs">
                    Get in touch
                  </a>
                  <a 
                    href="https://github.com/Youssefx64/CadArena" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="app-button-secondary app-button-compact text-xs flex items-center gap-1.5"
                  >
                    <Github className="h-3.5 w-3.5" />
                    <span>View Repository</span>
                  </a>
                </motion.div>
              </motion.div>
            </div>

          </div>
        </div>
      </section>

      {/* ═══ ENGINEERING PHILOSOPHY ABOUT SECTION ═══════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-label="About the founder">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start max-w-5xl mx-auto">
          <div className="lg:col-span-4">
            <p className="app-eyebrow mb-2">Engineering Position</p>
            <h2 className="text-xl font-black text-slate-950 dark:text-slate-50">
              On building AI for engineers
            </h2>
          </div>
          <div className="lg:col-span-8 space-y-4 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            <p>
              Generative models should solve concrete, computable problems — not produce artistic approximations. In structural engineering, layout coordinates require precision, physical alignment, and standards compliance. Generic AI models that generate coordinates directly from language model outputs produce drawings that fail in CAD editors.
            </p>
            <p>
              CadArena was built around a different approach: LLMs extract intent, deterministic planners resolve geometry. Egyptian Building Code rules are encoded directly into Qdrant vector collections and evaluated against every generated layout before export. The result is an AI output that is physically valid, editable, and immediately usable.
            </p>
          </div>
        </div>
      </section>

      {/* ═══ AREAS OF EXPERWISE ═════════════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-labelledby="expertise-heading">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">Capabilities</p>
          <h2 id="expertise-heading" className="app-section-title mb-4">Areas of Expertise</h2>
          <p className="app-section-copy mx-auto max-w-xl">
            Key fields of research and system design validated within the CadArena platform.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {EXPERTISE.map((exp, idx) => {
            const Icon = exp.icon;
            return (
              <div 
                key={idx}
                className="app-card border border-slate-150 dark:border-white/5 p-6 rounded-2xl flex flex-col justify-between hover:shadow-soft"
              >
                <div>
                  <div className="app-icon-badge mb-4" aria-hidden="true">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 mb-2">
                    {exp.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                    {exp.body}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ═══ TECHNICAL SKILLS LISTING ═══════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-labelledby="skills-heading">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">Skills</p>
          <h2 id="skills-heading" className="app-section-title mb-4">Technical Stack</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {SKILLS.map((skill, idx) => (
            <div 
              key={idx}
              className="app-card border border-slate-100 dark:border-white/5 p-6 rounded-2xl bg-white/50 dark:bg-zinc-900/40"
            >
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 dark:border-white/5 pb-2 mb-4">
                {skill.category}
              </h4>
              <ul className="space-y-2.5">
                {skill.items.map((item, idy) => (
                  <li key={idy} className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="h-4 w-4 text-primary-500 flex-shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ CADARENA JOURNEY TIMELINE ══════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-labelledby="journey-heading">
        <div className="text-center mb-16">
          <p className="app-eyebrow mb-3">Milestones</p>
          <h2 id="journey-heading" className="app-section-title mb-4">CadArena Journey</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {JOURNEY.map((step, idx) => (
            <div 
              key={idx}
              className="app-card border border-slate-150 dark:border-white/5 p-6 rounded-2xl flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4 border-b border-slate-100 dark:border-white/5 pb-3">
                  <span className="text-[10px] font-black text-primary-600 uppercase tracking-wider">
                    {step.phase}
                  </span>
                  <span className="text-[10px] font-bold text-slate-400">
                    {step.date}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2">
                  {step.title}
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ CURRENT FOCUS & ENGINEERING PRINCIPLES ════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          
          {/* Current Focus */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Compass className="h-4 w-4 text-slate-400" />
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                Active Projects &amp; Focus
              </h3>
            </div>
            <div className="app-card border border-slate-150 dark:border-white/5 p-6 bg-white/60 dark:bg-zinc-900/60 space-y-4">
              {[
                { title: 'Conversational CAD Intent', detail: 'Designing parsers to extract door spacing, opening metrics, and boundary setbacks from natural dialogue.' },
                { title: 'RAG Performance Auditing', desc: 'Optimizing collections embedding similarity queries inside Qdrant databases for Egyptian Building Code retrievals.' },
                { title: 'Local Agent Failovers', desc: 'Configuring multi-agent failover checks inside routers to switch to local Ollama nodes when API limits are reached.' }
              ].map((focus, idx) => (
                <div key={idx} className="text-xs">
                  <span className="font-bold text-slate-850 dark:text-slate-250 block mb-1">
                    {focus.title}
                  </span>
                  <span className="text-[11px] text-slate-500 leading-normal block">
                    {focus.detail || focus.desc}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Engineering Principles */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-slate-400" />
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                Engineering Principles
              </h3>
            </div>
            <div className="app-card border border-slate-150 dark:border-white/5 p-6 bg-white/60 dark:bg-zinc-900/60 space-y-4">
              {PRINCIPLES.map((pr, idx) => (
                <div key={idx} className="text-xs">
                  <span className="font-bold text-slate-850 dark:text-slate-250 block mb-1">
                    {pr.title}
                  </span>
                  <span className="text-[11px] text-slate-500 leading-normal block">
                    {pr.desc}
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </section>

      {/* ═══ FEATURED PROJECT (CADARENA) ═══════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-labelledby="featured-heading">
        <div className="text-center mb-12">
          <p className="app-eyebrow mb-3">Project Highlight</p>
          <h2 id="featured-heading" className="app-section-title mb-4">Featured Work: CadArena</h2>
        </div>

        <div className="app-card max-w-4xl mx-auto border border-slate-200/70 dark:border-white/5 p-8 rounded-3xl bg-white/40 dark:bg-zinc-900/40">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-7 space-y-4 text-xs">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Conversational CAD &amp; Compliance Verification
              </h3>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
                CadArena is a full-stack architectural engineering platform. It processes natural language design parameters through a conversational interface, computes spatial layouts with a deterministic planner, validates dimensions against the Egyptian Building Code, and exports compliant DXF drawings.
              </p>
              <div className="space-y-2 border-t border-slate-100 dark:border-white/5 pt-4">
                <p className="font-bold text-slate-700 dark:text-slate-300">Core Capabilities:</p>
                <ul className="list-disc pl-4 space-y-1 text-slate-500 dark:text-slate-400">
                  <li>Natural language intent parsing into structured layout parameters</li>
                  <li>Qdrant vector retrieval for Egyptian Building Code compliance context</li>
                  <li>Multi-layer interactive SVG canvas with pan and zoom</li>
                  <li>DXF, PNG, and PDF export from a single generation pipeline</li>
                </ul>
              </div>
            </div>

            <div className="lg:col-span-5 space-y-4">
              <div className="app-card-muted p-5 rounded-2xl text-xs space-y-3">
                <div>
                  <span className="text-[10px] text-slate-400 block font-bold uppercase">Status</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">1.0.0 Stable · Active development</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-bold uppercase">AI Pipeline</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">Ollama local / Cloud API Router</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-bold uppercase">Persistence</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">SQLite + HTTP-only JWT Sessions</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Link to="/studio" className="app-button-primary app-button-compact text-center text-[11px]">
                  Open CAD Studio
                </Link>
                <Link to="/rag-chat" className="app-button-secondary app-button-compact text-center text-[11px]">
                  Open ArchChat
                </Link>
                <Link to="/features" className="app-button-ghost text-center text-[11px]">
                  Explore Features
                </Link>
                <Link to="/docs" className="app-button-ghost text-center text-[11px]">
                  Read System Docs
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ PERSONAL VISION SECTION ════════════════════════════════════════ */}
      <section className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 mb-20" aria-label="Personal Vision">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          <p className="app-eyebrow">Personal Vision</p>
          <h3 className="text-xl md:text-2xl font-black text-slate-900 dark:text-slate-50 tracking-tight max-w-xl mx-auto">
            Treating physical blueprints as structured, computable data
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed max-w-2xl mx-auto">
            The long-term goal is to enable engineers and architects to describe a building in plain language and receive a geometrically valid, code-compliant drawing in return. Not a draft. Not an approximation. A file they can open in AutoCAD and hand to a contractor.
          </p>
        </div>
      </section>

      {/* ═══ CONTACT SECTION ════════════════════════════════════════════════ */}
      <section id="contact" className="app-shell border-t border-slate-100 dark:border-white/5 pt-16 max-w-4xl mx-auto">
        <div className="text-center mb-10">
          <p className="app-eyebrow mb-2">Connect</p>
          <h2 className="text-lg font-black text-slate-900 dark:text-slate-150">Get In Touch</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
          
          {/* GitHub Link */}
          <a 
            href="https://github.com/Youssefx64" 
            target="_blank" 
            rel="noopener noreferrer"
            className="app-card border border-slate-150 dark:border-white/5 p-6 text-center hover:border-primary-500 transition-colors block group"
          >
            <Github className="h-6 w-6 mx-auto text-slate-500 dark:text-slate-400 group-hover:text-primary-600 mb-3" />
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">GitHub</h4>
            <p className="text-[9px] text-slate-400 mt-1">@Youssefx64</p>
          </a>

          {/* LinkedIn Link */}
          <a 
            href="https://www.linkedin.com/in/yousseftahaai" 
            target="_blank" 
            rel="noopener noreferrer"
            className="app-card border border-slate-150 dark:border-white/5 p-6 text-center hover:border-primary-500 transition-colors block group"
          >
            <Linkedin className="h-6 w-6 mx-auto text-slate-500 dark:text-slate-400 group-hover:text-primary-600 mb-3" />
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">LinkedIn</h4>
            <p className="text-[9px] text-slate-400 mt-1">@yousseftahaai</p>
          </a>

          {/* X (Twitter) Link */}
          <a 
            href="https://x.com/Youssefx64" 
            target="_blank" 
            rel="noopener noreferrer"
            className="app-card border border-slate-150 dark:border-white/5 p-6 text-center hover:border-primary-500 transition-colors block group"
          >
            <Twitter className="h-6 w-6 mx-auto text-slate-500 dark:text-slate-400 group-hover:text-primary-600 mb-3" />
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">X (Twitter)</h4>
            <p className="text-[9px] text-slate-400 mt-1">@Youssefx64</p>
          </a>

          {/* Portfolio Link */}
          <a 
            href="https://personal-portfolio--yousseftaha11.replit.app/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="app-card border border-slate-150 dark:border-white/5 p-6 text-center hover:border-primary-500 transition-colors block group"
          >
            <Globe className="h-6 w-6 mx-auto text-slate-500 dark:text-slate-400 group-hover:text-primary-600 mb-3" />
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Portfolio</h4>
            <p className="text-[9px] text-slate-400 mt-1">Visit site</p>
          </a>

          {/* Email Link */}
          <a 
            href="mailto:cadarena.ai@gmail.com" 
            className="app-card border border-slate-150 dark:border-white/5 p-6 text-center hover:border-primary-500 transition-colors block group"
          >
            <Mail className="h-6 w-6 mx-auto text-slate-500 dark:text-slate-400 group-hover:text-primary-600 mb-3" />
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Email</h4>
            <p className="text-[9px] text-slate-400 mt-1">cadarena.ai</p>
          </a>

        </div>
      </section>

    </div>
  );
}
