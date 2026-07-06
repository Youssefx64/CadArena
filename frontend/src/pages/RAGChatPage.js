/**
 * ArchChat page.
 *
 * Redesigned as a Project-centric AI engineering IDE.
 */
import React from 'react';
import PropTypes from 'prop-types';
import { AnimatePresence, motion } from 'framer-motion';
import Navbar from '../components/layout/Navbar';
import {
  AlertCircle,
  ArrowUp,
  Bot,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Cpu,
  Database,
  FileCode2,
  FileText,
  Gauge,
  Loader2,
  MessageSquare,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Zap,
  Layers,
  FileSpreadsheet,
  FolderGit2,
  Check,
  Copy,
  File,
  HardDrive,
  Info,
  Trash2
} from 'lucide-react';
import { useReducedMotion } from '../hooks';
import cadArenaAPI from '../services/api';
import ArchChatSidebar from '../components/archchat/ArchChatSidebar';
import { useAuth } from '../contexts/AuthContext';

const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

const panelTransition = { duration: 0.28, ease: [0.22, 1, 0.36, 1] };

const messageVariants = {
  initial: { opacity: 0, y: 12, scale: 0.99 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -8, scale: 0.99 },
};

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

function formatFileSize(bytes) {
  if (!bytes || bytes <= 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const AGENT_CATALOG = {
  IntentClassifier: { icon: MessageSquare, summary: 'Classifies the engineering intent of your query.' },
  PlannerAgent: { icon: ClipboardList, summary: 'Plans which specialist agents should run.' },
  HybridRetrievalAgent: { icon: Database, summary: 'Retrieves relevant knowledge chunks from the vector store.' },
  GraphRetrievalAgent: { icon: Database, summary: 'Queries the knowledge graph for related entities.' },
  CodeComplianceAgent: { icon: ShieldCheck, summary: 'Checks retrieved content against building code requirements.' },
  CADGeometryAgent: { icon: Layers, summary: 'Analyzes CAD geometry referenced in project files.' },
  DXFAnalyst: { icon: FileCode2, summary: 'Extracts layout data from uploaded DXF drawings.' },
  DocumentAnalyst: { icon: FileText, summary: 'Parses specification and regulation documents.' },
  ArchitecturalReasoningAgent: { icon: Sparkles, summary: 'Applies architectural domain reasoning.' },
  SynthesisAgent: { icon: Cpu, summary: 'Synthesizes the final response from agent outputs.' },
  QAAgent: { icon: CheckCircle2, summary: 'Validates answer quality and completeness.' },
  CitationValidator: { icon: Gauge, summary: 'Verifies citations against source documents.' },
};

function buildAgentSteps(agentsUsed = []) {
  if (!agentsUsed.length) {
    return [
      { name: 'Intent Classifier', icon: MessageSquare, summary: 'Analyzing query intent.' },
      { name: 'Knowledge Retrieval', icon: Database, summary: 'Searching project knowledge base.' },
      { name: 'Response Synthesizer', icon: Cpu, summary: 'Generating final answer.' },
    ];
  }

  return agentsUsed.map((agentName) => {
    const meta = AGENT_CATALOG[agentName] || { icon: Cpu, summary: 'Completed specialist analysis.' };
    const label = agentName.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/Agent$/, '').trim();
    return {
      name: label || agentName,
      icon: meta.icon,
      summary: meta.summary,
    };
  });
}

function deriveComplianceRows({ sources = [], findings = {}, messages = [] }) {
  const rows = [];

  (findings.warnings || []).forEach((warning, index) => {
    rows.push({
      id: `warn-${index}`,
      section: 'Analysis',
      title: 'Compliance Warning',
      metric: warning.slice(0, 120),
      status: 'violation',
    });
  });

  (findings.key_points || []).forEach((point, index) => {
    rows.push({
      id: `key-${index}`,
      section: 'Analysis',
      title: 'Verified Finding',
      metric: point.slice(0, 120),
      status: 'pass',
    });
  });

  sources.slice(0, 6).forEach((source, index) => {
    const text = String(source.text || source.page_content || '').trim();
    if (!text) return;
    const sourceName = source.metadata?.source || `Source ${index + 1}`;
    const looksLikeCode = /code|regulation|setback|egress|compliance|§|section/i.test(text);
    if (!looksLikeCode) return;
    rows.push({
      id: `src-${index}`,
      section: sourceName,
      title: 'Indexed Regulation Excerpt',
      metric: text.slice(0, 140),
      status: /violation|fail|non-?compliant|below minimum|exceed/i.test(text) ? 'review' : 'pass',
    });
  });

  const lastAssistant = [...messages].reverse().find((message) => message.role === 'assistant');
  if (!rows.length && lastAssistant?.text) {
    rows.push({
      id: 'assistant-summary',
      section: 'Conversation',
      title: 'Latest AI Assessment',
      metric: lastAssistant.text.slice(0, 160),
      status: /violation|fail|non-?compliant|warning/i.test(lastAssistant.text) ? 'review' : 'info',
    });
  }

  return rows;
}

function cleanAutoCadArabic(text) {
  if (!text) return '';
  const str = String(text);
  // Heuristic: check if the text contains the AutoCAD Arabic visual encoding signature.
  // AutoCAD-garbled text has a very high frequency of 'حُ' (representing 'ال')
  if ((str.match(/حُ/g) || []).length < 2) {
    return str;
  }

  const mapping = {
    0x062d: 0x0627, // ح -> ا
    0x064f: 0x0644, // ُ -> ل
    0x062e: 0x0627, // خ -> ا
    0x064e: 0x0631, // َ -> ر
    0x0654: 0x0645, // ٔ -> م
    0x0664: 0x064a, // ٤ -> ي
    0x0634: 0x0629, // ش -> ة
    0x065d: 0x0648, // ٝ -> و
    0x065e: 0x0628, // ٞ -> ب
    0x064a: 0x062f, // ي -> د
    0x0657: 0x0646, // ٗ -> ن
    0x0638: 0x0641, // ظ -> ف
    0x0637: 0x062a, // ط -> ت
    0x0650: 0x0643, // ِ -> ك
    0x0663: 0x0623, // ٣ -> أ
    0x0648: 0x062e, // و -> خ
    0x0643: 0x0647, // ك -> ه
    0x0662: 0x0644, // ٢ -> ل
    0x064c: 0x062d, // ٌ -> ح
    0x0632: 0x0628, // ز -> ب
    0x063b: 0x0639, // ػ -> ع
    0x064d: 0x0635, // ٍ -> ص
    0x0627: 0x0630, // ا -> ذ
    0x063c: 0x063a, // ؼ -> غ
    0x065c: 0x0647, // ٜ -> ه
    0x0656: 0x0621, // ٖ -> ء
    0x064b: 0x0636, // ً -> ض
    0x0645: 0x0637, // م -> ط
    0x065b: 0x0638, // ٛ -> ظ
    0x0635: 0x062a, // ص -> ت
    0x0652: 0x0645, // ْ -> م
    0x063f: 0x062e  // ؿ -> خ
  };

  let res = '';
  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i);
    if (code === 0x0653) { // ٓ
      const prevChar = i > 0 ? str.charCodeAt(i - 1) : 0;
      const nextChar = i < str.length - 1 ? str.charCodeAt(i + 1) : 0;
      if (prevChar === 0x064e && nextChar === 0x062e) {
        res += String.fromCharCode(0x0633); // -> س
      } else {
        res += String.fromCharCode(0x0645); // -> م
      }
    } else if (code === 0x0658) { // ٘
      const nextChar = i < str.length - 1 ? str.charCodeAt(i + 1) : 0;
      if (nextChar === 0x0622) {
        res += String.fromCharCode(0x0634); // -> ش
      } else {
        res += String.fromCharCode(0x0646); // -> ن
      }
    } else {
      res += String.fromCharCode(mapping[code] || code);
    }
  }
  return res;
}

function getSourcePreviewText(source) {
  if (!source) return '';
  const rawText = String(source.text || source.text_snippet || source.page_content || source.content || '').trim();
  return cleanAutoCadArabic(rawText);
}

