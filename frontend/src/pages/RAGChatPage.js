/**
 * ArchChat page.
 *
 * This page talks directly to the standalone RAG API service configured by
 * REACT_APP_RAG_API_URL.
 */
import React from 'react';
import PropTypes from 'prop-types';
import { AnimatePresence, motion } from 'framer-motion';
import Navbar from '../components/layout/Navbar';
import { useDarkMode } from '../hooks/useDarkMode';
import {
  Activity,
  AlertCircle,
  ArrowUp,
  Bot,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Database,
  FileCode2,
  FileText,
  Gauge,
  Loader2,
  MessageSquare,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Trash2,
  UploadCloud,
} from 'lucide-react';
import { useReducedMotion } from '../hooks';
import cadArenaAPI from '../services/api';

const defaultQuestion = 'What engineering guidance is indexed for architectural layout, structural coordination, and code constraints?';

const promptSuggestions = [
  'Summarize the indexed structural and architectural constraints for this project.',
  'Extract code-related notes about setbacks, spans, circulation, fire safety, and daylighting.',
  'List coordination risks between architecture, structure, MEP shafts, and openings.',
];

const panelTransition = { duration: 0.28, ease: [0.22, 1, 0.36, 1] };

const messageVariants = {
  initial: { opacity: 0, y: 12, scale: 0.99 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -8, scale: 0.99 },
};

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

function getConfidence(score) {
  if (typeof score !== 'number') {
    return {
      label: 'Unscored',
      value: 'Pending',
      className: 'rag-score-neutral',
    };
  }

  if (score >= 0.78) {
    return {
      label: 'High',
      value: score.toFixed(3),
      className: 'rag-score-high',
    };
  }

  if (score >= 0.52) {
    return {
      label: 'Medium',
      value: score.toFixed(3),
      className: 'rag-score-medium',
    };
  }

  return {
    label: 'Review',
    value: score.toFixed(3),
    className: 'rag-score-low',
  };
}

function StatusPill({ state }) {
  const labels = {
    healthy: 'Online',
    error: 'Offline',
    checking: 'Checking',
  };

  return (
    <span className={classNames('rag-status-pill', `rag-status-${state}`)}>
      {state === 'checking' ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
      ) : state === 'healthy' ? (
        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
      ) : (
        <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
      )}
      RAG {labels[state]}
    </span>
  );
}

StatusPill.propTypes = {
  state: PropTypes.oneOf(['healthy', 'error', 'checking']).isRequired,
};

function MetricCard({ icon: Icon, label, value, detail, loading }) {
  return (
    <motion.article
      variants={messageVariants}
      initial="initial"
      animate="animate"
      transition={panelTransition}
      className="rag-metric-card"
      title={String(value)}
    >
      <span className="rag-metric-icon" aria-hidden="true">
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <p className="rag-eyebrow">{label}</p>
        {loading ? (
          <span className="app-skeleton mt-2 block h-5 w-28" />
        ) : (
          <p className="rag-metric-value">{value}</p>
        )}
        {detail && <p className="rag-metric-detail">{detail}</p>}
      </div>
    </motion.article>
  );
}

MetricCard.propTypes = {
  icon: PropTypes.elementType.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  detail: PropTypes.string,
  loading: PropTypes.bool,
};

MetricCard.defaultProps = {
  detail: '',
  loading: false,
};

function JsonToken({ token }) {
  let className = 'text-slate-300';
  if (/^"/.test(token)) {
    className = /:$/.test(token) ? 'text-sky-300' : 'text-violet-200';
  } else if (/true|false/.test(token)) {
    className = 'text-emerald-300';
  } else if (/null/.test(token)) {
    className = 'text-slate-500';
  } else {
    className = 'text-amber-200';
  }

  return <span className={className}>{token}</span>;
}

JsonToken.propTypes = {
  token: PropTypes.string.isRequired,
};

