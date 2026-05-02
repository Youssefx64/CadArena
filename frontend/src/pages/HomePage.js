import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRight, Zap, Brain, BarChart3, Sparkles, CheckCircle,
  Download, Edit3, ChevronRight, MessageSquare,
} from 'lucide-react';

const PROMPT_EXAMPLES = [
  '3-bedroom apartment with open kitchen and living room',
  'Studio flat with dedicated home office and ensuite',
  '2-bedroom family home with south-facing master bedroom',
  'Corner penthouse with panoramic windows and open plan',
];

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.09 } } };
const fadeUp  = { hidden: { y: 28, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } } };
const fadeIn  = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { duration: 0.45 } } };

// ─── Animated blueprint preview ───────────────────────────────────────────────
function BlueprintPreview() {
  const rooms = [
    { id: 'living', label: 'Living Room', x: '8%',  y: '8%',  w: '52%', h: '36%', accent: true },
    { id: 'kitchen',label: 'Kitchen',     x: '64%', y: '8%',  w: '28%', h: '22%' },
    { id: 'dining', label: 'Dining',      x: '64%', y: '34%', w: '28%', h: '10%' },
    { id: 'master', label: 'Master Bed',  x: '8%',  y: '50%', w: '36%', h: '34%', accent: true },
    { id: 'bed2',   label: 'Bedroom 2',   x: '48%', y: '50%', w: '26%', h: '34%' },
    { id: 'bath',   label: 'Bath',        x: '78%', y: '50%', w: '14%', h: '20%' },
    { id: 'hall',   label: '',            x: '48%', y: '44%', w: '44%', h: '6%',  muted: true },
  ];
  return (
    <div
      className="relative w-full overflow-hidden"
      style={{ aspectRatio: '16/9', background: 'var(--surface-2)', borderRadius: 14 }}
      aria-label="Animated floor plan preview" role="img"
    >
      <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(var(--line-soft) 1px,transparent 1px),linear-gradient(90deg,var(--line-soft) 1px,transparent 1px)', backgroundSize: '24px 24px', opacity: 0.9 }} />
      {rooms.map((r, i) => (
        <motion.div key={r.id}
          initial={{ opacity: 0, scale: 0.88 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.22 + i * 0.1, duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
          style={{
            position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, borderRadius: 8,
            border: r.muted
              ? '1px dashed var(--line-soft)'
              : r.accent
                ? '1.5px solid rgba(59,130,246,0.45)'
                : '1.5px solid var(--line-strong)',
            background: r.muted
              ? 'transparent'
              : r.accent
                ? 'rgba(239,246,255,0.55)'
                : 'var(--surface-1)',
            boxShadow: r.accent ? '0 2px 12px rgba(59,130,246,0.1),inset 0 1px 0 rgba(255,255,255,0.5)' : 'inset 0 1px 0 rgba(255,255,255,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
          {r.label && (
            <span style={{ fontSize: 'clamp(0.55rem,1vw,0.72rem)', fontWeight: 700, color: r.accent ? '#1d4ed8' : 'var(--text-muted)', letterSpacing: '0.02em', textAlign: 'center', padding: '0 4px', userSelect: 'none' }}>
              {r.label}
            </span>
          )}
        </motion.div>
      ))}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2, duration: 0.4 }}
        style={{ position: 'absolute', bottom: '6%', right: '2%', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
        <span style={{ fontSize: '0.6rem', fontWeight: 800, color: '#3b82f6', letterSpacing: '0.12em', textTransform: 'uppercase' }}>EBC 2023 Compliant</span>
        <span style={{ fontSize: '0.6rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>DXF Export Ready ✓</span>
      </motion.div>
      <motion.div initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 1.4, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 3, background: 'linear-gradient(90deg,#3b82f6,#7c3aed)', transformOrigin: 'left center', borderBottomLeftRadius: 14, borderBottomRightRadius: 14 }} />
    </div>
  );
}

// ─── Hero prompt input bar ────────────────────────────────────────────────────
function HeroPromptBar({ onDark = false }) {
  const navigate = useNavigate();
  const [value, setValue] = useState('');
  const [phIdx, setPhIdx] = useState(0);

  useEffect(() => {
    if (value) return;
    const id = setInterval(() => setPhIdx((i) => (i + 1) % PROMPT_EXAMPLES.length), 3700);
    return () => clearInterval(id);
  }, [value]);

  const submit = (e) => {
    e.preventDefault();
    navigate('/studio');
  };

  return (
    <form onSubmit={submit} className={`hero-prompt-bar${onDark ? ' hero-prompt-bar-dark' : ''}`}>
      <Edit3 className="h-5 w-5 flex-shrink-0 text-slate-400 dark:text-slate-500" aria-hidden="true" />
      <div className="relative flex min-w-0 flex-1 items-center">
        <AnimatePresence mode="wait">
          {!value && (
            <motion.span key={phIdx}
              initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.24 }}
              className="pointer-events-none absolute inset-y-0 left-0 flex items-center truncate pr-2 text-sm text-slate-400 dark:text-slate-500 sm:text-[0.9375rem]"
              aria-hidden="true">
              {PROMPT_EXAMPLES[phIdx]}
            </motion.span>
          )}
        </AnimatePresence>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder=""
          aria-label="Describe your floor plan"
          className="hero-prompt-input dark:bg-transparent dark:text-slate-100"
        />
      </div>
      <motion.button type="submit" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
        className="app-button-primary app-button-compact flex-shrink-0">
        <Sparkles className="h-4 w-4" aria-hidden="true" />
        <span className="hidden sm:inline">Generate</span>
        <span className="sm:hidden"><ArrowRight className="h-4 w-4" /></span>
      </motion.button>
    </form>
  );
}

// ─── Page data ────────────────────────────────────────────────────────────────
const HOW_IT_WORKS = [
  { step: '01', icon: Edit3, title: 'Describe your space', body: 'Write your requirements in natural language — room count, style, adjacencies, or specific constraints. No CAD knowledge needed.' },
  { step: '02', icon: Brain, title: 'AI generates the plan', body: 'An LLM-based generation pipeline interprets your description and produces a structured, EBC 2023-compliant floor plan with labelled rooms and spatial relationships.' },
  { step: '03', icon: Download, title: 'Export and refine', body: 'Download a DXF file ready for AutoCAD or Revit, or continue iterating inside the full CadArena Studio workspace.' },
];

const FEATURES = [
  { icon: Brain, title: 'AI-Powered Generation', body: 'An LLM-based pipeline converts your natural language description into a structured, EBC-compliant floor plan with labelled rooms and correct spatial adjacencies.' },
  { icon: Zap, title: 'Constraint-Aware Design', body: 'Automatically enforces spatial consistency, structural adjacencies, and flow relationships — so you don\'t have to.' },
  { icon: BarChart3, title: 'Structured Output', body: 'Every generated plan includes labelled rooms, spatial adjacency relationships, and EBC 2023 compliance — structured for real architectural use.' },
  { icon: Download, title: 'DXF Export', body: 'Every generated plan exports as a CAD-compatible DXF file, ready to open in AutoCAD, Revit, or any DXF-compatible tool.' },
];

const TRUST_ITEMS = [
  { value: 'Prompt → DXF', label: 'Core Workflow' },
  { value: 'EBC 2023',     label: 'Compliant' },
  { value: 'DXF',          label: 'Export-Ready' },
  { value: 'AR + EN',      label: 'Language Support' },
  { value: '12+ Layers',   label: 'CAD Output' },
];

const DEMO_PROMPTS = [
  '3-bedroom apartment with open kitchen and living room',
  'Studio flat with dedicated home office and ensuite',
  '2-bedroom family home with south-facing master suite',
  'Corner penthouse with panoramic windows and open plan',
];

// ─── Main component ───────────────────────────────────────────────────────────
const HomePage = () => {
  const [demoIdx, setDemoIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setDemoIdx((i) => (i + 1) % DEMO_PROMPTS.length), 4200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="min-h-screen">

      {/* ═══ HERO ══════════════════════════════════════════════════════════════ */}
      <section className="relative overflow-hidden pb-20 pt-28 sm:pb-32 sm:pt-40">
        {/* Ambient orb background */}
        <div className="hero-ambient-bg" aria-hidden="true">
          <div className="hero-orb hero-orb-1" />
          <div className="hero-orb hero-orb-2" />
          <div className="hero-orb hero-orb-3" />
        </div>
        <div className="hero-grid-pattern" aria-hidden="true" />

        <div className="app-shell relative z-10">
          <motion.div initial="hidden" animate="visible" variants={stagger} className="text-center">

            <motion.div variants={fadeUp} className="mb-8 flex justify-center">
              <motion.span className="app-pill" whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                AI-Powered Architecture · Live Demo Available
              </motion.span>
            </motion.div>

            <motion.h1 variants={fadeUp} className="app-hero-title mb-6 mx-auto max-w-5xl">
              Design floor plans
              <br />
              <span className="gradient-text-animated">with natural language</span>
            </motion.h1>

            <motion.p variants={fadeUp} className="app-page-copy mx-auto mb-10">
              Describe your space and get a precise, constraint-aware floor plan —
              EBC 2023-compliant and DXF-ready — straight from the Studio.
            </motion.p>

            <motion.div variants={fadeUp} className="mb-7 flex w-full justify-center">
              <HeroPromptBar />
            </motion.div>

            <motion.div variants={fadeUp} className="mb-10 flex flex-wrap items-center justify-center gap-2">
              <span className="text-xs font-medium text-slate-400 dark:text-slate-600">Try:</span>
              {['3-bedroom apartment', 'Studio flat', 'Family home'].map((hint) => (
                <ExampleChip key={hint} label={hint} />
              ))}
            </motion.div>

            {/* ── Blueprint preview card ── */}
            <motion.div
              variants={fadeUp}
              className="hero-preview-wrap"
            >
              <div className="app-card app-card-strong mx-auto max-w-4xl p-5 sm:p-7">
                <div className="mb-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2.5">
                    <div className="flex gap-1.5" aria-hidden="true">
                      <div className="h-3 w-3 rounded-full bg-red-400" />
                      <div className="h-3 w-3 rounded-full bg-yellow-400" />
                      <div className="h-3 w-3 rounded-full bg-green-400" />
                    </div>
                    <span className="hidden text-xs font-semibold text-slate-400 dark:text-slate-500 sm:block">CadArena Studio</span>
                  </div>
                  <div className="flex items-center gap-2 rounded-full border border-primary-100 bg-primary-50 px-3 py-1.5 text-xs font-semibold text-primary-700 dark:border-violet-900/40 dark:bg-violet-950/30 dark:text-violet-300">
                    <span className="glow-dot h-1.5 w-1.5 rounded-full bg-primary-500 dark:bg-violet-400" aria-hidden="true" />
                    Live Preview
                  </div>
                </div>
                <div className="app-card-muted rounded-xl p-3 text-left">
                  <div className="mb-2 flex items-center gap-2 font-mono text-xs text-slate-500 dark:text-slate-400">
                    <span className="font-bold text-primary-600 dark:text-violet-400">›</span>
                    <span>&quot;3-bedroom apartment with open kitchen and living room&quot;</span>
                  </div>
                  <BlueprintPreview />
                </div>
              </div>
            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ═══ TRUST STRIP ══════════════════════════════════════════════════════ */}
      <div className="landing-trust-strip border-y border-slate-100 py-5 dark:border-white/6" aria-label="Key capabilities">
        <div className="app-shell">
          <motion.ul
            initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
            className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 sm:gap-x-10 lg:gap-x-14">
            {TRUST_ITEMS.map(({ value, label }, i) => (
              <motion.li key={label} variants={fadeIn} className="flex items-center gap-3">
                <div>
                  <p className="text-sm font-black tracking-tight text-slate-950 dark:text-slate-50 leading-none">{value}</p>
                  <p className="mt-0.5 text-xs font-semibold text-slate-500 dark:text-slate-500">{label}</p>
                </div>
                {i < TRUST_ITEMS.length - 1 && (
                  <div className="ml-4 hidden h-6 w-px bg-slate-200 dark:bg-white/8 lg:block" aria-hidden="true" />
                )}
              </motion.li>
            ))}
          </motion.ul>
        </div>
      </div>

      {/* ═══ HOW IT WORKS ═════════════════════════════════════════════════════ */}
      <section className="py-28" aria-labelledby="how-heading">
        <div className="app-shell">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16 text-center">
            <motion.p variants={fadeUp} className="app-eyebrow mb-4">How It Works</motion.p>
            <motion.h2 id="how-heading" variants={fadeUp} className="app-section-title mb-5">
              From description to floor plan in seconds
            </motion.h2>
            <motion.p variants={fadeUp} className="app-section-copy mx-auto max-w-2xl">
              No CAD experience needed. Just describe your space the way you'd explain it to an architect.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
            className="relative grid grid-cols-1 gap-6 md:grid-cols-3">
            <div
              className="pointer-events-none absolute left-[33%] right-[33%] top-10 hidden h-px md:block"
              style={{ background: 'linear-gradient(90deg, transparent, rgba(99,102,241,0.28) 20%, rgba(99,102,241,0.28) 80%, transparent)' }}
              aria-hidden="true"
            />
            {HOW_IT_WORKS.map((step) => {
              const Icon = step.icon;
              return (
                <motion.div key={step.step} variants={fadeUp}
                  whileHover={{ y: -6, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } }}
                  className="app-card app-card-hover flex flex-col p-8 text-center">
                  <div className="mb-5 flex items-center justify-center gap-3">
                    <span className="landing-step-index">{step.step}</span>
                    <div className="app-icon-badge">
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </div>
                  </div>
                  <h3 className="app-card-title mb-3">{step.title}</h3>
                  <p className="app-body flex-1">{step.body}</p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* ═══ FEATURES ═════════════════════════════════════════════════════════ */}
      <section className="py-28 dark:bg-transparent" style={{ background: 'rgba(255,255,255,0.4)' }} aria-labelledby="features-heading">
        <div className="app-shell">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-16 text-center">
            <motion.p variants={fadeUp} className="app-eyebrow mb-4">Capabilities</motion.p>
            <motion.h2 id="features-heading" variants={fadeUp} className="app-section-title mb-5">
              Built for precision. Designed for speed.
            </motion.h2>
            <motion.p variants={fadeUp} className="app-section-copy mx-auto max-w-2xl">
              Every part of CadArena is engineered around one goal: turning your intent into
              production-ready architectural output.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
            className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <motion.div key={f.title} variants={fadeUp}
                  whileHover={{ y: -6, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } }}
                  className="app-card flex flex-col p-7">
                  <div className="app-icon-badge mb-5" aria-hidden="true">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="app-card-title mb-3">{f.title}</h3>
                  <p className="app-body flex-1">{f.body}</p>
                  <div className="mt-5 flex items-center gap-1 text-xs font-bold text-primary-600 dark:text-violet-400">
                    Learn more <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* ═══ LIVE DEMO ════════════════════════════════════════════════════════ */}
      <section className="py-28" aria-labelledby="demo-heading">
        <div className="app-shell">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-14 text-center">
            <motion.p variants={fadeUp} className="app-eyebrow mb-4">Live Demo</motion.p>
            <motion.h2 id="demo-heading" variants={fadeUp} className="app-section-title mb-5">
              See it in action
            </motion.h2>
            <motion.p variants={fadeUp} className="app-section-copy mx-auto max-w-2xl">
              Select an example prompt and watch the AI generate a structured, labelled floor plan
              with room adjacencies, dimensions, and EBC compliance markers.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
            className="grid grid-cols-1 items-center gap-10 lg:grid-cols-5">
            <motion.div variants={fadeUp} className="space-y-3 lg:col-span-2">
              <p className="mb-4 text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-600">
                Example prompts
              </p>
              {DEMO_PROMPTS.map((p, i) => (
                <motion.button
                  key={p}
                  onClick={() => setDemoIdx(i)}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  className={`w-full rounded-2xl border px-5 py-4 text-left text-sm font-semibold transition-colors duration-200 ${
                    demoIdx === i
                      ? 'border-primary-300 bg-primary-50 text-primary-800 shadow-soft dark:border-violet-800/50 dark:bg-violet-950/30 dark:text-violet-200'
                      : 'border-slate-100 bg-white/60 text-slate-700 hover:border-primary-200 hover:bg-primary-50/50 dark:border-white/7 dark:bg-white/3 dark:text-slate-400 dark:hover:border-violet-800/40 dark:hover:bg-violet-950/20'
                  }`}
                  aria-pressed={demoIdx === i}
                >
                  <span className="mr-2 font-mono text-primary-400 dark:text-violet-500">{String(i + 1).padStart(2, '0')}</span>
                  {p}
                </motion.button>
              ))}
              <div className="pt-4">
                <Link to="/studio" className="app-button-primary app-button-compact w-full justify-center">
                  <Zap className="h-4 w-4" aria-hidden="true" />
                  Try it yourself
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Link>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="lg:col-span-3">
              <div className="app-card app-card-strong p-5 sm:p-7">
                <div className="mb-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2.5">
                    <div className="flex gap-1.5" aria-hidden="true">
                      <div className="h-3 w-3 rounded-full bg-red-400" />
                      <div className="h-3 w-3 rounded-full bg-yellow-400" />
                      <div className="h-3 w-3 rounded-full bg-green-400" />
                    </div>
                    <span className="text-xs font-semibold text-slate-400 dark:text-slate-500">AI Generation</span>
                  </div>
                  <div className="flex items-center gap-2 rounded-full border border-green-100 bg-green-50 px-3 py-1.5 text-xs font-semibold text-green-700 dark:border-green-900/40 dark:bg-green-950/30 dark:text-green-400">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500 dark:bg-green-400" aria-hidden="true" />
                    DXF Ready
                  </div>
                </div>
                <div className="app-card-muted rounded-xl p-3 text-left">
                  <AnimatePresence mode="wait">
                    <motion.div key={demoIdx}
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      transition={{ duration: 0.22 }}
                      className="mb-2 flex items-center gap-2 font-mono text-xs text-slate-500 dark:text-slate-400">
                      <span className="font-bold text-primary-600 dark:text-violet-400">›</span>
                      <span>&quot;{DEMO_PROMPTS[demoIdx]}&quot;</span>
                    </motion.div>
                  </AnimatePresence>
                  <BlueprintPreview />
                </div>
                <div className="mt-4 grid grid-cols-4 gap-2">
                  {[
                    { label: 'Rooms',      value: '✓' },
                    { label: 'DXF Layers', value: '✓' },
                    { label: 'Dimensions', value: '✓' },
                    { label: 'EBC 2023',   value: '✓' },
                  ].map(({ label, value }) => (
                    <div key={label} className="rounded-xl border border-slate-100 bg-white/80 px-2 py-2.5 text-center dark:border-white/7 dark:bg-white/4">
                      <p className="text-sm font-black text-primary-700 dark:text-violet-300 leading-none">{value}</p>
                      <p className="mt-1 text-xs text-slate-500 dark:text-slate-500 leading-none">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══ CAPABILITIES ═════════════════════════════════════════════════════ */}
      <section className="py-28 dark:bg-transparent" style={{ background: 'rgba(255,255,255,0.4)' }} aria-labelledby="perf-heading">
        <div className="app-shell">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mb-14 text-center">
            <motion.p variants={fadeUp} className="app-eyebrow mb-4">What you get</motion.p>
            <motion.h2 id="perf-heading" variants={fadeUp} className="app-section-title mb-5">
              From a single prompt to a complete CAD file
            </motion.h2>
            <motion.p variants={fadeUp} className="app-section-copy mx-auto max-w-2xl">
              The Studio&apos;s LLM pipeline handles spatial reasoning, constraint enforcement, and
              DXF formatting — so you can focus on the design intent.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}
            className="app-card-muted p-8 lg:p-12">
            <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
              <motion.div variants={fadeUp}>
                <h3 className="app-card-title mb-6 text-xl">What the Studio produces</h3>
                <div className="space-y-5" role="list">
                  {[
                    { metric: 'Labelled room polygons', value: 'Per room',   desc: 'Living, bedroom, kitchen, bath — each correctly placed and sized' },
                    { metric: 'DXF layer assignment',   value: '12+ layers', desc: 'One layer per room type, ready for AutoCAD or Revit filtering' },
                    { metric: 'Linear dimensions',      value: 'Built-in',   desc: 'Width and height entities added automatically to each room' },
                    { metric: 'EBC 2023 compliance',    value: 'Enforced',   desc: 'Minimum room areas and adjacency rules applied during generation' },
                  ].map(({ metric, value, desc }) => (
                    <div key={metric} className="flex items-start gap-3" role="listitem">
                      <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary-600 dark:text-violet-400" aria-hidden="true" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-4">
                          <span className="font-semibold text-slate-950 dark:text-slate-100">{metric}</span>
                          <span className="font-black text-primary-700 dark:text-violet-300">{value}</span>
                        </div>
                        <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-500">{desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              <motion.div variants={fadeUp} className="text-center">
                <div className="app-card app-card-strong app-card-hover p-10 shadow-lg">
                  <p className="app-eyebrow mb-3">Output Format</p>
                  <motion.div
                    className="mb-1 text-6xl font-black tracking-tight"
                    style={{ backgroundImage: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}
                    initial={{ opacity: 0, scale: 0.88 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                  >
                    .DXF
                  </motion.div>
                  <p className="mb-6 text-sm text-slate-500 dark:text-slate-400">AutoCAD 2013+ · Revit · Any DXF-compatible tool</p>
                  <div className="space-y-2">
                    {['Room polygons', 'Room labels', 'Layer system', 'Dimensions'].map((item) => (
                      <div key={item} className="flex items-center justify-between rounded-xl border border-slate-100 bg-primary-50/60 px-4 py-2 dark:border-white/6 dark:bg-violet-950/20">
                        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{item}</span>
                        <span className="text-sm font-black text-primary-600 dark:text-violet-400">✓</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ═══ CTA ══════════════════════════════════════════════════════════════ */}
      <section className="py-28" aria-labelledby="cta-heading">
        <div className="app-shell">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger}>
            <motion.div variants={fadeUp}
              className="app-cta-panel relative overflow-hidden px-8 py-20 text-center sm:px-14 sm:py-24">
              <div className="pointer-events-none absolute inset-0" aria-hidden="true">
                <div className="absolute -left-20 -top-20 h-80 w-80 rounded-full bg-white opacity-[0.07] blur-3xl" />
                <div className="absolute -bottom-20 -right-20 h-80 w-80 rounded-full bg-white opacity-[0.07] blur-3xl" />
                <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent" />
                <div className="absolute left-1/2 top-0 h-px w-2/3 -translate-x-1/2 bg-white opacity-20" />
              </div>

              <motion.p variants={fadeUp} className="mb-4 text-xs font-bold uppercase tracking-widest text-primary-200">
                Start building today
              </motion.p>
              <motion.h2 id="cta-heading" variants={fadeUp}
                className="mb-5 text-3xl font-black tracking-tight text-white sm:text-4xl lg:text-5xl">
                Design your first floor plan.
                <br />
                <span className="opacity-75">No CAD experience needed.</span>
              </motion.h2>
              <motion.p variants={fadeUp} className="mx-auto mb-10 max-w-xl text-lg leading-relaxed text-primary-100">
                Type what you want to build. CadArena handles constraints, adjacencies, compliance, and export automatically.
              </motion.p>

              <motion.div variants={fadeUp} className="flex justify-center">
                <HeroPromptBar onDark />
              </motion.div>

              <motion.p variants={fadeUp} className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-sm text-primary-200">
                <span>Or open the full workspace:</span>
                <Link to="/studio" className="inline-flex items-center gap-1.5 font-bold text-white underline underline-offset-4 hover:text-primary-100">
                  <MessageSquare className="h-4 w-4" aria-hidden="true" />
                  Launch Studio
                </Link>
              </motion.p>
            </motion.div>
          </motion.div>
        </div>
      </section>

    </div>
  );
};

// ─── Reusable example chip ────────────────────────────────────────────────────
function ExampleChip({ label }) {
  const navigate = useNavigate();
  return (
    <motion.button
      type="button"
      onClick={() => navigate('/studio')}
      whileHover={{ scale: 1.04, y: -1 }}
      whileTap={{ scale: 0.97 }}
      className="app-pill-muted cursor-pointer py-1.5 text-xs transition-colors hover:border-primary-200 hover:bg-primary-50 dark:hover:border-violet-800/40 dark:hover:bg-violet-950/20"
    >
      {label}
    </motion.button>
  );
}

export default HomePage;
