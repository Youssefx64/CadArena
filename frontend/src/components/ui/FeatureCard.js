import React from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import {
  MessageSquare, History, Database, FileText, Link, LayoutGrid,
  Activity, Cpu, PenTool, Grid, Sliders, CheckSquare, Layers,
  Download, Upload, MousePointer, Lock, UserCheck, BarChart3,
  Heart, Trash2, Users, Eye, Calculator, HardDriveUpload, GitBranch, HelpCircle
} from '../IconRegistry';

const ICON_MAP = {
  multi_turn_chat: MessageSquare,
  chat_history: History,
  rag_search: Database,
  document_ingestion: FileText,
  citations: Link,
  preview_workspace: LayoutGrid,
  reasoner_timeline: Activity,
  model_selector: Cpu,
  text_to_dxf: PenTool,
  layout_planner: Grid,
  iterative_editing: Sliders,
  quality_gate: CheckSquare,
  cad_layers: Layers,
  raster_export: Download,
  dxf_upload: Upload,
  canvas_navigation: MousePointer,
  user_auth: Lock,
  guest_access: UserCheck,
  metrics: BarChart3,
  health_checks: Heart,
  cleanup_loop: Trash2,
  realtime_collab: Users,
  threejs_walkthrough: Eye,
  material_costing: Calculator,
  dwg_revit_support: HardDriveUpload,
  revision_history: GitBranch,
};

const PRODUCT_THEMES = {
  archchat: {
    label: 'ArchChat',
    class: 'border-violet-500/20 text-violet-700 dark:text-violet-300 bg-violet-50 dark:bg-violet-950/20'
  },
  cadstudio: {
    label: 'CadStudio',
    class: 'border-blue-500/20 text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/20'
  },
  platform: {
    label: 'Platform',
    class: 'border-emerald-500/20 text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/20'
  }
};

const STATUS_THEMES = {
  implemented: {
    label: 'Implemented',
    class: 'border-green-500/20 text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-950/20'
  },
  beta: {
    label: 'Beta',
    class: 'border-indigo-500/20 text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/20'
  },
  experimental: {
    label: 'Experimental',
    class: 'border-amber-500/20 text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/20'
  },
  'coming-soon': {
    label: 'Coming Soon',
    class: 'border-slate-500/20 text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-900/20'
  }
};

// Helper function to highlight matching search term
function HighlightedText({ text, search }) {
  if (!search || !text) return <span>{text}</span>;
  
  const regex = new RegExp(`(${search.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);
  
  return (
    <span>
      {parts.map((part, i) => 
        regex.test(part) ? (
          <span 
            key={i} 
            className="bg-primary-100 text-slate-950 dark:bg-violet-950/80 dark:text-violet-200 px-0.5 rounded font-bold"
          >
            {part}
          </span>
        ) : (
          part
        )
      )}
    </span>
  );
}

HighlightedText.propTypes = {
  text: PropTypes.string.isRequired,
  search: PropTypes.string,
};

function FeatureCard({ feature, onOpenDetails, searchTerm = '' }) {
  const IconComponent = ICON_MAP[feature.id] || HelpCircle;
  const productTheme = PRODUCT_THEMES[feature.product] || { label: feature.product, class: 'border-slate-200 bg-slate-50 text-slate-600' };
  const statusTheme = STATUS_THEMES[feature.status] || { label: feature.status, class: 'border-slate-200 bg-slate-50 text-slate-600' };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onOpenDetails(feature);
    }
  };

  return (
    <motion.div
      tabIndex={0}
      role="button"
      aria-label={`Inspect feature details for ${feature.title}`}
      onKeyDown={handleKeyDown}
      onClick={() => onOpenDetails(feature)}
      whileHover={{ y: -6, scale: 1.015 }}
      whileTap={{ scale: 0.985 }}
      className="app-card app-card-hover flex flex-col p-6 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 select-none relative overflow-hidden"
    >
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="app-icon-badge flex-shrink-0" aria-hidden="true">
          <IconComponent className="h-5 w-5" />
        </div>
        <div className="flex flex-wrap gap-1.5 justify-end">
          <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-full border ${productTheme.class}`}>
            {productTheme.label}
          </span>
          <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-full border ${statusTheme.class}`}>
            {statusTheme.label}
          </span>
        </div>
      </div>

      <h3 className="app-card-title mb-2 text-base font-bold">
        <HighlightedText text={feature.title} search={searchTerm} />
      </h3>
      
      <p className="app-body text-xs flex-1 line-clamp-3 text-slate-500 dark:text-slate-400">
        <HighlightedText text={feature.description} search={searchTerm} />
      </p>

      {feature.tags && feature.tags.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5" aria-label="Feature categories">
          {feature.tags.slice(0, 3).map((tag) => (
            <span 
              key={tag} 
              className="text-[10px] font-semibold bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/5 px-2 py-0.5 rounded text-slate-500 dark:text-slate-400"
            >
              {tag}
            </span>
          ))}
          {feature.tags.length > 3 && (
            <span className="text-[10px] font-semibold text-slate-400 px-1 py-0.5">
              +{feature.tags.length - 3}
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
}

FeatureCard.propTypes = {
  feature: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    product: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    tags: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  onOpenDetails: PropTypes.func.isRequired,
  searchTerm: PropTypes.string,
};

export default React.memo(FeatureCard);
