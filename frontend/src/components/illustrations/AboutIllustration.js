import React from 'react';
import { motion } from 'framer-motion';

export default function AboutIllustration() {
  return (
    <div className="relative w-full max-w-lg aspect-square mx-auto flex items-center justify-center p-4 bg-slate-50/40 dark:bg-zinc-900/30 rounded-3xl border border-slate-200/50 dark:border-white/5 shadow-medium overflow-hidden">
      {/* CAD Grid Backdrop */}
      <div 
        className="absolute inset-0 opacity-70 dark:opacity-40" 
        style={{
          backgroundImage: `
            linear-gradient(rgba(99, 102, 241, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px'
        }}
      />

      {/* CAD Blueprint Outline */}
      <svg
        viewBox="0 0 400 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full relative z-10 text-slate-400 dark:text-slate-500"
      >
        {/* Gradients */}
        <defs>
          <linearGradient id="blueprintGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#7c3aed" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="glowGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#818cf8" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#c4b5fd" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Boundary Area / Outer Setbacks */}
        <motion.rect
          x="30"
          y="30"
          width="340"
          height="340"
          rx="12"
          stroke="url(#blueprintGrad)"
          strokeWidth="1.5"
          strokeDasharray="6 4"
          initial={{ strokeDashoffset: 100, opacity: 0 }}
          animate={{ strokeDashoffset: 0, opacity: 0.5 }}
          transition={{ duration: 2, ease: "linear", repeat: Infinity }}
        />

        {/* Inner Building Footprint */}
        <motion.path
          d="M 60,60 L 340,60 L 340,340 L 200,340 L 200,240 L 60,240 Z"
          stroke="currentColor"
          strokeWidth="2"
          fill="url(#glowGrad)"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 2, ease: "easeInOut" }}
        />

        {/* Room Divisions & Dimensions */}
        {/* Living Room */}
        <motion.rect
          x="60"
          y="60"
          width="160"
          height="120"
          stroke="currentColor"
          strokeWidth="1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.8 }}
          transition={{ delay: 0.8, duration: 0.5 }}
        />
        <text x="140" y="120" fill="currentColor" fontSize="11" fontWeight="700" textAnchor="middle" letterSpacing="0.04em">LIVING AREA</text>
        <text x="140" y="135" fill="var(--text-muted)" fontSize="9" textAnchor="middle">5.20m x 4.00m</text>

        {/* Master Bedroom */}
        <motion.rect
          x="220"
          y="60"
          width="120"
          height="140"
          stroke="currentColor"
          strokeWidth="1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.8 }}
          transition={{ delay: 1.1, duration: 0.5 }}
        />
        <text x="280" y="125" fill="currentColor" fontSize="11" fontWeight="700" textAnchor="middle" letterSpacing="0.04em">MASTER BED</text>
        <text x="280" y="140" fill="var(--text-muted)" fontSize="9" textAnchor="middle">3.80m x 4.40m</text>

        {/* Kitchen */}
        <motion.rect
          x="60"
          y="180"
          width="100"
          height="60"
          stroke="currentColor"
          strokeWidth="1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.8 }}
          transition={{ delay: 1.4, duration: 0.5 }}
        />
        <text x="110" y="210" fill="currentColor" fontSize="10" fontWeight="700" textAnchor="middle" letterSpacing="0.04em">KITCHEN</text>
        <text x="110" y="222" fill="var(--text-muted)" fontSize="8" textAnchor="middle">3.00m x 2.00m</text>

        {/* Bathroom */}
        <motion.rect
          x="160"
          y="180"
          width="60"
          height="60"
          stroke="currentColor"
          strokeWidth="1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.8 }}
          transition={{ delay: 1.7, duration: 0.5 }}
        />
        <text x="190" y="210" fill="currentColor" fontSize="9" fontWeight="700" textAnchor="middle" letterSpacing="0.04em">BATH</text>

        {/* Coordinate annotations */}
        <circle cx="60" cy="60" r="3" fill="#6366f1" className="glow-dot" />
        <circle cx="340" cy="60" r="3" fill="#6366f1" />
        <circle cx="340" cy="340" r="3" fill="#6366f1" />
        <circle cx="60" cy="240" r="3" fill="#6366f1" />

        {/* Dimension lines (vertical & horizontal side labels) */}
        <line x1="45" y1="60" x2="45" y2="240" stroke="url(#blueprintGrad)" strokeWidth="1" />
        <line x1="40" y1="60" x2="50" y2="60" stroke="url(#blueprintGrad)" strokeWidth="1" />
        <line x1="40" y1="240" x2="50" y2="240" stroke="url(#blueprintGrad)" strokeWidth="1" />
        
        {/* Rotating Crosshair Anchor */}
        <motion.g
          animate={{ rotate: 360 }}
          transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
          style={{ originX: '200px', originY: '200px' }}
        >
          <circle cx="200" cy="200" r="16" stroke="#7c3aed" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.6" />
          <line x1="200" y1="180" x2="200" y2="220" stroke="#7c3aed" strokeWidth="0.8" opacity="0.6" />
          <line x1="180" y1="200" x2="220" y2="200" stroke="#7c3aed" strokeWidth="0.8" opacity="0.6" />
        </motion.g>
      </svg>
      
      {/* Decorative Blueprint Corner Overlay labels */}
      <div className="absolute top-4 left-4 font-mono text-[9px] text-slate-400/80 uppercase tracking-widest pointer-events-none select-none">
        Arena System Sheet: A-01
      </div>
      <div className="absolute bottom-4 right-4 font-mono text-[8px] text-slate-400/80 pointer-events-none select-none">
        Scale 1:50 · Egyptian Building Code Checked
      </div>
    </div>
  );
}
