import React from 'react';
import { motion } from 'framer-motion';

export default function FeaturesIllustration() {
  return (
    <div className="relative w-full max-w-lg aspect-square mx-auto flex items-center justify-center p-6 bg-slate-50/40 dark:bg-zinc-900/30 rounded-3xl border border-slate-200/50 dark:border-white/5 shadow-medium overflow-hidden">
      {/* Blueprint Grid Background */}
      <div 
        className="absolute inset-0 opacity-40 dark:opacity-20" 
        style={{
          backgroundImage: `
            linear-gradient(rgba(59, 130, 246, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px'
        }}
      />

      <svg
        viewBox="0 0 400 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full relative z-10 text-slate-500"
      >
        <defs>
          <linearGradient id="layerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#7c3aed" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="layerFill" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#818cf8" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#c4b5fd" stopOpacity="0.01" />
          </linearGradient>
        </defs>

        {/* Layer 3 - Dimensions Layer (Background) */}
        <g opacity="0.4" style={{ transform: 'translate(0px, -30px)' }}>
          <path d="M60 120h280v180H60z" stroke="currentColor" strokeWidth="0.8" strokeDasharray="4 4" />
          <line x1="60" y1="100" x2="340" y2="100" stroke="currentColor" strokeWidth="0.8" />
          <text x="200" y="93" fill="currentColor" fontSize="8" textAnchor="middle">DIM_OVERRIDE: 14.20m</text>
        </g>

        {/* Layer 2 - Layout/Walls Layer (Midground) */}
        <g opacity="0.6" style={{ transform: 'translate(15px, -15px)' }}>
          <path d="M60 120h280v180H60z" stroke="currentColor" strokeWidth="1.2" />
          {/* Inner walls */}
          <line x1="200" y1="120" x2="200" y2="300" stroke="currentColor" strokeWidth="1" />
          <line x1="60" y1="210" x2="200" y2="210" stroke="currentColor" strokeWidth="1" />
          <circle cx="200" cy="210" r="3" fill="#3b82f6" />
        </g>

        {/* Layer 1 - Active / Compliance Checker Layer (Foreground) */}
        <g style={{ transform: 'translate(30px, 0px)' }}>
          {/* Main layout card boundary */}
          <motion.rect
            x="60"
            y="120"
            width="280"
            height="180"
            rx="6"
            stroke="url(#layerGrad)"
            strokeWidth="2"
            fill="url(#layerFill)"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.8, ease: "easeInOut" }}
          />

          {/* Compliance Check Zones */}
          {/* Setback line */}
          <line x1="80" y1="120" x2="80" y2="300" stroke="#ef4444" strokeWidth="1.2" strokeDasharray="3 3" />
          <text x="88" y="140" fill="#ef4444" fontSize="7" fontWeight="bold">EBC SETBACK LIMIT</text>

          {/* Adjacency verification markers */}
          <circle cx="230" cy="180" r="14" stroke="#10b981" strokeWidth="1.2" fill="none" className="glow-dot" />
          <path d="M225 180l4 4 6-7" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" />
          <text x="230" y="210" fill="#10b981" fontSize="7" fontWeight="bold" textAnchor="middle">PASS: EGRESS WIDTH</text>

          {/* Geometry overlay measurements */}
          <line x1="160" y1="260" x2="290" y2="260" stroke="#3b82f6" strokeWidth="1.2" />
          <circle cx="160" cy="260" r="2.5" fill="#3b82f6" />
          <circle cx="290" cy="260" r="2.5" fill="#3b82f6" />
          <text x="225" y="253" fill="#3b82f6" fontSize="8" fontWeight="bold" textAnchor="middle">L = 6.40m</text>
        </g>

        {/* Isometric view indicator axes in top right */}
        <g style={{ transform: 'translate(330px, 40px)' }} opacity="0.7">
          <line x1="0" y1="0" x2="20" y2="10" stroke="currentColor" strokeWidth="1" />
          <line x1="0" y1="0" x2="-20" y2="10" stroke="currentColor" strokeWidth="1" />
          <line x1="0" y1="0" x2="0" y2="-20" stroke="currentColor" strokeWidth="1" />
          <text x="24" y="14" fill="currentColor" fontSize="6">X</text>
          <text x="-26" y="14" fill="currentColor" fontSize="6">Y</text>
          <text x="0" y="-24" fill="currentColor" fontSize="6" textAnchor="middle">Z</text>
        </g>
      </svg>

      {/* Decorative Blueprint Corner Overlay labels */}
      <div className="absolute top-4 left-4 font-mono text-[9px] text-slate-400/80 pointer-events-none select-none">
        LAYER: LAYER_CAD_COMPLIANCE
      </div>
      <div className="absolute bottom-4 right-4 font-mono text-[8px] text-slate-400/80 pointer-events-none select-none">
        Viewport: Multi-Layer Canvas
      </div>
    </div>
  );
}
