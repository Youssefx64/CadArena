/* eslint-disable react/prop-types */
import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { 
  FileCode2, Download, Eye, 
  CheckCircle, Database, Loader2, Sparkles, ShieldAlert
} from 'lucide-react';
import PromptComposerNext from './PromptComposerNext';
import ReasoningTimelineNext from './ReasoningTimelineNext';
import cadArenaAPI from '../../services/api';

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

function renderAssistantMessage(text) {
  if (!text) return null;
  
  const lines = text.split('\n');
  const renderedElements = [];
  let inList = false;
  let listItems = [];

  const flushList = (key) => {
    if (listItems.length > 0) {
      renderedElements.push(
        <ul key={`list_${key}`} className="list-disc pl-5 my-1.5 space-y-1 text-slate-700 dark:text-slate-300">
          {listItems}
        </ul>
      );
      listItems = [];
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList(index);
      return;
    }

    const isBullet = trimmed.startsWith('- ') || trimmed.startsWith('* ');
    const content = isBullet ? trimmed.substring(2) : line;

    // Parse **bold** parts
    const parts = content.split('**');
    const elements = parts.map((part, partIdx) => {
      if (partIdx % 2 === 1) {
        return <strong key={partIdx} className="font-extrabold text-slate-900 dark:text-white">{part}</strong>;
      }
      return part;
    });

    if (isBullet) {
      if (!inList) {
        inList = true;
      }
      listItems.push(
        <li key={index} className="text-xs leading-relaxed text-slate-655 dark:text-slate-350">
          {elements}
        </li>
      );
    } else {
      if (inList) {
        flushList(index);
        inList = false;
      }
      renderedElements.push(
        <p key={index} className="text-xs leading-relaxed text-slate-655 dark:text-slate-350 mb-1">
          {elements}
        </p>
      );
    }
  });

  if (inList) {
    flushList('final');
  }

  return (
    <div className="text-xs text-slate-655 dark:text-slate-350 leading-relaxed font-sans bg-slate-50/50 dark:bg-slate-950/20 p-3 rounded-lg border border-slate-200/50 dark:border-slate-850/50 space-y-1">
      {renderedElements}
    </div>
  );
}

