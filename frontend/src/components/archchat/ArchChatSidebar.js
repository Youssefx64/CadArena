import React from 'react';
import PropTypes from 'prop-types';
import {
  Plus,
  Search,
  Trash2,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  FolderGit2,
  FileText,
  Copy,
  Archive,
  ArchiveRestore,
  ChevronDown,
  ArrowUpDown,
  Filter,
} from 'lucide-react';

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

function getRelativeTime(timestamp) {
  if (!timestamp) return 'No activity';
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now - date;

  if (diffMs < 0) return 'Just now'; // handle tiny timezone discrepancies

  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hr ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  return date.toLocaleDateString();
}

export default function ArchChatSidebar({
  threads,
  activeThreadId = null,
  onSelectThread,
  onCreateThread,
  onRenameThread,
  onDuplicateThread,
  onArchiveThread,
  onDeleteThread,
  projectMetadata = {},
  isLoading = false,
  collapsed = false,
  onToggleCollapse = () => {},
}) {
  const [query, setQuery] = React.useState('');
  const [sortBy, setSortBy] = React.useState('activity'); // 'activity', 'name', 'messages', 'files'
  const [filterBy, setFilterBy] = React.useState('active'); // 'all', 'active', 'archived', 'has_files'
  const [activeMenuId, setActiveMenuId] = React.useState(null);

  const menuRef = React.useRef(null);

  React.useEffect(() => {
    const clickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setActiveMenuId(null);
      }
    };
    document.addEventListener('mousedown', clickOutside);
    return () => document.removeEventListener('mousedown', clickOutside);
  }, []);

  const enrichedThreads = React.useMemo(() => {
    return threads.map(t => {
      const meta = projectMetadata[t.id] || {};
      return {
        ...t,
        filesCount: Array.isArray(meta.files) ? meta.files.length : (meta.filesCount || 0),
        messageCount: typeof meta.messageCount === 'number' ? meta.messageCount : 0,
        status: meta.archived ? 'archived' : 'active',
        // Selecting or renaming a project must not change its activity order.
        lastActivity: t.last_message_at || t.created_at || t.updated_at
      };
    });
  }, [threads, projectMetadata]);

  const filtered = React.useMemo(() => {
    let result = enrichedThreads;

    // Search query
    const q = query.trim().toLowerCase();
    if (q) {
      result = result.filter(t =>
        (t.title || '').toLowerCase().includes(q) ||
        (projectMetadata[t.id]?.files || []).some(f => f.name.toLowerCase().includes(q))
      );
    }

    // Filter
    if (filterBy === 'active') {
      result = result.filter(t => t.status === 'active');
    } else if (filterBy === 'archived') {
      result = result.filter(t => t.status === 'archived');
    } else if (filterBy === 'has_files') {
      result = result.filter(t => t.filesCount > 0);
    }

    // Sort
    result.sort((a, b) => {
      if (sortBy === 'name') {
        return (a.title || '').localeCompare(b.title || '');
      }
      if (sortBy === 'messages') {
        return b.messageCount - a.messageCount;
      }
      if (sortBy === 'files') {
        return b.filesCount - a.filesCount;
      }
      // default: activity (newest first)
      return new Date(b.lastActivity) - new Date(a.lastActivity);
    });

    return result;
  }, [enrichedThreads, query, sortBy, filterBy, projectMetadata]);

  if (collapsed) {
    return (
      <aside className="rag-rail flex flex-col items-center py-4 px-1 gap-4" style={{ width: '48px', minWidth: '48px', overflow: 'hidden' }}>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="rag-toolbar-button p-2 min-h-0 border-0 bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800"
          title="Expand Project Explorer"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onCreateThread}
          className="rag-toolbar-button p-2 min-h-0 border-0 bg-sky-500 hover:bg-sky-600 text-white rounded-full"
          title="New Project"
          disabled={isLoading}
        >
          <Plus className="h-4 w-4" />
        </button>
        <div className="flex-1 w-full flex flex-col items-center gap-2 mt-4 overflow-y-auto overflow-x-hidden">
          {filtered.map((thread) => {
            const active = thread.id === activeThreadId;
            return (
              <button
                key={thread.id}
                type="button"
                onClick={() => onSelectThread(thread.id)}
                className={classNames(
                  'p-2.5 rounded-lg transition-all flex items-center justify-center relative group',
                  active ? 'bg-sky-100 text-sky-600 dark:bg-slate-800 dark:text-sky-400' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'
                )}
                title={thread.title || 'Untitled Project'}
              >
                <FolderGit2 className="h-4 w-4" />
                {thread.filesCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-sky-500 text-white text-[0.6rem] font-bold rounded-full w-4 h-4 flex items-center justify-center scale-90">
                    {thread.filesCount}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </aside>
    );
  }

  return (
    <aside className="rag-rail h-full select-none" style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
      <section className="rag-rail-group flex-1 flex flex-col min-h-0 p-3">
        {/* Header */}
        <div className="mb-3 flex items-center justify-between gap-2">
          <div>
            <p className="text-[0.68rem] font-bold text-sky-500 uppercase tracking-widest font-mono">Workspace</p>
            <h2 className="text-sm font-black text-slate-800 dark:text-slate-200">Project Explorer</h2>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={onCreateThread}
              className="rag-primary-button py-1.5 px-3 min-h-0 text-xs flex items-center gap-1 bg-sky-500 hover:bg-sky-600 text-white rounded-md font-bold shadow-sm"
              disabled={isLoading}
            >
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              <span>New Project</span>
            </button>
            <button
              type="button"
              onClick={onToggleCollapse}
              className="rag-toolbar-button p-1.5 min-h-0 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 rounded-md"
              title="Collapse sidebar"
            >
              <ChevronLeft className="h-3.5 w-3.5 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400 z-10" aria-hidden="true" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="app-input pl-9 text-xs py-1.5 w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-md text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
            placeholder="Search projects or files..."
            style={{ paddingLeft: '2.25rem' }}
          />
        </div>

        {/* Controls: Sorting & Filtering */}
        <div className="flex items-center justify-between gap-2 mb-3 text-[0.7rem] border-b border-slate-100 dark:border-slate-900 pb-2">
          {/* Filter */}
          <div className="flex items-center gap-1 text-slate-500">
            <Filter className="h-3 w-3" />
            <select
              value={filterBy}
              onChange={(e) => setFilterBy(e.target.value)}
              className="bg-transparent border-none text-slate-600 dark:text-slate-300 font-bold focus:outline-none cursor-pointer"
            >
              <option value="active">Active Projects</option>
              <option value="archived">Archived</option>
              <option value="has_files">With Files</option>
              <option value="all">All Projects</option>
            </select>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-1 text-slate-500">
            <ArrowUpDown className="h-3 w-3" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-transparent border-none text-slate-600 dark:text-slate-300 font-bold focus:outline-none cursor-pointer"
            >
              <option value="activity">Recent Activity</option>
              <option value="name">Name A-Z</option>
              <option value="messages">Message Count</option>
              <option value="files">Knowledge Files</option>
            </select>
          </div>
        </div>

        {/* Projects List */}
        <div className="space-y-2 flex-1 overflow-y-auto pr-1">
          {isLoading && threads.length === 0 ? (
            <div className="space-y-2">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="rag-source-card p-3 rounded-lg border border-slate-100 dark:border-slate-900 animate-pulse">
                  <span className="app-skeleton block h-4 w-3/4 mb-2 bg-slate-200 dark:bg-slate-800 rounded" />
                  <span className="app-skeleton block h-3 w-1/2 bg-slate-100 dark:bg-slate-900 rounded" />
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-8 text-center">
              <FolderGit2 className="h-8 w-8 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
              <p className="text-xs text-slate-400">
                No engineering projects found.
              </p>
            </div>
          ) : (
            filtered.map((thread) => {
              const active = thread.id === activeThreadId;
              const menuOpen = activeMenuId === thread.id;

              return (
                <div
                  key={thread.id}
                  className={classNames(
                    'group relative rounded-lg border p-2.5 transition-all cursor-pointer flex flex-col gap-1.5',
                    active
                      ? 'border-sky-500/50 bg-sky-50/10 dark:bg-sky-500/5 ring-1 ring-sky-500/25 shadow-sm'
                      : 'border-slate-200 dark:border-slate-900 hover:border-slate-300 dark:hover:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/50'
                  )}
                  onClick={() => onSelectThread(thread.id)}
                >
                  {/* Card Main Info */}
                  <div className="flex items-start justify-between gap-1.5 min-w-0">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <FolderGit2 className={classNames('h-3.5 w-3.5 shrink-0', active ? 'text-sky-500' : 'text-slate-400')} />
                        <span className={classNames(
                          'truncate text-[0.82rem] font-bold block',
                          active ? 'text-sky-600 dark:text-sky-400' : 'text-slate-800 dark:text-slate-200'
                        )}>
                          {thread.title || 'Untitled Project'}
                        </span>
                      </div>
                      <span className="text-[0.66rem] text-slate-400 font-mono block">
                        Updated {getRelativeTime(thread.lastActivity)}
                      </span>
                    </div>

                    {/* Context Actions Button */}
                    <div className="relative shrink-0" onClick={e => e.stopPropagation()}>
                      <button
                        type="button"
                        onClick={() => setActiveMenuId(menuOpen ? null : thread.id)}
                        className="opacity-0 group-hover:opacity-100 focus:opacity-100 p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded transition-opacity"
                        title="Project options"
                      >
                        <ChevronDown className="h-3.5 w-3.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" />
                      </button>

                      {/* Dropdown Menu */}
                      {menuOpen && (
                        <div
                          ref={menuRef}
                          className="absolute right-0 mt-1 w-36 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-md shadow-lg py-1 z-50 text-xs font-bold"
                        >
                          <button
                            type="button"
                            onClick={() => {
                              onRenameThread(thread.id);
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900"
                          >
                            Rename Project
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              onDuplicateThread(thread.id);
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900 flex items-center gap-1.5"
                          >
                            <Copy className="h-3 w-3" /> Duplicate
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              onArchiveThread(thread.id, thread.status === 'active');
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900 flex items-center gap-1.5"
                          >
                            {thread.status === 'active' ? (
                              <>
                                <Archive className="h-3 w-3" /> Archive
                              </>
                            ) : (
                              <>
                                <ArchiveRestore className="h-3 w-3" /> Unarchive
                              </>
                            )}
                          </button>
                          <div className="border-t border-slate-100 dark:border-slate-900 my-1" />
                          <button
                            type="button"
                            onClick={() => {
                              onDeleteThread(thread.id);
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-3 py-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 flex items-center gap-1.5"
                          >
                            <Trash2 className="h-3 w-3" /> Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Card Bottom Meta */}
                  <div className="flex items-center gap-3 text-[0.68rem] text-slate-500 font-bold border-t border-slate-100/50 dark:border-slate-900/50 pt-1.5 mt-0.5">
                    <span className="flex items-center gap-1" title="Knowledge base files count">
                      <FileText className="h-3.5 w-3.5 text-slate-400" />
                      {thread.filesCount} file{thread.filesCount === 1 ? '' : 's'}
                    </span>
                    <span className="flex items-center gap-1" title="Conversation count">
                      <MessageSquare className="h-3.5 w-3.5 text-slate-400" />
                      {thread.messageCount} msg{thread.messageCount === 1 ? '' : 's'}
                    </span>

                    {thread.status === 'archived' && (
                      <span className="ml-auto bg-slate-100 dark:bg-slate-800 text-slate-500 text-[0.55rem] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider">
                        Archived
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>
    </aside>
  );
}

ArchChatSidebar.propTypes = {
  threads: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string,
      last_message_at: PropTypes.string,
    })
  ).isRequired,
  activeThreadId: PropTypes.string,
  onSelectThread: PropTypes.func.isRequired,
  onCreateThread: PropTypes.func.isRequired,
  onRenameThread: PropTypes.func.isRequired,
  onDuplicateThread: PropTypes.func.isRequired,
  onArchiveThread: PropTypes.func.isRequired,
  onDeleteThread: PropTypes.func.isRequired,
  projectMetadata: PropTypes.object,
  isLoading: PropTypes.bool,
  collapsed: PropTypes.bool,
  onToggleCollapse: PropTypes.func,
};
