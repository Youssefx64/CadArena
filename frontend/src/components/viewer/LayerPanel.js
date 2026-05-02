import React from 'react';
import { Layers, Eye, EyeOff, Info } from 'lucide-react';

const LAYER_COLORS = {
  WALLS: '#0f172a',
  DOORS: '#1e293b',
  WINDOWS: '#334155',
  BORDER: '#0f172a',
  ROOM_LABELS: '#1e293b',
  DIMENSIONS: '#1d4ed8',
  HATCH: '#94a3b8',
  FURNITURE: '#9ca3af',
  FURNITURE_BEDROOM: '#a78bfa',
  FURNITURE_SANITARY: '#22d3ee',
  FURNITURE_LIVING: '#4ade80',
  FURNITURE_KITCHEN: '#fb923c',
  DEFPOINTS: '#6b7280',
  '0': '#6b7280',
};

function getLayerColor(name) {
  return LAYER_COLORS[name] || '#6366f1';
}

function LayerPanel({ layers, onToggle, loading, collapsed, onCollapse }) {
  const visible = layers.filter((l) => l.visible).length;

  if (collapsed) {
    return (
      <button
        className="viewer-layer-panel-collapsed"
        onClick={onCollapse}
        title="Show layer panel"
      >
        <Layers className="h-4 w-4 text-slate-500" />
      </button>
    );
  }

  return (
    <div className="viewer-layer-panel">
      <div className="flex items-center gap-1.5 mb-3">
        <Layers className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
        <span className="text-xs font-bold uppercase tracking-widest text-slate-400 flex-1">
          Layers
        </span>
        <span className="text-xs font-semibold text-primary-600">
          {visible}/{layers.length}
        </span>
        <button
          className="ml-1 p-0.5 rounded hover:bg-slate-100 transition-colors"
          onClick={onCollapse}
          title="Collapse panel"
        >
          <svg className="h-3.5 w-3.5 text-slate-400" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10 3L5 8l5 5" />
          </svg>
        </button>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="app-skeleton h-8 w-full rounded-xl" />
          ))}
        </div>
      ) : layers.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-6">No layers detected</p>
      ) : (
        <ul className="space-y-0.5">
          {layers.map((layer) => (
            <li key={layer.name}>
              <button
                className={`viewer-layer-item w-full${!layer.visible ? ' opacity-40' : ''}`}
                onClick={() => onToggle(layer.name)}
                title={layer.visible ? 'Hide layer' : 'Show layer'}
              >
                <span
                  className="viewer-layer-dot"
                  style={{ background: getLayerColor(layer.name) }}
                />
                <span className="flex-1 text-left truncate">{layer.name}</span>
                {layer.visible ? (
                  <Eye className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                ) : (
                  <EyeOff className="h-3.5 w-3.5 text-slate-300 flex-shrink-0" />
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {!loading && (
        <div className="mt-4 rounded-xl border border-primary-100 bg-primary-50 p-3">
          <p className="flex items-start gap-1.5 text-[0.6875rem] leading-relaxed text-primary-600">
            <Info className="mt-0.5 h-3 w-3 flex-shrink-0" />
            Layer legend reflects DXF structure. Regenerate in Studio to adjust layer visibility.
          </p>
        </div>
      )}
    </div>
  );
}

export default LayerPanel;
