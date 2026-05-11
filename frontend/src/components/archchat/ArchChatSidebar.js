import React from 'react';
import PropTypes from 'prop-types';
import { Plus, Search, Trash2 } from 'lucide-react';

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

export default function ArchChatSidebar({
  threads,
  activeThreadId = null,
  onSelectThread,
  onCreateThread,
  onDeleteThread,
  isLoading = false,
}) {
  const [query, setQuery] = React.useState('');

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return threads;
    return threads.filter((t) => (t.title || '').toLowerCase().includes(q));
  }, [threads, query]);

  return (
    <aside className="rag-rail">
      <section className="rag-rail-group">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="rag-eyebrow">Chats</p>
            <h2 className="rag-panel-title">Your history</h2>
          </div>
          <button type="button" onClick={onCreateThread} className="rag-toolbar-button" disabled={isLoading}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            <span>New</span>
          </button>
        </div>

        <label className="rag-field">
          <span className="sr-only">Search chats</span>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="app-input pl-10"
              placeholder="Search chats..."
            />
          </div>
        </label>

        <div className="mt-4 space-y-2">
          {isLoading && threads.length === 0 ? (
            <div className="space-y-2">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="rag-source-card p-3">
                  <span className="app-skeleton block h-4 w-3/4" />
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-sm leading-6 text-slate-500 dark:text-slate-400">
              No chats yet. Create one to start.
            </p>
          ) : (
            filtered.map((thread) => {
              const active = thread.id === activeThreadId;
              return (
                <div
                  key={thread.id}
                  className={classNames(
                    'rag-source-card p-3 flex items-center justify-between gap-3',
                    active && 'ring-2 ring-sky-500/40'
                  )}
                >
                  <button
                    type="button"
                    onClick={() => onSelectThread(thread.id)}
                    className={classNames(
                      'min-w-0 text-left flex-1',
                      active ? 'text-slate-900 dark:text-slate-50' : 'text-slate-700 dark:text-slate-200'
                    )}
                    title={thread.title}
                  >
                    <div className="truncate text-sm font-black">{thread.title || 'New chat'}</div>
                    {thread.last_message_at && (
                      <div className="mt-1 text-xs text-slate-500 dark:text-slate-400 truncate">
                        {new Date(thread.last_message_at).toLocaleString()}
                      </div>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => onDeleteThread(thread.id)}
                    className="rag-toolbar-button"
                    title="Delete chat"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </button>
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
  onDeleteThread: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
};



