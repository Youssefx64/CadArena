import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { 
  Loader2, AlertCircle, Cpu, ChevronDown, Check, ShieldAlert
} from 'lucide-react';

const STAGES = [
  { key: 'intent', name: 'Intent Parsing', desc: 'Classifying architectural intent and boundary requests.' },
  { key: 'extraction', name: 'Requirement Extraction', desc: 'Extracting room program and spatial constraints.' },
  { key: 'planning', name: 'Layout Planning', desc: 'Deterministic placement of structural boundaries.' },
  { key: 'constraints', name: 'Constraint Solving', desc: 'Solving topological connections and openings.' },
  { key: 'compliance', name: 'Compliance Validation', desc: 'Validating geometry against architectural code standards.' },
  { key: 'optimization', name: 'Geometry Optimization', desc: 'Optimizing wall sizes and layout efficiency.' },
  { key: 'generation', name: 'DXF Generation', desc: 'Translating geometry coordinates to standard DXF vectors.' }
];

export default function ReasoningTimelineNext({
  status = 'complete', // 'running', 'complete', 'error'
  activeModel = 'qwen_cloud',
  latencyMs = 0,
  errorPayload = null,
  activeStep = 0 // current index if running
}) {
  const [isOpen, setIsOpen] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);

  // Animate steps if running
  useEffect(() => {
    if (status !== 'running') return;
    
    // Auto-progress simulated steps during generating
    setCurrentStep(0);
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < STAGES.length - 1) return prev + 1;
        return prev;
      });
    }, 1800); // cycle step every 1.8 seconds

    return () => clearInterval(interval);
  }, [status]);

  // Determine stage visual state
  const getStageState = (index) => {
    if (status === 'running') {
      if (index < currentStep) return 'complete';
      if (index === currentStep) return 'running';
      return 'pending';
    }
    
    if (status === 'error') {
      const errorStageIndex = getErrorStageIndex();
      if (index < errorStageIndex) return 'complete';
      if (index === errorStageIndex) return 'error';
      return 'pending';
    }

    return 'complete'; // if successful, all are complete
  };

  // Map API error codes to the corresponding failing stage index
  const getErrorStageIndex = () => {
    if (!errorPayload || !errorPayload.code) return 2; // Default to layout planning
    const code = errorPayload.code;
    
    if (code === 'PROJECT_NOT_FOUND' || code === 'INVALID_WORKSPACE_INPUT') return 0;
    if (code === 'INVALID_STRUCTURED_OUTPUT') return 1;
    if (code === 'LAYOUT_PLANNING_FAILED') return 2;
    if (code === 'DXF_INTENT_INVALID') return 3;
    if (code === 'LAYOUT_QUALITY_REJECTED') return 4;
    if (code === 'GENERATE_DXF_FAILED') return 6;
    
    return 2; // default fallback
  };

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden bg-slate-50/50 dark:bg-slate-900/30 text-xs shadow-xs">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 text-left hover:bg-slate-100/40 dark:hover:bg-slate-800/20 transition-colors border-b border-slate-200 dark:border-slate-800 select-none font-bold"
      >
        <span className="flex items-center gap-2 font-mono text-[11px] text-slate-700 dark:text-slate-350">
          <Cpu className={`h-4.5 w-4.5 text-indigo-500 ${status === 'running' ? 'animate-spin' : ''}`} />
          AI Execution Pipeline 
          <span className="text-[10px] font-normal text-slate-400">
            {status === 'running' 
              ? `(Running stage ${currentStep + 1}/${STAGES.length})`
              : status === 'error'
                ? `(Failed at stage ${getErrorStageIndex() + 1}/${STAGES.length})`
                : `(Pipeline successful — ${latencyMs.toFixed(0)}ms)`}
          </span>
        </span>
        <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="p-3.5 space-y-2">
          {STAGES.map((stage, idx) => {
            const state = getStageState(idx);

            return (
              <div key={stage.key} className="flex flex-col">
                <div className="flex items-center gap-2.5 py-1">
                  {/* Status Indicator circle */}
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 border text-[10px] ${
                    state === 'complete' 
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500' 
                      : state === 'running'
                        ? 'bg-sky-500/10 border-sky-500/20 text-sky-500 ring-2 ring-sky-400/20'
                        : state === 'error'
                          ? 'bg-red-500/10 border-red-500/20 text-red-500 font-bold'
                          : 'bg-slate-100 border-slate-200 dark:bg-slate-800 dark:border-slate-700 text-slate-450'
                  }`}>
                    {state === 'complete' ? (
                      <Check className="w-3 h-3 stroke-[2.5]" />
                    ) : state === 'running' ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : state === 'error' ? (
                      <AlertCircle className="w-3.5 h-3.5" />
                    ) : (
                      <span>{idx + 1}</span>
                    )}
                  </span>

                  {/* Stage Details */}
                  <span className={`font-semibold truncate text-[11px] ${
                    state === 'complete' 
                      ? 'text-slate-800 dark:text-slate-200' 
                      : state === 'running'
                        ? 'text-sky-600 dark:text-sky-400 font-bold'
                        : state === 'error'
                          ? 'text-red-500 font-bold'
                          : 'text-slate-400'
                  }`}>
                    {stage.name}
                  </span>

                  <span className="text-[10px] text-slate-400 truncate hidden md:inline flex-1 leading-none">
                    — {stage.desc}
                  </span>

                  {/* Latency / Model Tag */}
                  <div className="ml-auto flex items-center gap-1.5 shrink-0 select-none">
                    {state === 'running' && (
                      <span className="text-[8px] uppercase tracking-wider bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 font-bold px-1.5 py-0.2 rounded font-mono">
                        {activeModel}
                      </span>
                    )}
                    {state === 'complete' && (
                      <span className="text-[9px] font-mono font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.2 rounded">
                        Success
                      </span>
                    )}
                  </div>
                </div>

                {/* Failing Stage Error Trace */}
                {state === 'error' && errorPayload && (
                  <div className="ml-7 mt-1.5 p-3 rounded-lg border border-red-200/50 dark:border-red-950/30 bg-red-50/20 dark:bg-red-950/10 text-[10px] text-red-600 dark:text-red-400 space-y-1 font-mono">
                    <p className="font-bold flex items-center gap-1">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Error Code: {errorPayload.code}
                    </p>
                    <p className="leading-relaxed">{errorPayload.message}</p>
                    {errorPayload.violated_rule && (
                      <p className="text-amber-600 dark:text-amber-400">Violated Rule: {errorPayload.violated_rule}</p>
                    )}
                    {errorPayload.room && (
                      <p>Target Room: {errorPayload.room}</p>
                    )}
                    {errorPayload.details && errorPayload.details.length > 0 && (
                      <div className="border-t border-red-200/30 dark:border-red-950/30 pt-1.5 mt-1.5">
                        <p className="font-bold mb-0.5">Execution Details:</p>
                        <ul className="list-disc pl-4 space-y-0.5">
                          {errorPayload.details.map((d, dIdx) => (
                            <li key={dIdx}>{d}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

ReasoningTimelineNext.propTypes = {
  status: PropTypes.oneOf(['running', 'complete', 'error']),
  activeModel: PropTypes.string,
  latencyMs: PropTypes.number,
  errorPayload: PropTypes.shape({
    code: PropTypes.string,
    message: PropTypes.string,
    violated_rule: PropTypes.string,
    room: PropTypes.string,
    details: PropTypes.arrayOf(PropTypes.string)
  }),
  activeStep: PropTypes.number
};
