import React, { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, Search, HelpCircle, Cancel as X, ChevronRight,
  CheckCircle2, AlertTriangle, BookOpenCheck, Clock, Folder, File, ChevronDown,
  Zap, MessageSquare, Sliders
} from '../components/IconRegistry';
import DocsIllustration from '../components/illustrations/DocsIllustration';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.02 } } };
const fadeUp  = { hidden: { y: 15, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } } };

const DOC_CATEGORIES = [
  { id: 'all', label: 'All Docs' },
  { id: 'getting-started', label: 'Getting Started' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'installation', label: 'Installation' },
  { id: 'configuration', label: 'Configuration' },
  { id: 'archchat', label: 'ArchChat (RAG)' },
  { id: 'cadstudio', label: 'CadStudio (CAD)' },
  { id: 'api', label: 'API Reference' },
  { id: 'export', label: 'Export Pipeline' },
  { id: 'troubleshooting', label: 'Troubleshooting' },
  { id: 'faq', label: 'FAQ' }
];

// Endpoint Row Component
function ApiRow({ method, path, desc }) {
  const color = method === 'GET' ? 'text-green-700 bg-green-50 border-green-200 dark:text-green-400 dark:bg-green-950/20 dark:border-green-900/40' : method === 'POST' ? 'text-blue-700 bg-blue-50 border-blue-200 dark:text-blue-400 dark:bg-blue-950/20 dark:border-blue-900/40' : 'text-orange-700 bg-orange-50 border-orange-200 dark:text-orange-400 dark:bg-orange-950/20 dark:border-orange-900/40';
  return (
    <div className="flex flex-col gap-2 border-b border-slate-100 dark:border-white/5 py-3 sm:flex-row sm:items-center justify-between text-xs font-semibold">
      <div className="flex items-center gap-3">
        <span className={`rounded px-2 py-0.5 text-[9px] font-black uppercase border ${color}`}>
          {method}
        </span>
        <code className="font-mono text-slate-800 dark:text-slate-200">{path}</code>
      </div>
      <span className="text-slate-500 dark:text-slate-400 text-[11px]">{desc}</span>
    </div>
  );
}

