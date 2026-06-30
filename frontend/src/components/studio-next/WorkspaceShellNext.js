import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Sidebar as SidebarIcon } from 'lucide-react';

export default function WorkspaceShellNext({
  leftColumn,
  centerColumn,
  rightColumn,
  projectId
}) {
  const [leftWidth, setLeftWidth] = useState(() => {
    const saved = localStorage.getItem('studio_next_left_col_width');
    return saved ? parseInt(saved, 10) : 280;
  });
  
  const [rightWidth, setRightWidth] = useState(() => {
    const saved = localStorage.getItem('studio_next_right_col_width');
    return saved ? parseInt(saved, 10) : 400;
  });

  const [leftCollapsed, setLeftCollapsed] = useState(() => {
    return localStorage.getItem('studio_next_left_collapsed') === 'true';
  });

  const [rightCollapsed, setRightCollapsed] = useState(() => {
    return localStorage.getItem('studio_next_right_collapsed') === 'true';
  });

  const currentLeftWidth = useRef(leftWidth);
  const currentRightWidth = useRef(rightWidth);

  useEffect(() => {
    currentLeftWidth.current = leftWidth;
  }, [leftWidth]);

  useEffect(() => {
    currentRightWidth.current = rightWidth;
  }, [rightWidth]);

  const shellRef = useRef(null);
  const isResizingLeft = useRef(false);
  const isResizingRight = useRef(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    localStorage.setItem('studio_next_left_collapsed', String(leftCollapsed));
  }, [leftCollapsed]);

  useEffect(() => {
    localStorage.setItem('studio_next_right_collapsed', String(rightCollapsed));
  }, [rightCollapsed]);

  const handleMouseDownLeft = (e) => {
    e.preventDefault();
    isResizingLeft.current = true;
    setIsDragging(true);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  const handleMouseDownRight = (e) => {
    e.preventDefault();
    isResizingRight.current = true;
    setIsDragging(true);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  const handleMouseMove = (e) => {
    if (!shellRef.current) return;
    const containerRect = shellRef.current.getBoundingClientRect();

    if (isResizingLeft.current) {
      const newWidth = e.clientX - containerRect.left;
      // enforce min/max constraints
      const boundedWidth = Math.min(Math.max(180, newWidth), 400);
      currentLeftWidth.current = boundedWidth;
      shellRef.current.style.setProperty('--left-width', `${boundedWidth}px`);
    } else if (isResizingRight.current) {
      const newWidth = containerRect.right - e.clientX;
      const boundedWidth = Math.min(Math.max(280, newWidth), 600);
      currentRightWidth.current = boundedWidth;
      shellRef.current.style.setProperty('--right-width', `${boundedWidth}px`);
    }
  };

  const handleMouseUp = () => {
    if (isResizingLeft.current) {
      isResizingLeft.current = false;
      setLeftWidth(currentLeftWidth.current);
      localStorage.setItem('studio_next_left_col_width', String(currentLeftWidth.current));
    }
    if (isResizingRight.current) {
      isResizingRight.current = false;
      setRightWidth(currentRightWidth.current);
      localStorage.setItem('studio_next_right_col_width', String(currentRightWidth.current));
    }
    setIsDragging(false);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  };

  return (
    <div 
      ref={shellRef}
      className="flex-1 min-h-0 w-full flex overflow-hidden relative"
      style={{ 
        height: 'calc(100vh - 72px)',
        '--left-width': `${leftWidth}px`,
        '--right-width': `${rightWidth}px`
      }}
    >
      {isDragging && (
        <div className="fixed inset-0 z-50 cursor-col-resize select-none pointer-events-auto bg-transparent" />
      )}
      {/* LEFT COLUMN: Project Explorer */}
      <div
        className={`flex flex-col border-r border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 backdrop-blur-md ${
          leftCollapsed ? 'w-[48px] min-w-[48px]' : ''
        }`}
        style={{
          width: leftCollapsed ? '48px' : 'var(--left-width)',
          minWidth: leftCollapsed ? '48px' : 'var(--left-width)',
          transition: isDragging ? 'none' : 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
      >
        {React.cloneElement(leftColumn, { 
          collapsed: leftCollapsed, 
          onToggleCollapse: () => setLeftCollapsed(!leftCollapsed) 
        })}
      </div>

      {/* LEFT SPLITTER */}
      {!leftCollapsed && (
        <div
          onMouseDown={handleMouseDownLeft}
          className="w-1.5 h-full cursor-col-resize hover:bg-sky-500/50 active:bg-sky-500 transition-colors z-20 shrink-0 select-none"
        />
      )}

      {/* CENTER COLUMN: Activity Feed */}
      <div className="flex-1 min-w-0 flex flex-col bg-slate-50/50 dark:bg-slate-950/20">
        {centerColumn}
      </div>

      {/* RIGHT SPLITTER */}
      {!rightCollapsed && (
        <div
          onMouseDown={handleMouseDownRight}
          className="w-1.5 h-full cursor-col-resize hover:bg-sky-500/50 active:bg-sky-500 transition-colors z-20 shrink-0 select-none"
        />
      )}

      {/* RIGHT COLUMN: Engineering Viewport + Inspector */}
      <div
        className={`flex flex-col border-l border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 backdrop-blur-md ${
          rightCollapsed ? 'w-[48px] min-w-[48px] items-center py-4' : ''
        }`}
        style={{
          width: rightCollapsed ? '48px' : 'var(--right-width)',
          minWidth: rightCollapsed ? '48px' : 'var(--right-width)',
          transition: isDragging ? 'none' : 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
      >
        {rightCollapsed ? (
          <button
            onClick={() => setRightCollapsed(false)}
            className="p-2 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md text-slate-500 hover:text-slate-700 dark:hover:text-slate-200"
            title="Expand Inspector Workspace"
          >
            <SidebarIcon className="h-4 w-4" />
          </button>
        ) : (
          React.cloneElement(rightColumn, { 
            onCollapse: () => setRightCollapsed(true) 
          })
        )}
      </div>
    </div>
  );
}

WorkspaceShellNext.propTypes = {
  leftColumn: PropTypes.element.isRequired,
  centerColumn: PropTypes.element.isRequired,
  rightColumn: PropTypes.element.isRequired,
  projectId: PropTypes.string
};
