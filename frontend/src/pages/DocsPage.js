import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  BookOpen, Zap, Brain, Download, Code2, Server, Layers,
  HelpCircle, ChevronRight, Terminal, FileCode2, ExternalLink,
  Cpu, CheckCircle,
} from 'lucide-react';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.08 } } };
const fadeUp  = { hidden: { y: 18, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.48, ease: [0.22, 1, 0.36, 1] } } };

const SECTIONS = [
  { id: 'overview',    label: 'Overview',     icon: BookOpen },
  { id: 'quickstart',  label: 'Quick Start',  icon: Zap },
  { id: 'studio',      label: 'The Studio',   icon: Layers },
  { id: 'api',         label: 'API Reference',icon: Server },
  { id: 'models',      label: 'Models',       icon: Brain },
  { id: 'export',      label: 'DXF Export',   icon: Download },
  { id: 'faq',         label: 'FAQ',          icon: HelpCircle },
];

function CodeBlock({ children, lang = 'bash' }) {
  return (
    <div className="my-4 overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 text-sm">
      <div className="flex items-center gap-2 border-b border-slate-800 px-4 py-2.5">
        <div className="flex gap-1.5">
          <span className="h-3 w-3 rounded-full bg-red-500/70" />
          <span className="h-3 w-3 rounded-full bg-yellow-500/70" />
          <span className="h-3 w-3 rounded-full bg-green-500/70" />
        </div>
        <span className="ml-1 font-mono text-xs text-slate-500">{lang}</span>
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-[0.8125rem] leading-relaxed text-slate-200">
        <code>{children}</code>
      </pre>
    </div>
  );
}

function SectionHeading({ id, icon: Icon, children }) {
  return (
    <h2 id={id} className="app-section-title mb-6 flex items-center gap-3 scroll-mt-24">
      <div className="app-icon-badge flex-shrink-0" aria-hidden="true">
        <Icon className="h-5 w-5" />
      </div>
      {children}
    </h2>
  );
}

function Pill({ children }) {
  return <span className="app-pill-muted inline-flex py-0.5 text-xs">{children}</span>;
}

function EndpointRow({ method, path, desc }) {
  const color = method === 'GET' ? 'text-green-700 bg-green-50 border-green-200' : method === 'POST' ? 'text-blue-700 bg-blue-50 border-blue-200' : 'text-orange-700 bg-orange-50 border-orange-200';
  return (
    <div className="flex flex-col gap-2 border-b border-slate-100 py-4 sm:flex-row sm:items-center">
      <span className={`rounded-lg border px-2.5 py-1 text-xs font-black tracking-wide flex-shrink-0 w-fit ${color}`}>{method}</span>
      <code className="flex-1 font-mono text-sm text-slate-800">{path}</code>
      <span className="text-sm text-slate-500">{desc}</span>
    </div>
  );
}