function HighlightedJson({ data }) {
  const json = JSON.stringify(data, null, 2);
  const parts = [];
  const pattern = /("(?:\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(?=\s*:)|"(?:\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"|\b(?:true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g;
  let lastIndex = 0;
  let match = pattern.exec(json);

  while (match) {
    if (match.index > lastIndex) {
      parts.push(json.slice(lastIndex, match.index));
    }
    parts.push(<JsonToken key={`${match[0]}-${match.index}`} token={match[0]} />);
    lastIndex = pattern.lastIndex;
    match = pattern.exec(json);
  }

  if (lastIndex < json.length) {
    parts.push(json.slice(lastIndex));
  }

  return <pre className="rag-json-code">{parts}</pre>;
}

HighlightedJson.propTypes = {
  data: PropTypes.object.isRequired,
};

function SourceList({ sources, isLoading }) {
  const [openItems, setOpenItems] = React.useState(() => new Set([0]));

  React.useEffect(() => {
    setOpenItems(new Set(sources.length ? [0] : []));
  }, [sources]);

  const toggleItem = (index) => {
    setOpenItems((current) => {
      const next = new Set(current);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  if (isLoading && !sources.length) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="rag-source-card p-4">
            <span className="app-skeleton mb-3 block h-4 w-32" />
            <span className="app-skeleton mb-2 block h-3 w-full" />
            <span className="app-skeleton block h-3 w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (!sources.length) {
    return (
      <div className="rag-empty-source">
        <FileText className="h-5 w-5 text-slate-500" aria-hidden="true" />
        <div>
          <p className="font-bold text-slate-900 dark:text-slate-100">No retrieved sources</p>
          <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Engineering evidence, code notes, and drawing/spec chunks will appear after retrieval.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sources.map((source, index) => {
        const expanded = openItems.has(index);
        const confidence = getConfidence(source.score);
        const metadata = source.metadata && Object.keys(source.metadata).length > 0 ? source.metadata : null;

        return (
          <motion.article
            key={`${source.text || 'source'}-${index}`}
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.22, delay: index * 0.03 }}
            className="rag-source-card"
          >
            <button
              type="button"
              onClick={() => toggleItem(index)}
              className="rag-source-toggle"
              aria-expanded={expanded}
            >
              <span className="flex min-w-0 items-center gap-3">
                <span className="rag-source-icon" aria-hidden="true">
                  <FileCode2 className="h-4 w-4" />
                </span>
                <span className="min-w-0">
                  <span className="rag-eyebrow">Source {index + 1}</span>
                  <span className="rag-source-title">
                    {metadata?.source || `Retrieved chunk ${index + 1}`}
                  </span>
                </span>
              </span>
              <span className="flex shrink-0 items-center gap-2">
                <span className={classNames('rag-score-chip', confidence.className)}>
                  {confidence.label}
                </span>
                <motion.span animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.18 }}>
                  <ChevronDown className="h-4 w-4 text-slate-500" aria-hidden="true" />
                </motion.span>
              </span>
            </button>

            <AnimatePresence initial={false}>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                  className="overflow-hidden"
                >
                  <div className="rag-source-body">
                    <p className="text-sm leading-7 text-slate-700 dark:text-slate-300">
                      {source.text || 'No source preview returned.'}
                    </p>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={classNames('rag-score-chip', confidence.className)}>
                        {confidence.label} confidence - {confidence.value}
                      </span>
                      {metadata?.chunk_index !== undefined && (
                        <span className="rag-score-chip rag-score-neutral">
                          Chunk {metadata.chunk_index}
                        </span>
                      )}
                    </div>
                    {metadata && <HighlightedJson data={metadata} />}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.article>
        );
      })}
    </div>
  );
}

SourceList.propTypes = {
  sources: PropTypes.arrayOf(
    PropTypes.shape({
      text: PropTypes.string,
      score: PropTypes.number,
      metadata: PropTypes.object,
    })
  ).isRequired,
  isLoading: PropTypes.bool,
};

SourceList.defaultProps = {
  isLoading: false,
};

function PromptButton({ prompt, onSelect }) {
  return (
    <button type="button" onClick={() => onSelect(prompt)} className="rag-prompt-button">
      <MessageSquare className="h-4 w-4" aria-hidden="true" />
      <span>{prompt}</span>
    </button>
  );
}

PromptButton.propTypes = {
  prompt: PropTypes.string.isRequired,
  onSelect: PropTypes.func.isRequired,
};

function EmptyChat({ onPromptSelect }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={panelTransition}
      className="rag-chat-empty"
    >
      <span className="rag-empty-icon" aria-hidden="true">
        <Sparkles className="h-6 w-6" />
      </span>
      <h2>Ask the engineering knowledge base</h2>
      <p>Query project specs, building-code notes, reports, and design references with evidence beside the answer.</p>
      <div className="rag-empty-prompts">
        {promptSuggestions.map((prompt) => (
          <PromptButton key={prompt} prompt={prompt} onSelect={onPromptSelect} />
        ))}
      </div>
    </motion.div>
  );
}