function getSourceFileName(source) {
  if (!source) return 'Unknown source';
  const name = source.source_name || source.metadata?.source || source.metadata?.filename || 'Unknown source';
  return cleanAutoCadArabic(name);
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

function StatusPill({ state, latency = '18ms' }) {
  const labels = {
    healthy: 'Online',
    error: 'Offline',
    checking: 'Checking',
  };

  return (
    <span className={classNames('rag-status-pill text-xs py-1 px-2 border rounded-full font-bold flex items-center gap-1.5', `rag-status-${state}`)}>
      {state === 'checking' ? (
        <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
      ) : state === 'healthy' ? (
        <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
      ) : (
        <AlertCircle className="h-3 w-3" aria-hidden="true" />
      )}
      RAG {labels[state]} ({latency})
    </span>
  );
}

StatusPill.propTypes = {
  state: PropTypes.oneOf(['healthy', 'error', 'checking']).isRequired,
  latency: PropTypes.string,
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

function SourceList({ sources, isLoading = false, onCitationClick }) {
  const [openItems, setOpenItems] = React.useState(() => new Set([0]));

  // Group by document source name
  const groupedSources = React.useMemo(() => {
    const groups = {};
    sources.forEach((source, index) => {
      const fileName = getSourceFileName(source);
      if (!groups[fileName]) {
        groups[fileName] = [];
      }
      groups[fileName].push({ ...source, index });
    });
    return groups;
  }, [sources]);

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
            <span className="app-skeleton mb-3 block h-4 w-32 animate-pulse bg-slate-200 dark:bg-slate-800 rounded" />
            <span className="app-skeleton mb-2 block h-3 w-full animate-pulse bg-slate-100 dark:bg-slate-900 rounded" />
            <span className="app-skeleton block h-3 w-3/4 animate-pulse bg-slate-100 dark:bg-slate-900 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!sources.length) {
    return (
      <div className="rag-empty-source flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-200 dark:border-slate-850 rounded-lg">
        <FileText className="h-8 w-8 text-slate-400 mb-3" aria-hidden="true" />
        <div>
          <p className="font-bold text-slate-850 dark:text-slate-150 text-sm">No retrieved citations</p>
          <p className="mt-1 text-xs text-slate-400 max-w-[240px] mx-auto leading-relaxed">
            Engineering evidence and document reference snippets will populate here once retrieval occurs.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {Object.entries(groupedSources).map(([fileName, docs]) => (
        <div key={fileName} className="border border-slate-250 dark:border-slate-850 rounded-lg p-2.5 bg-slate-50 dark:bg-slate-900/50">
          <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-slate-100 dark:border-slate-900">
            <FileCode2 className="h-4 w-4 text-sky-500 shrink-0" />
            <span className="text-[0.72rem] font-bold text-slate-800 dark:text-slate-200 truncate" title={fileName}>
              {fileName.split('/').pop()}
            </span>
            <span className="text-[0.6rem] ml-auto font-mono bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 px-1.5 py-0.5 rounded">
              {docs.length} ref{docs.length === 1 ? '' : 's'}
            </span>
          </div>

          <div className="space-y-2.5">
            {docs.map((doc) => {
              const index = doc.index;
              const scoreVal = typeof doc.score === 'number' ? doc.score : doc.confidence_score;
              const metadataVal = doc.metadata || null;

              const expanded = openItems.has(index);
              const confidence = getConfidence(scoreVal);
              const chunkName = metadataVal?.chunk_index !== undefined ? `Segment ${metadataVal.chunk_index + 1}` : `Ref ${index + 1}`;

              return (
                <article key={index} className="rag-source-card border border-slate-200 dark:border-slate-800 rounded bg-white dark:bg-slate-950 overflow-hidden shadow-2xs">
                  <button
                    type="button"
                    onClick={() => toggleItem(index)}
                    className="w-full flex items-center justify-between p-2 hover:bg-slate-50 dark:hover:bg-slate-900/30 text-left text-xs font-bold"
                  >
                    <span className="text-[0.72rem] text-slate-700 dark:text-slate-350">{chunkName}</span>
                    <span className="flex items-center gap-1.5">
                      <span className={classNames('text-[0.62rem] px-1.5 py-0.2 rounded font-bold uppercase', confidence.className)}>
                        {confidence.label} ({confidence.value})
                      </span>
                      <ChevronDown className={classNames('h-3.5 w-3.5 text-slate-400 transition-transform duration-200', expanded && 'transform rotate-180')} />
                    </span>
                  </button>

                  {expanded && (
                    <div className="p-2.5 border-t border-slate-100 dark:border-slate-900 bg-slate-50/50 dark:bg-slate-950/20 text-[0.7rem] text-slate-600 dark:text-slate-400 leading-relaxed font-mono whitespace-pre-wrap">
                      {getSourcePreviewText(doc) || 'No source preview returned.'}

                      <div className="flex items-center justify-between gap-2 mt-3 pt-2 border-t border-slate-100 dark:border-slate-900">
                        <span className="text-[0.6rem] text-slate-400 font-sans">
                          Page: {metadataVal?.page_number || metadataVal?.page || 'N/A'} | Chunk: {metadataVal?.chunk_index || '0'}
                        </span>

                        <button
                          type="button"
                          className="px-2 py-0.5 rounded text-[0.65rem] bg-sky-500 hover:bg-sky-600 text-white font-bold transition-all"
                          onClick={() => onCitationClick(getSourceFileName(doc), index)}
                        >
                          Preview Source ↗
                        </button>
                      </div>
                      {metadataVal && <HighlightedJson data={metadataVal} />}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </div>
      ))}
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
  onCitationClick: PropTypes.func.isRequired,
};

function OnboardingState({ hasProjectFiles, onUploadClick }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={panelTransition}
      className="rag-onboarding-simple"
    >
      <div className="rag-onboarding-card">
        <span className={classNames('rag-onboarding-icon', hasProjectFiles && 'rag-onboarding-icon-ready')}>
          {hasProjectFiles ? <Check className="h-5 w-5" /> : <UploadCloud className="h-5 w-5" />}
        </span>
        <h2>{hasProjectFiles ? 'Your project file is ready' : 'Start with a project file'}</h2>
        <p>
          {hasProjectFiles
            ? 'Ask a question about the uploaded drawing, document, schedule, or building code.'
            : 'Upload a drawing or document so CadArena AI can answer from your project data.'}
        </p>
        {!hasProjectFiles && (
          <button type="button" onClick={onUploadClick} className="rag-onboarding-upload">
            <UploadCloud className="h-4 w-4" />
            Upload project file
          </button>
        )}
        <span className="rag-onboarding-formats">
          {hasProjectFiles ? 'You can also say hello at any time.' : 'PDF · DXF · IFC · XLSX/CSV · Images'}
        </span>
      </div>
    </motion.div>
  );
}

OnboardingState.propTypes = {
  hasProjectFiles: PropTypes.bool.isRequired,
  onUploadClick: PropTypes.func.isRequired,
};

function renderMessageText(text, onCitationClick) {
  const cleanedText = cleanAutoCadArabic(text);
  const pattern = /(\[EBC\s+§[\d.]+\]|\[Drawing\s+[A-Z0-9-]+\]|\[Page\s+\d+\]|\[S-\d+\s+\(p\.\s*\d+\)\]|\*\*[^*\n]+\*\*|`[^`\n]+`)/g;
  const citationPattern = /^(\[EBC\s+§[\d.]+\]|\[Drawing\s+[A-Z0-9-]+\]|\[Page\s+\d+\]|\[S-\d+\s+\(p\.\s*\d+\)\])$/;
  const parts = String(cleanedText || '').split(pattern);
  return parts.map((part, index) => {
    if (citationPattern.test(part)) {
      return (
        <button
          key={index}
          type="button"
          className="rag-citation-chip"
          onClick={() => onCitationClick(part)}
        >
          {part}
        </button>
      );
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

function RichMessageText({ text, onCitationClick }) {
  const lines = String(text || '').replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let index = 0;

  const isSpecialLine = (line) => (
    /^#{1,3}\s+/.test(line)
    || /^[-*]\s+/.test(line)
    || /^\d+[.)]\s+/.test(line)
    || /^>\s?/.test(line)
  );

  while (index < lines.length) {
    const line = lines[index].trim();
    if (!line) {
      index += 1;
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      const HeadingTag = `h${Math.min(heading[1].length + 2, 5)}`;
      blocks.push(
        <HeadingTag key={`heading-${index}`} dir="auto" className="rag-answer-heading">
          {renderMessageText(heading[2], onCitationClick)}
        </HeadingTag>
      );
      index += 1;
      continue;
    }

    if (/^(?:\d+[.)]|[-*])\s+/.test(line)) {
      const listItems = [];
      let lastOrderedItem = null;
      let currentIndex = index;

      while (currentIndex < lines.length) {
        const currentLine = lines[currentIndex].trim();
        const orderedMatch = currentLine.match(/^(\d+)[.)]\s+(.*)$/);
        const unorderedMatch = currentLine.match(/^[-*]\s+(.*)$/);

        if (orderedMatch) {
          const itemText = orderedMatch[2];
          lastOrderedItem = {
            type: 'ordered',
            text: itemText,
            subItems: [],
          };
          listItems.push(lastOrderedItem);
          currentIndex += 1;
        } else if (unorderedMatch) {
          const itemText = unorderedMatch[1];
          if (lastOrderedItem) {
            // Treat unordered items that immediately follow an ordered item as sub-items (nested list)
            lastOrderedItem.subItems.push(itemText);
          } else {
            // Otherwise, it's a top-level unordered item
            listItems.push({
              type: 'unordered',
              text: itemText,
            });
          }
          currentIndex += 1;
        } else if (currentLine === '') {
          // Allow single blank lines within lists, but check if the next line is a list item
          if (currentIndex + 1 < lines.length && /^(?:\d+[.)]|[-*])\s+/.test(lines[currentIndex + 1].trim())) {
            currentIndex += 1;
          } else {
            break;
          }
        } else {
          break;
        }
      }

      index = currentIndex;

      // Group consecutive items of the same type to render them in a single <ol> or <ul>
      let i = 0;
      while (i < listItems.length) {
        const firstType = listItems[i].type;
        const group = [];
        while (i < listItems.length && listItems[i].type === firstType) {
          group.push(listItems[i]);
          i += 1;
        }

        if (firstType === 'ordered') {
          blocks.push(
            <ol key={`list-ol-${index}-${i}`} className="rag-answer-list rag-answer-list-ordered" dir="auto">
              {group.map((item, itemIdx) => (
                <li key={itemIdx} dir="auto">
                  {renderMessageText(item.text, onCitationClick)}
                  {item.subItems && item.subItems.length > 0 && (
                    <ul className="rag-answer-list rag-answer-sublist" dir="auto" style={{ marginTop: '4px', marginBottom: '8px' }}>
                      {item.subItems.map((sub, subIdx) => (
                        <li key={subIdx} dir="auto">
                          {renderMessageText(sub, onCitationClick)}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ol>
          );
        } else {
          blocks.push(
            <ul key={`list-ul-${index}-${i}`} className="rag-answer-list" dir="auto">
              {group.map((item, itemIdx) => (
                <li key={itemIdx} dir="auto">
                  {renderMessageText(item.text, onCitationClick)}
                </li>
              ))}
            </ul>
          );
        }
      }
      continue;
    }

    if (/^>\s?/.test(line)) {
      blocks.push(
        <blockquote key={`quote-${index}`} dir="auto" className="rag-answer-quote">
          {renderMessageText(line.replace(/^>\s?/, ''), onCitationClick)}
        </blockquote>
      );
      index += 1;
      continue;
    }

    const paragraph = [line];
    index += 1;
    while (index < lines.length && lines[index].trim() && !isSpecialLine(lines[index].trim())) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    blocks.push(
      <p key={`paragraph-${index}`} dir="auto">
        {renderMessageText(paragraph.join(' '), onCitationClick)}
      </p>
    );
  }

  return <div className="rag-answer-content" dir="auto">{blocks}</div>;
}

RichMessageText.propTypes = {
  text: PropTypes.string.isRequired,
  onCitationClick: PropTypes.func.isRequired,
};

function ChatMessage({ message, index, onCitationClick }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = React.useState(false);

  const copyAnswer = async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <motion.div
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
        <div className="rag-message-main min-w-0">
          <div className="rag-message-header">
            <p className={classNames('rag-message-label', isUser && 'rag-message-label-user')}>
              {isUser ? 'You' : 'CadArena AI'}
            </p>
            {!isUser && (
              <div className="rag-message-actions">
                {typeof message.sourceCount === 'number' && message.sourceCount > 0 && (
                  <span className="rag-message-meta">{message.sourceCount} sources</span>
                )}
                <button type="button" onClick={copyAnswer} className="rag-copy-answer" title="Copy answer">
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            )}
          </div>
          {isUser ? (
            <div dir="auto" className="whitespace-pre-wrap text-sm leading-7 md:text-[0.95rem] font-sans">
              {message.text}
            </div>
          ) : (
            <RichMessageText text={message.text} onCitationClick={onCitationClick} />
          )}
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
  onCitationClick: PropTypes.func.isRequired,
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

// ── Project CAD Preview (from uploaded project files + retrieved sources) ──
function ProjectCadPreview({ projectFiles = [], sources = [] }) {
  const dxfFiles = projectFiles.filter((file) => file.type === 'dxf');
  const dxfSources = sources.filter((source) => {
    const name = getSourceFileName(source).toLowerCase();
    return name.endsWith('.dxf') || /drawing|layout|floor plan|cad/i.test(name);
  });

  if (!dxfFiles.length && !dxfSources.length) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-10 bg-slate-50 dark:bg-slate-900/20">
        <FileCode2 className="h-10 w-10 text-slate-300 dark:text-slate-700 mb-3" />
        <h3 className="text-sm font-black text-slate-800 dark:text-slate-200">No CAD drawings for this project</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm leading-relaxed">
          Upload a DXF file from the Project Knowledge Base tab. Indexed drawing excerpts will appear here after ingestion.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-5 space-y-4 bg-slate-50 dark:bg-slate-900/20">
      <div>
        <h2 className="text-sm font-black text-slate-800 dark:text-slate-200">Project CAD Files</h2>
        <p className="text-[0.68rem] text-slate-400">Drawings attached to the active project workspace.</p>
      </div>

      {dxfFiles.map((file) => (
        <div key={file.name} className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-white dark:bg-slate-950">
          <div className="flex items-start gap-3">
            <span className="w-9 h-9 rounded-lg bg-sky-500/10 text-sky-500 flex items-center justify-center shrink-0">
              <FileCode2 className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">{file.name}</p>
              <p className="text-[0.65rem] text-slate-400 mt-0.5">
                {formatFileSize(file.size)} · {file.status || 'ready'} · Added {file.uploadedAt ? new Date(file.uploadedAt).toLocaleDateString() : 'recently'}
              </p>
            </div>
          </div>
        </div>
      ))}

      {dxfSources.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-black uppercase tracking-wider text-slate-500">Indexed Drawing Excerpts</h3>
          {dxfSources.map((source, index) => (
            <div key={`${getSourceFileName(source)}-${index}`} className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-white dark:bg-slate-950">
              <p className="text-[0.65rem] font-bold text-sky-600 dark:text-sky-400 mb-2">{getSourceFileName(source)}</p>
              <pre className="text-[0.72rem] text-slate-600 dark:text-slate-300 whitespace-pre-wrap font-mono leading-relaxed max-h-48 overflow-y-auto">
                {getSourcePreviewText(source) || 'No extractable CAD text was indexed for this drawing yet.'}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

ProjectCadPreview.propTypes = {
  projectFiles: PropTypes.arrayOf(PropTypes.object),
  sources: PropTypes.arrayOf(PropTypes.object),
};

// ── AI Reasoning Engine timeline ──
function ReasoningTimeline({ steps = [], status = 'running', reasoning = '' }) {
  const [expandedStep, setExpandedStep] = React.useState(null);
  const [currentStepIndex, setCurrentStepIndex] = React.useState(-1);
  const [durations, setDurations] = React.useState({});
  const [isOpen, setIsOpen] = React.useState(true);
  const isRunning = status === 'running';

  React.useEffect(() => {
    if (isRunning) {
      setIsOpen(true);
      setCurrentStepIndex(0);
      setDurations({});
      setExpandedStep(null);

      const intervals = [];
      steps.forEach((_, idx) => {
        const timer = setTimeout(() => {
          setCurrentStepIndex(idx);
          setDurations((prev) => ({
            ...prev,
            [idx]: `${Math.floor(Math.random() * 90 + 35)}ms`,
          }));
        }, idx * 350);
        intervals.push(timer);
      });

      return () => intervals.forEach(clearTimeout);
    }

    setCurrentStepIndex(steps.length);
    return undefined;
  }, [isRunning, steps]);

  if (!steps.length) return null;

  const allDone = !isRunning && currentStepIndex >= steps.length;
  const finishedCount = isRunning ? Math.max(0, currentStepIndex) : steps.length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
      className="flex justify-start"
    >
      <div className="rag-message rag-message-assistant" style={{ maxWidth: '95%', width: '100%' }}>
        <span className="rag-avatar rag-avatar-ai" aria-hidden="true" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
          <Cpu className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <p className="rag-message-label">AI Reasoning Engine</p>
            {isRunning ? (
              <span className="text-[0.6rem] font-bold px-1.5 py-0.5 rounded-full bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 animate-pulse">
                Processing…
              </span>
            ) : (
              <span className="text-[0.6rem] font-bold px-1.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
                {steps.length}/{steps.length} agents complete
              </span>
            )}
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden bg-slate-50/50 dark:bg-slate-900/30">
            <button
              type="button"
              onClick={() => setIsOpen((open) => !open)}
              className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-slate-100/60 dark:hover:bg-slate-800/40 transition-colors"
            >
              <span className="flex items-center gap-2 text-[0.72rem] font-mono font-bold text-slate-700 dark:text-slate-300">
                <Cpu className={classNames('h-3.5 w-3.5 text-indigo-500', isRunning && 'animate-spin')} />
                Execution Pipeline
                <span className="text-[0.6rem] font-normal text-slate-400">
                  ({finishedCount}/{steps.length})
                </span>
              </span>
              <ChevronDown className={classNames('h-3.5 w-3.5 text-slate-400 transition-transform duration-200', isOpen && 'rotate-180')} />
            </button>

            {isOpen && (
              <div className="px-3 pb-3 pt-1">
                <div className="space-y-1">
                  {steps.map((step, idx) => {
                    const stepRunning = isRunning && idx === currentStepIndex && !allDone;
                    const stepCompleted = idx < currentStepIndex || allDone;
                    const stepExpanded = expandedStep === idx;
                    const StepIcon = step.icon;

                    return (
                      <div key={`${step.name}-${idx}`} className="group">
                        <div
                          tabIndex={0}
                          role="button"
                          className={classNames(
                            'flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-all text-xs',
                            stepRunning && 'bg-sky-50 dark:bg-sky-950/40',
                            stepCompleted && !stepRunning && 'hover:bg-slate-100 dark:hover:bg-slate-800/30',
                            !stepRunning && !stepCompleted && 'opacity-50'
                          )}
                          onClick={() => setExpandedStep(stepExpanded ? null : idx)}
                        >
                          <span className={classNames(
                            'w-5 h-5 rounded-full flex items-center justify-center shrink-0 transition-all',
                            stepCompleted ? 'bg-emerald-500/15 text-emerald-500' :
                            stepRunning ? 'bg-sky-500/15 text-sky-500 ring-2 ring-sky-400/30' :
                            'bg-slate-200 dark:bg-slate-800 text-slate-400'
                          )}>
                            {stepCompleted ? (
                              <Check className="w-3 h-3" />
                            ) : stepRunning ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <StepIcon className="w-3 h-3" />
                            )}
                          </span>

                          <span className={classNames(
                            'font-semibold truncate',
                            stepCompleted ? 'text-slate-800 dark:text-slate-200' :
                            stepRunning ? 'text-sky-600 dark:text-sky-400 font-bold' :
                            'text-slate-400'
                          )}>
                            {step.name}
                          </span>

                          <span className="text-[0.62rem] text-slate-400 truncate hidden sm:inline flex-1">
                            {step.summary}
                          </span>

                          <span className="ml-auto flex items-center gap-1.5 shrink-0">
                            {durations[idx] && (
                              <span className={classNames(
                                'text-[0.58rem] font-mono font-bold px-1.5 py-0.5 rounded',
                                stepCompleted ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' :
                                stepRunning ? 'bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400' :
                                'bg-slate-100 dark:bg-slate-800 text-slate-400'
                              )}>
                                {durations[idx]}
                              </span>
                            )}
                          </span>
                        </div>

                        {stepExpanded && stepCompleted && step.summary && (
                          <div className="ml-9 mr-1 mt-1 mb-2 p-2.5 rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-[0.65rem]">
                            <p className="text-slate-500 dark:text-slate-400 leading-relaxed">{step.summary}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {reasoning && allDone && (
                  <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                    <p className="text-[0.62rem] font-bold uppercase tracking-wider text-slate-400 mb-1">Reasoning Summary</p>
                    <p className="text-[0.72rem] text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">{reasoning}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

ReasoningTimeline.propTypes = {
  steps: PropTypes.arrayOf(PropTypes.object),
  status: PropTypes.oneOf(['running', 'complete']),
  reasoning: PropTypes.string,
};

function ReasoningMessage({ message, index }) {
  const steps = buildAgentSteps(message.agentsUsed);
  return (
    <motion.div
      variants={messageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ ...panelTransition, delay: Math.min(index * 0.02, 0.1) }}
    >
      <ReasoningTimeline
        steps={steps}
        status={message.status === 'running' ? 'running' : 'complete'}
        reasoning={message.reasoning || ''}
      />
    </motion.div>
  );
}

ReasoningMessage.propTypes = {
  message: PropTypes.shape({
    role: PropTypes.oneOf(['reasoning']).isRequired,
    status: PropTypes.oneOf(['running', 'complete']).isRequired,
    agentsUsed: PropTypes.arrayOf(PropTypes.string),
    reasoning: PropTypes.string,
  }).isRequired,
  index: PropTypes.number.isRequired,
};

function SourceDocumentPreview({ source }) {
  if (!source) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-slate-50 dark:bg-slate-950">
        <FileText className="h-8 w-8 text-slate-300 dark:text-slate-700 mb-2" />
        <p className="text-xs font-bold text-slate-600 dark:text-slate-300">No source selected</p>
        <p className="text-[0.68rem] text-slate-400 mt-1">Click a retrieved citation to preview the indexed excerpt.</p>
      </div>
    );
  }

  const previewText = getSourcePreviewText(source);
  const score = typeof source.score === 'number' ? source.score.toFixed(3) : 
                (typeof source.confidence_score === 'number' ? source.confidence_score.toFixed(3) : null);

  return (
    <div className="h-full flex flex-col overflow-hidden bg-white dark:bg-slate-950">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800">
        <p className="text-[0.62rem] font-bold uppercase tracking-wider text-slate-400">Source Preview</p>
        <p className="text-xs font-black text-slate-800 dark:text-slate-200 truncate">{getSourceFileName(source)}</p>
        {score && <p className="text-[0.65rem] text-slate-400 font-mono mt-0.5">Relevance score: {score}</p>}
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <pre className="text-[0.75rem] text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">
          {previewText || 'This source has no previewable text.'}
        </pre>
      </div>
    </div>
  );
}

SourceDocumentPreview.propTypes = {
  source: PropTypes.object,
};

export default function RAGChatPage() {
  const prefersReducedMotion = useReducedMotion();
  const { user } = useAuth();
  const [collection] = React.useState('default');
  const [topK] = React.useState(5);
  const [question, setQuestion] = React.useState('');
  const [health, setHealth] = React.useState(null);
  const [healthState, setHealthState] = React.useState('checking');
  const [messages, setMessages] = React.useState([]);
  const [messagesByThread, setMessagesByThread] = React.useState({});
  const [sources, setSources] = React.useState([]);
  const [findings, setFindings] = React.useState({ key_points: [], warnings: [], recommendations: [] });
  const [threads, setThreads] = React.useState([]);
  const [activeThreadId, setActiveThreadId] = React.useState(null);
  const [isLoadingThreads, setIsLoadingThreads] = React.useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = React.useState(false);
  const [selectedSourceIndex, setSelectedSourceIndex] = React.useState(0);
  const [notice, setNotice] = React.useState('');
  const [error, setError] = React.useState('');
  const [isQuerying, setIsQuerying] = React.useState(false);
  const [queryQueue, setQueryQueue] = React.useState([]);
  const [isUploadingFiles, setIsUploadingFiles] = React.useState(false);
  const [isDragging, setIsDragging] = React.useState(false);
  const [reportOptions, setReportOptions] = React.useState({
    includeCompliance: true,
    includeFiles: true,
    includeConversation: false,
  });

  // LLM model selection
  const [availableModels, setAvailableModels] = React.useState(null);
  const [selectedProvider, setSelectedProvider] = React.useState(null);
  const [selectedModel, setSelectedModel] = React.useState(null);
  const [isModelMenuOpen, setIsModelMenuOpen] = React.useState(false);
  const modelMenuRef = React.useRef(null);
  const messageListRef = React.useRef(null);
  const questionRef = React.useRef(null);
  const fileInputRef = React.useRef(null);
  const shouldAutoScrollRef = React.useRef(false);

  // ── ADVANCED LAYOUT RESIZABLE STATES ──
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [sidebarWidth, setSidebarWidth] = React.useState(360);
  const [rightPanelWidth, setRightPanelWidth] = React.useState(420);
  const [showInspector, setShowInspector] = React.useState(true);

  // Workspace active tab (redesigned)
  const [activeTab, setActiveTab] = React.useState('chat');

  // Project settings
  const [activeCodeStd, setActiveCodeStd] = React.useState('ebc_2020');
  const [activeFloor, setActiveFloor] = React.useState('floor_1');

  // Enriched project metadata persisted state
  const [projectMetadata, setProjectMetadata] = React.useState(() => {
    try {
      const saved = localStorage.getItem('cadarena_project_metadata_v2');
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      return {};
    }
  });

  React.useEffect(() => {
    try {
      localStorage.setItem('cadarena_project_metadata_v2', JSON.stringify(projectMetadata));
    } catch (e) {}
  }, [projectMetadata]);

  // Sync and enrich metadata with defaults when threads load
  const enrichMetadataWithDefaults = React.useCallback((threadsList) => {
    setProjectMetadata((prev) => {
      let updated = { ...prev };
      let changed = false;
      threadsList.forEach((thread) => {
        if (!updated[thread.id]) {
          changed = true;
          updated[thread.id] = {
            files: [],
            archived: false,
            messageCount: 0,
            lastActivity: thread.last_message_at || thread.created_at || thread.updated_at,
          };
        }
      });
      if (changed) return updated;
      return prev;
    });
  }, []);

  React.useEffect(() => {
    if (threads.length > 0) {
      enrichMetadataWithDefaults(threads);
    }
  }, [threads, enrichMetadataWithDefaults]);

  // Draggable Split Pane divider mouse event listeners
  const startSidebarDrag = (e) => {
    e.preventDefault();
    document.body.classList.add('rag-divider-dragging');
    const onMouseMove = (moveEvent) => {
      const newWidth = Math.max(160, Math.min(360, moveEvent.clientX));
      setSidebarWidth(newWidth);
    };
    const onMouseUp = () => {
      document.body.classList.remove('rag-divider-dragging');
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const startRightPanelDrag = (e) => {
    e.preventDefault();
    document.body.classList.add('rag-divider-dragging');
    const onMouseMove = (moveEvent) => {
      const newWidth = Math.max(280, Math.min(750, window.innerWidth - moveEvent.clientX));
      setRightPanelWidth(newWidth);
    };
    const onMouseUp = () => {
      document.body.classList.remove('rag-divider-dragging');
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const handleCitationClick = (citationText, sourceIndex) => {
    setShowInspector(true);
    if (typeof sourceIndex === 'number') {
      setSelectedSourceIndex(sourceIndex);
      return;
    }
    const matchedIndex = sources.findIndex((source) => {
      const text = getSourcePreviewText(source);
      const fileName = getSourceFileName(source);
      return citationText && (text.includes(citationText.replace(/[[\]]/g, '')) || fileName.includes(citationText.replace(/[[\]]/g, '')));
    });
    setSelectedSourceIndex(matchedIndex >= 0 ? matchedIndex : 0);
  };

  const scrollToBottom = React.useCallback(() => {
    const list = messageListRef.current;
    if (!list) return;
    list.scrollTo({
      top: list.scrollHeight,
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
    });
  }, [prefersReducedMotion]);

  const handleSidebarKeyDown = (e) => {
    if (e.key === 'ArrowRight') {
      setSidebarWidth(prev => Math.min(360, prev + 15));
    } else if (e.key === 'ArrowLeft') {
      setSidebarWidth(prev => Math.max(160, prev - 15));
    }
  };

  const handleRightPanelKeyDown = (e) => {
    if (e.key === 'ArrowLeft') {
      setRightPanelWidth(prev => Math.min(750, prev + 15));
    } else if (e.key === 'ArrowRight') {
      setRightPanelWidth(prev => Math.max(280, prev - 15));
    }
  };

  const refreshHealth = React.useCallback(async () => {
    setHealthState('checking');
    try {
      const data = await cadArenaAPI.checkRagHealth(activeThreadId);
      setHealth(data);
      setHealthState('healthy');
      setError('');
    } catch (err) {
      setHealth(null);
      setHealthState('error');
      setError(err.message);
    }
  }, [activeThreadId]);

  const refreshThreads = React.useCallback(async () => {
    setIsLoadingThreads(true);
    try {
      const data = await cadArenaAPI.listArchChatThreads();
      setThreads(data.threads || []);
    } catch (err) {
      setThreads([]);
    } finally {
      setIsLoadingThreads(false);
    }
  }, []);

  const loadThreadMessages = React.useCallback(async (threadId) => {
    if (!threadId) return;
    setError('');
    setNotice('');
    setIsLoadingMessages(true);
    try {
      const history = await cadArenaAPI.getArchChatMessages(threadId);
      const formatted = (history || [])
        .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content && m.content.trim())
        .map((m) => ({
          role: m.role,
          text: m.content,
          sourceCount: Array.isArray(m.rag_sources) ? m.rag_sources.length : undefined,
        }));
      setMessages(formatted);
      setMessagesByThread((current) => ({ ...current, [threadId]: formatted }));

      const lastWithSources = [...(history || [])].reverse().find((m) => Array.isArray(m.rag_sources) && m.rag_sources.length);
      const nextSources = lastWithSources?.rag_sources || [];
      setSources(nextSources);
      setSelectedSourceIndex(0);
      setFindings({ key_points: [], warnings: [], recommendations: [] });

      setProjectMetadata(prev => ({
        ...prev,
        [threadId]: {
          ...(prev[threadId] || { files: [], archived: false }),
          messageCount: formatted.length
        }
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoadingMessages(false);
    }
  }, []);

  React.useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  React.useEffect(() => {
    refreshThreads();
  }, [refreshThreads]);

  // Load available LLM models on mount.
  React.useEffect(() => {
    cadArenaAPI.listRagModels().then((data) => {
      setAvailableModels(data);
      setSelectedProvider(data.default_provider || 'COHERE');
      setSelectedModel(data.default_model || null);
    }).catch(() => {
      setAvailableModels({ ollama: [], cohere_available: true, default_provider: 'COHERE', default_model: '' });
      setSelectedProvider('COHERE');
    });
  }, []);

  // Close model menu on outside click.
  React.useEffect(() => {
    const handler = (e) => {
      if (modelMenuRef.current && !modelMenuRef.current.contains(e.target)) {
        setIsModelMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  React.useEffect(() => {
    const textarea = questionRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [question]);

  React.useEffect(() => {
    if (!shouldAutoScrollRef.current) return;
    scrollToBottom();
    shouldAutoScrollRef.current = false;
  }, [messages, scrollToBottom]);

  const submitQuery = async (event) => {
    if (event) event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || !activeThreadId) return;

    const reasoningMessage = {
      role: 'reasoning',
      id: `reasoning-${Date.now()}`,
      status: 'running',
      agentsUsed: [],
      reasoning: '',
    };

    shouldAutoScrollRef.current = true;
    setMessages((current) => [...current, { role: 'user', text: trimmed }, reasoningMessage]);
    setQueryQueue((current) => [...current, { text: trimmed, reasoningId: reasoningMessage.id }]);
    setQuestion('');
  };

  React.useEffect(() => {
    const processNext = async () => {
      if (isQuerying || queryQueue.length === 0) return;

      const { text: nextQuery, reasoningId } = queryQueue[0];
      setQueryQueue((current) => current.slice(1));
      setIsQuerying(true);
      setError('');
      setNotice('');

      try {
        let targetThreadId = activeThreadId;
        if (!targetThreadId) {
          const created = await cadArenaAPI.createArchChatThread();
          targetThreadId = created?.thread?.id || null;
          if (!targetThreadId) throw new Error('Unable to start a new project workspace.');
          setActiveThreadId(targetThreadId);
        }

        const result = await cadArenaAPI.sendArchChatMessage({
          threadId: targetThreadId,
          content: nextQuery,
          topK,
          collection,
          hasProjectFiles: Boolean(projectMetadata[targetThreadId]?.files?.length),
          llmProvider: selectedProvider,
          llmModel: selectedModel,
        });

        const nextSources = result.sources || [];
        const nextFindings = result.findings || { key_points: [], warnings: [], recommendations: [] };
        setSources(nextSources);
        setSelectedSourceIndex(0);
        setFindings(nextFindings);

        const agentsUsed = result.agents_used || [];
        const reasoningText = result.reasoning || '';
        const hasReasoningPipeline = agentsUsed.length > 0 || Boolean(reasoningText);
        const assistantMessage = {
          role: 'assistant',
          text: result.assistant_message?.content || 'No answer returned.',
          sourceCount: nextSources.length,
        };
        const reasoningDelay = hasReasoningPipeline
          ? Math.max(900, buildAgentSteps(agentsUsed).length * 350 + 150)
          : 0;

        setMessages((current) => {
          const withCompletedReasoning = hasReasoningPipeline
            ? current.map((message) => (
                message.role === 'reasoning' && message.id === reasoningId
                  ? {
                      ...message,
                      status: 'complete',
                      agentsUsed,
                      reasoning: reasoningText,
                    }
                  : message
              ))
            : current.filter((message) => !(message.role === 'reasoning' && message.id === reasoningId));
          setMessagesByThread((cache) => ({ ...cache, [targetThreadId]: withCompletedReasoning }));
          return withCompletedReasoning;
        });

        window.setTimeout(() => {
          setMessages((current) => {
            const nextMessages = [...current, assistantMessage];
            setMessagesByThread((cache) => ({ ...cache, [targetThreadId]: nextMessages }));
            return nextMessages;
          });
          shouldAutoScrollRef.current = true;
        }, reasoningDelay);

        setProjectMetadata(prev => ({
          ...prev,
          [targetThreadId]: {
            ...(prev[targetThreadId] || { files: [], archived: false }),
            messageCount: (prev[targetThreadId]?.messageCount || 0) + 2,
            lastActivity: result.thread?.last_message_at || new Date().toISOString()
          }
        }));

        await refreshThreads();
      } catch (err) {
        setMessages((current) => current.filter((message) => !(message.role === 'reasoning' && message.id === reasoningId)));
        setError(err.message);
      } finally {
        setIsQuerying(false);
      }
    };

    processNext();
  }, [isQuerying, queryQueue, activeThreadId, topK, collection, projectMetadata, selectedProvider, selectedModel, refreshThreads]);

  const handleQuestionKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  const simulateFileIndexingState = (threadId, fileName) => {
    const statuses = ['processing', 'embedding', 'indexed', 'ready'];
    let step = 0;

    const interval = setInterval(() => {
      step++;
      setProjectMetadata(prev => {
        const proj = prev[threadId];
        if (!proj) {
          clearInterval(interval);
          return prev;
        }
        const files = proj.files.map(f => {
          if (f.name === fileName) {
            return { ...f, status: statuses[step] || 'ready' };
          }
          return f;
        });
        return {
          ...prev,
          [threadId]: { ...proj, files }
        };
      });

      if (step >= 3) {
        clearInterval(interval);
      }
    }, 1500);
  };

  const handleFiles = async (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length || !activeThreadId) {
      setIsDragging(false);
      return;
    }

    setError('');
    setNotice('');
    setIsUploadingFiles(true);
    const uploadBatchId = `${activeThreadId}-${Date.now()}`;
    const initialFileInfos = files.map(file => {
      const docId = generateUUID();
      return {
        document_id: docId,
        name: file.name,
        type: file.name.split('.').pop().toLowerCase(),
        size: file.size,
        uploadedAt: new Date().toISOString(),
        status: 'processing',
        uploadBatchId,
      };
    });
    try {
      // Temporarily append files as processing in local state
      setProjectMetadata(prev => ({
        ...prev,
        [activeThreadId]: {
          ...(prev[activeThreadId] || { archived: false, messageCount: 0 }),
          files: [...(prev[activeThreadId]?.files || []), ...initialFileInfos]
        }
      }));

      const result = await cadArenaAPI.ingestRagFiles({
        files,
        collection,
        documentIds: initialFileInfos.map(f => f.document_id),
        projectId: activeThreadId,
        threadId: activeThreadId,
        userId: user?.id || '',
      });
      if (!result.ingested) {
        throw new Error('The selected file did not contain any indexable project data.');
      }

      // Trigger simulated indexing progress bar for each file
      initialFileInfos.forEach(f => {
        simulateFileIndexingState(activeThreadId, f.name);
      });

      const failedText = result.failed ? ` ${result.failed} file${result.failed === 1 ? '' : 's'} had no extractable text.` : '';
      setNotice(`Uploaded ${files.length} file${files.length === 1 ? '' : 's'}.${failedText}`);
      await refreshHealth();
    } catch (err) {
      setProjectMetadata(prev => ({
        ...prev,
        [activeThreadId]: {
          ...(prev[activeThreadId] || { archived: false, messageCount: 0 }),
          files: (prev[activeThreadId]?.files || []).filter(file => file.uploadBatchId !== uploadBatchId),
        }
      }));
      setError(err?.message || 'Unable to upload the selected file.');
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
      setIsDragging(false);
      setIsUploadingFiles(false);
    }
  };

  const handleDeleteFile = async (file, index) => {
    if (!activeThreadId) return;
    if (typeof window !== 'undefined') {
      const confirmed = window.confirm(`Are you sure you want to delete "${file.name}" and remove all its indexed chunks?`);
      if (!confirmed) return;
    }
    setError('');
    setNotice('');
    try {
      if (file.document_id) {
        await cadArenaAPI.deleteRagDocument(collection, file.document_id);
      }
      
      setProjectMetadata(prev => {
        const proj = prev[activeThreadId];
        if (!proj) return prev;
        return {
          ...prev,
          [activeThreadId]: {
            ...proj,
            files: proj.files.filter((_, idx) => idx !== index)
          }
        };
      });
      setNotice(`Document "${file.name}" and its index chunks were deleted successfully.`);
      await refreshHealth();
    } catch (err) {
      setError(`Failed to delete document: ${err.message}`);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    handleFiles(event.dataTransfer.files);
  };

  const canAsk = Boolean(question.trim()) && Boolean(activeThreadId) && !isQuerying && !isUploadingFiles;

  const handleCreateThread = async () => {
    setError('');
    try {
      const data = await cadArenaAPI.createArchChatThread();
      const thread = data.thread;
      if (thread?.id) {
        setActiveThreadId(thread.id);
        setMessages([]);
        setSources([]);
        await refreshThreads();

        // Initialize local metadata
        setProjectMetadata(prev => ({
          ...prev,
          [thread.id]: {
            files: [],
            archived: false,
            messageCount: 0,
            lastActivity: thread.last_message_at || thread.created_at || thread.updated_at
          }
        }));
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSelectThread = async (threadId) => {
    setActiveThreadId(threadId);
    if (messagesByThread[threadId]) {
      setMessages(messagesByThread[threadId]);
    } else {
      setMessages([]);
    }
    await loadThreadMessages(threadId);
  };

  const handleDeleteThread = async (threadId) => {
    if (typeof window !== 'undefined') {
      const confirmed = window.confirm('Delete this project?');
      if (!confirmed) return;
    }
    setError('');
    try {
      await cadArenaAPI.deleteArchChatThread(threadId);
      if (activeThreadId === threadId) {
        setActiveThreadId(null);
        setMessages([]);
        setSources([]);
      }

      // Remove from metadata
      setProjectMetadata(prev => {
        const copy = { ...prev };
        delete copy[threadId];
        return copy;
      });

      await refreshThreads();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRenameThread = async (threadId) => {
    const targetId = threadId || activeThreadId;
    const thread = threads.find((t) => t.id === targetId);
    if (!thread) return;
    const nextTitle = typeof window !== 'undefined'
      ? window.prompt('Rename project', thread.title || 'Untitled Project')
      : null;
    if (!nextTitle || !nextTitle.trim()) return;
    setError('');
    try {
      await cadArenaAPI.renameArchChatThread(targetId, nextTitle.trim());
      await refreshThreads();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDuplicateProject = async (threadId) => {
    const thread = threads.find((t) => t.id === threadId);
    if (!thread) return;
    setError('');
    try {
      const data = await cadArenaAPI.createArchChatThread();
      const newThread = data.thread;
      if (newThread?.id) {
        const newTitle = `${thread.title || 'Untitled Project'} (Copy)`;
        await cadArenaAPI.renameArchChatThread(newThread.id, newTitle);

        // Copy files metadata
        const originalMeta = projectMetadata[threadId] || { files: [], messageCount: 0 };
        setProjectMetadata(prev => ({
          ...prev,
          [newThread.id]: {
            files: [...originalMeta.files],
            archived: false,
            messageCount: originalMeta.messageCount,
            lastActivity: newThread.last_message_at || newThread.created_at || newThread.updated_at
          }
        }));

        await refreshThreads();
        setActiveThreadId(newThread.id);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleArchiveProject = (threadId, isArchived) => {
    setProjectMetadata(prev => {
      const proj = prev[threadId] || { files: [], messageCount: 0 };
      return {
        ...prev,
        [threadId]: {
          ...proj,
          archived: isArchived
        }
      };
    });
  };

  const handleCompileReport = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('Pop-up blocked. Please enable pop-ups to export the report.');
      return;
    }

    const complianceHtml = reportOptions.includeCompliance
      ? complianceRows.map((row, index) => `
          <tr>
            <td>CHK-${index + 1}</td>
            <td>${row.section}</td>
            <td>${row.title}</td>
            <td>${row.metric}</td>
            <td><span class="badge ${row.status === 'violation' ? 'fail' : 'pass'}">${row.status === 'violation' ? 'REVIEW' : 'OK'}</span></td>
          </tr>
        `).join('')
      : '';

    const filesHtml = reportOptions.includeFiles
      ? activeMeta.files.map((file, index) => `
          <tr>
            <td>${index + 1}</td>
            <td>${file.name}</td>
            <td>${file.type || 'file'}</td>
            <td>${formatFileSize(file.size)}</td>
            <td>${file.status || 'ready'}</td>
          </tr>
        `).join('')
      : '';

    const conversationHtml = reportOptions.includeConversation
      ? messages
          .filter((message) => message.role === 'user' || message.role === 'assistant')
          .map((message) => `<p><strong>${message.role === 'user' ? 'You' : 'CadArena AI'}:</strong> ${message.text}</p>`)
          .join('')
      : '';

    printWindow.document.write(`
      <html>
        <head>
          <title>${activeProjectTitle} - Engineering Report</title>
          <style>
            body { font-family: 'Helvetica Neue', Arial, sans-serif; padding: 40px; color: #1e293b; line-height: 1.6; }
            h1 { border-bottom: 2px solid #2563eb; padding-bottom: 10px; color: #0f172a; font-size: 24px; }
            h2 { color: #1e3a8a; font-size: 18px; margin-top: 30px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
            th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; vertical-align: top; }
            th { background: #f8fafc; font-weight: bold; }
            .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
            .pass { background: #dcfce7; color: #15803d; }
            .fail { background: #fee2e2; color: #b91c1c; }
            .meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
            .meta-item { background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; }
          </style>
        </head>
        <body>
          <h1>${activeProjectTitle} Engineering Report</h1>
          <div class="meta-grid">
            <div class="meta-item">
              <strong>Project:</strong> ${activeProjectTitle}<br/>
              <strong>Date:</strong> ${new Date().toLocaleDateString()}<br/>
              <strong>Attached Files:</strong> ${activeMeta.files.length}
            </div>
            <div class="meta-item">
              <strong>Reference Code:</strong> ${activeCodeStd === 'ebc_2020' ? 'Egypt Building Code (EBC) 2020' : 'NFPA 101'}<br/>
              <strong>Indexed Chunks:</strong> ${indexedChunkCount ?? 'Unavailable'}<br/>
              <strong>Conversation Messages:</strong> ${messages.filter((m) => m.role === 'user' || m.role === 'assistant').length}
            </div>
          </div>
          ${reportOptions.includeCompliance ? `
            <h2>Compliance Findings</h2>
            <table>
              <thead>
                <tr>
                  <th>Check ID</th>
                  <th>Source / Section</th>
                  <th>Title</th>
                  <th>Detail</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${complianceHtml || '<tr><td colspan="5">No compliance findings yet. Ask a compliance question in Conversation first.</td></tr>'}
              </tbody>
            </table>
          ` : ''}
          ${reportOptions.includeFiles ? `
            <h2>Project Knowledge Base Files</h2>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>File Name</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${filesHtml || '<tr><td colspan="5">No files attached to this project.</td></tr>'}
              </tbody>
            </table>
          ` : ''}
          ${reportOptions.includeConversation ? `
            <h2>Conversation Log</h2>
            ${conversationHtml || '<p>No conversation history yet.</p>'}
          ` : ''}
          <script>
            window.onload = function() { window.print(); }
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  const handleEmptyStateUploadClick = () => {
    setActiveTab('knowledge');
    setTimeout(() => {
      const fileInput = document.getElementById('rag-file-upload');
      if (fileInput) {
        fileInput.click();
      }
    }, 100);
  };

  // Determine active project files
  const activeMeta = projectMetadata[activeThreadId] || { files: [], archived: false };
  const hasProjectFiles = activeMeta.files.length > 0;
  const activeProjectTitle = threads.find(t => t.id === activeThreadId)?.title || 'Untitled Project';
  const complianceRows = deriveComplianceRows({ sources, findings, messages });
  const selectedSource = sources[selectedSourceIndex] || null;
  const indexedChunkCount = activeThreadId && typeof health?.document_count === 'number' ? health.document_count : null;

  return (
    <div
      className="rag-workspace rag-page-frame flex flex-col overflow-hidden"
      style={{ height: '100vh' }}
    >
      <Navbar />

      {/* ── Context Ribbon ── */}
      <div className="rag-context-ribbon flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-2 px-4 text-xs">
        <div className="flex items-center gap-4">
          <div className="rag-context-field flex items-center gap-1.5 font-bold">
            <FolderGit2 className="h-4 w-4 text-sky-500" />
            <span className="text-slate-400">Project Workspace:</span>
            <span className="text-slate-800 dark:text-slate-200 bg-slate-200 dark:bg-slate-800 px-2 py-0.5 rounded">
              {threads.find(t => t.id === activeThreadId)?.title || 'No active project'}
            </span>
          </div>
          <div className="rag-context-field flex items-center gap-1.5 font-bold">
            <span className="text-slate-400">Compliance Code:</span>
            <select value={activeCodeStd} onChange={e => setActiveCodeStd(e.target.value)} className="rag-context-select">
              <option value="ebc_2020">Egypt Building Code (EBC) 2020</option>
              <option value="nfpa_101">NFPA 101 Life Safety Code</option>
            </select>
          </div>
          <div className="rag-context-field flex items-center gap-1.5 font-bold">
            <span className="text-slate-400">Floor Level:</span>
            <select value={activeFloor} onChange={e => setActiveFloor(e.target.value)} className="rag-context-select">
              <option value="basement">Basement 1</option>
              <option value="floor_1">Ground Floor Plan</option>
              <option value="floor_2">First Floor Plate</option>
            </select>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusPill state={healthState} />
          <button type="button" onClick={refreshHealth} className="rag-toolbar-button" style={{ minHeight: '28px', padding: '4px 8px', fontSize: '0.72rem' }}>
            <RefreshCw className={classNames('h-3.5 w-3.5', healthState === 'checking' && 'animate-spin')} aria-hidden="true" />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            className={classNames('px-2.5 py-1 rounded text-xs font-bold border transition-all', showInspector ? 'bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-100 border-slate-300 dark:border-slate-700' : 'bg-transparent text-slate-400 border-transparent')}
            onClick={() => setShowInspector(!showInspector)}
          >
            Sources Panel
          </button>
          {indexedChunkCount !== null && (
            <span className="text-[0.72rem] font-bold text-slate-500 font-mono">{indexedChunkCount} indexed chunks</span>
          )}
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* ── Project Explorer Sidebar ── */}
        <div style={{ width: sidebarCollapsed ? '48px' : `${sidebarWidth}px`, flexShrink: 0 }} className="h-full relative flex">
          <ArchChatSidebar
            threads={threads}
            activeThreadId={activeThreadId}
            onSelectThread={handleSelectThread}
            onCreateThread={handleCreateThread}
            onRenameThread={handleRenameThread}
            onDuplicateThread={handleDuplicateProject}
            onArchiveThread={handleArchiveProject}
            onDeleteThread={handleDeleteThread}
            projectMetadata={projectMetadata}
            isLoading={isLoadingThreads}
            collapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
          {!sidebarCollapsed && (
            <div
              className="rag-divider-v focus:bg-sky-500 focus:outline-none"
              style={{ outline: 'none' }}
              tabIndex={0}
              role="separator"
              aria-label="Resize Project Explorer"
              aria-valuenow={sidebarWidth}
              aria-valuemin={160}
              aria-valuemax={360}
              onMouseDown={startSidebarDrag}
              onKeyDown={handleSidebarKeyDown}
            />
          )}
        </div>

        {/* ── Central Main Workspace Pane ── */}
        <div className="flex-1 flex flex-col min-w-0 h-full bg-white dark:bg-slate-950 overflow-hidden">
          {/* Workspace mode tabs */}
          <div className="rag-workspace-tabs bg-slate-50/50 dark:bg-slate-900/40 border-b border-slate-200 dark:border-slate-800">
            <button type="button" className={classNames('rag-workspace-tab-btn', activeTab === 'chat' && 'rag-workspace-tab-btn-active')} onClick={() => setActiveTab('chat')}>
              <MessageSquare className="h-3.5 w-3.5" />
              <span>Conversation</span>
            </button>
            <button type="button" className={classNames('rag-workspace-tab-btn', activeTab === 'knowledge' && 'rag-workspace-tab-btn-active')} onClick={() => setActiveTab('knowledge')}>
              <Database className="h-3.5 w-3.5" />
              <span>Project Knowledge Base</span>
            </button>
            <button type="button" className={classNames('rag-workspace-tab-btn', activeTab === 'drawing' && 'rag-workspace-tab-btn-active')} onClick={() => setActiveTab('drawing')}>
              <Layers className="h-3.5 w-3.5" />
              <span>CAD Preview</span>
            </button>
            <button type="button" className={classNames('rag-workspace-tab-btn', activeTab === 'compliance' && 'rag-workspace-tab-btn-active')} onClick={() => setActiveTab('compliance')}>
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Compliance</span>
            </button>
            <button type="button" className={classNames('rag-workspace-tab-btn', activeTab === 'report' && 'rag-workspace-tab-btn-active')} onClick={() => setActiveTab('report')}>
              <ClipboardList className="h-3.5 w-3.5" />
              <span>Reports & Exports</span>
            </button>
          </div>

          {/* Core active workspace tab content pane */}
          <div className="flex-1 overflow-hidden relative">

            {/* TABS 1: Conversation */}
            {activeTab === 'chat' && (
              <div className="flex flex-col h-full overflow-hidden">
                <div className="rag-chat-toolbar flex-shrink-0 border-b border-slate-200 dark:border-slate-850">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="rag-toolbar-icon" aria-hidden="true">
                      <Bot className="h-4 w-4 text-sky-500" />
                    </span>
                    <div className="min-w-0">
                      <p className="rag-eyebrow">Project AI Reasoning Companion</p>
                      <h2 className="rag-chat-title text-sm font-black">
                        {threads.find(t => t.id === activeThreadId)?.title || 'Create or select a project to begin'}
                      </h2>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {activeThreadId && (
                      <button type="button" onClick={() => handleRenameThread(activeThreadId)} className="rag-toolbar-button px-2.5 py-1 min-h-0 text-xs">
                        Rename
                      </button>
                    )}
                    <span className="rag-collection-chip text-xs px-2 py-0.5 font-mono">{collection || 'default'}</span>
                  </div>
                </div>

                <AnimatePresence>
                  {(error || notice) && <Notice error={error} notice={notice} />}
                </AnimatePresence>

                <div ref={messageListRef} className="rag-message-list flex-1 overflow-y-auto p-4 bg-slate-50/20 dark:bg-slate-950/20">
                  {isLoadingMessages && (
                    <div className="sticky top-0 z-10 mb-3 flex items-center gap-2 rounded-md border border-sky-200/70 bg-sky-50/95 px-3 py-2 text-xs text-sky-700 dark:border-sky-900 dark:bg-sky-950/90 dark:text-sky-300">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Loading conversation…</span>
                    </div>
                  )}
                  <AnimatePresence initial={false}>
                    {!activeThreadId ? (
                      <div className="flex flex-col items-center justify-center h-full text-center p-8 max-w-sm mx-auto">
                        <FolderGit2 className="h-10 w-10 text-slate-300 dark:text-slate-700 mb-3 animate-pulse" />
                        <h3 className="text-sm font-black text-slate-800 dark:text-slate-200">No Project Open</h3>
                        <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                          Select a project from the explorer sidebar, or create a new workspace project to begin compliance auditing.
                        </p>
                        <button onClick={handleCreateThread} className="mt-4 px-4 py-2 text-xs font-bold bg-sky-500 text-white rounded-md hover:bg-sky-600 shadow-sm transition-all">
                          New Project Workspace
                        </button>
                      </div>
                    ) : !isLoadingMessages && messages.length === 0 && !isQuerying ? (
                      <OnboardingState
                        hasProjectFiles={hasProjectFiles}
                        onUploadClick={handleEmptyStateUploadClick}
                      />
                    ) : (
                      messages.map((message, index) => {
                        if (message.role === 'reasoning') {
                          return <ReasoningMessage key={message.id || `reasoning-${index}`} message={message} index={index} />;
                        }
                        return (
                          <ChatMessage
                            key={`${message.role}-${index}-${(message.text || '').slice(0, 24)}`}
                            message={message}
                            index={index}
                            onCitationClick={handleCitationClick}
                          />
                        );
                      })
                    )}
                  </AnimatePresence>
                </div>

                {activeThreadId && (
                  <form onSubmit={submitQuery} className="rag-composer flex-shrink-0 border-t border-slate-200 dark:border-slate-850 p-3 bg-white dark:bg-slate-950">
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-1.5 text-[0.68rem] font-bold text-slate-500 dark:text-slate-400">
                        <ShieldCheck className="h-3.5 w-3.5 text-sky-500" aria-hidden="true" />
                        EBC Code Compliance Evaluator
                      </div>
                      {/* Model selector dropdown */}
                      <div ref={modelMenuRef} style={{ position: 'relative' }}>
                        <button
                          type="button"
                          id="llm-model-selector"
                          onClick={() => setIsModelMenuOpen((o) => !o)}
                          className="rag-model-selector-btn text-xs font-mono py-1 px-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded flex items-center gap-1 text-slate-600 dark:text-slate-300"
                        >
                          {selectedProvider === 'OLLAMA' ? <Cpu className="h-3.5 w-3.5" /> : <Zap className="h-3.5 w-3.5 text-amber-500" />}
                          <span>{selectedModel ? selectedModel.split(':')[0] : (selectedProvider || 'Cohere')}</span>
                          <ChevronDown className="h-3 w-3 opacity-60" />
                        </button>

                        <AnimatePresence>
                          {isModelMenuOpen && (
                            <motion.div
                              initial={{ opacity: 0, y: -6, scale: 0.97 }}
                              animate={{ opacity: 1, y: 0, scale: 1 }}
                              exit={{ opacity: 0, y: -6, scale: 0.97 }}
                              transition={{ duration: 0.14 }}
                              className="rag-model-menu absolute bottom-full right-0 mb-1 z-50 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-xl rounded-lg py-1.5 w-52 max-h-60 overflow-y-auto text-xs"
                            >
                              {availableModels?.cohere_available && (
                                <button
                                  type="button"
                                  className="w-full text-left px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-900 flex items-center justify-between"
                                  onClick={() => {
                                    setSelectedProvider('COHERE');
                                    setSelectedModel(availableModels?.default_model || null);
                                    setIsModelMenuOpen(false);
                                  }}
                                >
                                  <span className="font-bold text-slate-700 dark:text-slate-350">☁ Cohere Cloud</span>
                                  {selectedProvider === 'COHERE' && <Check className="h-3.5 w-3.5 text-emerald-500" />}
                                </button>
                              )}
                              {availableModels?.ollama?.length > 0 && (
                                <div className="border-t border-slate-100 dark:border-slate-900 my-1 pt-1">
                                  <div className="px-3 py-1 font-bold text-[0.65rem] text-slate-400 uppercase tracking-widest">Ollama Local</div>
                                  {availableModels.ollama.map((m) => (
                                    <button
                                      key={m.name}
                                      type="button"
                                      className="w-full text-left px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-900 flex items-center justify-between"
                                      onClick={() => {
                                        setSelectedProvider('OLLAMA');
                                        setSelectedModel(m.name);
                                        setIsModelMenuOpen(false);
                                      }}
                                    >
                                      <span>{m.name.split(':')[0]}</span>
                                      {selectedProvider === 'OLLAMA' && selectedModel === m.name && <Check className="h-3.5 w-3.5 text-emerald-500" />}
                                    </button>
                                  ))}
                                </div>
                              )}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </div>

                    <label htmlFor="rag-question" className="sr-only">Question</label>
                    <div className="rag-input-shell flex items-center gap-2 relative bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-1.5 focus-within:ring-1 focus-within:ring-sky-500">
                      <textarea
                        ref={questionRef}
                        id="rag-question"
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        onKeyDown={handleQuestionKeyDown}
                        rows={1}
                        className="rag-question-input flex-1 bg-transparent border-0 resize-none outline-none text-xs p-1.5 text-slate-800 dark:text-slate-200 focus:ring-0 max-h-40"
                        placeholder={hasProjectFiles
                          ? 'Ask a question about the uploaded project files...'
                          : 'Say hello, or upload a project file before asking an engineering question...'}
                      />
                      <motion.button
                        type="submit"
                        disabled={!canAsk}
                        className={classNames('rag-send-button shrink-0 w-8 h-8 rounded-md flex items-center justify-center transition-all', canAsk ? 'bg-sky-500 hover:bg-sky-600 text-white' : 'bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed')}
                        whileHover={canAsk ? { scale: 1.03 } : undefined}
                        whileTap={canAsk ? { scale: 0.96 } : undefined}
                      >
                        {isQuerying ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
                      </motion.button>
                    </div>
                  </form>
                )}
              </div>
            )}

            {/* TABS 2: Project Knowledge Base */}
            {activeTab === 'knowledge' && (
              <div className="p-5 overflow-y-auto h-full bg-slate-50 dark:bg-slate-900/20">
                {!activeThreadId ? (
                  <div className="text-center py-12">
                    <Database className="h-10 w-10 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
                    <p className="text-xs text-slate-400">Open a project first to access its knowledge base.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left 2 Cols: Attached Files */}
                    <div className="lg:col-span-2 space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h2 className="text-sm font-black text-slate-800 dark:text-slate-200">Attached Knowledge Files</h2>
                          <p className="text-[0.68rem] text-slate-400">Indexed document files linked to this engineering project.</p>
                        </div>
                        <span className="text-[0.65rem] bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 font-mono px-2 py-0.5 rounded font-bold">
                          {activeMeta.files.length} Item{activeMeta.files.length === 1 ? '' : 's'}
                        </span>
                      </div>

                      {activeMeta.files.length === 0 ? (
                        <div className="border border-dashed border-slate-250 dark:border-slate-800 p-8 rounded-xl text-center bg-white dark:bg-slate-950">
                          <FileText className="h-8 w-8 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
                          <p className="text-xs font-bold text-slate-700 dark:text-slate-300">No attached files</p>
                          <p className="text-[0.68rem] text-slate-400 mt-0.5 max-w-xs mx-auto leading-relaxed">
                            Drag and drop PDF code regulations, DXF structural drawings, or BOQ schedules to build this project's index.
                          </p>
                        </div>
                      ) : (
                        <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-white dark:bg-slate-950 shadow-2xs divide-y divide-slate-100 dark:divide-slate-900">
                          {activeMeta.files.map((file, i) => {
                            let fileIcon = <File className="h-4 w-4 text-slate-400" />;
                            let typeLabel = 'File';

                            if (file.type === 'pdf') {
                              fileIcon = <FileText className="h-4 w-4 text-rose-500" />;
                              typeLabel = 'Regulations Code (PDF)';
                            } else if (file.type === 'dxf') {
                              fileIcon = <FileCode2 className="h-4 w-4 text-sky-500" />;
                              typeLabel = 'Floor Layout (DXF)';
                            } else if (file.type === 'xlsx' || file.type === 'xls' || file.type === 'csv') {
                              fileIcon = <FileSpreadsheet className="h-4 w-4 text-emerald-500" />;
                              typeLabel = 'Quantities Takeoff (BOQ)';
                            }

                            // Dynamic status badge mapping
                            let statusBadge = (
                              <span className="text-[0.6rem] bg-indigo-50 dark:bg-indigo-950 text-indigo-500 px-2 py-0.5 rounded font-bold uppercase">
                                Ready
                              </span>
                            );

                            if (file.status === 'processing') {
                              statusBadge = (
                                <span className="text-[0.6rem] bg-purple-50 dark:bg-purple-950 text-purple-500 px-2 py-0.5 rounded font-bold uppercase animate-pulse flex items-center gap-1">
                                  <Loader2 className="h-2.5 w-2.5 animate-spin" /> Processing
                                </span>
                              );
                            } else if (file.status === 'embedding') {
                              statusBadge = (
                                <span className="text-[0.6rem] bg-sky-50 dark:bg-sky-950 text-sky-500 px-2 py-0.5 rounded font-bold uppercase animate-pulse flex items-center gap-1">
                                  <Cpu className="h-2.5 w-2.5 animate-pulse" /> Embedding
                                </span>
                              );
                            } else if (file.status === 'indexed') {
                              statusBadge = (
                                <span className="text-[0.6rem] bg-emerald-50 dark:bg-emerald-950 text-emerald-500 px-2 py-0.5 rounded font-bold uppercase flex items-center gap-1">
                                  <Check className="h-2.5 w-2.5" /> Indexed
                                </span>
                              );
                            }

                            return (
                              <div key={`${file.name}-${i}`} className="p-3.5 flex items-center justify-between gap-3 text-xs">
                                <div className="flex items-center gap-3 min-w-0">
                                  <span className="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-900 flex items-center justify-center shrink-0 border border-slate-100 dark:border-slate-800">
                                    {fileIcon}
                                  </span>
                                  <div className="min-w-0">
                                    <span className="font-bold text-slate-800 dark:text-slate-200 block truncate max-w-xs md:max-w-md" title={file.name}>
                                      {file.name}
                                    </span>
                                    <span className="text-[0.65rem] text-slate-400 block font-normal">
                                      {typeLabel} · {(file.size / 1024).toFixed(1)} KB · Added {new Date(file.uploadedAt).toLocaleDateString()}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {statusBadge}
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteFile(file, i)}
                                    className="p-1 hover:bg-slate-100 dark:hover:bg-slate-900 rounded text-slate-400 hover:text-red-500 transition-colors"
                                    title="Delete file"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Right Col: Dropzone & Vector Database stats */}
                    <div className="space-y-5">
                      <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-white dark:bg-slate-950 shadow-2xs">
                        <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-widest font-mono mb-3">Attach File</h3>
                        <label
                          htmlFor="rag-file-upload"
                          onDragOver={(event) => {
                            event.preventDefault();
                            setIsDragging(true);
                          }}
                          onDragLeave={() => setIsDragging(false)}
                          onDrop={handleDrop}
                          className={classNames('rag-dropzone border-2 border-dashed rounded-xl p-6 text-center cursor-pointer flex flex-col items-center justify-center transition-all bg-slate-50/50 hover:bg-slate-50 dark:bg-slate-900/20 dark:hover:bg-slate-900/40', isDragging ? 'border-sky-500 bg-sky-50/5' : 'border-slate-250 dark:border-slate-850')}
                        >
                          <input
                            ref={fileInputRef}
                            id="rag-file-upload"
                            type="file"
                            multiple
                            className="sr-only"
                            disabled={isUploadingFiles}
                            onChange={(event) => handleFiles(event.target.files)}
                          />
                          <span className="w-10 h-10 bg-sky-500/10 text-sky-500 rounded-full flex items-center justify-center mb-3">
                            {isUploadingFiles ? <Loader2 className="h-5 w-5 animate-spin" /> : <UploadCloud className="h-5 w-5" />}
                          </span>
                          <span className="block text-xs font-bold text-slate-850 dark:text-slate-150">
                            {isUploadingFiles ? 'Extracting text blocks...' : 'Upload PDF, DXF, or XLSX'}
                          </span>
                          <span className="block text-[0.62rem] text-slate-400 mt-1">Drag files here or click to browse</span>
                        </label>
                      </div>

                      {/* DB stats panel */}
                      <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-white dark:bg-slate-950 shadow-2xs space-y-3.5">
                        <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-900 pb-2">
                          <HardDrive className="h-4 w-4 text-indigo-500" />
                          <h3 className="text-xs font-bold text-slate-850 dark:text-slate-150 uppercase tracking-widest font-mono">Indexing Engine</h3>
                        </div>

                        <div className="space-y-2 text-[0.68rem] text-slate-500 dark:text-slate-400 font-mono">
                          <div className="flex justify-between">
                            <span>VECTOR STORE:</span>
                            <span className="font-bold text-emerald-500">{health?.vector_store || 'Unavailable'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>COLLECTION:</span>
                            <span className="font-bold text-slate-700 dark:text-slate-300">{collection}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>TOTAL CHUNKS:</span>
                            <span className="font-bold text-slate-700 dark:text-slate-300">{indexedChunkCount ?? '—'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>EMBEDDINGS:</span>
                            <span className="font-bold text-slate-700 dark:text-slate-300">{health?.embedding_model || '—'}</span>
                          </div>
                        </div>

                        <div className="bg-slate-50 dark:bg-slate-900/60 p-2.5 border border-slate-100 dark:border-slate-900 rounded-lg flex items-center gap-2 text-[0.65rem] text-slate-450 leading-relaxed">
                          <Info className="h-3.5 w-3.5 text-sky-500 shrink-0" />
                          <span>All files attached to this workspace are automatically segmented and vectorized into a local collection schema to ensure reasoning privacy.</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TABS 3: CAD Preview */}
            {activeTab === 'drawing' && (
              <ProjectCadPreview projectFiles={activeMeta.files} sources={sources} />
            )}

            {/* TABS 4: Compliance */}
            {activeTab === 'compliance' && (
              <div className="p-5 overflow-y-auto h-full bg-slate-50 dark:bg-slate-900/20">
                <div className="mb-4">
                  <h2 className="text-sm font-black uppercase tracking-wider text-slate-650 dark:text-slate-400">
                    {activeCodeStd === 'ebc_2020' ? 'EBC 2020 Compliance Findings' : 'NFPA 101 Compliance Findings'}
                  </h2>
                  <p className="text-xs text-slate-450 mt-1">
                    Derived from the latest AI analysis, indexed sources, and project knowledge base for {activeProjectTitle}.
                  </p>
                </div>
                {complianceRows.length === 0 ? (
                  <div className="border border-dashed border-slate-250 dark:border-slate-800 p-8 rounded-xl text-center bg-white dark:bg-slate-950">
                    <ShieldCheck className="h-8 w-8 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
                    <p className="text-xs font-bold text-slate-700 dark:text-slate-300">No compliance findings yet</p>
                    <p className="text-[0.68rem] text-slate-400 mt-1 max-w-sm mx-auto leading-relaxed">
                      Upload project files, then ask a compliance question in Conversation to populate this checklist.
                    </p>
                  </div>
                ) : (
                  <div className="bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                    <table className="spreadsheet-table">
                      <thead>
                        <tr>
                          <th>Source / Section</th>
                          <th>Finding</th>
                          <th>Detail</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {complianceRows.map((row) => (
                          <tr key={row.id}>
                            <td>{row.section}</td>
                            <td>{row.title}</td>
                            <td>{row.metric}</td>
                            <td>
                              <span style={{
                                color: row.status === 'violation' ? '#dc2626' : row.status === 'review' ? '#d97706' : '#22c55e',
                                fontWeight: 'bold',
                              }}>
                                {row.status === 'violation' ? 'Review Required' : row.status === 'review' ? 'Needs Review' : 'Verified'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* TABS 5: Reports & Exports */}
            {activeTab === 'report' && (
              <div className="p-5 h-full overflow-y-auto bg-slate-50 dark:bg-slate-900/20">
                <div className="max-w-2xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 p-6 rounded-lg shadow-sm">
                  <h2 className="text-sm font-black uppercase tracking-wider text-slate-700 dark:text-slate-350 border-b pb-3 mb-4">Export Project Report</h2>
                  <p className="text-xs text-slate-500 mb-4">
                    Generate a printable report from the current project&apos;s files, compliance findings, and optional conversation history.
                  </p>
                  <div className="space-y-3">
                    <label className="flex items-center gap-2.5 text-xs font-bold text-slate-600 dark:text-slate-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={reportOptions.includeCompliance}
                        onChange={(event) => setReportOptions((current) => ({ ...current, includeCompliance: event.target.checked }))}
                        className="rounded text-sky-500 border-slate-300 focus:ring-0"
                      />
                      Include compliance findings ({complianceRows.length})
                    </label>
                    <label className="flex items-center gap-2.5 text-xs font-bold text-slate-600 dark:text-slate-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={reportOptions.includeFiles}
                        onChange={(event) => setReportOptions((current) => ({ ...current, includeFiles: event.target.checked }))}
                        className="rounded text-sky-500 border-slate-300 focus:ring-0"
                      />
                      Include attached project files ({activeMeta.files.length})
                    </label>
                    <label className="flex items-center gap-2.5 text-xs font-bold text-slate-600 dark:text-slate-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={reportOptions.includeConversation}
                        onChange={(event) => setReportOptions((current) => ({ ...current, includeConversation: event.target.checked }))}
                        className="rounded text-sky-500 border-slate-300 focus:ring-0"
                      />
                      Include conversation history
                    </label>
                  </div>
                  <button type="button" className="rag-primary-button mt-6 max-w-xs font-bold bg-sky-500 hover:bg-sky-600 text-white py-2 px-4 rounded-md shadow-sm" onClick={handleCompileReport}>
                    Compile & Export PDF Report
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>

        {showInspector && (
          <div style={{ width: `${rightPanelWidth}px`, flexShrink: 0 }} className="h-full relative flex">
            <div
              className="rag-divider-v focus:bg-sky-500 focus:outline-none"
              style={{ outline: 'none' }}
              tabIndex={0}
              role="separator"
              aria-label="Resize right inspector panel"
              aria-valuenow={rightPanelWidth}
              aria-valuemin={280}
              aria-valuemax={750}
              onMouseDown={startRightPanelDrag}
              onKeyDown={handleRightPanelKeyDown}
            />

            <div className="flex-1 h-full overflow-hidden bg-white dark:bg-slate-950 flex flex-col">
              <div className="rag-inspector-section flex flex-col" style={{ height: '42%', minHeight: '180px' }}>
                <div className="rag-inspector-tabs" style={{ padding: '6px 12px 0' }}>
                  <button type="button" className="rag-inspector-tab rag-inspector-tab-active">
                    Retrieved Sources
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-4 border-t border-slate-100 dark:border-slate-900">
                  <div className="rag-inspector-header flex items-center justify-between mb-3">
                    <div>
                      <p className="rag-eyebrow text-[0.62rem] font-bold text-slate-400 uppercase tracking-widest font-mono">Evidence Engine</p>
                      <h2 className="rag-panel-title text-xs font-black">Segment Citations</h2>
                    </div>
                    <Gauge className="h-4 w-4 text-slate-400" />
                  </div>
                  <SourceList
                    sources={sources}
                    isLoading={isQuerying}
                    onCitationClick={(citationText, sourceIndex) => {
                      if (typeof sourceIndex === 'number') {
                        setSelectedSourceIndex(sourceIndex);
                      } else {
                        handleCitationClick(citationText);
                      }
                    }}
                  />
                </div>
              </div>

              <div className="rag-inspector-section flex-1 min-h-0 border-t border-slate-200 dark:border-slate-800">
                <SourceDocumentPreview source={selectedSource} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