const DocsPage = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const scrollTo = (id) => {
    setActiveSection(id);
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="app-page">
      <div className="app-shell">

        {/* ── Header ── */}
        <motion.div initial="hidden" animate="visible" variants={stagger} className="app-page-header mb-12">
          <motion.div variants={fadeUp} className="mb-5">
            <span className="app-pill">
              <BookOpen className="h-4 w-4" />
              Documentation
            </span>
          </motion.div>
          <motion.h1 variants={fadeUp} className="app-page-title mb-4">
            <span className="gradient-text">CadArena</span> Docs
          </motion.h1>
          <motion.p variants={fadeUp} className="app-page-copy">
            Everything you need to understand, run, and build with CadArena — the conversational
            AI platform that turns natural language into CAD floor plans.
          </motion.p>
        </motion.div>

        <div className="flex flex-col gap-10 lg:flex-row lg:gap-12">

          {/* ── Sidebar ── */}
          <aside className="lg:w-56 lg:flex-shrink-0">
            <div className="sticky top-24">
              <p className="mb-3 text-xs font-bold uppercase tracking-widest text-slate-400">Contents</p>
              <nav>
                <ul className="space-y-1">
                  {SECTIONS.map(({ id, label, icon: Icon }) => (
                    <li key={id}>
                      <button
                        onClick={() => scrollTo(id)}
                        className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition-colors ${
                          activeSection === id
                            ? 'bg-primary-50 text-primary-700 border border-primary-100'
                            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
                        }`}
                      >
                        <Icon className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                        {label}
                      </button>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </aside>

          {/* ── Main content ── */}
          <main className="min-w-0 flex-1 space-y-16">

            {/* OVERVIEW */}
            <section>
              <SectionHeading id="overview" icon={BookOpen}>Overview</SectionHeading>
              <p className="app-body mb-6">
                CadArena is an AI-powered conversational CAD platform that transforms natural language descriptions into structured,
                EBC 2023-compliant architectural floor plans. It combines a constraint-aware diffusion model with a FastAPI backend,
                a React frontend, and a full studio workspace for iterative design.
              </p>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {[
                  { icon: Brain, title: 'Constraint-Aware AI', body: 'Diffusion model trained with spatial adjacency and structural constraints.' },
                  { icon: Cpu,   title: '84.5% Accuracy',     body: 'Benchmarked on FID, CLIP-Score, and adjacency consistency metrics.' },
                  { icon: FileCode2, title: 'DXF Export',     body: 'Every generated plan is exported as a CAD-compatible DXF file.' },
                ].map(({ icon: Icon, title, body }) => (
                  <div key={title} className="app-card p-5">
                    <div className="app-icon-badge mb-3" aria-hidden="true"><Icon className="h-5 w-5" /></div>
                    <p className="mb-1 font-bold text-slate-950">{title}</p>
                    <p className="text-sm text-slate-600">{body}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* QUICK START */}
            <section>
              <SectionHeading id="quickstart" icon={Zap}>Quick Start</SectionHeading>
              <p className="app-body mb-5">Get CadArena running locally in three steps.</p>

              <h3 className="mb-2 font-bold text-slate-950">1. Clone the repository</h3>
              <CodeBlock lang="bash">{`git clone https://github.com/Youssefx64/CadArena.git
cd CadArena`}</CodeBlock>

              <h3 className="mb-2 font-bold text-slate-950">2. Start the backend</h3>
              <CodeBlock lang="bash">{`cd backend
pip install -r requirements.txt
cp .env.example .env        # fill in CADARENA_JWT_SECRET
python -m uvicorn app.main:app --host localhost --port 8000`}</CodeBlock>

              <h3 className="mb-2 font-bold text-slate-950">3. Start the frontend</h3>
              <CodeBlock lang="bash">{`cd frontend
npm install
npm start                   # runs on http://localhost:5000`}</CodeBlock>

              <div className="app-card-muted mt-6 flex items-start gap-3 rounded-2xl p-5">
                <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary-600" aria-hidden="true" />
                <div>
                  <p className="font-semibold text-slate-950">Environment variables</p>
                  <p className="mt-1 text-sm text-slate-600">
                    Copy <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs">backend/.env.example</code> to{' '}
                    <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs">backend/.env</code> and set at minimum:{' '}
                    <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs">CADARENA_JWT_SECRET</code> and optionally{' '}
                    <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs">HF_TOKEN</code> for higher Hugging Face rate limits.
                  </p>
                </div>
              </div>
            </section>

            {/* STUDIO */}
            <section>
              <SectionHeading id="studio" icon={Layers}>The Studio</SectionHeading>
              <p className="app-body mb-5">
                The Studio (<code className="rounded bg-slate-100 px-1 font-mono text-xs">/studio</code>) is CadArena&apos;s full-featured CAD workspace.
                It provides a conversational interface to describe your floor plan, review the generated output, and refine it iteratively.
              </p>
              <div className="space-y-4">
                {[
                  { step: '01', title: 'Open the Studio', body: 'Navigate to /studio from the top navigation bar or click "Launch Studio" on the homepage.' },
                  { step: '02', title: 'Describe your layout', body: 'Type your requirements in plain language in the prompt panel. Be as specific or as brief as you like.' },
                  { step: '03', title: 'Review the output', body: 'The AI generates a structured floor plan with labelled rooms, adjacency relationships, and spatial dimensions.' },
                  { step: '04', title: 'Export as DXF', body: 'Download the generated plan as a DXF file compatible with AutoCAD, Revit, or any DXF-capable tool.' },
                ].map(({ step, title, body }) => (
                  <div key={step} className="flex items-start gap-4">
                    <span className="landing-step-index flex-shrink-0">{step}</span>
                    <div>
                      <p className="font-semibold text-slate-950">{title}</p>
                      <p className="mt-1 text-sm text-slate-600">{body}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6">
                <Link to="/studio" className="app-button-primary app-button-compact">
                  Open Studio <ChevronRight className="h-4 w-4" aria-hidden="true" />
                </Link>
              </div>
            </section>

            {/* API REFERENCE */}
            <section>
              <SectionHeading id="api" icon={Server}>API Reference</SectionHeading>
              <p className="app-body mb-4">
                The backend exposes a RESTful API at <code className="rounded bg-slate-100 px-1 font-mono text-xs">http://localhost:8000/api/v1/</code>.
                All endpoints return JSON. Authentication uses HTTP-only JWT cookies.
              </p>

              <div className="mb-6">
                <h3 className="mb-3 font-semibold text-slate-950 flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-primary-600" /> Health &amp; System
                </h3>
                <div className="app-card p-4">
                  <EndpointRow method="GET" path="/health" desc="Backend health check" />
                  <EndpointRow method="GET" path="/api/v1/generate/model-info" desc="Loaded model information" />
                  <EndpointRow method="GET" path="/api/v1/generate/presets" desc="Available generation presets" />
                </div>
              </div>

              <div className="mb-6">
                <h3 className="mb-3 font-semibold text-slate-950 flex items-center gap-2">
                  <Brain className="h-4 w-4 text-primary-600" /> Generation
                </h3>
                <div className="app-card p-4">
                  <EndpointRow method="POST" path="/api/v1/generate" desc="Generate a floor plan from a text prompt" />
                  <EndpointRow method="GET"  path="/api/v1/generate/result/{id}" desc="Poll generation result by ID" />
                </div>
              </div>

              <div className="mb-6">
                <h3 className="mb-3 font-semibold text-slate-950 flex items-center gap-2">
                  <Code2 className="h-4 w-4 text-primary-600" /> Auth &amp; Profile
                </h3>
                <div className="app-card p-4">
                  <EndpointRow method="POST" path="/api/v1/auth/register" desc="Register a new user account" />
                  <EndpointRow method="POST" path="/api/v1/auth/login"    desc="Log in (sets HTTP-only cookie)" />
                  <EndpointRow method="POST" path="/api/v1/auth/logout"   desc="Clear the session cookie" />
                  <EndpointRow method="GET"  path="/api/v1/auth/me"       desc="Get current authenticated user" />
                  <EndpointRow method="GET"  path="/api/v1/profile/me"    desc="Get full user profile" />
                  <EndpointRow method="PATCH" path="/api/v1/profile/me"   desc="Update profile fields" />
                  <EndpointRow method="POST" path="/api/v1/profile/me/avatar" desc="Upload avatar image" />
                </div>
              </div>

              <h3 className="mb-3 font-semibold text-slate-950">Example: Generate a floor plan</h3>
              <CodeBlock lang="curl">{`curl -X POST http://localhost:8000/api/v1/generate \\
  -H "Content-Type: application/json" \\
  -b "cadarena_auth=<your_token>" \\
  -d '{
    "description": "3-bedroom apartment with open kitchen",
    "model_type": "constraint_aware",
    "style": "modern"
  }'`}</CodeBlock>
            </section>

            {/* MODELS */}
            <section>
              <SectionHeading id="models" icon={Brain}>Models</SectionHeading>
              <p className="app-body mb-6">
                CadArena ships with two trained diffusion models. Both are built on top of Stable Diffusion 2.1
                and fine-tuned on the CubiCasa5K floor plan dataset.
              </p>

              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                {[
                  {
                    id: 'baseline',
                    name: 'Baseline',
                    badge: 'Foundation',
                    badgeColor: 'border-primary-200 bg-primary-50 text-primary-700',
                    desc: 'Standard fine-tuned Stable Diffusion 2.1 on architectural data. Good for quick prototyping and baseline comparisons.',
                    metrics: [['Accuracy', '71.3%'], ['FID', '85.2'], ['CLIP', '0.62'], ['Adjacency', '0.41']],
                  },
                  {
                    id: 'constraint_aware',
                    name: 'Constraint-Aware',
                    badge: 'Recommended',
                    badgeColor: 'border-secondary-200 bg-secondary-50 text-secondary-700',
                    desc: 'Enhanced with spatial constraint loss and adjacency modeling. Use this for production-quality floor plans.',
                    metrics: [['Accuracy', '84.5%'], ['FID', '57.4'], ['CLIP', '0.75'], ['Adjacency', '0.73']],
                  },
                ].map((m) => (
                  <div key={m.id} className="app-card p-6">
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <h3 className="app-card-title">{m.name}</h3>
                      <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${m.badgeColor}`}>{m.badge}</span>
                    </div>
                    <p className="mb-4 text-sm text-slate-600">{m.desc}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {m.metrics.map(([label, value]) => (
                        <div key={label} className="app-card-muted rounded-xl p-3 text-center">
                          <p className="text-sm font-black text-slate-950">{value}</p>
                          <p className="text-xs text-slate-500">{label}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="app-card-muted mt-6 flex items-start gap-3 rounded-2xl p-5">
                <Cpu className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary-600" aria-hidden="true" />
                <div>
                  <p className="font-semibold text-slate-950">Training hardware</p>
                  <p className="mt-1 text-sm text-slate-600">
                    Models were trained on Google Colab with an A100 GPU (CUDA 11.8+), totalling 120+ GPU hours.
                    Architecture: 865M parameter Stable Diffusion 2.1 base with custom constraint layers.
                  </p>
                </div>
              </div>
            </section>

            {/* DXF EXPORT */}
            <section>
              <SectionHeading id="export" icon={Download}>DXF Export</SectionHeading>
              <p className="app-body mb-5">
                CadArena generates DXF (Drawing Exchange Format) files compatible with AutoCAD 2013+ and Revit.
                The export pipeline is handled by the <code className="rounded bg-slate-100 px-1 font-mono text-xs">ezdxf</code> library.
              </p>
              <div className="space-y-4">
                {[
                  { title: 'Room polygons', body: 'Each room is drawn as a closed polyline with layer assignment matching the room type (LIVING_ROOM, BEDROOM, KITCHEN, etc.).' },
                  { title: 'Room labels',   body: 'Text entities are placed at room centroids using the STANDARD text style, in paper space units.' },
                  { title: 'Dimensions',    body: 'Linear dimension entities are added for room width and height where dimensions are available.' },
                  { title: 'Layer system',  body: 'Every room type is placed on its own DXF layer for easy filtering and styling in AutoCAD or Revit.' },
                ].map(({ title, body }) => (
                  <div key={title} className="flex items-start gap-3">
                    <CheckCircle className="mt-1 h-4 w-4 flex-shrink-0 text-primary-600" aria-hidden="true" />
                    <div>
                      <p className="font-semibold text-slate-950">{title}</p>
                      <p className="text-sm text-slate-600">{body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* FAQ */}
            <section>
              <SectionHeading id="faq" icon={HelpCircle}>FAQ</SectionHeading>
              <div className="space-y-4">
                {[
                  {
                    q: 'Is CadArena open source?',
                    a: 'The project is currently Proprietary. The repository is viewable on GitHub but not open for public contributions at this time.',
                  },
                  {
                    q: 'What languages are supported for prompts?',
                    a: 'English and Arabic are both supported. The CLIP text encoder handles multilingual input, though English prompts tend to produce the most consistent results.',
                  },
                  {
                    q: 'How long does generation take?',
                    a: 'Average generation time is 2.3 seconds on GPU. CPU inference is significantly slower (30-120s depending on hardware).',
                  },
                  {
                    q: 'Can I use the generated floor plans commercially?',
                    a: 'Generated plans are yours to use, but the model weights and codebase are proprietary. Contact the team for licensing questions.',
                  },
                  {
                    q: 'What is the difference between the Studio and the Generator?',
                    a: 'The Studio (/studio) is a full CAD workspace with a conversational interface and iterative design tools. The Generator page (/generate) is a simpler text-to-floor-plan form — both use the same underlying AI models.',
                  },
                  {
                    q: 'What is EBC 2023 compliance?',
                    a: 'The Egyptian Building Code 2023 defines minimum room sizes, adjacency requirements, and spatial standards. CadArena\'s constraint-aware model is trained to satisfy these constraints automatically.',
                  },
                ].map(({ q, a }) => (
                  <details key={q} className="app-card group rounded-2xl p-0 open:shadow-lg">
                    <summary className="flex cursor-pointer list-none items-center justify-between px-6 py-5 font-semibold text-slate-950 select-none">
                      {q}
                      <ChevronRight className="h-4 w-4 flex-shrink-0 text-slate-400 transition-transform group-open:rotate-90" aria-hidden="true" />
                    </summary>
                    <p className="border-t border-slate-100 px-6 py-5 text-sm leading-relaxed text-slate-600">
                      {a}
                    </p>
                  </details>
                ))}
              </div>
            </section>

            {/* Bottom CTA */}
            <section className="app-cta-panel p-10 text-center">
              <p className="mb-3 text-xs font-bold uppercase tracking-widest text-primary-200">Ready to build?</p>
              <h2 className="mb-4 text-2xl font-black text-white">Open the Studio and start designing</h2>
              <p className="mx-auto mb-8 max-w-md text-primary-100">
                The full CadArena workspace is ready. Describe a floor plan and get a DXF-ready output in seconds.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <Link to="/studio" className="app-button-secondary">
                  Launch Studio <ExternalLink className="h-4 w-4" aria-hidden="true" />
                </Link>
                <Link to="/about" className="app-button-ghost">
                  About the Project
                </Link>
              </div>
            </section>

          </main>
        </div>
      </div>
    </div>
  );
};

export default DocsPage;