EmptyChat.propTypes = {
  onPromptSelect: PropTypes.func.isRequired,
};

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
      className="flex justify-start"
      aria-live="polite"
    >
      <div className="rag-message rag-message-assistant">
        <span className="rag-avatar rag-avatar-ai" aria-hidden="true">
          <Bot className="h-4 w-4" />
        </span>
        <div>
          <p className="rag-message-label">CadArena AI</p>
          <div className="rag-typing" aria-label="CadArena is typing">
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function ChatMessage({ message, index }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      layout
      variants={messageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ ...panelTransition, delay: Math.min(index * 0.02, 0.1) }}
      className={classNames('flex', isUser ? 'justify-end' : 'justify-start')}
    >
      <div className={classNames('rag-message', isUser ? 'rag-message-user' : 'rag-message-assistant')}>
        {!isUser && (
          <span className="rag-avatar rag-avatar-ai" aria-hidden="true">
            <Bot className="h-4 w-4" />
          </span>
        )}
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <p className={classNames('rag-message-label', isUser && 'rag-message-label-user')}>
              {isUser ? 'You' : 'CadArena AI'}
            </p>
            {!isUser && typeof message.sourceCount === 'number' && (
              <span className="rag-message-meta">{message.sourceCount} sources</span>
            )}
          </div>
          <p className="whitespace-pre-wrap text-sm leading-7 md:text-[0.95rem]">{message.text}</p>
        </div>
      </div>
    </motion.div>
  );
}

ChatMessage.propTypes = {
  message: PropTypes.shape({
    role: PropTypes.oneOf(['user', 'assistant']).isRequired,
    text: PropTypes.string.isRequired,
    sourceCount: PropTypes.number,
  }).isRequired,
  index: PropTypes.number.isRequired,
};

function Notice({ error, notice }) {
  if (!error && !notice) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
      className={classNames('rag-notice', error ? 'rag-notice-error' : 'rag-notice-success')}
      role="status"
    >
      {error ? <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" /> : <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />}
      <span>{error || notice}</span>
    </motion.div>
  );
}

Notice.propTypes = {
  error: PropTypes.string.isRequired,
  notice: PropTypes.string.isRequired,
};

