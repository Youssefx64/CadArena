import React, { useState, useMemo, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { 
  Plus, Search, ChevronLeft, ChevronRight, 
  FolderGit2, ArrowUpDown, Filter,
  ChevronDown, Copy, Archive, Trash2,
  MessageSquare, Layers
} from 'lucide-react';
import toast from 'react-hot-toast';

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

function getRelativeTime(timestamp) {
  if (!timestamp) return 'No activity';
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now - date;

  if (diffMs < 0) return 'Just now';

  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export default function ProjectExplorerNext({
  projects,
  activeProjectId,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
  messages,
  activeFileToken,
  onSelectVersion,
  isLoading = false,
  collapsed = false,
  onToggleCollapse = () => {}
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('activity'); // 'activity', 'name', 'drawings'
  const [filterBy, setFilterBy] = useState('active'); // 'all', 'active', 'has_cad'
  const [activeMenuId, setActiveMenuId] = useState(null);

  const menuRef = useRef(null);

  useEffect(() => {
    const clickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setActiveMenuId(null);
      }
    };
    document.addEventListener('mousedown', clickOutside);
    return () => document.removeEventListener('mousedown', clickOutside);
  }, []);

  // Compute drawing count per project from messages if possible, or fallback to metadata
  const enrichedProjects = useMemo(() => {
    return projects.map((p) => {
      // Find all successful dxf files in project messages
      const msgCount = p.message_count || 0;
      const drawCount = p.drawings_count || 0; // if backend returned it
      return {
        ...p,
        msgCount,
        drawCount,
        lastActivity: p.last_message_at || p.updated_at || p.created_at
      };
    });
  }, [projects]);

  // Extract drawing versions from current project's messages
  const drawingVersions = useMemo(() => {
    if (!messages) return [];
    return messages
      .filter((m) => m.role === 'assistant' && m.file_token)
      .map((m, idx) => ({
        id: m.id,
        fileToken: m.file_token,
        dxfName: m.dxf_name || `version_${idx + 1}.dxf`,
        timestamp: m.created_at || new Date().toISOString(),
        modelUsed: m.model_used || 'default'
      }))
      .reverse(); // Newest versions first
  }, [messages]);

  const filteredProjects = useMemo(() => {
    let result = enrichedProjects;

    const q = searchQuery.trim().toLowerCase();
    if (q) {
      result = result.filter((p) => (p.name || '').toLowerCase().includes(q));
    }

    if (filterBy === 'has_cad') {
      result = result.filter((p) => p.drawCount > 0);
    }

    result.sort((a, b) => {
      if (sortBy === 'name') {
        return (a.name || '').localeCompare(b.name || '');
      }
      if (sortBy === 'drawings') {
        return b.drawCount - a.drawCount;
      }
      return new Date(b.lastActivity) - new Date(a.lastActivity);
    });

    return result;
  }, [enrichedProjects, searchQuery, sortBy, filterBy]);

  const handleRenameClick = (e, projectId, currentName) => {
    e.stopPropagation();
    const newName = window.prompt('Rename Project:', currentName);
    if (newName && newName.trim()) {
      onRenameProject(projectId, newName.trim());
    }
    setActiveMenuId(null);
  };

  const handleDeleteClick = (e, projectId, name) => {
    e.stopPropagation();
    const confirmed = window.confirm(`Are you sure you want to delete project "${name}"?`);
    if (confirmed) {
      onDeleteProject(projectId);
    }
    setActiveMenuId(null);
  };

  if (collapsed) {
    return (
      <aside className="w-full h-full flex flex-col items-center py-4 px-1 gap-4 select-none">
        <button
          type="button"
          onClick={onToggleCollapse}
          className="p-2 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md text-slate-500 hover:text-slate-700 dark:hover:text-slate-200"
          title="Expand Project Explorer"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onCreateProject}
          className="p-2 bg-sky-500 hover:bg-sky-600 text-white rounded-full transition-transform hover:scale-105"
          title="New Project"
          disabled={isLoading}
        >
          <Plus className="h-4 w-4" />
        </button>
        <div className="flex-1 w-full flex flex-col items-center gap-2 mt-4 overflow-y-auto pr-0.5">
          {filteredProjects.map((p) => {
            const active = p.id === activeProjectId;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => onSelectProject(p.id)}
                className={classNames(
                  'p-2.5 rounded-lg transition-all flex items-center justify-center relative group',
                  active 
                    ? 'bg-sky-100 text-sky-600 dark:bg-slate-800 dark:text-sky-400' 
                    : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'
                )}
                title={p.name}
              >
                <FolderGit2 className="h-4 w-4" />
              </button>
            );
          })}
        </div>
      </aside>
    );
  }

  return (
    <aside className="rag-rail h-full select-none" style={{ display: 'flex', flexDirection: 'column', width: '100%', padding: 0 }}>
      {/* Title Header */}
      <div className="h-12 px-3 border-b border-slate-100 dark:border-slate-855 bg-white/95 dark:bg-slate-900/95 flex items-center justify-between gap-2 shrink-0">
        <div>
          <span className="text-[10px] font-bold text-sky-500 uppercase tracking-widest font-mono block">Workspace</span>
          <h2 className="text-xs font-bold text-slate-855 dark:text-slate-100">Project Explorer</h2>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={onCreateProject}
            className="py-1.5 px-3 min-h-0 text-xs flex items-center gap-1 bg-sky-500 hover:bg-sky-600 text-white rounded-md font-bold shadow-sm transition-all"
            disabled={isLoading}
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New</span>
          </button>
          <button
            type="button"
            onClick={onToggleCollapse}
            className="p-1.5 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-850 rounded-md text-slate-400 hover:text-slate-655 transition-colors"
            title="Collapse Sidebar"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 p-3 overflow-hidden">
        {/* Search Input */}
        <div className="relative mb-3 shrink-0">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400 z-10" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-md text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500 transition-all placeholder-slate-400"
            style={{ paddingLeft: '2.25rem' }}
          />
        </div>

      {/* Filter and Sort options */}
      <div className="flex items-center justify-between text-[10px] border-b border-slate-100 dark:border-slate-850 pb-2 mb-3 text-slate-500 font-semibold">
        <div className="flex items-center gap-1">
          <Filter className="h-3 w-3" />
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value)}
            className="bg-transparent border-none text-slate-600 dark:text-slate-350 focus:outline-none cursor-pointer font-bold"
          >
            <option value="active">Active Projects</option>
            <option value="all">All Projects</option>
            <option value="has_cad">With Drawings</option>
          </select>
        </div>
        <div className="flex items-center gap-1">
          <ArrowUpDown className="h-3 w-3" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-transparent border-none text-slate-600 dark:text-slate-350 focus:outline-none cursor-pointer font-bold"
          >
            <option value="activity">Recent Activity</option>
            <option value="name">Name A-Z</option>
          </select>
        </div>
      </div>

      {/* Projects and Drawing list wrapper */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {isLoading && projects.length === 0 ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 animate-pulse bg-slate-50/50">
                <span className="block h-4 w-3/4 mb-2 bg-slate-200 dark:bg-slate-850 rounded" />
                <span className="block h-3 w-1/2 bg-slate-100 dark:bg-slate-900 rounded" />
              </div>
            ))}
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="text-center py-8">
            <FolderGit2 className="h-8 w-8 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
            <p className="text-xs text-slate-400">No engineering projects found</p>
          </div>
        ) : (
          filteredProjects.map((p) => {
            const active = p.id === activeProjectId;
            const menuOpen = activeMenuId === p.id;

            return (
              <div key={p.id} className="space-y-1">
                {/* Project Item */}
                <div
                  onClick={() => onSelectProject(p.id)}
                  className={classNames(
                    'group relative rounded-lg border p-2.5 transition-all cursor-pointer flex flex-col gap-1.5 shadow-sm',
                    active 
                      ? 'border-sky-500/50 bg-sky-50/10 dark:bg-sky-500/5 ring-1 ring-sky-500/25 shadow-xs' 
                      : 'border-slate-200 dark:border-slate-805 hover:border-slate-300 dark:hover:border-slate-750 hover:bg-slate-50 dark:hover:bg-slate-900/50'
                  )}
                >
                  <div className="flex items-start justify-between gap-1.5 min-w-0">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <FolderGit2 className={classNames('h-3.5 w-3.5 shrink-0', active ? 'text-sky-500' : 'text-slate-400')} />
                        <span className={classNames(
                          'truncate text-[0.82rem] font-bold block',
                          active ? 'text-sky-600 dark:text-sky-400' : 'text-slate-800 dark:text-slate-200'
                        )}>
                          {p.name || 'Untitled Project'}
                        </span>
                      </div>
                      <span className="text-[0.66rem] text-slate-400 font-mono block">
                        Updated {getRelativeTime(p.lastActivity)}
                      </span>
                    </div>

                    {/* Options Toggle */}
                    <div className="relative shrink-0" onClick={e => e.stopPropagation()}>
                      <button
                        type="button"
                        onClick={() => setActiveMenuId(menuOpen ? null : p.id)}
                        className="opacity-0 group-hover:opacity-100 focus:opacity-100 p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded transition-opacity"
                        title="Project options"
                      >
                        <ChevronDown className="h-3.5 w-3.5 text-slate-400 hover:text-slate-650 dark:hover:text-slate-200" />
                      </button>

                      {menuOpen && (
                        <div
                          ref={menuRef}
                          className="absolute right-0 mt-1 w-36 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-md shadow-lg py-1 z-50 text-xs font-bold"
                        >
                          <button
                            type="button"
                            onClick={(e) => handleRenameClick(e, p.id, p.name)}
                            className="w-full text-left px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900"
                          >
                            Rename Project
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              toast.success('Project duplication coming soon!');
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-3 py-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900 flex items-center gap-1.5"
                          >
                            <Copy className="h-3 w-3" /> Duplicate
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              toast.success('Project archiving coming soon!');
                              setActiveMenuId(null);
                            }}
                            className="w-full text-left px-3 py-1.5 text-slate-600 dark:text-slate-350 hover:bg-slate-100 dark:hover:bg-slate-900 flex items-center gap-1.5"
                          >
                            <Archive className="h-3 w-3" /> Archive
                          </button>
                          <div className="border-t border-slate-100 dark:border-slate-900 my-1" />
                          <button
                            type="button"
                            onClick={(e) => handleDeleteClick(e, p.id, p.name)}
                            className="w-full text-left px-3 py-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 flex items-center gap-1.5"
                          >
                            <Trash2 className="h-3 w-3" /> Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Project metadata pills */}
                  <div className="flex items-center gap-2.5 text-[9px] text-slate-400 font-mono mt-1 border-t border-slate-100 dark:border-slate-850/50 pt-1.5">
                    <span className="flex items-center gap-0.5">
                      <MessageSquare className="h-3 w-3 text-slate-350" />
                      {p.msgCount} msg
                    </span>
                    <span className="flex items-center gap-0.5">
                      <Layers className="h-3 w-3 text-slate-350" />
                      {p.drawCount} drawings
                    </span>
                  </div>
                </div>

                {/* Drawings / Versions subsection (only visible for active project) */}
                {active && drawingVersions.length > 0 && (
                  <div className="ml-4 pl-3.5 border-l border-slate-200 dark:border-slate-800 py-1.5 space-y-1">
                    <span className="text-[9px] uppercase font-bold tracking-wider text-slate-400 block mb-1">
                      Versions History ({drawingVersions.length})
                    </span>
                    {drawingVersions.map((v, vIdx) => {
                      const isSelected = v.fileToken === activeFileToken;
                      return (
                        <button
                          key={v.id}
                          type="button"
                          onClick={() => onSelectVersion(v.fileToken, v.dxfName)}
                          className={classNames(
                            'w-full text-left px-2 py-1.5 rounded text-[10px] font-mono flex items-center justify-between border transition-all truncate',
                            isSelected
                              ? 'bg-sky-50/50 dark:bg-sky-950/20 border-sky-500/40 text-sky-600 dark:text-sky-400 font-bold'
                              : 'bg-transparent border-transparent text-slate-500 dark:text-slate-450 hover:bg-slate-100/50 dark:hover:bg-slate-900/40 hover:text-slate-750 dark:hover:text-slate-200'
                          )}
                          title={`${v.dxfName} (${v.modelUsed})`}
                        >
                          <span className="truncate flex-1 pr-1">{v.dxfName}</span>
                          <span className="text-[8px] bg-slate-100 dark:bg-slate-800 text-slate-400 px-1 py-0.2 rounded shrink-0">
                            v{drawingVersions.length - vIdx}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
      </div>
    </aside>
  );
}

ProjectExplorerNext.propTypes = {
  projects: PropTypes.arrayOf(PropTypes.object).isRequired,
  activeProjectId: PropTypes.string,
  onSelectProject: PropTypes.func.isRequired,
  onCreateProject: PropTypes.func.isRequired,
  onRenameProject: PropTypes.func.isRequired,
  onDeleteProject: PropTypes.func.isRequired,
  messages: PropTypes.arrayOf(PropTypes.object),
  activeFileToken: PropTypes.string,
  onSelectVersion: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
  collapsed: PropTypes.bool,
  onToggleCollapse: PropTypes.func
};
