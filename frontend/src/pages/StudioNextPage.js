import React, { useState, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import Navbar from '../components/layout/Navbar';
import WorkspaceShellNext from '../components/studio-next/WorkspaceShellNext';
import ProjectExplorerNext from '../components/studio-next/ProjectExplorerNext';
import EngineeringViewportNext from '../components/studio-next/EngineeringViewportNext';
import ActivityFeedNext from '../components/studio-next/ActivityFeedNext';
import InspectorTabsNext from '../components/studio-next/InspectorTabsNext';
import cadArenaAPI from '../services/api';
import toast from 'react-hot-toast';
import { Loader2 } from 'lucide-react';

function RightPanel({
  activeFileToken,
  activeFileName,
  activeMessage,
  layers,
  handleToggleLayer,
  inspectorTab,
  handleSelectTab,
  onCollapse
}) {
  return (
    <div className="h-full flex flex-col min-h-0 bg-white dark:bg-slate-900 w-full">
      {/* Viewport upper container */}
      <div className="flex-1 flex flex-col min-h-0 border-b border-slate-200 dark:border-slate-800">
        <EngineeringViewportNext
          fileToken={activeFileToken}
          fileName={activeFileName}
          onImgLoadComplete={() => {}}
          onCollapse={onCollapse}
          layers={layers}
        />
      </div>
      {/* Inspector bottom container */}
      <div className="h-[280px] border-t border-slate-200 dark:border-slate-800 flex flex-col min-h-[200px]">
        <InspectorTabsNext
          activeMessage={activeMessage}
          layers={layers}
          onToggleLayer={handleToggleLayer}
          activeTab={inspectorTab}
          onChangeTab={handleSelectTab}
        />
      </div>
    </div>
  );
}

RightPanel.propTypes = {
  activeFileToken: PropTypes.string,
  activeFileName: PropTypes.string,
  activeMessage: PropTypes.object,
  layers: PropTypes.arrayOf(PropTypes.object),
  handleToggleLayer: PropTypes.func.isRequired,
  inspectorTab: PropTypes.string,
  handleSelectTab: PropTypes.func.isRequired,
  onCollapse: PropTypes.func
};

export default function StudioNextPage() {
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(() => {
    return localStorage.getItem('studio_next_active_project_id') || null;
  });
  const [messages, setMessages] = useState([]);
  const [activeFileToken, setActiveFileToken] = useState(null);
  const [activeFileName, setActiveFileName] = useState('');
  
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  
  const [modelsCatalog, setModelsCatalog] = useState([]);
  const [defaultModel, setDefaultModel] = useState('qwen_cloud');
  const [isGenerating, setIsGenerating] = useState(false);
  const [activePromptParams, setActivePromptParams] = useState(null);

  const [layers, setLayers] = useState([]);
  const [inspectorTab, setInspectorTab] = useState('properties');
  const [refinementMsgId, setRefinementMsgId] = useState(null);

  // Derive active message from active file token
  const activeMessage = useMemo(() => {
    if (!activeFileToken || !messages) return null;
    return messages.find(m => m.file_token === activeFileToken) || null;
  }, [activeFileToken, messages]);

  // Derive refinement label for the composer badge
  const refinementLabel = useMemo(() => {
    if (!refinementMsgId || !messages) return null;
    const records = messages.filter(m => m.role === 'assistant' || m.role === 'error');
    const idx = records.findIndex(m => m.id === refinementMsgId);
    return idx !== -1 ? `Iteration #${idx + 1}` : 'Selected Layout';
  }, [refinementMsgId, messages]);

  // Initialize layers when active message/drawing updates
  useEffect(() => {
    if (!activeMessage || !activeMessage.data) {
      setLayers([]);
      return;
    }
    const data = activeMessage.data;
    const defaultLayers = [
      { name: 'WALLS', visible: data.walls && data.walls.length > 0 },
      { name: 'DOORS', visible: data.openings && data.openings.some(o => o.type === 'door') },
      { name: 'WINDOWS', visible: data.openings && data.openings.some(o => o.type === 'window') },
      { name: 'ROOM_LABELS', visible: data.rooms && data.rooms.length > 0 },
      { name: 'FURNITURE_BEDROOM', visible: data.rooms && data.rooms.some(r => r.room_type === 'bedroom' || r.room_type === 'master_bedroom') },
      { name: 'FURNITURE_LIVING', visible: data.rooms && data.rooms.some(r => r.room_type === 'living' || r.room_type === 'living_room' || r.room_type === 'lounge') },
      { name: 'FURNITURE_KITCHEN', visible: data.rooms && data.rooms.some(r => r.room_type === 'kitchen') },
      { name: 'FURNITURE_SANITARY', visible: data.rooms && data.rooms.some(r => r.room_type === 'bathroom') },
      { name: 'BORDER', visible: true }
    ].filter(l => l.visible || l.name === 'BORDER' || l.name === 'ROOM_LABELS');
    setLayers(defaultLayers);
  }, [activeMessage]);

  const handleToggleLayer = (layerName) => {
    setLayers(prev => prev.map(l => l.name === layerName ? { ...l, visible: !l.visible } : l));
  };

  // 1. Fetch Projects List
  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const data = await cadArenaAPI.listWorkspaceMeProjects();
      const projectList = data.projects || [];
      setProjects(projectList);
      
      // Auto-select project if not empty
      if (projectList.length > 0) {
        if (!activeProjectId || !projectList.some(p => p.id === activeProjectId)) {
          const defaultId = projectList[0].id;
          setActiveProjectId(defaultId);
          localStorage.setItem('studio_next_active_project_id', defaultId);
        }
      } else {
        setActiveProjectId(null);
        localStorage.removeItem('studio_next_active_project_id');
      }
    } catch (err) {
      toast.error('Failed to load projects: ' + err.message);
    } finally {
      setProjectsLoading(false);
    }
  }, [activeProjectId]);

  const fetchModels = useCallback(async () => {
    try {
      const data = await cadArenaAPI.getParseDesignModels();
      if (data && data.models) {
        setModelsCatalog(data.models);
        setDefaultModel(data.default_model || 'qwen_cloud');
      }
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn('Failed to load models catalog: ', err);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
    fetchModels();
  }, [fetchProjects, fetchModels]);

  // 2. Fetch Messages/Activity history for active project
  const fetchMessages = useCallback(async (projectId, forceLatest = false) => {
    if (!projectId) return;
    setMessagesLoading(true);
    try {
      const data = await cadArenaAPI.getWorkspaceMeMessages(projectId);
      const msgList = data.messages || [];
      setMessages(msgList);

      // Check if project has a saved viewport token
      const savedToken = localStorage.getItem(`studio_next_${projectId}_active_file_token`);
      const savedName = localStorage.getItem(`studio_next_${projectId}_active_file_name`);

      // Find latest message with file token to display as active viewport version
      const dxfMessages = msgList.filter(m => m.role === 'assistant' && m.file_token);
      
      if (!forceLatest && savedToken && dxfMessages.some(m => m.file_token === savedToken)) {
        setActiveFileToken(savedToken);
        setActiveFileName(savedName || 'design.dxf');
      } else if (dxfMessages.length > 0) {
        // Select latest version
        const latest = dxfMessages[dxfMessages.length - 1];
        setActiveFileToken(latest.file_token);
        setActiveFileName(latest.dxf_name || 'design.dxf');
        localStorage.setItem(`studio_next_${projectId}_active_file_token`, latest.file_token);
        localStorage.setItem(`studio_next_${projectId}_active_file_name`, latest.dxf_name || 'design.dxf');
      } else {
        setActiveFileToken(null);
        setActiveFileName('');
      }
    } catch (err) {
      toast.error('Failed to load activity feed: ' + err.message);
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeProjectId) {
      fetchMessages(activeProjectId);
    }
  }, [activeProjectId, fetchMessages]);

  // Sidebar project CRUD callbacks
  const handleSelectProject = (projectId) => {
    setActiveProjectId(projectId);
    localStorage.setItem('studio_next_active_project_id', projectId);
    
    // Restore project-scoped tab
    const savedTab = localStorage.getItem(`studio_next_${projectId}_active_tab`);
    setInspectorTab(savedTab || 'properties');
    
    setRefinementMsgId(null);
  };

  const handleCreateProject = async () => {
    try {
      const name = `Project #${projects.length + 1}`;
      const newProj = await cadArenaAPI.createWorkspaceMeProject(name);
      setProjects(prev => [newProj, ...prev]);
      setActiveProjectId(newProj.id);
      localStorage.setItem('studio_next_active_project_id', newProj.id);
      setRefinementMsgId(null);
      toast.success('Project created successfully');
    } catch (err) {
      toast.error('Could not create project: ' + err.message);
    }
  };

  const handleRenameProject = async (projectId, newName) => {
    try {
      const updated = await cadArenaAPI.renameWorkspaceMeProject(projectId, newName);
      setProjects(prev => prev.map(p => p.id === projectId ? { ...p, name: updated.name } : p));
      toast.success('Project renamed');
    } catch (err) {
      toast.error('Could not rename project: ' + err.message);
    }
  };

  const handleDeleteProject = async (projectId) => {
    try {
      await cadArenaAPI.deleteWorkspaceMeProject(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
      toast.success('Project deleted');
      
      // Select another project
      if (activeProjectId === projectId) {
        const remaining = projects.filter(p => p.id !== projectId);
        if (remaining.length > 0) {
          setActiveProjectId(remaining[0].id);
          localStorage.setItem('studio_next_active_project_id', remaining[0].id);
        } else {
          setActiveProjectId(null);
          localStorage.removeItem('studio_next_active_project_id');
        }
      }
    } catch (err) {
      toast.error('Could not delete project: ' + err.message);
    }
  };

  const handleSelectVersion = (token, name) => {
    setActiveFileToken(token);
    setActiveFileName(name);
    if (activeProjectId) {
      localStorage.setItem(`studio_next_${activeProjectId}_active_file_token`, token);
      localStorage.setItem(`studio_next_${activeProjectId}_active_file_name`, name);
    }
    toast.success('Drawing version loaded');
  };

  const handleSelectTab = (tab) => {
    setInspectorTab(tab);
    if (activeProjectId) {
      localStorage.setItem(`studio_next_${activeProjectId}_active_tab`, tab);
    }
  };

  // Generation & Iteration callbacks
  const handleSendPrompt = async ({ prompt, model, recoveryMode }) => {
    if (!activeProjectId) return;
    setIsGenerating(true);
    setActivePromptParams({ prompt, model, recoveryMode });
    
    // Add user message locally so it displays in feed immediately
    const userMsg = {
      id: `usr_${Date.now()}`,
      role: 'user',
      text: prompt,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      let response;
      if (refinementMsgId) {
        // Find refinement context layout structure
        const sourceMessage = messages.find(m => m.id === refinementMsgId);
        const currentLayout = sourceMessage?.data || null;
        
        const payload = {
          prompt,
          current_layout: currentLayout,
          model,
          recovery_mode: recoveryMode,
          selection_offset: 0
        };
        response = await cadArenaAPI.iterateWorkspaceMeDxf(activeProjectId, payload);
      } else {
        const payload = {
          prompt,
          model,
          recovery_mode: recoveryMode,
          model_id: model
        };
        response = await cadArenaAPI.generateWorkspaceMeDxf(activeProjectId, payload);
      }
      
      // Toast and update active viewport token
      if (response && response.type === 'chat') {
        toast.success('Message sent successfully');
        setRefinementMsgId(null);
        await fetchMessages(activeProjectId);
      } else if (response && response.file_token) {
        toast.success('DXF layout generated successfully');
        setRefinementMsgId(null);
        // Fetch new messages list from backend to get the real structured assistant message record
        await fetchMessages(activeProjectId, true);
      } else {
        throw new Error('No file token returned from generation');
      }
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error(err);
      
      // Append an error record to messages list locally so it displays on timeline
      const errDetail = err.response?.data?.detail;
      const errorMsg = {
        id: `err_${Date.now()}`,
        role: 'error',
        text: typeof errDetail === 'string' ? errDetail : (errDetail?.message || err.message || 'Geometry generation failed'),
        model_used: model,
        error_details: {
          code: errDetail?.code || 'GENERATE_DXF_FAILED',
          message: typeof errDetail === 'string' ? errDetail : (errDetail?.message || err.message || 'Constraint solver failed'),
          violated_rule: errDetail?.violated_rule || null,
          room: errDetail?.room || null,
          details: errDetail?.details || []
        },
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
      toast.error('Generation failed: ' + (typeof errDetail === 'string' ? errDetail : (errDetail?.message || err.message)));
    } finally {
      setIsGenerating(false);
      setActivePromptParams(null);
    }
  };

  return (
    <div className="platform-fullscreen-page flex flex-col h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100">
      <Navbar />
      
      <WorkspaceShellNext
        projectId={activeProjectId}
        leftColumn={
          <ProjectExplorerNext
            projects={projects}
            activeProjectId={activeProjectId}
            onSelectProject={handleSelectProject}
            onCreateProject={handleCreateProject}
            onRenameProject={handleRenameProject}
            onDeleteProject={handleDeleteProject}
            messages={messages}
            activeFileToken={activeFileToken}
            onSelectVersion={handleSelectVersion}
            isLoading={projectsLoading}
          />
        }
        centerColumn={
          messagesLoading ? (
            <div className="flex-1 flex flex-col items-center justify-center bg-slate-50/50 dark:bg-slate-950/20">
              <Loader2 className="h-7 w-7 text-sky-500 animate-spin mb-2" />
              <p className="text-[10px] text-slate-400 font-mono">Syncing project records...</p>
            </div>
          ) : (
            <ActivityFeedNext
              messages={messages}
              activeFileToken={activeFileToken}
              onSelectVersion={handleSelectVersion}
              onSendPrompt={handleSendPrompt}
              onRefine={(msgId) => {
                setRefinementMsgId(msgId);
                toast.success('Ready to refine selected layout iteration');
              }}
              isGenerating={isGenerating}
              activePromptParams={activePromptParams}
              modelsCatalog={modelsCatalog}
              defaultModel={defaultModel}
              projectName={projects.find(p => p.id === activeProjectId)?.name || ''}
              refinementLabel={refinementLabel}
              onClearRefine={() => setRefinementMsgId(null)}
            />
          )
        }
        rightColumn={
          <RightPanel
            activeFileToken={activeFileToken}
            activeFileName={activeFileName}
            activeMessage={activeMessage}
            layers={layers}
            handleToggleLayer={handleToggleLayer}
            inspectorTab={inspectorTab}
            handleSelectTab={handleSelectTab}
          />
        }
      />
    </div>
  );
}