export default function RAGChatPage() {
  const ragUrl = process.env.REACT_APP_RAG_API_URL || 'http://localhost:8001';
  const prefersReducedMotion = useReducedMotion();
  const [collection, setCollection] = React.useState('default');
  const [topK, setTopK] = React.useState(5);
  const [question, setQuestion] = React.useState(defaultQuestion);
  const [documentText, setDocumentText] = React.useState('');
  const [sourceName, setSourceName] = React.useState('');
  const [health, setHealth] = React.useState(null);
  const [healthState, setHealthState] = React.useState('checking');
  const [messages, setMessages] = React.useState([]);
  const [sources, setSources] = React.useState([]);
  const [activeInspector, setActiveInspector] = React.useState('sources');
  const [notice, setNotice] = React.useState('');
  const [error, setError] = React.useState('');
  const [isQuerying, setIsQuerying] = React.useState(false);
  const [isIngesting, setIsIngesting] = React.useState(false);
  const [isClearing, setIsClearing] = React.useState(false);
  const [isUploadingFiles, setIsUploadingFiles] = React.useState(false);
  const [isDragging, setIsDragging] = React.useState(false);
  const messageListRef = React.useRef(null);
  const questionRef = React.useRef(null);
  const fileInputRef = React.useRef(null);

  const refreshHealth = React.useCallback(async () => {
    setHealthState('checking');
    try {
      const data = await cadArenaAPI.checkRagHealth();
      setHealth(data);
      setHealthState('healthy');
      setError('');
    } catch (err) {
      setHealth(null);
      setHealthState('error');
      setError(err.message);
    }
  }, []);

  React.useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  React.useEffect(() => {
    const textarea = questionRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [question]);

  React.useEffect(() => {
    const list = messageListRef.current;
    if (!list) return;
    list.scrollTo({
      top: list.scrollHeight,
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
    });
  }, [messages, isQuerying, prefersReducedMotion]);

  const submitQuery = async (event) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;

    setIsQuerying(true);
    setError('');
    setNotice('');
    setActiveInspector('sources');
    setMessages((current) => [...current, { role: 'user', text: trimmed }]);
    setQuestion('');
    try {
      const result = await cadArenaAPI.queryRag({
        question: trimmed,
        topK,
        collection,
      });
      const nextSources = result.sources || [];
      setSources(nextSources);
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          text: result.answer || 'No answer returned.',
          sourceCount: nextSources.length,
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsQuerying(false);
    }
  };

  const ingestDocument = async (event) => {
    event.preventDefault();
    const trimmed = documentText.trim();
    if (!trimmed) return;

    setIsIngesting(true);
    setError('');
    setNotice('');
    try {
      const metadata = sourceName.trim() ? [{ source: sourceName.trim() }] : [{}];
      const result = await cadArenaAPI.ingestRagDocuments({
        documents: [trimmed],
        metadata,
        collection,
      });
      setNotice(`Ingested ${result.ingested} chunk${result.ingested === 1 ? '' : 's'} into ${result.collection}.`);
      setDocumentText('');
      await refreshHealth();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsIngesting(false);
    }
  };

  const clearCollection = async () => {
    const collectionName = collection || 'default';
    if (typeof window !== 'undefined') {
      const confirmed = window.confirm(`Clear the "${collectionName}" RAG collection?`);
      if (!confirmed) return;
    }

    setIsClearing(true);
    setError('');
    setNotice('');
    try {
      await cadArenaAPI.clearRagCollection(collectionName);
      setMessages([]);
      setSources([]);
      setNotice(`Collection ${collectionName} cleared.`);
      await refreshHealth();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsClearing(false);
    }
  };

  const handlePromptSelect = (prompt) => {
    setQuestion(prompt);
    window.requestAnimationFrame(() => questionRef.current?.focus());
  };

  const handleQuestionKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  const handleTopKChange = (value) => {
    const nextValue = Number(value);
    if (!Number.isFinite(nextValue)) return;
    setTopK(Math.min(20, Math.max(1, nextValue)));
  };

  const handleFiles = async (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length) {
      setIsDragging(false);
      return;
    }

    setError('');
    setNotice('');
    setIsUploadingFiles(true);
    try {
      const result = await cadArenaAPI.ingestRagFiles({
        files,
        collection,
        source: sourceName,
      });
      const failedText = result.failed ? ` ${result.failed} file${result.failed === 1 ? '' : 's'} had no extractable text.` : '';
      setNotice(`Uploaded ${files.length} file${files.length === 1 ? '' : 's'} and ingested ${result.ingested} chunk${result.ingested === 1 ? '' : 's'} into ${result.collection}.${failedText}`);
      await refreshHealth();
    } catch (err) {
      setError(err?.message || 'Unable to upload the selected file.');
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
      setIsDragging(false);
      setIsUploadingFiles(false);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    handleFiles(event.dataTransfer.files);
  };

  const { isDark } = useDarkMode();
  const documentWordCount = documentText.trim() ? documentText.trim().split(/\s+/).length : 0;
  const healthLoading = healthState === 'checking' && !health;
  const canAsk = Boolean(question.trim()) && !isQuerying;

  return (
    <div
      style={{
        minHeight: '100vh',
        background: isDark ? '#09090b' : '#f8faff',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Navbar />
      <div
        style={{
          flex: '1 1 auto',
          minHeight: '0',
          height: 'calc(100dvh - 72px)',
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div className="rag-workspace app-page">
          <div className="app-shell rag-shell">
            <motion.header
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={panelTransition}
              className="rag-consolebar"
            >
          <div className="rag-console-title">
            <span className="rag-product-mark" aria-hidden="true">
              <Database className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <p className="rag-eyebrow">CadArena RAG</p>
              <h1>Engineering Knowledge Console</h1>
            </div>
          </div>

          <div className="rag-console-actions">
            <StatusPill state={healthState} />
            <button type="button" onClick={refreshHealth} className="rag-toolbar-button">
              <RefreshCw className={classNames('h-4 w-4', healthState === 'checking' && 'animate-spin')} aria-hidden="true" />
              <span>Refresh</span>
            </button>
          </div>
        </motion.header>

        <section className="rag-metrics-grid">
          <MetricCard icon={Activity} label="API URL" value={ragUrl} detail="Standalone service" loading={false} />
          <MetricCard icon={Database} label="Vector Store" value={health?.vector_store || 'Unavailable'} detail={health?.embedding_model || 'Embedding pending'} loading={healthLoading} />
          <MetricCard icon={ClipboardList} label="Documents" value={health?.document_count ?? 'Unavailable'} detail={`Collection: ${collection || 'default'}`} loading={healthLoading} />
        </section>

        <AnimatePresence>
          {(error || notice) && <Notice error={error} notice={notice} />}
        </AnimatePresence>

        <div className="rag-layout">
          <motion.aside
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...panelTransition, delay: 0.04 }}
            className="rag-rail"
          >
            <section className="rag-rail-group">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="rag-eyebrow">Workspace</p>
                  <h2 className="rag-panel-title">Project retrieval</h2>
                </div>
                <ShieldCheck className="h-5 w-5 text-slate-500" aria-hidden="true" />
              </div>

              <div className="space-y-4">
                <label className="rag-field">
                  <span>Collection</span>
                  <input
                    value={collection}
                    onChange={(event) => setCollection(event.target.value || 'default')}
                    className="app-input"
                  />
                </label>
                <label className="rag-field">
                  <span>Top results</span>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={topK}
                    onChange={(event) => handleTopKChange(event.target.value)}
                    className="app-input"
                  />
                </label>
                <button type="button" onClick={clearCollection} disabled={isClearing} className="rag-danger-button">
                  {isClearing ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Trash2 className="h-4 w-4" aria-hidden="true" />}
                  Clear collection
                </button>
              </div>
            </section>

            <section className="rag-rail-group">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="rag-eyebrow">Prompts</p>
                  <h2 className="rag-panel-title">Starting points</h2>
                </div>
                <MessageSquare className="h-5 w-5 text-slate-500" aria-hidden="true" />
              </div>
              <div className="space-y-2">
                {promptSuggestions.map((prompt) => (
                  <PromptButton key={prompt} prompt={prompt} onSelect={handlePromptSelect} />
                ))}
              </div>
            </section>
          </motion.aside>

          <motion.section
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...panelTransition, delay: 0.08 }}
            className="rag-chat-panel"
          >
            <div className="rag-chat-toolbar">
              <div className="flex min-w-0 items-center gap-3">
                <span className="rag-toolbar-icon" aria-hidden="true">
                  <Bot className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <p className="rag-eyebrow">Knowledge Chat</p>
                  <h2 className="rag-chat-title">Civil and architectural context synthesis</h2>
                </div>
              </div>
              <span className="rag-collection-chip">{collection || 'default'}</span>
            </div>

            <div ref={messageListRef} className="rag-message-list">
              <AnimatePresence initial={false}>
                {messages.length === 0 && !isQuerying && <EmptyChat onPromptSelect={handlePromptSelect} />}
                {messages.map((message, index) => (
                  <ChatMessage key={`${message.role}-${index}-${message.text.slice(0, 24)}`} message={message} index={index} />
                ))}
                {isQuerying && <TypingIndicator />}
              </AnimatePresence>
            </div>

            <form onSubmit={submitQuery} className="rag-composer">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-500 dark:text-slate-400">
                  <ShieldCheck className="h-4 w-4 text-slate-600 dark:text-slate-300" aria-hidden="true" />
                  Source-grounded engineering retrieval
                </div>
                <div className="flex items-center gap-2 text-xs font-bold text-slate-500 dark:text-slate-400">
                  <Gauge className="h-4 w-4" aria-hidden="true" />
                  Top {topK}
                </div>
              </div>
              <label htmlFor="rag-question" className="sr-only">Question</label>
              <div className="rag-input-shell">
                <textarea
                  ref={questionRef}
                  id="rag-question"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={handleQuestionKeyDown}
                  rows={1}
                  className="rag-question-input"
                  placeholder="Ask the indexed knowledge base..."
                />
                <motion.button
                  type="submit"
                  disabled={!canAsk}
                  className="rag-send-button"
                  whileHover={canAsk ? { scale: 1.03 } : undefined}
                  whileTap={canAsk ? { scale: 0.96 } : undefined}
                  aria-label="Ask CadArena RAG"
                >
                  {isQuerying ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> : <ArrowUp className="h-5 w-5" aria-hidden="true" />}
                </motion.button>
              </div>
            </form>
          </motion.section>

          <motion.aside
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...panelTransition, delay: 0.12 }}
            className="rag-inspector"
          >
            <div className="rag-inspector-tabs" role="tablist" aria-label="RAG inspector">
              <button
                type="button"
                role="tab"
                aria-selected={activeInspector === 'sources'}
                className={classNames('rag-inspector-tab', activeInspector === 'sources' && 'rag-inspector-tab-active')}
                onClick={() => setActiveInspector('sources')}
              >
                <FileText className="h-4 w-4" aria-hidden="true" />
                Sources
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeInspector === 'ingest'}
                className={classNames('rag-inspector-tab', activeInspector === 'ingest' && 'rag-inspector-tab-active')}
                onClick={() => setActiveInspector('ingest')}
              >
                <UploadCloud className="h-4 w-4" aria-hidden="true" />
                Ingest
              </button>
            </div>

            <AnimatePresence mode="wait">
              {activeInspector === 'sources' ? (
                <motion.section
                  key="sources"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  <div className="rag-inspector-header">
                    <div>
                      <p className="rag-eyebrow">Evidence</p>
                      <h2 className="rag-panel-title">Retrieved evidence</h2>
                    </div>
                    <Gauge className="h-5 w-5 text-slate-500" aria-hidden="true" />
                  </div>
                  <SourceList sources={sources} isLoading={isQuerying} />
                </motion.section>
              ) : (
                <motion.section
                  key="ingest"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  <div className="rag-inspector-header">
                    <div>
                      <p className="rag-eyebrow">Intake</p>
                      <h2 className="rag-panel-title">Project knowledge upload</h2>
                    </div>
                    <UploadCloud className="h-5 w-5 text-slate-500" aria-hidden="true" />
                  </div>
                  <form onSubmit={ingestDocument} className="space-y-4">
                    <label className="rag-field">
                      <span>Source</span>
                      <input
                        value={sourceName}
                        onChange={(event) => setSourceName(event.target.value)}
                        className="app-input"
                        placeholder="Optional label"
                      />
                    </label>

                    <label
                      htmlFor="rag-file-upload"
                      onDragOver={(event) => {
                        event.preventDefault();
                        setIsDragging(true);
                      }}
                      onDragLeave={() => setIsDragging(false)}
                      onDrop={handleDrop}
                      className={classNames('rag-dropzone', (isDragging || isUploadingFiles) && 'rag-dropzone-active')}
                    >
                      <input
                        ref={fileInputRef}
                        id="rag-file-upload"
                        type="file"
                        multiple
                        accept=".pdf,.txt,.md,.csv,.json,application/pdf,text/plain,text/markdown,text/csv,application/json"
                        className="sr-only"
                        disabled={isUploadingFiles}
                        onChange={(event) => handleFiles(event.target.files)}
                      />
                      <span className="rag-dropzone-icon" aria-hidden="true">
                        {isUploadingFiles ? <Loader2 className="h-5 w-5 animate-spin" /> : <UploadCloud className="h-5 w-5" />}
                      </span>
                      <span className="block text-sm font-black text-slate-900 dark:text-slate-100">
                        {isUploadingFiles ? 'Uploading and indexing' : 'PDF/TXT/MD/CSV/JSON upload'}
                      </span>
                    </label>

                    <label className="rag-field">
                      <span>Document text</span>
                      <textarea
                        value={documentText}
                        onChange={(event) => setDocumentText(event.target.value)}
                        rows={8}
                        className="app-textarea min-h-[220px] resize-none"
                        placeholder="Paste specs, code notes, BOQs, meeting notes, or design constraints to index."
                      />
                    </label>

                    <div className="rag-intake-summary">
                      <span>{documentWordCount.toLocaleString()} words</span>
                      <span>{collection || 'default'}</span>
                    </div>

                    <button type="submit" disabled={isIngesting || !documentText.trim()} className="rag-primary-button">
                      {isIngesting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <UploadCloud className="h-4 w-4" aria-hidden="true" />}
                      Ingest document
                    </button>
                  </form>
                </motion.section>
              )}
            </AnimatePresence>
          </motion.aside>
        </div>
          </div>
        </div>
      </div>
    </div>
  );
}
