import React from 'react';
import { motion } from 'framer-motion';

export default function DocsIllustration() {
  return (
    <div className="relative w-full max-w-lg aspect-square mx-auto flex items-center justify-center p-6 bg-slate-50/40 dark:bg-zinc-900/30 rounded-3xl border border-slate-200/50 dark:border-white/5 shadow-medium overflow-hidden">
      {/* Subtle Blueprint Grid */}
      <div 
        className="absolute inset-0 opacity-40 dark:opacity-20" 
        style={{
          backgroundImage: `
            linear-gradient(rgba(124, 58, 237, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(124, 58, 237, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      />

      <svg
        viewBox="0 0 400 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full relative z-10 text-slate-500"
      >
        <defs>
          <linearGradient id="purpleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.85" />
          </linearGradient>
          <linearGradient id="nodeGlow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#818cf8" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.01" />
          </linearGradient>
        </defs>

        {/* Central Vertical Connector Line */}
        <line x1="200" y1="50" x2="200" y2="350" stroke="rgba(124, 58, 237, 0.2)" strokeWidth="1.5" />

        {/* API Entry Node (Top) */}
        <g>
          <motion.circle 
            cx="200" 
            cy="70" 
            r="18" 
            fill="url(#purpleGradient)" 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
          />
          <path d="M195 70h10M200 65v10" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
          <text x="230" y="74" fill="currentColor" fontSize="10" fontWeight="800" letterSpacing="0.04em">POST /api/v1/generate</text>
        </g>

        {/* Vector DB / Qdrant Retrival Node (Left Branch) */}
        <g>
          <motion.line 
            x1="200" y1="170" x2="110" y2="170" 
            stroke="url(#purpleGradient)" strokeWidth="1.5"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          />
          <motion.rect 
            x="30" y="130" width="80" height="80" rx="8" 
            fill="url(#nodeGlow)" stroke="currentColor" strokeWidth="1"
            initial={{ opacity: 0, y: 140 }}
            animate={{ opacity: 0.9, y: 130 }}
            transition={{ delay: 0.7, duration: 0.5 }}
          />
          {/* Cylinder Layers for DB symbol */}
          <ellipse cx="70" cy="155" rx="20" ry="6" stroke="currentColor" strokeWidth="1" />
          <path d="M50 155v12c0 3.3 9 6 20 6s20-2.7 20-6v-12" stroke="currentColor" strokeWidth="1" fill="none" />
          <path d="M50 167v12c0 3.3 9 6 20 6s20-2.7 20-6v-12" stroke="currentColor" strokeWidth="1" fill="none" />
          <text x="70" y="198" fill="currentColor" fontSize="8" fontWeight="700" textAnchor="middle" letterSpacing="0.02em">VECTOR STORE</text>
        </g>

        {/* Parameter Intent Parser / Model Config Node (Right Branch) */}
        <g>
          <motion.line 
            x1="200" y1="270" x2="290" y2="270" 
            stroke="url(#purpleGradient)" strokeWidth="1.5"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
          />
          <motion.rect 
            x="290" y="230" width="80" height="80" rx="8" 
            fill="url(#nodeGlow)" stroke="currentColor" strokeWidth="1"
            initial={{ opacity: 0, y: 240 }}
            animate={{ opacity: 0.9, y: 230 }}
            transition={{ delay: 1.1, duration: 0.5 }}
          />
          {/* Layout coordinates matrix preview */}
          <line x1="305" y1="250" x2="335" y2="250" stroke="currentColor" strokeWidth="1" />
          <line x1="305" y1="262" x2="355" y2="262" stroke="currentColor" strokeWidth="1" strokeDasharray="3 3" />
          <line x1="305" y1="274" x2="345" y2="274" stroke="currentColor" strokeWidth="1" />
          <circle cx="345" cy="286" r="3" fill="#7c3aed" className="glow-dot" />
          <line x1="305" y1="286" x2="335" y2="286" stroke="currentColor" strokeWidth="1" />
          <text x="330" y="300" fill="currentColor" fontSize="8" fontWeight="700" textAnchor="middle" letterSpacing="0.02em">INTENT PARSER</text>
        </g>

        {/* File Exporter / DXF Node (Bottom) */}
        <g>
          <motion.circle 
            cx="200" 
            cy="330" 
            r="16" 
            fill="url(#purpleGradient)" 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 1.4, duration: 0.5 }}
          />
          <path d="M194 330h12M197 325l3 5-3 5" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <text x="226" y="333" fill="currentColor" fontSize="10" fontWeight="800" letterSpacing="0.04em">ezdxf EXPORTER (.dxf)</text>
        </g>

        {/* Moving data packets along lines */}
        <motion.circle
          cx="200"
          cy="70"
          r="4"
          fill="#3b82f6"
          animate={{
            cy: [70, 170, 170, 170],
            cx: [200, 200, 110, 110],
            opacity: [0, 1, 1, 0]
          }}
          transition={{
            duration: 3,
            ease: "easeInOut",
            repeat: Infinity,
            repeatDelay: 1
          }}
        />

        <motion.circle
          cx="200"
          cy="170"
          r="4"
          fill="#7c3aed"
          animate={{
            cy: [170, 270, 270, 270],
            cx: [200, 200, 290, 290],
            opacity: [0, 1, 1, 0]
          }}
          transition={{
            duration: 3,
            ease: "easeInOut",
            repeat: Infinity,
            repeatDelay: 1.5
          }}
        />
      </svg>

      {/* Side labels */}
      <div className="absolute top-4 left-4 font-mono text-[9px] text-slate-400/80 pointer-events-none select-none">
        SCHEMA :: EBC_ZONING_V1
      </div>
      <div className="absolute bottom-4 right-4 font-mono text-[8px] text-slate-400/80 pointer-events-none select-none">
        Local vector search collections online
      </div>
    </div>
  );
}
