import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Send, Sparkles, History, Keyboard, ShieldAlert } from 'lucide-react';

const PROMPT_TEMPLATES = [
  { label: 'Studio Apt', text: 'Modern 1-bedroom studio apartment with open layout, kitchen, bathroom' },
  { label: '2-Bed Apt', text: 'Cozy 2-bedroom apartment with separate kitchen and living room' },
  { label: '3-Bed Family', text: 'Spacious 3-bedroom family apartment with master suite and balcony' },
  { label: 'Small Office', text: 'Small office layout with reception area, meeting room, and 4 desks' }
];

export default function PromptComposerNext({
  onSend,
  modelsCatalog = [],
  defaultModel = 'qwen_cloud',
  disabled = false,
  refinementLabel = null,
  onClearRefine = () => {},
  placeholder = "Describe your floor plan layout (e.g. 'Modern 2-bedroom with 80sqm area...')"
}) {
  const [prompt, setPrompt] = useState('');
  const [selectedModel, setSelectedModel] = useState(defaultModel);
  const [recoveryMode, setRecoveryMode] = useState('repair'); // 'repair' or 'strict'

  const textareaRef = useRef(null);

  useEffect(() => {
    if (defaultModel) {
      setSelectedModel(defaultModel);
    }
  }, [defaultModel]);

  // Auto-grow textarea height
  const handleTextareaChange = (e) => {
    const value = e.target.value;
    setPrompt(value);
    
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleSend = () => {
    const trimmed = prompt.trim();
    if (!trimmed || trimmed.length < 3) return;
    
    onSend({
      prompt: trimmed,
      model: selectedModel,
      recoveryMode
    });
    
    setPrompt('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift key)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const applyTemplate = (text) => {
    setPrompt(text);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
      }, 0);
    }
  };

  return (
    <div className="border-t border-slate-200 dark:border-slate-850 bg-white/95 dark:bg-slate-900/95 p-4 flex flex-col gap-3 z-10 shadow-lg shadow-slate-100/50 dark:shadow-none">
      {/* Template Suggestions list */}
      <div className="flex flex-wrap gap-1.5 overflow-x-auto pb-1 select-none no-scrollbar">
        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider py-1 mr-1 flex items-center gap-1 shrink-0">
          <History className="h-3 w-3" /> Templates:
        </span>
        {PROMPT_TEMPLATES.map((tmpl) => (
          <button
            key={tmpl.label}
            type="button"
            onClick={() => applyTemplate(tmpl.text)}
            className="text-[10px] font-bold px-2 py-1 bg-slate-50 hover:bg-slate-100 dark:bg-slate-850 dark:hover:bg-slate-800 text-slate-655 dark:text-slate-350 border border-slate-200 dark:border-slate-800 rounded-md transition-all shrink-0"
            disabled={disabled}
          >
            {tmpl.label}
          </button>
        ))}
      </div>

      {/* Composer Input Area */}
      <div className="relative border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-950 p-2.5 flex flex-col gap-2.5 focus-within:ring-1 focus-within:ring-sky-500/50 focus-within:border-sky-500 shadow-sm focus-within:shadow-md transition-all">
        {refinementLabel && (
          <div className="flex items-center justify-between bg-sky-500/5 dark:bg-sky-500/10 border border-sky-200/50 dark:border-sky-900/30 rounded-lg p-1.5 px-2.5 animate-fade-in">
            <span className="text-[10px] text-sky-600 dark:text-sky-400 font-mono font-bold flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-sky-500" />
              Refining context: {refinementLabel}
            </span>
            <button
              type="button"
              onClick={onClearRefine}
              className="text-[10px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-250 font-bold font-sans transition-colors"
              title="Clear refinement source"
            >
              ✕
            </button>
          </div>
        )}

        <textarea
          ref={textareaRef}
          rows={2}
          value={prompt}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full resize-none bg-transparent border-none text-xs md:text-sm text-slate-800 dark:text-slate-150 focus:outline-none p-1 placeholder-slate-450 dark:placeholder-slate-600 leading-relaxed font-sans"
          disabled={disabled}
        />

        <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-850 pt-2 px-1">
          {/* Controls: Model Catalog & Recovery Mode */}
          <div className="flex items-center gap-3">
            {/* Model catalogs picker */}
            <div className="flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-sky-550 shrink-0" />
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-transparent border-none text-[10px] font-bold text-slate-600 dark:text-slate-350 focus:outline-none cursor-pointer hover:text-slate-800 dark:hover:text-slate-100 transition-colors"
                disabled={disabled}
              >
                {modelsCatalog.length > 0 ? (
                  modelsCatalog.map((m) => (
                    <option key={m.request_value} value={m.request_value} className="bg-white dark:bg-slate-900">
                      {m.display_name}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="qwen_cloud" className="bg-white dark:bg-slate-900">Ollama Cloud (Qwen)</option>
                    <option value="huggingface" className="bg-white dark:bg-slate-900">HuggingFace Local</option>
                    <option value="ollama" className="bg-white dark:bg-slate-900">Ollama Local</option>
                  </>
                )}
              </select>
            </div>

            <div className="w-px h-3 bg-slate-200 dark:bg-slate-850" />

            {/* Recovery Mode toggler */}
            <div className="flex items-center gap-1">
              <ShieldAlert className="h-3 w-3 text-amber-550 shrink-0" />
              <select
                value={recoveryMode}
                onChange={(e) => setRecoveryMode(e.target.value)}
                className="bg-transparent border-none text-[10px] font-bold text-slate-600 dark:text-slate-350 focus:outline-none cursor-pointer hover:text-slate-800 dark:hover:text-slate-100 transition-colors"
                disabled={disabled}
              >
                <option value="repair" className="bg-white dark:bg-slate-900">Auto Repair</option>
                <option value="strict" className="bg-white dark:bg-slate-900">Strict Mode</option>
              </select>
            </div>
          </div>

          {/* Submit Action */}
          <div className="flex items-center gap-2.5">
            <span className="hidden md:inline-flex items-center gap-0.5 text-[9px] text-slate-400 font-mono">
              <Keyboard className="h-3 w-3" />
              <span>Enter</span>
            </span>
            <button
              type="button"
              onClick={handleSend}
              disabled={disabled || !prompt.trim() || prompt.trim().length < 3}
              className="p-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition-all disabled:opacity-40 disabled:hover:bg-sky-500 shrink-0 shadow-sm"
              title="Generate DXF layout"
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

PromptComposerNext.propTypes = {
  onSend: PropTypes.func.isRequired,
  modelsCatalog: PropTypes.arrayOf(PropTypes.object),
  defaultModel: PropTypes.string,
  disabled: PropTypes.bool,
  refinementLabel: PropTypes.string,
  onClearRefine: PropTypes.func,
  placeholder: PropTypes.string
};