// Collapsible FAQ Accordion Component
function FaqAccordion({ question, answer }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="app-card border border-slate-150 dark:border-white/5 bg-white/60 dark:bg-zinc-900/60 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-6 py-4 font-bold text-slate-900 dark:text-slate-100 text-left text-xs"
      >
        <span>{question}</span>
        <ChevronRight className={`h-4 w-4 text-slate-400 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-slate-100 dark:border-white/5 bg-slate-50/50 dark:bg-zinc-950/20"
          >
            <p className="px-6 py-4 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Code Block Display with copy-to-clipboard functionality
function DocsCodeBlock({ code, lang = 'bash' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Copy failed
    }
  };

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 dark:border-white/5 bg-slate-950 text-xs font-mono mb-4 relative group">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2 text-slate-500">
        <div className="flex gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500/60" />
          <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/60" />
          <span className="h-2.5 w-2.5 rounded-full bg-green-500/60" />
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] uppercase font-bold">{lang}</span>
          <button 
            onClick={handleCopy}
            className="text-[10px] text-slate-400 hover:text-white transition-colors py-0.5 px-2 rounded bg-slate-800 hover:bg-slate-700 font-sans font-bold"
          >
            {copied ? 'Copied ✓' : 'Copy'}
          </button>
        </div>
      </div>
      <pre className="p-4 text-slate-200 overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

ApiRow.propTypes = {
  method: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  desc: PropTypes.string.isRequired
};

FaqAccordion.propTypes = {
  question: PropTypes.string.isRequired,
  answer: PropTypes.string.isRequired
};

DocsCodeBlock.propTypes = {
  code: PropTypes.string.isRequired,
  lang: PropTypes.string
};

// Repository tree structure
const REPO_TREE = {
  name: 'CadArena',
  type: 'folder',
  children: [
    {
      name: 'backend',
      type: 'folder',
      children: [
        {
          name: 'app',
          type: 'folder',
          children: [
            {
              name: 'api',
              type: 'folder',
              children: [
                { name: 'v1/routes.py', type: 'file' }
              ]
            },
            {
              name: 'routers',
              type: 'folder',
              children: [
                { name: 'archchat.py', type: 'file' },
                { name: 'auth.py', type: 'file' },
                { name: 'design_parser.py', type: 'file' },
                { name: 'workspace.py', type: 'file' }
              ]
            },
            {
              name: 'services',
              type: 'folder',
              children: [
                { name: 'archchat_storage.py', type: 'file' },
                { name: 'dxf_room_renderer.py', type: 'file' },
                { name: 'file_token_registry.py', type: 'file' },
                { name: 'output_cleanup.py', type: 'file' }
              ]
            },
            { name: 'main.py', type: 'file' }
          ]
        },
        { name: 'requirements.txt', type: 'file' }
      ]
    },
    {
      name: 'RAG',
      type: 'folder',
      children: [
        {
          name: 'app',
          type: 'folder',
          children: [
            { name: 'document_loader.py', type: 'file' },
            { name: 'rag_engine.py', type: 'file' }
          ]
        },
        { name: 'requirements.txt', type: 'file' }
      ]
    },
    {
      name: 'frontend',
      type: 'folder',
      children: [
        {
          name: 'src',
          type: 'folder',
          children: [
            {
              name: 'components',
              type: 'folder',
              children: [
                { name: 'layout/Navbar.js', type: 'file' },
                { name: 'ui/FeatureCard.js', type: 'file' }
              ]
            },
            {
              name: 'data',
              type: 'folder',
              children: [
                { name: 'developers.json', type: 'file' },
                { name: 'features.js', type: 'file' }
              ]
            },
            {
              name: 'pages',
              type: 'folder',
              children: [
                { name: 'AboutPage.js', type: 'file' },
                { name: 'DevelopersPage.js', type: 'file' },
                { name: 'DocsPage.js', type: 'file' },
                { name: 'FeaturesPage.js', type: 'file' },
                { name: 'RAGChatPage.js', type: 'file' }
              ]
            },
            { name: 'App.js', type: 'file' }
          ]
        },
        {
          name: 'studio-source',
          type: 'folder',
          children: [
            { name: 'scripts/viewer.js', type: 'file' },
            { name: 'index.html', type: 'file' }
          ]
        },
        { name: 'package.json', type: 'file' }
      ]
    }
  ]
};

function TreeFolder({ node, depth = 0 }) {
  const [isOpen, setIsOpen] = useState(depth < 2);

  if (node.type === 'file') {
    return (
      <div className="flex items-center gap-2 py-1.5 pl-3 text-slate-500 dark:text-slate-400 font-mono text-[11px] hover:text-slate-800 dark:hover:text-slate-250 transition-colors">
        <File className="h-3.5 w-3.5 text-slate-400" aria-hidden="true" />
        <span>{node.name}</span>
      </div>
    );
  }

  return (
    <div className="select-none">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 py-1.5 pl-1.5 hover:bg-slate-100 dark:hover:bg-white/5 rounded-lg text-slate-800 dark:text-slate-200 text-left font-mono text-[11px] font-bold transition-colors"
      >
        {isOpen ? <ChevronDown className="h-3 w-3 text-slate-400" /> : <ChevronRight className="h-3 w-3 text-slate-400" />}
        <Folder className="h-3.5 w-3.5 text-primary-500" aria-hidden="true" />
        <span>{node.name}/</span>
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden border-l border-slate-200 dark:border-white/5 ml-[13px] pl-3"
          >
            {node.children.map((child, idx) => (
              <TreeFolder key={idx} node={child} depth={depth + 1} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

TreeFolder.propTypes = {
  node: PropTypes.shape({
    name: PropTypes.string.isRequired,
    type: PropTypes.string.isRequired,
    children: PropTypes.array
  }).isRequired,
  depth: PropTypes.number
};

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [activeCard, setActiveCard] = useState(null);
  const searchInputRef = useRef(null);

  // SEO Title setup
  useEffect(() => { document.title = 'System Docs — CadArena'; }, []);

  // Static documents database
  const DOCUMENTS = useMemo(() => [
    {
      id: 'overview',
      title: 'Product Overview',
      summary: 'An introduction to CadArena spatial planning engines and RAG retrieval pipelines.',
      category: 'architecture',
      readingTime: '2 min read',
      difficulty: 'Beginner',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            CadArena combines conversational AI interfaces with deterministic geometric solves. It avoids LLM spatial hallucinations by parsing natural language design requests into structured parameters, which are then passed to a geometric solver for planning and ez_dxf output.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="app-card border border-slate-100 dark:border-white/5 p-4 bg-slate-50/50 dark:bg-zinc-900/30">
              <h5 className="font-bold text-slate-800 dark:text-slate-200 text-xs mb-1">ArchChat (AI + RAG)</h5>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Ingests documents and executes vector similarity queries over construction rules collections.</p>
            </div>
            <div className="app-card border border-slate-100 dark:border-white/5 p-4 bg-slate-50/50 dark:bg-zinc-900/30">
              <h5 className="font-bold text-slate-800 dark:text-slate-200 text-xs mb-1">CadStudio (Drawing Planner)</h5>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Computes geometric layouts, resolves boundary setbacks, and exports layered DXF files.</p>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'repo-structure',
      title: 'Repository Structure',
      summary: 'Map of backend servers, local RAG files, and React workspace directories.',
      category: 'architecture',
      readingTime: '3 min read',
      difficulty: 'Beginner',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            CadArena partitions logic between an asynchronous FastAPI api, local RAG indexing databases, and the React client viewer:
          </p>
          <div className="app-card border border-slate-100 dark:border-white/5 p-4 bg-slate-50/50 dark:bg-zinc-900/30 max-h-96 overflow-y-auto">
            <TreeFolder node={REPO_TREE} />
          </div>
        </div>
      )
    },
    {
      id: 'local-setup',
      title: 'Local Environment Setup',
      summary: 'Setting up local services, virtual environments, and node packages.',
      category: 'getting-started',
      readingTime: '3 min read',
      difficulty: 'Intermediate',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4 text-xs text-slate-500 dark:text-slate-400">
          <p className="leading-relaxed">
            Follow these commands to configure the workspace environment. Ensure python 3.10+ and Node 18+ are active:
          </p>
          <DocsCodeBlock 
            lang="bash"
            code={`# 1. Clone the project files
git clone https://github.com/Youssefx64/CadArena.git
cd CadArena

# 2. Build local python environments
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt -r RAG/requirements.txt

# 3. Load frontend dependencies
cd frontend
npm install
npm run start`}
          />
          <div className="app-card-muted p-4 rounded-2xl flex items-start gap-3">
            <CheckCircle2 className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
            <div className="text-[11px] leading-relaxed">
              <span className="font-bold text-slate-800 dark:text-slate-200">Recommended setup:</span> Create a python virtualenv environment inside the workspace root before starting pip dependencies.
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'configuration',
      title: 'Configuration Settings',
      summary: 'Setting environment variables, JWT secrets, SQLite DB, and Ollama tags.',
      category: 'configuration',
      readingTime: '2 min read',
      difficulty: 'Intermediate',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Create a <code className="font-mono text-primary-600 bg-slate-100 px-1 py-0.5 rounded">.env</code> file under the backend folder to manage local properties:
          </p>
          <DocsCodeBlock 
            lang="dotenv"
            code={`CADARENA_JWT_SECRET=your_jwt_secret_token
CADARENA_DATABASE_URL=sqlite:///./cadarena.db
OLLAMA_HOST=http://localhost:11434
# Optional Hugging Face Token for rate-limits
HF_TOKEN=your_hugging_face_token`}
          />
        </div>
      )
    },
    {
      id: 'archchat',
      title: 'ArchChat (RAG) Architecture',
      summary: 'In-depth description of Qdrant vector retrieval, ingestion parsers, and citations routing.',
      category: 'archchat',
      readingTime: '4 min read',
      difficulty: 'Advanced',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            ArchChat ingests PDF, Markdown, TXT, CSV, or JSON reference guides. It splits text into chunks, calculates similarity matrices, and writes them to a local Qdrant collection. When querying, the vector retriever injects EBC code standards into the system prompt.
          </p>
          <div className="app-card border border-slate-100 dark:border-white/5 p-4 bg-slate-50/50 dark:bg-zinc-900/30">
            <h5 className="font-bold text-slate-800 dark:text-slate-200 text-xs mb-1">Citations Alignment</h5>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Generates deep-link citation indices. Clicking a citation in the thread highlights the exact parsed PDF page in the viewer sidebar.</p>
          </div>
        </div>
      )
    },
    {
      id: 'cadstudio',
      title: 'CadStudio Layout Workflows',
      summary: 'Conversational spatial planner solver, room balances, and compliance gates check.',
      category: 'cadstudio',
      readingTime: '4 min read',
      difficulty: 'Advanced',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            CadStudio implements dynamic planning solvers. After the LLM extracts zoning areas and dimensions, spatial planners place room polygons inside boundaries. Compliance gates then verify the setback lines and minimum area dimensions against EBC codes.
          </p>
        </div>
      )
    },
    {
      id: 'api-reference',
      title: 'REST API Contracts',
      summary: 'Complete endpoint routing indices grouped by category with methods.',
      category: 'api',
      readingTime: '5 min read',
      difficulty: 'Advanced',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            The FastAPI server exposes REST APIs at <code className="font-mono text-primary-600 bg-slate-100 px-1 py-0.5 rounded">/api/v1/</code>.
          </p>
          <div className="space-y-1">
            <ApiRow method="POST" path="/api/v1/auth/login" desc="Establishes cookie user token" />
            <ApiRow method="GET" path="/api/v1/auth/me" desc="Fetches authorized profile identities" />
            <ApiRow method="POST" path="/api/v1/generate" desc="Accepts prompts and generates drawings coordinates" />
            <ApiRow method="GET" path="/health" desc="Audits databases, vector collection, ollama daemons" />
          </div>
        </div>
      )
    },
    {
      id: 'export-pipeline',
      title: 'ezdxf Export Blueprint',
      summary: 'Layer mappings (WALLS, WINDOWS, DOORS, DIMENSIONS) and printable PDF plotting.',
      category: 'export',
      readingTime: '3 min read',
      difficulty: 'Intermediate',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            The export pipeline converts planned coordinates into DXF vectors using ezdxf. Layer assignments align with standard naming protocols:
          </p>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-500">
            <div className="app-card-muted p-2 rounded">WALLS (Color 0, LW 50)</div>
            <div className="app-card-muted p-2 rounded">DOORS (Color 0, LW 25)</div>
            <div className="app-card-muted p-2 rounded">DIMENSIONS (Color 0, LW 13)</div>
            <div className="app-card-muted p-2 rounded">FURNITURE (Color 252, LW 13)</div>
          </div>
        </div>
      )
    },
    {
      id: 'troubleshooting',
      title: 'Troubleshooting Common Issues',
      summary: 'Resolving missing dependencies, Ollama daemon connection errors, and DB blocks.',
      category: 'troubleshooting',
      readingTime: '3 min read',
      difficulty: 'Intermediate',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-4">
          <div className="space-y-3">
            <div className="flex gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-800 dark:text-slate-200 text-xs">Error: PyMuPDF not found</p>
                <p className="text-[11px] text-slate-500">Ensure you install the packages correctly: <code className="font-mono text-primary-600">pip install pymupdf</code>. PyMuPDF is necessary for uploading reference documents.</p>
              </div>
            </div>
            <div className="flex gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-800 dark:text-slate-200 text-xs">Error: Connection to Ollama failed</p>
                <p className="text-[11px] text-slate-500">Verify that the Ollama daemon is running locally: `ollama run qwen2.5:72b` or check host address rules.</p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'faq',
      title: 'Operational FAQ',
      summary: 'Frequently asked questions regarding commercial rules, formats, and Arabic language.',
      category: 'faq',
      readingTime: '3 min read',
      difficulty: 'Beginner',
      lastUpdated: 'June 2026',
      content: (
        <div className="space-y-3">
          <FaqAccordion 
            question="Is CadArena open source?" 
            answer="The project is currently Proprietary. The repository is viewable on GitHub but not open for public contributions at this time." 
          />
          <FaqAccordion 
            question="What languages are supported for prompts?" 
            answer="English and Arabic are both supported. The underlying LLM handles both languages natively, though English prompts tend to produce the most consistent results." 
          />
          <FaqAccordion 
            question="What is EBC 2023 compliance?" 
            answer="The Egyptian Building Code 2023 defines minimum room sizes, adjacency requirements, and spatial standards. CadArena's generation pipeline encodes these constraints so that every generated floor plan satisfies them automatically." 
          />
        </div>
      )
    }
  ], []);

  // Filter and search logic
  const filteredDocs = useMemo(() => {
    return DOCUMENTS.filter((doc) => {
      // Category Filter
      if (activeCategory !== 'all' && doc.category !== activeCategory) {
        return false;
      }
      
      // Search Filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = doc.title.toLowerCase().includes(q);
        const matchesSummary = doc.summary.toLowerCase().includes(q);
        const matchesCat = doc.category.toLowerCase().includes(q);
        return matchesTitle || matchesSummary || matchesCat;
      }
      return true;
    });
  }, [DOCUMENTS, activeCategory, searchQuery]);

  const handleClearFilters = useCallback(() => {
    setSearchQuery('');
    setActiveCategory('all');
    if (searchInputRef.current) searchInputRef.current.focus();
  }, []);

  const handleCardClick = (doc) => {
    setActiveCard(doc);
  };

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
                  <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
                  System Documentation
                </span>
              </motion.div>
              
              <motion.h1 variants={fadeUp} className="app-hero-title leading-tight text-4xl sm:text-5xl lg:text-6xl font-black mb-6">
                Platform reference
                <br />
                <span className="gradient-text-animated">for engineers</span>
              </motion.h1>

              <motion.p variants={fadeUp} className="app-page-copy mx-auto lg:mx-0 mb-8 max-w-2xl text-slate-500 dark:text-slate-400">
                Installation guides, API reference, configuration parameters, and troubleshooting —
                everything needed to understand, deploy, and extend CadArena.
              </motion.p>

              {/* Quick Links / Popular Topics */}
              <motion.div 
                variants={fadeUp}
                className="flex flex-wrap items-center justify-center lg:justify-start gap-2 max-w-lg mx-auto lg:mx-0 text-xs"
              >
                <span className="text-slate-400 font-bold mr-1">Jump to:</span>
                {[
                  { label: 'Quick Start', action: () => { setActiveCategory('getting-started'); setSearchQuery(''); } },
                  { label: 'API Endpoints', action: () => { setActiveCategory('api'); setSearchQuery(''); } },
                  { label: 'DXF Export', action: () => { setActiveCategory('export'); setSearchQuery(''); } },
                  { label: 'EBC Compliance', action: () => { setActiveCategory('cadstudio'); setSearchQuery(''); } }
                ].map((link, idx) => (
                  <button
                    key={idx}
                    onClick={link.action}
                    className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-400 font-bold transition-colors"
                  >
                    {link.label}
                  </button>
                ))}
              </motion.div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="lg:col-span-5 flex justify-center w-full"
            >
              <DocsIllustration />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ═══ DYNAMIC CONTENT SECTION ════════════════════════════════════════ */}
      <section className="app-shell relative z-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* ── STICKY SIDEBAR NAVIGATION ── */}
          <aside className="hidden lg:block lg:col-span-3 sticky top-24">
            <div className="flex items-center gap-2 mb-4">
              <BookOpenCheck className="h-4 w-4 text-slate-400" />
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                Documentation
              </h3>
            </div>
            <nav className="space-y-1" aria-label="Documentation sidebar filter list">
              {DOC_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => { setActiveCategory(cat.id); setActiveCard(null); }}
                  className={`w-full flex items-center justify-between px-3 py-2.5 text-xs font-bold rounded-xl transition-all ${
                    activeCategory === cat.id
                      ? 'bg-primary-50 text-primary-700 dark:bg-violet-950/30 dark:text-violet-300 border border-primary-200/50 dark:border-violet-900/40'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <span>{cat.label}</span>
                  <ChevronRight className={`h-3 w-3 text-slate-400 transition-transform ${activeCategory === cat.id ? 'translate-x-0.5' : ''}`} />
                </button>
              ))}
            </nav>
          </aside>

          {/* ── MAIN CONTENT (SEARCH & LIST) ── */}
          <div className="lg:col-span-9 space-y-6">
            
            {/* Instant Search Bar */}
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4" aria-hidden="true">
                <Search className="h-5 w-5 text-slate-400 dark:text-slate-500" />
              </div>
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setActiveCard(null); }}
                placeholder="Search documentation topics (e.g. environment variables, endpoints, ezdxf)..."
                className="w-full bg-white dark:bg-zinc-900 border border-slate-200 dark:border-slate-800 rounded-2xl py-3.5 pl-12 pr-10 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-primary-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-shadow hover:shadow-soft"
              />
              {searchQuery && (
                <button 
                  onClick={() => { setSearchQuery(''); setActiveCard(null); }}
                  className="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  aria-label="Clear search query"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>

            {/* EMPTY STATE */}
            {filteredDocs.length === 0 && (
              <div className="app-card p-12 text-center border-dashed border-slate-200 dark:border-white/5 bg-transparent rounded-2xl">
                <HelpCircle className="h-10 w-10 text-slate-400 dark:text-slate-500 mx-auto mb-4" />
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-2">No matching topics</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 max-w-sm mx-auto">
                  Your query returned no documentation matches. Try clearing your search or selecting a different category.
                </p>
                <div className="flex justify-center gap-2">
                  <button 
                    onClick={handleClearFilters}
                    className="app-button-primary app-button-compact"
                  >
                    Reset
                  </button>
                </div>
              </div>
            )}

            {/* DYNAMIC CARDS LIST */}
            {filteredDocs.length > 0 && !activeCard && (
              <motion.div 
                initial="hidden"
                animate="visible"
                variants={stagger}
                className="grid grid-cols-1 md:grid-cols-2 gap-6"
              >
                {filteredDocs.map((doc) => (
                  <motion.div
                    key={doc.id}
                    variants={fadeUp}
                    whileHover={{ y: -4, scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => handleCardClick(doc)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleCardClick(doc); } }}
                    aria-label={`Open document section ${doc.title}`}
                    className="app-card app-card-hover p-6 cursor-pointer flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-3 border-b border-slate-100 dark:border-white/5 pb-2">
                        <span className="text-[9px] font-black uppercase text-primary-600 dark:text-violet-400 tracking-wider">
                          {doc.category}
                        </span>
                        <div className="flex gap-1">
                          <span className="px-2 py-0.5 text-[9px] font-bold bg-slate-100 dark:bg-white/5 border border-slate-200/50 dark:border-white/5 rounded text-slate-500 dark:text-slate-400 uppercase">
                            {doc.difficulty}
                          </span>
                        </div>
                      </div>
                      <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-2">
                        {doc.title}
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-6">
                        {doc.summary}
                      </p>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-bold border-t border-slate-100 dark:border-white/5 pt-3">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {doc.readingTime}
                      </span>
                      <span>Updated: {doc.lastUpdated}</span>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}

            {/* DYNAMIC CARD VIEW WITH BACK TOGGLE */}
            {activeCard && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="app-card border border-slate-200/70 dark:border-white/5 p-6 md:p-8 bg-white/70 dark:bg-zinc-900/60"
              >
                <div className="flex items-center justify-between mb-6 border-b border-slate-100 dark:border-white/5 pb-4">
                  <button 
                    onClick={() => setActiveCard(null)}
                    className="app-button-secondary app-button-compact text-xs"
                  >
                    ← Back to Topics
                  </button>
                  <span className="text-[10px] font-bold uppercase text-primary-600 bg-primary-50 dark:bg-violet-950/20 dark:text-violet-400 border border-primary-200/30 px-2 py-0.5 rounded-full">
                    {activeCard.category}
                  </span>
                </div>
                <h3 className="text-base font-black text-slate-900 dark:text-slate-50 mb-3">
                  {activeCard.title}
                </h3>
                <p className="text-xs text-slate-400 mb-6 font-bold">
                  Reading estimate: {activeCard.readingTime} · Difficulty: {activeCard.difficulty} · Last updated: {activeCard.lastUpdated}
                </p>
                <div className="border-t border-slate-100 dark:border-white/5 pt-6">
                  {activeCard.content}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </section>

      {/* ═══ PREMIUM CALL-TO-ACTION (CTA) SECTION ══════════════════════════ */}
      <section className="app-shell mt-24" aria-labelledby="cta-heading">
        <div className="app-cta-panel relative overflow-hidden px-8 py-16 text-center sm:px-14 sm:py-20 rounded-3xl">
          <div className="pointer-events-none absolute inset-0" aria-hidden="true">
            <div className="absolute -left-20 -top-20 h-80 w-80 rounded-full bg-white opacity-[0.05] blur-3xl" />
            <div className="absolute -bottom-20 -right-20 h-80 w-80 rounded-full bg-white opacity-[0.05] blur-3xl" />
          </div>

          <h2 id="cta-heading" className="mb-4 text-2xl font-black text-white">
            Ready to run the platform?
          </h2>
          <p className="mx-auto mb-10 max-w-lg text-sm text-primary-100">
            Generate a floor plan in CadStudio, query the Egyptian Building Code through ArchChat,
            or review the full feature index before you start.
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
            <Link to="/features" className="app-button-secondary border-white/20 text-white hover:bg-white/10 flex items-center gap-2">
              <Sliders className="h-4 w-4" />
              Explore Features
            </Link>
            <Link to="/developers" className="app-button-ghost text-white">
              Meet the Builder
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}