// eslint-disable-next-line react/prop-types
function EngineeringErrorCard({ errorDetails, text }) {
  const [expanded, setExpanded] = useState(false);
  const code = errorDetails?.code || 'GENERATION_ERROR';
  const message = errorDetails?.message || text || 'An unexpected failure occurred during layout generation';
  const stage = errorDetails?.stage || (code.includes('PARSER') || code.includes('JSON') || code.includes('OUTPUT') ? 'Design Parser' : 'Constraint Solver');

  return (
    <div className="border border-red-200/50 dark:border-red-900/30 bg-red-50/10 dark:bg-red-950/10 rounded-xl p-3.5 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-red-650 dark:text-red-400">
        <ShieldAlert className="h-4 w-4" />
        <span className="text-[10px] font-bold uppercase tracking-wider">Generation Failed</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px] border-b border-red-150/40 dark:border-red-900/10 pb-3">
        <div>
          <span className="text-slate-400 dark:text-slate-500 font-bold block text-[9px] uppercase tracking-wide">Reason:</span>
          <span className="text-slate-700 dark:text-slate-350 font-medium leading-relaxed">{message}</span>
        </div>
        <div>
          <span className="text-slate-400 dark:text-slate-500 font-bold block text-[9px] uppercase tracking-wide">Stage:</span>
          <span className="text-slate-700 dark:text-slate-350 font-medium">{stage}</span>
        </div>
        <div>
          <span className="text-slate-400 dark:text-slate-500 font-bold block text-[9px] uppercase tracking-wide">Code:</span>
          <span className="text-red-600 dark:text-red-450 font-mono font-bold">{code}</span>
        </div>
      </div>

      {errorDetails && (
        <div className="flex flex-col gap-1.5 pt-0.5">
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-[9px] text-slate-500 hover:text-slate-750 dark:hover:text-slate-250 font-bold flex items-center gap-1 self-start transition-colors"
          >
            <span>{expanded ? 'Hide Details ▲' : 'Show Details ▼'}</span>
          </button>

          {expanded && (
            <pre className="text-[10px] font-mono p-3 bg-slate-950 text-red-400 dark:text-red-300/90 rounded-lg border border-slate-900 overflow-x-auto max-h-[160px] leading-normal w-full">
              {JSON.stringify(errorDetails, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export default function ActivityFeedNext({
  messages,
  activeFileToken,
  onSelectVersion,
  onSendPrompt,
  onRefine, // trigger refinement selection
  isGenerating = false,
  activePromptParams = null, // prompt, model, recoveryMode when active
  modelsCatalog = [],
  defaultModel = 'qwen_cloud',
  projectName = '',
  refinementLabel = null,
  onClearRefine = () => {}
}) {
  const feedEndRef = useRef(null);

  // Auto-scroll to bottom of activity feed
  useEffect(() => {
    if (feedEndRef.current) {
      feedEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isGenerating]);

  // Compile assistant generations
  const generationRecords = React.useMemo(() => {
    const findTriggeringPrompt = (assistantMsgIndex) => {
      for (let i = assistantMsgIndex - 1; i >= 0; i--) {
        if (messages[i].role === 'user') {
          return messages[i].text || messages[i].content || '';
        }
      }
      return 'Initial Generation Trigger';
    };
    const records = [];
    messages.forEach((msg, idx) => {
      if (msg.role === 'assistant') {
        const triggerPrompt = findTriggeringPrompt(idx);
        records.push({
          msgId: msg.id,
          prompt: triggerPrompt,
          text: msg.text || msg.content || '',
          fileToken: msg.file_token,
          dxfName: msg.dxf_name || 'layout.dxf',
          modelUsed: msg.model_used || 'default',
          providerUsed: msg.provider_used || 'default',
          latencyMs: msg.latency_ms || 0,
          qualityReport: msg.quality_report || null,
          metrics: msg.metrics || null,
          timestamp: msg.created_at || new Date().toISOString(),
          errorDetails: msg.error_details || null,
          isError: msg.role === 'error' || (!msg.file_token && msg.text && msg.text.includes('Error'))
        });
      } else if (msg.role === 'error') {
        const triggerPrompt = findTriggeringPrompt(idx);
        records.push({
          msgId: msg.id,
          prompt: triggerPrompt,
          text: msg.text || msg.content || 'Generation failed',
          isError: true,
          errorDetails: msg.error_details || { code: 'GENERATE_DXF_FAILED', message: msg.text || 'Geometry constraint execution failed' },
          timestamp: msg.created_at || new Date().toISOString(),
          modelUsed: msg.model_used || 'default'
        });
      }
    });
    return records;
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col min-h-0 relative select-none">
      {/* Activity Header */}
      <div className="h-12 px-4 border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 flex items-center justify-between z-10 select-none">
        <div>
          <span className="text-[9px] font-bold text-sky-500 uppercase tracking-wider block">Activity Feed</span>
          <h2 className="text-xs font-bold truncate text-slate-855 dark:text-slate-200">
            {projectName ? `${projectName} History` : 'Engineering Action History'}
          </h2>
        </div>
        <div className="text-[10px] font-mono font-bold text-slate-400">
          Iterations: {generationRecords.length}
        </div>
      </div>

      {/* Generation List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {generationRecords.length === 0 && !isGenerating ? (
          <div className="h-full flex flex-col items-center justify-center text-center py-16">
            <span className="app-icon-badge-lg mb-4" style={{ background: 'rgba(56,189,248,0.06)' }}>
              <FileCode2 className="h-8 w-8 text-sky-500" />
            </span>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-1">No Activity Records</h3>
            <p className="text-xs text-slate-400 max-w-sm">
              Use the Prompt Composer below to generate your initial floor plan. Every run creates an isolated engineering audit record.
            </p>
          </div>
        ) : (
          generationRecords.map((rec, rIdx) => {
            const isLoaded = rec.fileToken && rec.fileToken === activeFileToken;
            
            return (
              <div 
                key={rec.msgId || rIdx}
                className={classNames(
                  "rounded-xl border p-4 flex flex-col gap-3.5 transition-all",
                  isLoaded
                    ? "border-sky-500 bg-sky-50/5 dark:bg-sky-500/5 ring-1 ring-sky-500/10 shadow-sm"
                    : "border-slate-200 dark:border-slate-850 bg-white dark:bg-slate-900/70 hover:border-slate-350 dark:hover:border-slate-800"
                )}
              >
                {/* Iteration Header metadata */}
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-850/50 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-100 dark:bg-slate-850 text-slate-655 dark:text-slate-350 rounded font-mono">
                      Iteration #{rIdx + 1}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {new Date(rec.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  {rec.modelUsed && (
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
                      <Database className="h-3 w-3" />
                      <span>{rec.modelUsed}</span>
                    </div>
                  )}
                </div>

                {/* User Trigger Prompt */}
                <div className="flex flex-col gap-1.5">
                  <span className="text-[9px] uppercase font-bold tracking-wider text-slate-400 font-mono">Trigger Prompt</span>
                  <blockquote className="text-xs italic pl-3 border-l-2 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                    {rec.prompt}
                  </blockquote>
                </div>

                {/* AI Reasoning Timeline */}
                <ReasoningTimelineNext
                  status={rec.isError ? 'error' : 'complete'}
                  activeModel={rec.modelUsed}
                  latencyMs={rec.latencyMs}
                />

                {/* Error Report (Render professional error cards instead of dumping raw payloads) */}
                {rec.isError && (
                  <EngineeringErrorCard 
                    errorDetails={rec.errorDetails} 
                    text={rec.text} 
                  />
                )}

                {/* Assistant Summary (Only if successful layout generation) */}
                {!rec.isError && rec.text && (
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[9px] uppercase font-bold tracking-wider text-slate-400 font-mono">Assistant Summary</span>
                    {renderAssistantMessage(rec.text)}
                  </div>
                )}

                {/* Compliance score & Grade (Only if successful and quality report exists) */}
                {!rec.isError && rec.qualityReport && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-850 rounded-lg flex items-center gap-4">
                    <div className={classNames(
                      "w-10 h-10 rounded-full flex items-center justify-center font-bold text-base shrink-0 border",
                      rec.qualityReport.passed
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                        : "bg-red-500/10 border-red-500/20 text-red-500"
                    )}>
                      {rec.qualityReport.grade || 'C'}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] font-bold text-slate-800 dark:text-slate-200">
                          {rec.qualityReport.passed ? 'Compliance Standard Passed' : 'Compliance Standard Failed'}
                        </span>
                        <span className="text-[9px] bg-slate-205 dark:bg-slate-850 text-slate-550 font-mono px-1 rounded">
                          {rec.qualityReport.code_profile || 'EBC_RESIDENTIAL_V1'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 truncate mt-0.5 font-mono">
                        Validation Checklist Score: {(rec.qualityReport.score * 100).toFixed(0)}% | Topology: {rec.qualityReport.selected_topology || 'Standard'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Generated CAD Assets */}
                {!rec.isError && rec.fileToken && (
                  <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-850/50 pt-3 mt-1 gap-4">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileCode2 className="h-4.5 w-4.5 text-sky-500 shrink-0" />
                      <span className="text-xs font-mono font-bold truncate text-slate-700 dark:text-slate-300">
                        {rec.dxfName}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {/* Load viewport button */}
                      {!isLoaded ? (
                        <button
                          type="button"
                          onClick={() => onSelectVersion(rec.fileToken, rec.dxfName)}
                          className="px-2 py-1 text-[10px] font-bold border border-sky-400 dark:border-sky-600 bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-900/50 rounded flex items-center gap-1 transition-all"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          <span>Show</span>
                        </button>
                      ) : (
                        <span className="px-2 py-1 text-[10px] font-mono font-bold bg-sky-50 dark:bg-sky-950 text-sky-655 dark:text-sky-400 rounded border border-sky-200/50 dark:border-sky-900/30 flex items-center gap-1 select-none">
                          <CheckCircle className="h-3.5 w-3.5 text-sky-500" />
                          <span>Viewport Active</span>
                        </span>
                      )}

                      {/* Direct DXF Download */}
                      <a
                        href={cadArenaAPI.dxfDownloadUrl(rec.fileToken, rec.dxfName)}
                        download={rec.dxfName}
                        className="px-2 py-1 text-[10px] font-bold border border-slate-200 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-850 rounded text-slate-600 dark:text-slate-350 flex items-center gap-1 transition-all"
                      >
                        <Download className="h-3.5 w-3.5" />
                        <span>Download</span>
                      </a>

                      {/* Refine layout option */}
                      <button
                        type="button"
                        onClick={() => onRefine(rec.msgId, rec.prompt)}
                        className="px-2 py-1 text-[10px] font-bold bg-sky-500 hover:bg-sky-600 text-white rounded flex items-center gap-1 transition-all"
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        <span>Refine</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* ACTIVE RUNNING GENERATION CARD */}
        {isGenerating && activePromptParams && (
          <div className="rounded-xl border border-sky-500 bg-sky-50/5 dark:bg-sky-500/5 ring-1 ring-sky-500/10 shadow-xs p-4 flex flex-col gap-3.5 animate-pulse">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-850/50 pb-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold px-2 py-0.5 bg-sky-100 dark:bg-sky-950 text-sky-655 dark:text-sky-400 rounded font-mono flex items-center gap-1">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Generating...
                </span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Active</span>
            </div>

            <div className="flex flex-col gap-1.5">
              <span className="text-[9px] uppercase font-bold tracking-wider text-slate-400 font-mono">Trigger Prompt</span>
              <blockquote className="text-xs italic pl-3 border-l-2 border-slate-350 dark:border-slate-700 text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                {activePromptParams.prompt}
              </blockquote>
            </div>

            <ReasoningTimelineNext
              status="running"
              activeModel={activePromptParams.model || defaultModel}
              latencyMs={0}
            />
          </div>
        )}

        <div ref={feedEndRef} />
      </div>

      {/* Fixed Composer Bottom */}
      <PromptComposerNext
        onSend={onSendPrompt}
        modelsCatalog={modelsCatalog}
        defaultModel={defaultModel}
        disabled={isGenerating || !projectName}
        refinementLabel={refinementLabel}
        onClearRefine={onClearRefine}
        placeholder={!projectName ? "Create or select a project from the left panel to begin layout generation..." : "Describe your floor plan layout (e.g. 'Modern 2-bedroom with 80sqm area...')"}
      />
    </div>
  );
}

ActivityFeedNext.propTypes = {
  messages: PropTypes.arrayOf(PropTypes.object).isRequired,
  activeFileToken: PropTypes.string,
  onSelectVersion: PropTypes.func.isRequired,
  onSendPrompt: PropTypes.func.isRequired,
  onRefine: PropTypes.func.isRequired,
  isGenerating: PropTypes.bool,
  activePromptParams: PropTypes.shape({
    prompt: PropTypes.string,
    model: PropTypes.string,
    recoveryMode: PropTypes.string
  }),
  modelsCatalog: PropTypes.arrayOf(PropTypes.object),
  defaultModel: PropTypes.string,
  projectName: PropTypes.string,
  refinementLabel: PropTypes.string,
  onClearRefine: PropTypes.func
};
