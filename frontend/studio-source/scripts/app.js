const projectList = document.getElementById("project-list");
const projectCreateForm = document.getElementById("project-create-form");
const projectNameInput = document.getElementById("project-name-input");
const projectCreateButton = document.getElementById("project-create-btn");
const projectCountPill = document.getElementById("project-count-pill");
const userIdPill = document.getElementById("user-id-pill");
const profileSettingsSection = document.getElementById("profile-settings");
const profileForm = document.getElementById("profile-form");
const profileDisplayNameInput = document.getElementById("profile-display-name-input");
const profileHeadlineInput = document.getElementById("profile-headline-input");
const profileCompanyInput = document.getElementById("profile-company-input");
const profileWebsiteInput = document.getElementById("profile-website-input");
const profileTimezoneInput = document.getElementById("profile-timezone-input");
const profileSaveButton = document.getElementById("profile-save-btn");
const profileFeedback = document.getElementById("profile-feedback");
const profileEmailPill = document.getElementById("profile-email-pill");
const providerKeyList = document.getElementById("provider-key-list");

const chatThread = document.getElementById("chat-thread");
const chatScrollBottomButton = document.getElementById("chat-scroll-bottom-btn");
const chatForm = document.getElementById("chat-form");
const chatPanel = document.querySelector(".chat");
const promptInput = document.getElementById("prompt-input");
const modelSelect = document.getElementById("model-select");
const modelPicker = document.getElementById("model-picker");
const modelPickerTrigger = document.getElementById("model-picker-trigger");
const modelPickerMenu = document.getElementById("model-picker-menu");
const modelPickerOptions = document.getElementById("model-picker-options");
const modelHint = document.getElementById("model-hint");
const iterativeModeIndicator = document.getElementById("iterative-mode-indicator");
const sendButton = document.getElementById("send-btn");
const activeProjectTitle = document.getElementById("active-project-title");
const chatSubtitle = document.getElementById("chat-subtitle");
const statusBadge = document.getElementById("status-badge");

const previewCanvas = document.getElementById("preview-canvas");
const previewImage = document.getElementById("preview-image");
const previewEmpty = document.getElementById("preview-empty");
const previewFilename = document.getElementById("preview-filename");
const previewSource = document.getElementById("preview-source");
const previewRefreshButton = document.getElementById("preview-refresh-btn");
const previewDownloadPngButton = document.getElementById("preview-download-png-btn");
const previewDownloadPdfButton = document.getElementById("preview-download-pdf-btn");
const previewZoomInButton = document.getElementById("preview-zoom-in-btn");
const previewZoomOutButton = document.getElementById("preview-zoom-out-btn");
const previewZoomResetButton = document.getElementById("preview-zoom-reset-btn");
const dxfRenderPanel = document.getElementById("dxf-render-panel");
const dxfRenderCanvas = document.getElementById("dxf-render-canvas");
const dxfRenderImage = document.getElementById("dxf-render-image");
const dxfRenderEmpty = document.getElementById("dxf-render-empty");
const dxfRenderRefreshButton = document.getElementById("dxf-render-refresh-btn");
const dxfRenderDownloadPngButton = document.getElementById("dxf-render-download-png-btn");
const dxfRenderDownloadPdfButton = document.getElementById("dxf-render-download-pdf-btn");
const dxfRenderZoomInButton = document.getElementById("dxf-render-zoom-in-btn");
const dxfRenderZoomOutButton = document.getElementById("dxf-render-zoom-out-btn");
const dxfRenderZoomResetButton = document.getElementById("dxf-render-zoom-reset-btn");
const panelNodes = Array.from(document.querySelectorAll(".panel"));
const workspaceShell = document.getElementById("workspace-shell");
const workspaceLeftResizer = document.getElementById("workspace-resizer-left");
const workspaceRightResizer = document.getElementById("workspace-resizer-right");

const authGate = document.getElementById("auth-gate");
const topbarUserLabel = document.getElementById("topbar-user-label");
const topbarUserName = document.getElementById("topbar-user-name");
const topbarUserAvatar = document.getElementById("topbar-user-avatar");
const themeToggleButton = document.getElementById("theme-toggle-btn");
const togglePreviewButton = document.getElementById("toggle-preview-btn");
const topbarAuthButton = document.getElementById("topbar-auth-btn");
const topbarLogoutButton = document.getElementById("topbar-logout-btn");
const authLoginTab = document.getElementById("auth-login-tab");
const authRegisterTab = document.getElementById("auth-register-tab");
const authLoginForm = document.getElementById("auth-login-form");
const authRegisterForm = document.getElementById("auth-register-form");
const authLoginButton = document.getElementById("auth-login-btn");
const authRegisterButton = document.getElementById("auth-register-btn");
const loginEmailInput = document.getElementById("login-email-input");
const loginPasswordInput = document.getElementById("login-password-input");
const registerNameInput = document.getElementById("register-name-input");
const registerEmailInput = document.getElementById("register-email-input");
const registerPasswordInput = document.getElementById("register-password-input");
const authFeedback = document.getElementById("auth-feedback");
const googleAuthContainer = document.getElementById("google-auth-container");
const googleAuthButton = document.getElementById("google-auth-button");
const sidebarChatTabButton = document.getElementById("sidebar-chat-tab-btn");
const sidebarProjectsTabButton = document.getElementById("sidebar-projects-tab-btn");
const sidebarDxfUploadTriggerButton = document.getElementById("sidebar-dxf-upload-trigger-btn");
const sidebarChatSearchInput = document.getElementById("sidebar-chat-search-input");
const sidebarChatPanel = document.getElementById("sidebar-chat-panel");
const sidebarProjectsPanel = document.getElementById("sidebar-projects-panel");
const sidebarFocusChatButton = document.getElementById("sidebar-focus-chat-btn");
const sidebarManageProjectsButton = document.getElementById("sidebar-manage-projects-btn");
const sidebarQuickHideButton = document.getElementById("sidebar-quick-hide-btn");
const authTabFromQuery = new URLSearchParams(window.location.search).get("auth");
const explicitAuthTab = authTabFromQuery === "register" || authTabFromQuery === "login" ? authTabFromQuery : null;

const USER_STORAGE_KEY = "cadarena_workspace_user_id";
const THEME_STORAGE_KEY = "cadarena_theme";
const AUTH_VISITED_STORAGE_KEY = "cadarena_auth_visited";
const AUTH_KNOWN_ACCOUNT_STORAGE_KEY = "cadarena_has_registered_account";
const WORKSPACE_LAYOUT_STORAGE_KEY = "cadarena_workspace_layout_v1";
const PROJECT_LAYOUTS_STORAGE_KEY_PREFIX = "cadarena_project_layouts_v1"; // LAYOUT-FIX: namespace persisted per-project layouts by workspace identity
const AUTH_UI_ENABLED = false;
const DEFAULT_PROFILE_AVATAR = "/static/assets/cadarena-mark.svg";
const WORKSPACE_TOGGLE_ANIMATION_MS = 220;
const WHEEL_ZOOM_HINT = "Use Ctrl/Cmd + mouse wheel to zoom";
const DXF_RENDER_EMPTY_MESSAGE = "Generate a DXF from chat to render it here.";

const state = {
  userId: getOrCreateUserId(),
  activeProjectId: null,
  currentLayout: null, // LAYOUT-FIX: active layout pointer for the selected project
  projectLayouts: {}, // LAYOUT-FIX: per-project layout store keyed by project id
  sidebarTab: "chat",
  projectSearchQuery: "",
  projects: [],
  busy: false,
  modelLoading: false,
  messageCount: 0,
  serverMessageCount: 0,
  lastPreviewFileToken: null,
  previewScale: 1,
  previewPanX: 0,
  previewPanY: 0,
  previewBaseWidth: 0,
  previewBaseHeight: 0,
  previewPollTimer: null,
  previewPollInFlight: false,
  typingIndicator: null,
  workspaceMode: "studio",
  workspaceLayout: {
    sidebarWidth: 292,
    previewWidth: 512,
    sidebarCollapsed: false,
    previewHidden: false,
  },
  dxfRenderScale: 1,
  dxfRenderPanX: 0,
  dxfRenderPanY: 0,
  dxfRenderBaseWidth: 0,
  dxfRenderBaseHeight: 0,
  dxfRenderFileToken: null,
  dxfRenderFileName: null,
  dxfRenderSource: null,
  dxfRenderProjectId: null,
  latestProjectDxfToken: null,
  authMode: "unknown",
  authUser: null,
  profile: null,
};

const fallbackModelCatalog = {
  default_model: "huggingface",
  models: [
    {
      request_value: "ollama_cloud::qwen3.5:397b-cloud",
      provider: "ollama_cloud",
      model_id: "qwen3.5:397b-cloud",
      display_name: "Ollama Cloud (qwen3.5:397b-cloud)",
    },
    {
      request_value: "ollama_cloud::gemma3:27b-cloud",
      provider: "ollama_cloud",
      model_id: "gemma3:27b-cloud",
      display_name: "Ollama Cloud (gemma3:27b-cloud)",
    },
    {
      request_value: "ollama_cloud::minimax-m2.7:cloud",
      provider: "ollama_cloud",
      model_id: "minimax-m2.7:cloud",
      display_name: "Ollama Cloud (minimax-m2.7:cloud)",
    },
    {
      request_value: "ollama_cloud::qwen3-coder-next:cloud",
      provider: "ollama_cloud",
      model_id: "qwen3-coder-next:cloud",
      display_name: "Ollama Cloud (qwen3-coder-next:cloud)",
    },
    {
      request_value: "ollama::qwen2.5:7b-instruct",
      provider: "ollama",
      model_id: "qwen2.5:7b-instruct",
      display_name: "Ollama Local (qwen2.5:7b-instruct)",
    },
    {
      request_value: "ollama",
      provider: "ollama",
      model_id: "llama3.1:8b",
      display_name: "Ollama Local (llama3.1:8b)",
    },
    {
      request_value: "huggingface",
      provider: "huggingface",
      model_id: "LiquidAI/LFM2-1.2B-Extract",
      display_name: "HuggingFace Local (LiquidAI/LFM2-1.2B-Extract)",
    },
  ],
};

let googleClientId = "";
let workspaceToggleAnimationTimer = null;
let activeCanvasPanSession = null;
let modelMenuOpen = false;

if (previewCanvas) {
  previewCanvas.title = WHEEL_ZOOM_HINT;
}

if (dxfRenderCanvas) {
  dxfRenderCanvas.title = WHEEL_ZOOM_HINT;
}

function getOrCreateUserId() {
  const existing = localStorage.getItem(USER_STORAGE_KEY);
  if (existing && existing.trim()) {
    return existing.trim();
  }
  const fallback = `user_${Math.random().toString(16).slice(2, 10)}_${Date.now()}`;
  const generated =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : fallback;
  localStorage.setItem(USER_STORAGE_KEY, generated);
  return generated;
}

function projectLayoutsStorageKey() {
  const identityId = state.authUser?.id || state.userId; // LAYOUT-FIX: scope persisted layouts to the signed-in user or guest identity
  const identityScope = state.authUser?.id ? "user" : "guest"; // LAYOUT-FIX: prevent guest and authenticated sessions from sharing the same storage bucket
  return `${PROJECT_LAYOUTS_STORAGE_KEY_PREFIX}:${identityScope}:${identityId}`; // LAYOUT-FIX: build a stable localStorage key for the current workspace identity
}

function readStoredProjectLayouts() {
  try {
    const raw = localStorage.getItem(projectLayoutsStorageKey()); // LAYOUT-FIX: read the current identity's persisted project layouts
    if (!raw) {
      return {}; // LAYOUT-FIX: default to an empty project-layout map when nothing has been stored yet
    }
    const parsed = JSON.parse(raw); // LAYOUT-FIX: decode the persisted per-project layout map from localStorage
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {}; // LAYOUT-FIX: ignore malformed persisted layout payloads instead of breaking bootstrap
    }
    const normalizedLayouts = {}; // LAYOUT-FIX: rebuild only valid project-to-layout object entries
    for (const [projectId, layout] of Object.entries(parsed)) {
      if (!projectId || !layout || typeof layout !== "object" || Array.isArray(layout)) {
        continue; // LAYOUT-FIX: skip invalid persisted entries so only real layout objects survive hydration
      }
      normalizedLayouts[projectId] = layout; // LAYOUT-FIX: keep valid persisted project layouts for runtime use
    }
    return normalizedLayouts; // LAYOUT-FIX: hydrate the in-memory project layout map from validated storage data
  } catch (_error) {
    return {}; // LAYOUT-FIX: treat storage read/parse failures as a cold start instead of surfacing UI errors
  }
}

function writeStoredProjectLayouts() {
  try {
    localStorage.setItem(projectLayoutsStorageKey(), JSON.stringify(state.projectLayouts)); // LAYOUT-FIX: persist the full per-project layout map for reload recovery
  } catch (_error) {
    // LAYOUT-FIX: best effort persistence only
  }
}

function readStoredFlag(key) {
  try {
    return localStorage.getItem(key) === "1";
  } catch (_error) {
    return false;
  }
}

function writeStoredFlag(key, enabled) {
  try {
    localStorage.setItem(key, enabled ? "1" : "0");
  } catch (_error) {
    // best effort persistence
  }
}

function markAuthVisited() {
  writeStoredFlag(AUTH_VISITED_STORAGE_KEY, true);
}

function markKnownAccount() {
  writeStoredFlag(AUTH_KNOWN_ACCOUNT_STORAGE_KEY, true);
  markAuthVisited();
}

function inferAuthTabFromHistory() {
  const visitedBefore = readStoredFlag(AUTH_VISITED_STORAGE_KEY);
  const hasKnownAccount = readStoredFlag(AUTH_KNOWN_ACCOUNT_STORAGE_KEY);
  if (!visitedBefore) {
    return "login";
  }
  return hasKnownAccount ? "login" : "register";
}

function resolvePreferredAuthTab() {
  return explicitAuthTab || inferAuthTabFromHistory();
}

let activeWorkspaceResizeSession = null;
// FIX 1: double-submit guard
let _loginPending = false;
let _registerPending = false;
let _projectCreatePending = false;
// FIX 6: RAF panel resize and spotlight updates
let _resizeRAF = null;
let _pendingResizeClientX = null;

/**
 * Toggle the inline iterative-mode indicator based on current layout availability.
 *
 * @returns {void}
 */
// LAYOUT-FIX: save layout for a specific project
function saveProjectLayout(projectId, layout) {
  if (!projectId || !layout) return;
  state.projectLayouts[projectId] = layout; // LAYOUT-FIX: persist layout by project id
  writeStoredProjectLayouts(); // LAYOUT-FIX: mirror the in-memory layout update into reload-safe browser storage
  if (projectId === state.activeProject || projectId === state.activeProjectId) { // LAYOUT-FIX: keep active pointer synced
    state.currentLayout = layout; // LAYOUT-FIX: currentLayout remains the active project pointer
  }
}

// LAYOUT-FIX: load layout for a specific project
function loadProjectLayout(projectId) {
  if (!projectId) return null;
  return state.projectLayouts[projectId] ?? null; // LAYOUT-FIX: missing projects naturally return null
}

// LAYOUT-FIX: clear layout for a specific project
function clearProjectLayout(projectId) {
  if (!projectId) return;
  delete state.projectLayouts[projectId]; // LAYOUT-FIX: remove only the targeted project's layout snapshot
  writeStoredProjectLayouts(); // LAYOUT-FIX: persist the layout removal so deleted or reset projects stay cleared after reload
  if (projectId === state.activeProject || projectId === state.activeProjectId) { // LAYOUT-FIX: clear active pointer only for active project
    state.currentLayout = null; // LAYOUT-FIX: active project no longer has an iterative base layout
  }
}

function updateIterativeModeIndicator() {
  if (!iterativeModeIndicator) {
    return;
  }
  const activeId = state.activeProject ?? state.activeProjectId; // LAYOUT-FIX: resolve the selected project before reading layout state
  const hasLayout = Boolean(loadProjectLayout(activeId)); // LAYOUT-FIX: indicator depends on project-specific layout availability
  iterativeModeIndicator.style.display = hasLayout ? "inline-flex" : "none"; // LAYOUT-FIX: show editing mode only when the active project has a saved layout
}

/**
 * Store the active layout snapshot and refresh the iterative-mode UI.
 *
 * @param {Object|null} layout
 * @returns {void}
 */
function setCurrentLayout(layout) {
  state.currentLayout = layout ?? null;
  updateIterativeModeIndicator();
}

/**
 * Persist the latest successful layout returned by either prompt endpoint.
 *
 * @param {Object} response
 * @param {"generate"|"iterate"} requestMode
 * @returns {void}
 */
function syncCurrentLayoutFromResponse(response, requestMode) {
  const activeId = state.activeProject ?? state.activeProjectId; // LAYOUT-FIX: resolve the active project before persisting any returned layout
  if (requestMode === "generate") { // LAYOUT-FIX: generate-dxf may return layout at the top level or inside legacy data wrappers
    const layout = response?.layout ?? response?.data?.layout ?? response?.data; // LAYOUT-FIX: accept top-level generate layouts while preserving legacy response support
    if (layout && typeof layout === "object" && layout.rooms) { // LAYOUT-FIX: only persist valid layout objects that can drive iterative mode
      saveProjectLayout(activeId, layout); // LAYOUT-FIX: save the generated layout for the active project
      updateIterativeModeIndicator(); // LAYOUT-FIX: refresh iterative-mode UI after a successful generate response
    }
  }
  if (requestMode === "iterate") { // LAYOUT-FIX: iterate responses already return layout at the top level
    const layout = response?.layout; // LAYOUT-FIX: read the iterated layout from the current response shape
    if (layout && typeof layout === "object" && layout.rooms) { // LAYOUT-FIX: ignore empty or malformed iterate payloads
      saveProjectLayout(activeId, layout); // LAYOUT-FIX: save the iterated layout for the active project
      updateIterativeModeIndicator(); // LAYOUT-FIX: refresh iterative-mode UI after a successful iterate response
    }
  }
}

function clamp(value, minimum, maximum) {
  if (!Number.isFinite(value)) {
    return minimum;
  }
  if (!Number.isFinite(maximum) || maximum < minimum) {
    return minimum;
  }
  return Math.min(maximum, Math.max(minimum, value));
}

function isDesktopWorkspaceLayout() {
  return window.matchMedia("(min-width: 1201px)").matches;
}

function keepWorkspaceViewportStable() {
  if (!isDesktopWorkspaceLayout()) {
    return;
  }
  if (typeof window.scrollTo === "function") {
    window.scrollTo(0, 0);
  }
  if (document.documentElement) {
    document.documentElement.scrollTop = 0;
    document.documentElement.scrollLeft = 0;
  }
  if (document.body) {
    document.body.scrollTop = 0;
    document.body.scrollLeft = 0;
  }
}

function readWorkspaceLayout() {
  try {
    const raw = localStorage.getItem(WORKSPACE_LAYOUT_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    return {
      sidebarWidth: Number(parsed.sidebarWidth),
      previewWidth: Number(parsed.previewWidth),
      sidebarCollapsed: Boolean(parsed.sidebarCollapsed ?? parsed.sidebarHidden),
      previewHidden: Boolean(parsed.previewHidden),
    };
  } catch (_error) {
    return null;
  }
}

function writeWorkspaceLayout() {
  try {
    localStorage.setItem(WORKSPACE_LAYOUT_STORAGE_KEY, JSON.stringify(state.workspaceLayout));
  } catch (_error) {
    // best effort persistence
  }
}

function updateLayoutToggleButtons() {
  if (togglePreviewButton) {
    const hidden = state.workspaceLayout.previewHidden;
    togglePreviewButton.classList.toggle("is-active", hidden);
    togglePreviewButton.setAttribute("aria-pressed", String(hidden));
    const label = hidden ? "Show DXF render" : "Hide DXF render";
    togglePreviewButton.setAttribute("aria-label", label);
    togglePreviewButton.title = label;
  }

  if (sidebarDxfUploadTriggerButton) {
    const renderActive = state.sidebarTab === "render";
    sidebarDxfUploadTriggerButton.classList.toggle("active", renderActive);
    sidebarDxfUploadTriggerButton.classList.remove("is-open");
    sidebarDxfUploadTriggerButton.setAttribute("aria-pressed", renderActive ? "true" : "false");
    sidebarDxfUploadTriggerButton.setAttribute("aria-current", renderActive ? "true" : "false");
  }

  if (sidebarQuickHideButton) {
    const collapsed = state.workspaceLayout.sidebarCollapsed;
    const label = collapsed ? "Expand sidebar" : "Collapse sidebar";
    sidebarQuickHideButton.setAttribute("aria-label", label);
    sidebarQuickHideButton.setAttribute("aria-pressed", String(collapsed));
    sidebarQuickHideButton.title = label;
    sidebarQuickHideButton.classList.toggle("is-active", collapsed);
  }
}

function applyWorkspaceLayout({ persist = true } = {}) {
  if (!workspaceShell) {
    return;
  }

  const layout = state.workspaceLayout;
  const workspaceWidth = Math.max(workspaceShell.clientWidth, 900);
  const minChatWidth = 420;
  const minSidebarWidth = 220;
  const collapsedSidebarWidth = 86;
  const minPreviewWidth = 320;
  const handleWidth = 12;

  if (isDesktopWorkspaceLayout()) {
    if (!layout.sidebarCollapsed) {
      const rightReserved = layout.previewHidden ? 0 : layout.previewWidth + handleWidth;
      const maxSidebar = workspaceWidth - rightReserved - minChatWidth - handleWidth;
      layout.sidebarWidth = clamp(layout.sidebarWidth, minSidebarWidth, maxSidebar);
    }

    if (!layout.previewHidden) {
      const visibleSidebarWidth = layout.sidebarCollapsed ? collapsedSidebarWidth : layout.sidebarWidth;
      const leftReserved = visibleSidebarWidth + (layout.sidebarCollapsed ? 0 : handleWidth);
      const maxPreview = workspaceWidth - leftReserved - minChatWidth - handleWidth;
      layout.previewWidth = clamp(layout.previewWidth, minPreviewWidth, maxPreview);
    }
  }

  const visibleSidebarWidth = layout.sidebarCollapsed ? collapsedSidebarWidth : layout.sidebarWidth;
  workspaceShell.style.setProperty("--sidebar-width", `${Math.round(visibleSidebarWidth)}px`);
  workspaceShell.style.setProperty("--preview-width", `${Math.round(layout.previewWidth)}px`);
  workspaceShell.classList.toggle("is-sidebar-collapsed", layout.sidebarCollapsed);
  workspaceShell.classList.toggle("is-preview-hidden", layout.previewHidden);

  updateLayoutToggleButtons();
  if (persist) {
    writeWorkspaceLayout();
  }
}

function beginWorkspaceResize(side, event) {
  if (!workspaceShell || !isDesktopWorkspaceLayout()) {
    return;
  }
  if (side === "left" && state.workspaceLayout.sidebarCollapsed) {
    return;
  }
  if (side === "right" && state.workspaceLayout.previewHidden) {
    return;
  }

  event.preventDefault();
  _pendingResizeClientX = event.clientX;
  activeWorkspaceResizeSession = {
    side,
    startX: event.clientX,
    sidebarWidth: state.workspaceLayout.sidebarWidth,
    previewWidth: state.workspaceLayout.previewWidth,
  };

  document.body.classList.add("is-resizing-workspace");
  workspaceShell.classList.add("is-dragging");
  if (workspaceLeftResizer) {
    workspaceLeftResizer.classList.toggle("is-active", side === "left");
  }
  if (workspaceRightResizer) {
    workspaceRightResizer.classList.toggle("is-active", side === "right");
  }

  window.addEventListener("pointermove", handleWorkspaceResizeDrag);
  window.addEventListener("pointerup", endWorkspaceResize);
  window.addEventListener("pointercancel", endWorkspaceResize);
}

function flushWorkspaceResizeDrag() {
  if (!activeWorkspaceResizeSession || _pendingResizeClientX === null) {
    return;
  }

  const deltaX = _pendingResizeClientX - activeWorkspaceResizeSession.startX;
  if (activeWorkspaceResizeSession.side === "left") {
    state.workspaceLayout.sidebarWidth = activeWorkspaceResizeSession.sidebarWidth + deltaX;
  } else {
    state.workspaceLayout.previewWidth = activeWorkspaceResizeSession.previewWidth - deltaX;
  }

  applyWorkspaceLayout({ persist: false });
}

function handleWorkspaceResizeDrag(event) {
  if (!activeWorkspaceResizeSession) {
    return;
  }
  _pendingResizeClientX = event.clientX;
  if (_resizeRAF) {
    return;
  }
  _resizeRAF = window.requestAnimationFrame(() => {
    flushWorkspaceResizeDrag();
    _resizeRAF = null;
  });
}

function endWorkspaceResize() {
  if (!activeWorkspaceResizeSession) {
    return;
  }

  if (_resizeRAF) {
    window.cancelAnimationFrame(_resizeRAF);
    _resizeRAF = null;
  }
  flushWorkspaceResizeDrag();
  _pendingResizeClientX = null;

  activeWorkspaceResizeSession = null;
  document.body.classList.remove("is-resizing-workspace");
  workspaceShell?.classList.remove("is-dragging");
  if (workspaceLeftResizer) {
    workspaceLeftResizer.classList.remove("is-active");
  }
  if (workspaceRightResizer) {
    workspaceRightResizer.classList.remove("is-active");
  }
  window.removeEventListener("pointermove", handleWorkspaceResizeDrag);
  window.removeEventListener("pointerup", endWorkspaceResize);
  window.removeEventListener("pointercancel", endWorkspaceResize);
  applyWorkspaceLayout({ persist: true });
}

function triggerWorkspaceToggleAnimation() {
  if (!workspaceShell || !isDesktopWorkspaceLayout()) {
    return;
  }
  workspaceShell.classList.add("is-layout-animating");
  if (workspaceToggleAnimationTimer) {
    window.clearTimeout(workspaceToggleAnimationTimer);
  }
  workspaceToggleAnimationTimer = window.setTimeout(() => {
    workspaceShell.classList.remove("is-layout-animating");
    workspaceToggleAnimationTimer = null;
  }, WORKSPACE_TOGGLE_ANIMATION_MS + 40);
}

function toggleSidebarVisibility() {
  triggerWorkspaceToggleAnimation();
  state.workspaceLayout.sidebarCollapsed = !state.workspaceLayout.sidebarCollapsed;
  applyWorkspaceLayout({ persist: true });
}

function togglePreviewVisibility() {
  triggerWorkspaceToggleAnimation();
  state.workspaceLayout.previewHidden = !state.workspaceLayout.previewHidden;
  applyWorkspaceLayout({ persist: true });
}

function revealDxfRenderPanel({ scrollIntoView = true } = {}) {
  if (state.workspaceLayout.previewHidden) {
    triggerWorkspaceToggleAnimation();
    state.workspaceLayout.previewHidden = false;
    applyWorkspaceLayout({ persist: true });
  }

  if (!dxfRenderPanel) {
    return;
  }

  if (!isDesktopWorkspaceLayout() && scrollIntoView && typeof dxfRenderPanel.scrollIntoView === "function") {
    dxfRenderPanel.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }
}

function initializeWorkspaceLayout() {
  const stored = readWorkspaceLayout();
  if (stored) {
    if (Number.isFinite(stored.sidebarWidth)) {
      state.workspaceLayout.sidebarWidth = stored.sidebarWidth;
    }
    if (Number.isFinite(stored.previewWidth)) {
      state.workspaceLayout.previewWidth = stored.previewWidth;
    }
    state.workspaceLayout.sidebarCollapsed = stored.sidebarCollapsed;
    state.workspaceLayout.previewHidden = stored.previewHidden;
  }

  applyWorkspaceLayout({ persist: false });
}

function currentTheme() {
  return "light";
}

function updateThemeToggleButton() {
  if (!themeToggleButton) {
    return;
  }
  themeToggleButton.hidden = true;
  const label = "Light mode";
  themeToggleButton.setAttribute("aria-label", label);
  themeToggleButton.title = label;
}

function setTheme() {
  const normalized = "light";
  document.documentElement.setAttribute("data-theme", normalized);
  try {
    localStorage.setItem(THEME_STORAGE_KEY, normalized);
  } catch (_error) {
    // best effort persistence
  }
  updateThemeToggleButton();
  renderGoogleAuthButton();
}

function toggleTheme() {
  setTheme();
}

function setStatus(text, tone = "ready") {
  statusBadge.textContent = text;
  statusBadge.classList.remove("ready", "pending", "error");
  statusBadge.classList.add(tone);
}

function setBusy(isBusy) {
  state.busy = isBusy;
  promptInput.disabled = isBusy;
  modelSelect.disabled = isBusy || state.modelLoading;
  if (modelPickerTrigger) {
    modelPickerTrigger.disabled = isBusy || state.modelLoading;
  }
  if (isBusy) {
    setModelMenuOpen(false);
  }
  sendButton.disabled = isBusy || !state.activeProjectId;
  projectNameInput.disabled = isBusy;
  projectCreateButton.disabled = isBusy;
}

function setModelLoading(isLoading) {
  state.modelLoading = isLoading;
  modelSelect.disabled = isLoading || state.busy;
  if (modelPickerTrigger) {
    modelPickerTrigger.disabled = isLoading || state.busy;
  }
  if (isLoading) {
    setModelMenuOpen(false);
  }
}

function setupPanelSpotlight() {
  if (!panelNodes.length) {
    return;
  }

  if (
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
    window.matchMedia("(pointer: coarse)").matches
  ) {
    return;
  }

  /* FIX 6: RAF panel resize and spotlight updates */
  for (const panel of panelNodes) {
    let spotlightRAF = null;
    let pendingClientX = 0;
    let pendingClientY = 0;
    panel.addEventListener(
      "pointermove",
      (event) => {
        pendingClientX = event.clientX;
        pendingClientY = event.clientY;
        if (spotlightRAF) {
          return;
        }
        spotlightRAF = window.requestAnimationFrame(() => {
          const bounds = panel.getBoundingClientRect();
          panel.style.setProperty("--spot-x", `${pendingClientX - bounds.left}px`);
          panel.style.setProperty("--spot-y", `${pendingClientY - bounds.top}px`);
          panel.classList.add("is-spotlit");
          spotlightRAF = null;
        });
      },
      { passive: true },
    );

    panel.addEventListener("pointerleave", () => {
      if (spotlightRAF) {
        window.cancelAnimationFrame(spotlightRAF);
        spotlightRAF = null;
      }
      panel.classList.remove("is-spotlit");
    });
  }
}

function messageStamp(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function shortUserId(value) {
  if (!value || value.length <= 16) {
    return value;
  }
  return `${value.slice(0, 8)}...${value.slice(-4)}`;
}

function isAuthenticatedMode() {
  return state.authMode === "user" && state.authUser;
}

/**
 * Reset in-memory workspace state before bootstrapping a fresh session.
 *
 * @returns {void}
 */
function resetWorkspaceState() {
  stopPreviewPolling();
  removeTypingIndicator();
  state.projects = [];
  state.activeProjectId = null;
  state.projectLayouts = {}; // LAYOUT-FIX: clear all project layouts on full workspace reset
  state.currentLayout = null; // LAYOUT-FIX: clear the active layout pointer on full workspace reset
  updateIterativeModeIndicator(); // LAYOUT-FIX: reflect that no active project layout remains after reset
  state.projectSearchQuery = "";
  state.sidebarTab = "chat";
  state.serverMessageCount = 0;
  state.messageCount = 0;
  if (sidebarChatSearchInput) {
    sidebarChatSearchInput.value = "";
  }
  projectList.innerHTML = "";
  projectCountPill.textContent = projectCountLabel(0);
  renderChatHistory([]);
  resetPreview();
  resetDxfRenderPreview();
  setWorkspaceMode("studio");
  setSidebarTab("chat");
}

function setAuthFeedback(message, tone = "info") {
  authFeedback.textContent = message || "";
  authFeedback.classList.toggle("error", tone === "error");
}

function setProfileFeedback(message, tone = "info") {
  if (!profileFeedback) {
    return;
  }
  profileFeedback.textContent = message || "";
  profileFeedback.classList.toggle("error", tone === "error");
}

function setAuthTab(mode) {
  const isLogin = mode === "login";
  authLoginTab.classList.toggle("active", isLogin);
  authRegisterTab.classList.toggle("active", !isLogin);
  authLoginTab.setAttribute("aria-selected", String(isLogin));
  authRegisterTab.setAttribute("aria-selected", String(!isLogin));
  authLoginForm.hidden = !isLogin;
  authRegisterForm.hidden = isLogin;
  if (!isLogin) {
    registerNameInput.value = "";
    registerEmailInput.value = "";
    registerPasswordInput.value = "";
  }
  setAuthFeedback("");
}

function setProfileSectionVisibility(visible) {
  if (!profileSettingsSection) {
    return;
  }
  profileSettingsSection.hidden = !visible;
}

function resetProfileState() {
  state.profile = null;
  if (profileForm) {
    profileForm.reset();
  }
  if (providerKeyList) {
    providerKeyList.innerHTML = "";
  }
  if (profileEmailPill) {
    profileEmailPill.textContent = "Account";
  }
  setProfileFeedback("");
  setProfileSectionVisibility(false);
}

function setWorkspaceLocked(locked) {
  workspaceShell.classList.toggle("is-locked", locked);
}

function setSidebarTab(tab) {
  const normalized = tab === "projects" || tab === "render" ? tab : "chat";
  state.sidebarTab = normalized;
  const chatActive = normalized === "chat";
  const projectsActive = normalized === "projects";
  const renderActive = normalized === "render";

  if (sidebarChatTabButton) {
    sidebarChatTabButton.classList.toggle("active", chatActive);
    sidebarChatTabButton.setAttribute("aria-current", chatActive ? "true" : "false");
  }
  if (sidebarProjectsTabButton) {
    sidebarProjectsTabButton.classList.toggle("active", projectsActive);
    sidebarProjectsTabButton.setAttribute("aria-current", projectsActive ? "true" : "false");
  }
  if (sidebarDxfUploadTriggerButton) {
    sidebarDxfUploadTriggerButton.classList.toggle("active", renderActive);
    sidebarDxfUploadTriggerButton.classList.remove("is-open");
    sidebarDxfUploadTriggerButton.setAttribute("aria-pressed", renderActive ? "true" : "false");
    sidebarDxfUploadTriggerButton.setAttribute("aria-current", renderActive ? "true" : "false");
  }
  if (sidebarChatPanel) {
    sidebarChatPanel.classList.toggle("is-muted", !chatActive);
  }
  if (sidebarProjectsPanel) {
    const shouldMuteProjectsPanel = chatActive && Boolean(sidebarChatPanel);
    sidebarProjectsPanel.classList.toggle("is-muted", shouldMuteProjectsPanel);
  }
}

function setWorkspaceMode(mode) {
  if (!workspaceShell) {
    return;
  }
  state.workspaceMode = "studio";
  workspaceShell.classList.remove("is-dxf-render-mode");

  if (togglePreviewButton) {
    togglePreviewButton.disabled = false;
    togglePreviewButton.setAttribute("aria-disabled", "false");
  }

  setSidebarTab(state.sidebarTab);
  keepWorkspaceViewportStable();
}

function buildAvatarUrl(profileRecord) {
  const raw = typeof profileRecord?.avatar_url === "string" ? profileRecord.avatar_url.trim() : "";
  if (!raw) {
    return DEFAULT_PROFILE_AVATAR;
  }
  const stamp = typeof profileRecord?.avatar_updated_at === "string" ? profileRecord.avatar_updated_at.trim() : "";
  if (!stamp) {
    return raw;
  }
  const separator = raw.includes("?") ? "&" : "?";
  return `${raw}${separator}v=${encodeURIComponent(stamp)}`;
}

function setTopbarIdentityLabel() {
  if (!topbarUserLabel) {
    return;
  }

  if (isAuthenticatedMode()) {
    const profileRecord = state.profile?.profile || null;
    const displayName = (profileRecord?.display_name || state.authUser.name || "").trim();
    if (topbarUserName) {
      topbarUserName.textContent = displayName || "My profile";
    } else {
      topbarUserLabel.textContent = displayName || "My profile";
    }
    if (topbarUserAvatar) {
      topbarUserAvatar.src = buildAvatarUrl(profileRecord);
    }
    topbarUserLabel.hidden = false;
    topbarUserLabel.removeAttribute("aria-disabled");
    return;
  }
  topbarUserLabel.hidden = true;
  if (topbarUserName) {
    topbarUserName.textContent = "Not signed in";
  } else {
    topbarUserLabel.textContent = "Not signed in";
  }
  if (topbarUserAvatar) {
    topbarUserAvatar.src = DEFAULT_PROFILE_AVATAR;
  }
  topbarUserLabel.setAttribute("aria-disabled", "true");
}

function setWorkspaceIdentityLabel() {
  if (!userIdPill) {
    return;
  }
  if (isAuthenticatedMode()) {
    userIdPill.textContent = shortUserId(state.authUser.id);
    return;
  }
  userIdPill.textContent = shortUserId(state.userId);
}

function showAuthGate(mode = null) {
  if (!AUTH_UI_ENABLED) {
    authGate.hidden = true;
    setWorkspaceLocked(false);
    topbarAuthButton.hidden = true;
    topbarLogoutButton.hidden = !isAuthenticatedMode();
    return;
  }

  authGate.hidden = false;
  setWorkspaceLocked(true);
  topbarAuthButton.hidden = true;
  topbarLogoutButton.hidden = true;
  setAuthTab(mode === "register" || mode === "login" ? mode : resolvePreferredAuthTab());
  markAuthVisited();
}

function showAuthCheckingState() {
  if (!AUTH_UI_ENABLED) {
    authGate.hidden = true;
    setWorkspaceLocked(false);
    topbarUserLabel.hidden = !isAuthenticatedMode();
    topbarAuthButton.hidden = true;
    topbarLogoutButton.hidden = !isAuthenticatedMode();
    return;
  }

  authGate.hidden = true;
  setWorkspaceLocked(true);
  topbarUserLabel.hidden = true;
  topbarAuthButton.hidden = true;
  topbarLogoutButton.hidden = true;
}

function hideAuthGate() {
  authGate.hidden = true;
  setWorkspaceLocked(false);
  const authenticated = isAuthenticatedMode();
  topbarUserLabel.hidden = !authenticated;
  topbarAuthButton.hidden = true;
  topbarLogoutButton.hidden = !authenticated;
}

function projectCountLabel(count) {
  return `${count} ${count === 1 ? "project" : "projects"}`;
}

function normalizedProjectSearchQuery() {
  return state.projectSearchQuery.trim().toLowerCase();
}

function getVisibleProjects() {
  const query = normalizedProjectSearchQuery();
  if (!query) {
    return state.projects;
  }
  return state.projects.filter((project) => {
    const name = String(project?.name || "").toLowerCase();
    const id = String(project?.id || "").toLowerCase();
    return name.includes(query) || id.includes(query);
  });
}

function suggestNextProjectName() {
  const baseName = "New Project";
  const existingNames = new Set(state.projects.map((project) => String(project?.name || "").toLowerCase()));
  if (!existingNames.has(baseName.toLowerCase())) {
    return baseName;
  }
  for (let index = 2; index < 1000; index += 1) {
    const candidate = `${baseName} ${index}`;
    if (!existingNames.has(candidate.toLowerCase())) {
      return candidate;
    }
  }
  return `${baseName} ${Date.now()}`;
}

function parseErrorMessage(status, payload) {
  if (payload && typeof payload === "object") {
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (payload.detail && typeof payload.detail.message === "string") {
      return payload.detail.message;
    }
    if (payload.error && typeof payload.error.message === "string") {
      return payload.error.message;
    }
    if (typeof payload.message === "string") {
      return payload.message;
    }
  }
  return `Request failed with status ${status}`;
}

function sanitizeExportBaseName(rawValue, fallback = "design_export") {
  const value = String(rawValue || "").trim();
  const leaf = value.split(/[/\\]/).pop() || "";
  const withoutExt = leaf.replace(/\.[^.]+$/, "");
  const normalized = withoutExt
    .replace(/[^a-zA-Z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 72);
  return normalized || fallback;
}

function buildDxfExportUrl(fileToken, format, filenameBase) {
  const normalizedFormat = format === "pdf" ? "pdf" : "image";
  const extension = normalizedFormat === "pdf" ? ".pdf" : ".png";
  const filename = `${sanitizeExportBaseName(filenameBase)}${extension}`;
  return (
    `/api/v1/dxf/export?file_token=${encodeURIComponent(fileToken)}` +
    `&format=${encodeURIComponent(normalizedFormat)}` +
    `&filename=${encodeURIComponent(filename)}`
  );
}

function triggerFileDownload(downloadUrl) {
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.rel = "noopener";
  link.style.display = "none";
  document.body.append(link);
  link.click();
  link.remove();
}

function setPreviewExportButtonsEnabled(enabled) {
  if (previewDownloadPngButton) {
    previewDownloadPngButton.disabled = !enabled;
  }
  if (previewDownloadPdfButton) {
    previewDownloadPdfButton.disabled = !enabled;
  }
}

function setDxfRenderExportButtonsEnabled(enabled) {
  if (dxfRenderDownloadPngButton) {
    dxfRenderDownloadPngButton.disabled = !enabled;
  }
  if (dxfRenderDownloadPdfButton) {
    dxfRenderDownloadPdfButton.disabled = !enabled;
  }
}

function previewExportBaseName() {
  const hintedName = previewFilename?.textContent && previewFilename.textContent !== "No file yet"
    ? previewFilename.textContent
    : activeProjectTitle?.textContent || "chat_design";
  return sanitizeExportBaseName(hintedName, "chat_design");
}

function dxfRenderExportBaseName() {
  const hintedName = state.dxfRenderFileName || "dxf_render";
  return sanitizeExportBaseName(hintedName, "dxf_render");
}

function downloadDxfExport(fileToken, format, filenameBase) {
  if (!fileToken) {
    return;
  }
  const downloadUrl = buildDxfExportUrl(fileToken, format, filenameBase);
  triggerFileDownload(downloadUrl);
}

async function apiFetch(url, options = {}) {
  const requestOptions = {
    credentials: "include",
    ...options,
  };

  const response = await fetch(url, requestOptions);
  let payload = null;
  try {
    payload = await response.json();
  } catch (_error) {
    payload = null;
  }
  if (!response.ok) {
    throw new Error(parseErrorMessage(response.status, payload));
  }
  return payload;
}

function resetPreview() {
  previewCanvas.classList.remove("loading");
  previewImage.style.display = "none";
  previewImage.classList.remove("is-visible");
  previewImage.removeAttribute("src");
  previewImage.style.transform = "translate(0px, 0px) scale(1)";
  state.previewScale = 1;
  state.previewPanX = 0;
  state.previewPanY = 0;
  state.previewBaseWidth = 0;
  state.previewBaseHeight = 0;
  state.lastPreviewFileToken = null;
  setPreviewExportButtonsEnabled(false);
  previewEmpty.style.display = "grid";
  previewEmpty.textContent = "Generate a DXF from chat to see its live preview here.";
  if (previewFilename) {
    previewFilename.textContent = "No file yet";
  }
  if (previewSource) {
    previewSource.textContent = "-";
  }
  updatePreviewCanvasInteractionState();
  updateZoomLevelLabel();
}

function getContainedImageSize(imageNode, canvasNode) {
  const naturalWidth = Number(imageNode?.naturalWidth || 0);
  const naturalHeight = Number(imageNode?.naturalHeight || 0);
  const canvasWidth = Number(canvasNode?.clientWidth || 0);
  const canvasHeight = Number(canvasNode?.clientHeight || 0);
  if (!naturalWidth || !naturalHeight || !canvasWidth || !canvasHeight) {
    return {
      width: Math.max(canvasWidth, 1),
      height: Math.max(canvasHeight, 1),
    };
  }
  const fitScale = Math.min(canvasWidth / naturalWidth, canvasHeight / naturalHeight);
  return {
    width: Math.max(1, naturalWidth * fitScale),
    height: Math.max(1, naturalHeight * fitScale),
  };
}

function clampPreviewPan() {
  const canvasWidth = Number(previewCanvas?.clientWidth || 0);
  const canvasHeight = Number(previewCanvas?.clientHeight || 0);
  const renderedWidth = state.previewBaseWidth * state.previewScale;
  const renderedHeight = state.previewBaseHeight * state.previewScale;
  const maxPanX = Math.max(0, (renderedWidth - canvasWidth) / 2);
  const maxPanY = Math.max(0, (renderedHeight - canvasHeight) / 2);
  state.previewPanX = clamp(state.previewPanX, -maxPanX, maxPanX);
  state.previewPanY = clamp(state.previewPanY, -maxPanY, maxPanY);
}

function getPreviewPanBounds() {
  const canvasWidth = Number(previewCanvas?.clientWidth || 0);
  const canvasHeight = Number(previewCanvas?.clientHeight || 0);
  const renderedWidth = state.previewBaseWidth * state.previewScale;
  const renderedHeight = state.previewBaseHeight * state.previewScale;
  return {
    maxPanX: Math.max(0, (renderedWidth - canvasWidth) / 2),
    maxPanY: Math.max(0, (renderedHeight - canvasHeight) / 2),
  };
}

function updatePreviewCanvasInteractionState() {
  const hasImage = previewImage.style.display === "block";
  const isZoomed = hasImage && state.previewScale > 1.01;
  previewCanvas.classList.toggle("has-image", hasImage);
  previewCanvas.classList.toggle("is-zoomed", isZoomed);
  if (!isZoomed) {
    previewCanvas.classList.remove("is-panning");
  }
}

function applyPreviewScale() {
  clampPreviewPan();
  previewImage.style.transform = `translate(${state.previewPanX}px, ${state.previewPanY}px) scale(${state.previewScale})`;
  updatePreviewCanvasInteractionState();
}

function updateZoomLevelLabel() {
  if (!previewZoomResetButton) {
    return;
  }
  const percent = Math.round(state.previewScale * 100);
  previewZoomResetButton.textContent = `${percent}%`;
}

function setPreviewScale(nextScale) {
  state.previewScale = Math.max(0.45, Math.min(nextScale, 3.2));
  if (state.previewScale <= 1.01) {
    state.previewPanX = 0;
    state.previewPanY = 0;
  }
  applyPreviewScale();
  updateZoomLevelLabel();
}

function panPreviewBy(deltaX, deltaY) {
  if (state.previewScale <= 1.01) {
    return;
  }
  state.previewPanX += deltaX;
  state.previewPanY += deltaY;
  applyPreviewScale();
}

function shouldZoomPreviewOnWheel(event) {
  return Boolean(event.ctrlKey || event.metaKey);
}

function beginCanvasPan(mode, event) {
  const isPreview = mode === "preview";
  const canvas = isPreview ? previewCanvas : dxfRenderCanvas;
  const image = isPreview ? previewImage : dxfRenderImage;
  const scale = isPreview ? state.previewScale : state.dxfRenderScale;
  if (!canvas || !image || image.style.display !== "block" || scale <= 1.01) {
    return;
  }

  event.preventDefault();
  activeCanvasPanSession = {
    mode,
    pointerId: event.pointerId,
    lastX: event.clientX,
    lastY: event.clientY,
  };
  canvas.classList.add("is-panning");
  if (typeof canvas.setPointerCapture === "function") {
    try {
      canvas.setPointerCapture(event.pointerId);
    } catch (_error) {
      // pointer capture is best effort
    }
  }
}

function moveCanvasPan(event) {
  if (!activeCanvasPanSession || event.pointerId !== activeCanvasPanSession.pointerId) {
    return;
  }
  event.preventDefault();
  const deltaX = event.clientX - activeCanvasPanSession.lastX;
  const deltaY = event.clientY - activeCanvasPanSession.lastY;
  activeCanvasPanSession.lastX = event.clientX;
  activeCanvasPanSession.lastY = event.clientY;

  if (activeCanvasPanSession.mode === "preview") {
    panPreviewBy(deltaX, deltaY);
    return;
  }
  panDxfRenderBy(deltaX, deltaY);
}

function endCanvasPan(event) {
  if (!activeCanvasPanSession || event.pointerId !== activeCanvasPanSession.pointerId) {
    return;
  }

  const mode = activeCanvasPanSession.mode;
  const pointerId = activeCanvasPanSession.pointerId;
  activeCanvasPanSession = null;

  const canvas = mode === "preview" ? previewCanvas : dxfRenderCanvas;
  if (!canvas) {
    return;
  }
  canvas.classList.remove("is-panning");
  if (typeof canvas.releasePointerCapture === "function") {
    try {
      canvas.releasePointerCapture(pointerId);
    } catch (_error) {
      // pointer capture release is best effort
    }
  }
}

function updatePreview({ fileName, fileToken }) {
  if (previewFilename) {
    previewFilename.textContent = fileName;
  }
  if (previewSource) {
    previewSource.textContent = fileToken ? `Session token: ${fileToken}` : "-";
  }
  state.lastPreviewFileToken = fileToken;
  setPreviewExportButtonsEnabled(Boolean(fileToken));
  previewEmpty.textContent = "Rendering preview...";
  previewEmpty.style.display = "grid";
  previewImage.style.display = "none";
  previewImage.classList.remove("is-visible");
  previewCanvas.classList.add("loading");

  const previewUrl = `/api/v1/dxf/preview?file_token=${encodeURIComponent(fileToken)}&v=${Date.now()}`;

  previewImage.onload = () => {
    previewCanvas.classList.remove("loading");
    previewEmpty.style.display = "none";
    previewImage.style.display = "block";
    previewImage.classList.add("is-visible");
    const fitted = getContainedImageSize(previewImage, previewCanvas);
    state.previewBaseWidth = fitted.width;
    state.previewBaseHeight = fitted.height;
    state.previewPanX = 0;
    state.previewPanY = 0;
    applyPreviewScale();
  };

  previewImage.onerror = () => {
    previewCanvas.classList.remove("loading");
    previewImage.style.display = "none";
    previewImage.classList.remove("is-visible");
    previewEmpty.style.display = "grid";
    previewEmpty.textContent =
      "Preview is not available right now. You can still download the DXF from chat.";
    state.previewPanX = 0;
    state.previewPanY = 0;
    state.previewBaseWidth = 0;
    state.previewBaseHeight = 0;
    setPreviewExportButtonsEnabled(false);
    updatePreviewCanvasInteractionState();
  };

  previewImage.src = previewUrl;
}

function resetDxfRenderPreview({
  emptyMessage = DXF_RENDER_EMPTY_MESSAGE,
  projectId = state.activeProjectId,
} = {}) {
  if (!dxfRenderCanvas || !dxfRenderImage || !dxfRenderEmpty) {
    return;
  }
  dxfRenderCanvas.classList.remove("loading");
  dxfRenderImage.style.display = "none";
  dxfRenderImage.classList.remove("is-visible");
  dxfRenderImage.removeAttribute("src");
  dxfRenderImage.style.transform = "translate(0px, 0px) scale(1)";
  dxfRenderEmpty.style.display = "grid";
  dxfRenderEmpty.textContent = emptyMessage;
  state.dxfRenderScale = 1;
  state.dxfRenderPanX = 0;
  state.dxfRenderPanY = 0;
  state.dxfRenderBaseWidth = 0;
  state.dxfRenderBaseHeight = 0;
  state.dxfRenderFileToken = null;
  state.dxfRenderFileName = null;
  state.dxfRenderSource = null;
  state.dxfRenderProjectId = projectId || null;
  state.latestProjectDxfToken = null;
  setDxfRenderExportButtonsEnabled(false);
  updateDxfRenderCanvasInteractionState();
  updateDxfRenderZoomLabel();
  syncFilePreviewActionState();
}

function clampDxfRenderPan() {
  const canvasWidth = Number(dxfRenderCanvas?.clientWidth || 0);
  const canvasHeight = Number(dxfRenderCanvas?.clientHeight || 0);
  const renderedWidth = state.dxfRenderBaseWidth * state.dxfRenderScale;
  const renderedHeight = state.dxfRenderBaseHeight * state.dxfRenderScale;
  const maxPanX = Math.max(0, (renderedWidth - canvasWidth) / 2);
  const maxPanY = Math.max(0, (renderedHeight - canvasHeight) / 2);
  state.dxfRenderPanX = clamp(state.dxfRenderPanX, -maxPanX, maxPanX);
  state.dxfRenderPanY = clamp(state.dxfRenderPanY, -maxPanY, maxPanY);
}

function getDxfRenderPanBounds() {
  const canvasWidth = Number(dxfRenderCanvas?.clientWidth || 0);
  const canvasHeight = Number(dxfRenderCanvas?.clientHeight || 0);
  const renderedWidth = state.dxfRenderBaseWidth * state.dxfRenderScale;
  const renderedHeight = state.dxfRenderBaseHeight * state.dxfRenderScale;
  return {
    maxPanX: Math.max(0, (renderedWidth - canvasWidth) / 2),
    maxPanY: Math.max(0, (renderedHeight - canvasHeight) / 2),
  };
}

function updateDxfRenderCanvasInteractionState() {
  if (!dxfRenderCanvas || !dxfRenderImage) {
    return;
  }
  const hasImage = dxfRenderImage.style.display === "block";
  const isZoomed = hasImage && state.dxfRenderScale > 1.01;
  dxfRenderCanvas.classList.toggle("has-image", hasImage);
  dxfRenderCanvas.classList.toggle("is-zoomed", isZoomed);
  if (!isZoomed) {
    dxfRenderCanvas.classList.remove("is-panning");
  }
}

function applyDxfRenderScale() {
  if (!dxfRenderImage) {
    return;
  }
  clampDxfRenderPan();
  dxfRenderImage.style.transform = `translate(${state.dxfRenderPanX}px, ${state.dxfRenderPanY}px) scale(${state.dxfRenderScale})`;
  updateDxfRenderCanvasInteractionState();
}

function updateDxfRenderZoomLabel() {
  if (!dxfRenderZoomResetButton) {
    return;
  }
  dxfRenderZoomResetButton.textContent = `${Math.round(state.dxfRenderScale * 100)}%`;
}

function setDxfRenderScale(nextScale) {
  state.dxfRenderScale = Math.max(0.45, Math.min(nextScale, 3.2));
  if (state.dxfRenderScale <= 1.01) {
    state.dxfRenderPanX = 0;
    state.dxfRenderPanY = 0;
  }
  applyDxfRenderScale();
  updateDxfRenderZoomLabel();
}

function panDxfRenderBy(deltaX, deltaY) {
  if (state.dxfRenderScale <= 1.01) {
    return;
  }
  state.dxfRenderPanX += deltaX;
  state.dxfRenderPanY += deltaY;
  applyDxfRenderScale();
}

function updateStandaloneDxfRender({
  fileName,
  fileToken,
  projectId = state.activeProjectId,
  source = "chat",
}) {
  if (!dxfRenderCanvas || !dxfRenderImage || !dxfRenderEmpty) {
    return;
  }

  state.dxfRenderFileToken = fileToken;
  state.dxfRenderFileName = fileName || "generated_file.dxf";
  state.dxfRenderSource = source;
  state.dxfRenderProjectId = projectId || null;
  setDxfRenderExportButtonsEnabled(Boolean(fileToken));
  syncFilePreviewActionState();
  dxfRenderEmpty.textContent = "Rendering DXF...";
  dxfRenderEmpty.style.display = "grid";
  dxfRenderImage.style.display = "none";
  dxfRenderImage.classList.remove("is-visible");
  dxfRenderCanvas.classList.add("loading");

  const previewUrl = `/api/v1/dxf/preview?file_token=${encodeURIComponent(fileToken)}&v=${Date.now()}`;

  dxfRenderImage.onload = () => {
    dxfRenderCanvas.classList.remove("loading");
    dxfRenderEmpty.style.display = "none";
    dxfRenderImage.style.display = "block";
    dxfRenderImage.classList.add("is-visible");
    const fitted = getContainedImageSize(dxfRenderImage, dxfRenderCanvas);
    state.dxfRenderBaseWidth = fitted.width;
    state.dxfRenderBaseHeight = fitted.height;
    state.dxfRenderPanX = 0;
    state.dxfRenderPanY = 0;
    applyDxfRenderScale();
  };

  dxfRenderImage.onerror = () => {
    dxfRenderCanvas.classList.remove("loading");
    dxfRenderImage.style.display = "none";
    dxfRenderImage.classList.remove("is-visible");
    dxfRenderEmpty.style.display = "grid";
    dxfRenderEmpty.textContent = "DXF render is unavailable right now.";
    state.dxfRenderPanX = 0;
    state.dxfRenderPanY = 0;
    state.dxfRenderBaseWidth = 0;
    state.dxfRenderBaseHeight = 0;
    setDxfRenderExportButtonsEnabled(false);
    updateDxfRenderCanvasInteractionState();
  };

  dxfRenderImage.src = previewUrl;
}

function createDownloadIcon() {
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("aria-hidden", "true");
  icon.innerHTML =
    '<path d="M12 3v11m0 0 4-4m-4 4-4-4m-5 8h18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />';
  return icon;
}

function createEyeIcon() {
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("aria-hidden", "true");
  icon.innerHTML =
    '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6zm9.5-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>';
  return icon;
}

function createPencilIcon() {
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("aria-hidden", "true");
  icon.innerHTML =
    '<path d="M4 20h4l10-10-4-4L4 16v4zm9-13 4 4M14 6l4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>';
  return icon;
}

function createTrashIcon() {
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("aria-hidden", "true");
  icon.innerHTML =
    '<path d="M4 7h16M9 7V5h6v2M8 7l1 12h6l1-12M10 11v5M14 11v5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>';
  return icon;
}

function isChatNearBottom() {
  if (!chatThread) {
    return true;
  }
  const distance = chatThread.scrollHeight - chatThread.scrollTop - chatThread.clientHeight;
  return distance < 44;
}

function updateChatScrollBottomButton() {
  if (!chatThread || !chatScrollBottomButton) {
    return;
  }
  const hasOverflow = chatThread.scrollHeight - chatThread.clientHeight > 28;
  const shouldShow = hasOverflow && !isChatNearBottom();
  chatScrollBottomButton.classList.toggle("is-visible", shouldShow);
}

function scrollChatToBottom({ behavior = "auto" } = {}) {
  if (!chatThread) {
    return;
  }
  if (typeof chatThread.scrollTo === "function") {
    chatThread.scrollTo({ top: chatThread.scrollHeight, behavior });
  } else {
    chatThread.scrollTop = chatThread.scrollHeight;
  }
  updateChatScrollBottomButton();
}

// FIX 2: preserve user scroll position during polling
function appendMessage(role, text, { isError = false, createdAt = null, autoScroll = true } = {}) {
  const bubbleRole = role === "user" ? "user" : "assistant";
  const message = document.createElement("article");
  message.className = `message ${bubbleRole}${isError ? " error" : ""}`;
  message.setAttribute("data-message-id", String(++state.messageCount));
  message.textContent = text;

  const stamp = document.createElement("div");
  stamp.className = "file-hint";
  stamp.textContent = messageStamp(createdAt);
  message.appendChild(stamp);

  chatThread.appendChild(message);
  if (autoScroll) {
    scrollChatToBottom({ behavior: "smooth" });
  }
  return message;
}

function appendTypingIndicator({ autoScroll = true } = {}) {
  removeTypingIndicator();
  const message = document.createElement("article");
  message.className = "message assistant typing";
  const dots = document.createElement("div");
  dots.className = "typing-dots";
  dots.innerHTML = "<span></span><span></span><span></span>";
  message.appendChild(dots);
  chatThread.appendChild(message);
  if (autoScroll) {
    scrollChatToBottom({ behavior: "smooth" });
  }
  state.typingIndicator = message;
  return message;
}

function removeTypingIndicator() {
  if (state.typingIndicator && state.typingIndicator.isConnected) {
    state.typingIndicator.remove();
  }
  state.typingIndicator = null;
  updateChatScrollBottomButton();
}

function syncBusyIndicator(messages, { autoScroll = true } = {}) {
  if (!state.busy) {
    removeTypingIndicator();
    return;
  }
  const last = messages[messages.length - 1];
  if (!last || last.role === "user") {
    appendTypingIndicator({ autoScroll });
    return;
  }
  removeTypingIndicator();
}

function syncFilePreviewActionState() {
  if (!chatThread) {
    return;
  }
  const previewButtons = chatThread.querySelectorAll("[data-dxf-preview-token]");
  for (const button of previewButtons) {
    const isActive = button.dataset.dxfPreviewToken === state.dxfRenderFileToken;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
    button.setAttribute("title", isActive ? "Currently shown in DXF render" : "Show in DXF render");
    const label = button.querySelector("[data-file-action-label]");
    if (label) {
      label.textContent = isActive ? "Showing" : "View";
    }
  }
}

function buildDownloadUrl(fileToken, dxfName) {
  return (
    `/api/v1/dxf/download?file_token=${encodeURIComponent(fileToken)}` +
    `&filename=${encodeURIComponent(dxfName)}`
  );
}

function buildIterativeEditHint(message) {
  const changedRooms = Array.isArray(message?.changed_rooms)
    ? message.changed_rooms.map((room) => String(room || "").trim()).filter(Boolean)
    : [];
  if (message?.is_new_design === false && changedRooms.length) {
    return `✦ Edited — ${changedRooms.join(", ")} updated`;
  }
  return "";
}

function appendFileMessage(message, { autoScroll = true } = {}) {
  const wrapper = appendMessage("assistant", message.text, {
    createdAt: message.created_at,
    autoScroll,
  });
  const dxfName = message.dxf_name || "generated_file.dxf";

  const card = document.createElement("div");
  card.className = "file-card";

  const main = document.createElement("div");
  main.className = "file-main";

  const name = document.createElement("span");
  name.className = "file-name";
  name.textContent = dxfName;

  const actions = document.createElement("div");
  actions.className = "file-actions";

  const previewButton = document.createElement("button");
  previewButton.type = "button";
  previewButton.className = "file-action file-preview-btn";
  previewButton.dataset.dxfPreviewToken = message.file_token;
  previewButton.setAttribute("aria-label", `Show ${dxfName} in DXF render`);
  const previewLabel = document.createElement("span");
  previewLabel.dataset.fileActionLabel = "true";
  previewLabel.textContent = "View";
  previewButton.append(previewLabel, createEyeIcon());
  previewButton.addEventListener("click", () => {
    revealDxfRenderPanel({ scrollIntoView: true });
    updateStandaloneDxfRender({
      fileName: dxfName,
      fileToken: message.file_token,
      projectId: state.activeProjectId,
      source: "chat",
    });
  });

  const link = document.createElement("a");
  link.className = "file-action file-link";
  link.href = buildDownloadUrl(message.file_token, dxfName);
  link.setAttribute("download", dxfName);
  link.setAttribute("title", "Download DXF");
  link.append("Download");
  link.append(createDownloadIcon());

  actions.append(previewButton, link);
  main.append(name, actions);

  const pathHint = document.createElement("p");
  pathHint.className = "file-hint";
  pathHint.textContent = `Session token: ${message.file_token}`;

  const modelHintText = message.model_used || message.provider_used
    ? `Model: ${message.model_used || "unknown"} | Provider: ${message.provider_used || "unknown"}`
    : "";

  card.append(main, pathHint);
  if (modelHintText) {
    const modelHintLine = document.createElement("p");
    modelHintLine.className = "file-hint";
    modelHintLine.textContent = modelHintText;
    card.append(modelHintLine);
  }

  const iterativeHintText = buildIterativeEditHint(message);
  if (iterativeHintText) {
    const iterativeHintLine = document.createElement("p");
    iterativeHintLine.className = "file-hint";
    iterativeHintLine.textContent = iterativeHintText;
    card.append(iterativeHintLine);
  }

  wrapper.appendChild(card);
}

function appendIterativeResponseMessage(response) {
  const fileToken = response?.preview_token || response?.file_token || null;
  const dxfName = `${previewExportBaseName()}.dxf`;

  if (fileToken) {
    appendFileMessage(
      {
        text: response?.is_new_design ? "DXF generated successfully." : "DXF updated successfully.",
        created_at: new Date().toISOString(),
        dxf_name: dxfName,
        file_token: fileToken,
        changed_rooms: Array.isArray(response?.changed_rooms) ? response.changed_rooms : [],
        is_new_design: Boolean(response?.is_new_design),
      },
      { autoScroll: true }
    );
    updatePreview({
      fileName: dxfName,
      fileToken,
    });
    state.latestProjectDxfToken = fileToken;
    updateStandaloneDxfRender({
      fileName: dxfName,
      fileToken,
      projectId: state.activeProjectId,
      source: "chat",
    });
    syncFilePreviewActionState();
    return;
  }

  appendMessage(
    "assistant",
    response?.is_new_design
      ? "Design generated, but DXF preview is unavailable right now."
      : "Design updated, but DXF preview is unavailable right now.",
    { autoScroll: true }
  );
}

function renderChatHistory(messages) {
  const shouldAutoScroll =
    !chatThread || chatThread.scrollHeight - chatThread.scrollTop - chatThread.clientHeight < 120;

  state.messageCount = 0;
  chatThread.innerHTML = "";
  if (chatPanel) {
    chatPanel.classList.toggle("is-empty-project", messages.length === 0);
  }

  if (!messages.length) {
    appendMessage(
      "assistant",
      "This project is empty. Write your first prompt and the project conversation will be saved automatically.",
      { autoScroll: false }
    );
  } else {
    for (const message of messages) {
      if (message.role === "user") {
        appendMessage("user", message.text, {
          createdAt: message.created_at,
          autoScroll: false,
        });
        continue;
      }
      if (message.file_token) {
        appendFileMessage(message, { autoScroll: false });
        continue;
      }
      appendMessage("assistant", message.text, {
        isError: message.role === "error",
        createdAt: message.created_at,
        autoScroll: false,
      });
    }
  }

  syncBusyIndicator(messages, { autoScroll: shouldAutoScroll });
  syncFilePreviewActionState();
  if (shouldAutoScroll) {
    scrollChatToBottom({ behavior: "auto" });
  } else {
    updateChatScrollBottomButton();
  }
}

function getLatestDxfMessage(messages) {
  return [...messages].reverse().find((item) => Boolean(item.file_token)) || null;
}

function syncPreviewFromMessages(messages) {
  const latestWithDxf = getLatestDxfMessage(messages);
  if (!latestWithDxf) {
    resetPreview();
    return;
  }
  updatePreview({
    fileName: latestWithDxf.dxf_name || "generated_file.dxf",
    fileToken: latestWithDxf.file_token,
  });
}

function syncDxfRenderFromMessages(messages, projectId) {
  const latestWithDxf = getLatestDxfMessage(messages);
  const latestFileToken = latestWithDxf ? latestWithDxf.file_token : null;
  const projectChanged = state.dxfRenderProjectId !== projectId;
  const latestTokenChanged = latestFileToken !== state.latestProjectDxfToken;
  state.latestProjectDxfToken = latestFileToken;

  if (!latestWithDxf) {
    if (projectChanged || state.dxfRenderSource === "chat") {
      resetDxfRenderPreview({ projectId });
      return;
    }
    syncFilePreviewActionState();
    return;
  }

  if (projectChanged || latestTokenChanged) {
    updateStandaloneDxfRender({
      fileName: latestWithDxf.dxf_name || "generated_file.dxf",
      fileToken: latestWithDxf.file_token,
      projectId,
      source: "chat",
    });
    return;
  }

  syncFilePreviewActionState();
}

function findModelMeta(modelValue) {
  const selected = modelSelect.selectedOptions[0];
  if (selected && selected.dataset.modelId) {
    return {
      request_value: modelValue,
      display_name: selected.textContent || modelValue,
      model_id: selected.dataset.modelId,
    };
  }
  return null;
}

function parseModelSelection(selectValue) {
  // Parse either the new provider::model_id value or the legacy provider-only value.
  if (selectValue.includes("::")) {
    const [provider, modelId] = selectValue.split("::");
    return { provider, model_id: modelId };
  }
  return { provider: selectValue, model_id: null };
}

function normalizeIterativeModelSelection(selection) {
  // Keep the iterative endpoint on its legacy enum until the backend accepts model_id there too.
  if (selection.provider === "ollama_cloud") {
    return "qwen_cloud";
  }
  return selection.provider;
}

function providerDisplayLabel(provider) {
  switch (provider) {
    case "ollama_cloud":
      return "Ollama Cloud";
    case "ollama":
      return "Ollama Local";
    case "huggingface":
      return "HuggingFace Local";
    default:
      return provider || "Model";
  }
}

function modelDisplayLabel(model) {
  return model?.model_id || model?.display_name || model?.request_value || "Model";
}

function setModelMenuOpen(isOpen) {
  modelMenuOpen = Boolean(isOpen && modelPickerMenu && modelPickerTrigger && !modelPickerTrigger.disabled);
  if (modelPicker) {
    modelPicker.classList.toggle("is-open", modelMenuOpen);
  }
  if (modelPickerMenu) {
    modelPickerMenu.hidden = !modelMenuOpen;
  }
  if (modelPickerTrigger) {
    modelPickerTrigger.setAttribute("aria-expanded", String(modelMenuOpen));
  }
}

function renderModelPicker(models = []) {
  if (!modelPickerOptions) {
    return;
  }

  modelPickerOptions.innerHTML = "";
  const groupedModels = new Map();
  for (const model of models) {
    const provider = model.provider || "other";
    if (!groupedModels.has(provider)) {
      groupedModels.set(provider, []);
    }
    groupedModels.get(provider).push(model);
  }

  for (const [provider, providerModels] of groupedModels.entries()) {
    const group = document.createElement("section");
    group.className = "compact-model-group";

    const label = document.createElement("p");
    label.className = "compact-model-group-label";
    label.textContent = providerDisplayLabel(provider);
    group.appendChild(label);

    for (const model of providerModels) {
      const optionButton = document.createElement("button");
      optionButton.type = "button";
      optionButton.className = "compact-model-option";
      optionButton.dataset.value = model.request_value;
      if (model.request_value === modelSelect.value) {
        optionButton.classList.add("is-active");
      }

      const title = document.createElement("span");
      title.className = "compact-model-option-title";
      title.textContent = modelDisplayLabel(model);

      const meta = document.createElement("span");
      meta.className = "compact-model-option-meta";
      meta.textContent = providerDisplayLabel(model.provider);

      optionButton.append(title, meta);
      optionButton.addEventListener("click", () => {
        modelSelect.value = model.request_value;
        modelSelect.dispatchEvent(new Event("change", { bubbles: true }));
        setModelMenuOpen(false);
      });

      group.appendChild(optionButton);
    }

    modelPickerOptions.appendChild(group);
  }
}

function updateModelHint() {
  const selectedValue = modelSelect.value;
  const metadata = findModelMeta(selectedValue);
  if (!metadata) {
    modelHint.textContent = "Model metadata unavailable.";
    return;
  }
  modelHint.textContent = `Selected: ${metadata.display_name}`;
}

function applyModelCatalog(catalog) {
  const models = Array.isArray(catalog?.models) ? catalog.models : fallbackModelCatalog.models;
  const defaultModel = catalog?.default_model || fallbackModelCatalog.default_model;

  modelSelect.innerHTML = "";
  for (const model of models) {
    const option = document.createElement("option");
    option.value = model.request_value;
    option.textContent = model.display_name;
    option.dataset.modelId = model.model_id;
    option.dataset.provider = model.provider;
    modelSelect.appendChild(option);
  }

  const values = new Set(models.map((model) => model.request_value));
  modelSelect.value = values.has(defaultModel) ? defaultModel : models[0]?.request_value || "huggingface";
  renderModelPicker(models);
  updateModelHint();
}

async function loadModelCatalog() {
  setModelLoading(true);
  modelHint.textContent = "Loading available models...";

  try {
    const catalog = await apiFetch("/api/v1/parse-design-models");
    applyModelCatalog(catalog);
  } catch (_error) {
    applyModelCatalog(fallbackModelCatalog);
    modelHint.textContent = "Using default catalog. Server model list is unavailable.";
  } finally {
    setModelLoading(false);
  }
}

function projectById(projectId) {
  return state.projects.find((project) => project.id === projectId) || null;
}

function applyConversationPayload(payload, { forceRender = true } = {}) {
  const updatedProject = payload.project;
  const messages = payload.messages || [];

  const projectIndex = state.projects.findIndex((project) => project.id === updatedProject.id);
  if (projectIndex >= 0) {
    state.projects[projectIndex] = updatedProject;
  }
  if (state.activeProjectId === updatedProject.id) {
    activeProjectTitle.textContent = updatedProject.name;
    const count = messages.length;
    const lastLabel = updatedProject.last_message_at ? ` • Last activity ${messageStamp(updatedProject.last_message_at)}` : "";
    chatSubtitle.textContent = `${count} ${count === 1 ? "message" : "messages"}${lastLabel}`;
  }
  state.serverMessageCount = messages.length;

  const latestWithDxf = getLatestDxfMessage(messages);
  const latestFileToken = latestWithDxf ? latestWithDxf.file_token : null;
  const shouldRefreshPreview = latestFileToken && latestFileToken !== state.lastPreviewFileToken;
  if (forceRender) {
    renderProjectList();
    renderChatHistory(messages);
    syncPreviewFromMessages(messages);
    syncDxfRenderFromMessages(messages, updatedProject.id);
    return;
  }

  if (shouldRefreshPreview) {
    updatePreview({
      fileName: latestWithDxf.dxf_name || "generated_file.dxf",
      fileToken: latestWithDxf.file_token,
    });
  }

  syncDxfRenderFromMessages(messages, updatedProject.id);
}

function renderProjectList() {
  projectList.innerHTML = "";
  const visibleProjects = getVisibleProjects();
  if (normalizedProjectSearchQuery()) {
    projectCountPill.textContent = `${visibleProjects.length}/${state.projects.length} projects`;
  } else {
    projectCountPill.textContent = projectCountLabel(state.projects.length);
  }

  if (!visibleProjects.length) {
    const empty = document.createElement("p");
    empty.className = "subtle";
    empty.textContent = state.projects.length
      ? "No chats match your search."
      : "No projects yet.";
    projectList.appendChild(empty);
    return;
  }

  for (const [index, project] of visibleProjects.entries()) {
    const item = document.createElement("div");
    item.className = "project-item";
    item.style.animationDelay = `${Math.min(index, 8) * 40}ms`;

    const selectButton = document.createElement("button");
    selectButton.type = "button";
    selectButton.className = `project-select-btn${project.id === state.activeProjectId ? " active" : ""}`;
    selectButton.setAttribute("title", project.name);
    selectButton.addEventListener("click", () => {
      void openProjectFromSidebar(project.id);
    });

    const name = document.createElement("span");
    name.className = "project-name";
    name.textContent = project.name;

    const meta = document.createElement("small");
    meta.className = "project-meta";
    const messageWord = project.message_count === 1 ? "message" : "messages";
    meta.textContent = `${project.message_count} ${messageWord}`;

    selectButton.append(name, meta);

    const actions = document.createElement("div");
    actions.className = "project-actions";

    const renameButton = document.createElement("button");
    renameButton.type = "button";
    renameButton.title = "Rename project";
    renameButton.setAttribute("aria-label", `Rename ${project.name}`);
    renameButton.append(createPencilIcon());
    renameButton.addEventListener("click", (event) => {
      event.stopPropagation();
      renameProjectFlow(project.id);
    });

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.title = "Delete project";
    deleteButton.className = "delete";
    deleteButton.setAttribute("aria-label", `Delete ${project.name}`);
    deleteButton.append(createTrashIcon());
    deleteButton.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteProjectFlow(project.id);
    });

    actions.append(renameButton, deleteButton);
    item.append(selectButton, actions);
    projectList.appendChild(item);
  }
}

async function fetchProjects() {
  const payload = isAuthenticatedMode()
    ? await apiFetch("/api/v1/workspace/me/projects")
    : await apiFetch(`/api/v1/workspace/projects?user_id=${encodeURIComponent(state.userId)}`);
  return Array.isArray(payload.projects) ? payload.projects : [];
}

async function createProjectRequest(name) {
  if (isAuthenticatedMode()) {
    return apiFetch("/api/v1/workspace/me/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
  }

  return apiFetch("/api/v1/workspace/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: state.userId,
      name,
    }),
  });
}

/**
 * Create a new chat project and clear the active iterative layout state.
 *
 * @returns {Promise<void>}
 */
async function createNewChatProject() {
  const nextName = suggestNextProjectName();
  if (sidebarChatTabButton) {
    sidebarChatTabButton.disabled = true;
  }
  try {
    const createdProject = await createProjectRequest(nextName);
    state.projects.unshift(createdProject);
    clearProjectLayout(createdProject.id); // LAYOUT-FIX: a brand-new project starts without any saved layout
    state.projectSearchQuery = "";
    if (sidebarChatSearchInput) {
      sidebarChatSearchInput.value = "";
    }
    setWorkspaceMode("studio");
    setSidebarTab("chat");
    await selectProject(createdProject.id);
    promptInput?.focus({ preventScroll: true });
    keepWorkspaceViewportStable();
  } catch (error) {
    appendMessage("assistant", `New chat failed: ${error.message}`, { isError: true });
  } finally {
    if (sidebarChatTabButton) {
      sidebarChatTabButton.disabled = false;
    }
  }
}

async function renameProjectRequest(projectId, name) {
  if (isAuthenticatedMode()) {
    return apiFetch(`/api/v1/workspace/me/projects/${encodeURIComponent(projectId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
  }

  return apiFetch(`/api/v1/workspace/projects/${encodeURIComponent(projectId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: state.userId,
      name,
    }),
  });
}

async function deleteProjectRequest(projectId) {
  if (isAuthenticatedMode()) {
    return apiFetch(`/api/v1/workspace/me/projects/${encodeURIComponent(projectId)}`, { method: "DELETE" });
  }

  return apiFetch(
    `/api/v1/workspace/projects/${encodeURIComponent(projectId)}?user_id=${encodeURIComponent(state.userId)}`,
    { method: "DELETE" }
  );
}

async function fetchProjectMessages(projectId) {
  if (isAuthenticatedMode()) {
    return apiFetch(`/api/v1/workspace/me/projects/${encodeURIComponent(projectId)}/messages`);
  }

  return apiFetch(`/api/v1/workspace/projects/${encodeURIComponent(projectId)}/messages?user_id=${encodeURIComponent(state.userId)}`);
}

function buildIterateUrl(projectId, isAuthenticated) {
  // ITERATIVE FIX: use /me/ path for authenticated users
  if (isAuthenticated) {
    return `/api/v1/workspace/me/projects/${projectId}/iterate`;
  }
  return `/api/v1/workspace/${projectId}/iterate`;
}

/**
 * Send either a full-generate or iterative-edit request for the active project.
 *
 * @param {string} projectId
 * @param {string} prompt
 * @returns {Promise<Object>}
 */
async function sendPrompt(projectId, prompt) {
  const activeId = state.activeProject ?? state.activeProjectId; // LAYOUT-FIX: resolve active project before selecting iterative base layout
  const projectLayout = loadProjectLayout(activeId); // LAYOUT-FIX: use the active project's stored layout instead of a global singleton
  state.currentLayout = projectLayout; // LAYOUT-FIX: sync currentLayout pointer before building the request body
  const useIterative = Boolean(projectLayout); // LAYOUT-FIX: iterative mode depends on the active project's saved layout only
  const authenticated = isAuthenticatedMode();
  // Split the selector value once so both request paths use the same provider/model selection.
  const { provider, model_id } = parseModelSelection(modelSelect.value);

  if (useIterative) {
    const iterateUrl = buildIterateUrl(encodeURIComponent(projectId), authenticated);
    const iterateBody = authenticated
      ? {
          prompt,
          current_layout: projectLayout ?? null, // LAYOUT-FIX: send the active project's stored layout snapshot
          model: normalizeIterativeModelSelection({ provider, model_id }),
          recovery_mode: "repair",
        }
      : {
          user_id: state.userId,
          prompt,
          current_layout: projectLayout ?? null, // LAYOUT-FIX: send the active project's stored layout snapshot
          model: normalizeIterativeModelSelection({ provider, model_id }),
          recovery_mode: "repair",
        };
    const payload = await apiFetch(iterateUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(iterateBody),
    });
    return { ...payload, _requestMode: "iterate" };
  }

  if (authenticated) {
    const payload = await apiFetch(`/api/v1/workspace/me/projects/${encodeURIComponent(projectId)}/generate-dxf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        model: provider,
        model_id,
        recovery_mode: "repair",
      }),
    });
    return { ...payload, _requestMode: "generate" };
  }

  const payload = await apiFetch(`/api/v1/workspace/projects/${encodeURIComponent(projectId)}/generate-dxf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: state.userId,
      prompt,
      model: provider,
      model_id,
      recovery_mode: "repair",
    }),
  });
  return { ...payload, _requestMode: "generate" };
}

async function fetchCurrentUser() {
  return apiFetch("/api/v1/auth/me");
}

async function fetchGoogleAuthConfig() {
  return apiFetch("/api/v1/auth/google/config");
}

async function fetchProfileRequest() {
  return apiFetch("/api/v1/profile/me");
}

async function updateProfileRequest(payload) {
  return apiFetch("/api/v1/profile/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function upsertProviderApiKeyRequest(provider, apiKey) {
  return apiFetch(`/api/v1/profile/me/providers/${encodeURIComponent(provider)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey }),
  });
}

async function deleteProviderApiKeyRequest(provider) {
  return apiFetch(`/api/v1/profile/me/providers/${encodeURIComponent(provider)}`, {
    method: "DELETE",
  });
}

async function registerRequest({ name, email, password }) {
  return apiFetch("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
}

async function loginRequest({ email, password }) {
  return apiFetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

async function logoutRequest() {
  return apiFetch("/api/v1/auth/logout", {
    method: "POST",
  });
}

async function googleLoginRequest(credential) {
  return apiFetch("/api/v1/auth/google", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credential }),
  });
}

function renderGoogleAuthUnavailable(message) {
  if (!googleAuthContainer || !googleAuthButton) {
    return;
  }
  googleAuthContainer.hidden = false;
  googleAuthButton.innerHTML = `<button class="google-auth-fallback" type="button" disabled>${message}</button>`;
}

function renderGoogleAuthButton() {
  if (!googleClientId || !googleAuthButton) {
    return;
  }
  if (!window.google?.accounts?.id) {
    return;
  }

  googleAuthContainer.hidden = false;
  googleAuthButton.innerHTML = "";
  window.google.accounts.id.renderButton(googleAuthButton, {
    theme: "outline",
    size: "large",
    text: "continue_with",
    shape: "pill",
    width: 360,
    logo_alignment: "left",
  });
}

async function handleGoogleCredentialResponse(response) {
  const credential = response?.credential;
  if (typeof credential !== "string" || !credential.trim()) {
    setAuthFeedback("Google sign-in failed. Please try again.", "error");
    return;
  }

  setAuthFeedback("Signing in with Google...");
  try {
    const payload = await googleLoginRequest(credential);
    applyAuthenticatedUser(payload.user);
    await startWorkspaceSession();
    setStatus("Ready", "ready");
    setAuthFeedback("");
  } catch (error) {
    setAuthFeedback(error.message, "error");
  }
}

async function initializeGoogleAuth() {
  if (!googleAuthContainer || !googleAuthButton) {
    return;
  }

  googleAuthContainer.hidden = false;
  googleAuthButton.innerHTML = "";
  googleClientId = "";

  try {
    const config = await fetchGoogleAuthConfig();
    if (!config?.enabled || typeof config.client_id !== "string" || !config.client_id.trim()) {
      renderGoogleAuthUnavailable("Google sign-in is not configured");
      return;
    }
    googleClientId = config.client_id.trim();
  } catch (_error) {
    renderGoogleAuthUnavailable("Google sign-in is unavailable");
    return;
  }

  if (!window.google?.accounts?.id) {
    renderGoogleAuthUnavailable("Google script not loaded");
    setAuthFeedback("Google sign-in is unavailable right now.", "error");
    return;
  }

  window.google.accounts.id.initialize({
    client_id: googleClientId,
    callback: handleGoogleCredentialResponse,
  });
  googleAuthContainer.hidden = false;
  renderGoogleAuthButton();
}

function applyAuthenticatedUser(user) {
  state.authMode = "user";
  state.authUser = user;
  state.userId = user.id;
  state.profile = null;
  markKnownAccount();
  setTopbarIdentityLabel();
  setWorkspaceIdentityLabel();
  hideAuthGate();
}

function providerDisplayName(provider) {
  return provider
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function normalizeProviderRecords(payload) {
  const byProvider = new Map();
  const existing = Array.isArray(payload?.providers) ? payload.providers : [];
  const available = Array.isArray(payload?.available_providers) ? payload.available_providers : [];

  for (const item of existing) {
    if (!item || typeof item.provider !== "string") {
      continue;
    }
    byProvider.set(item.provider, {
      provider: item.provider,
      has_key: Boolean(item.has_key),
      masked_key: item.masked_key || null,
      updated_at: item.updated_at || null,
    });
  }

  for (const provider of available) {
    if (typeof provider !== "string" || !provider.trim() || byProvider.has(provider)) {
      continue;
    }
    byProvider.set(provider, {
      provider,
      has_key: false,
      masked_key: null,
      updated_at: null,
    });
  }

  return [...byProvider.values()].sort((a, b) => a.provider.localeCompare(b.provider));
}

function setProviderRowBusy(row, busy) {
  const controls = row.querySelectorAll("input, button");
  for (const control of controls) {
    control.disabled = busy;
  }
  row.classList.toggle("is-busy", busy);
}

function renderProviderKeyRows(records) {
  if (!providerKeyList) {
    return;
  }

  providerKeyList.innerHTML = "";
  if (!records.length) {
    const empty = document.createElement("p");
    empty.className = "provider-key-empty";
    empty.textContent = "No providers available yet.";
    providerKeyList.appendChild(empty);
    return;
  }

  for (const record of records) {
    const row = document.createElement("article");
    row.className = "provider-key-row";
    row.dataset.provider = record.provider;

    const head = document.createElement("div");
    head.className = "provider-key-head";

    const title = document.createElement("strong");
    title.className = "provider-key-provider";
    title.textContent = providerDisplayName(record.provider);

    const status = document.createElement("span");
    status.className = `provider-key-status${record.has_key ? " configured" : ""}`;
    status.textContent = record.has_key && record.masked_key ? `Saved (${record.masked_key})` : "Not set";
    head.append(title, status);

    const controls = document.createElement("div");
    controls.className = "provider-key-controls";

    const input = document.createElement("input");
    input.type = "password";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.placeholder = record.has_key ? "Paste new key to replace current one" : "Paste API key";

    const saveButton = document.createElement("button");
    saveButton.type = "button";
    saveButton.className = "provider-key-btn save";
    saveButton.textContent = record.has_key ? "Update key" : "Save key";

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "provider-key-btn remove";
    deleteButton.textContent = "Remove";
    deleteButton.disabled = !record.has_key;

    saveButton.addEventListener("click", async () => {
      const apiKey = input.value.trim();
      if (!apiKey) {
        setProfileFeedback(`Enter ${providerDisplayName(record.provider)} API key first.`, "error");
        input.focus();
        return;
      }

      setProviderRowBusy(row, true);
      try {
        const payload = await upsertProviderApiKeyRequest(record.provider, apiKey);
        applyProfilePayload(payload);
        setProfileFeedback(`${providerDisplayName(record.provider)} API key saved.`);
      } catch (error) {
        setProfileFeedback(error.message, "error");
        setProviderRowBusy(row, false);
      }
    });

    deleteButton.addEventListener("click", async () => {
      const confirmed = window.confirm(`Remove ${providerDisplayName(record.provider)} API key?`);
      if (!confirmed) {
        return;
      }

      setProviderRowBusy(row, true);
      try {
        const payload = await deleteProviderApiKeyRequest(record.provider);
        applyProfilePayload(payload);
        setProfileFeedback(`${providerDisplayName(record.provider)} API key removed.`);
      } catch (error) {
        setProfileFeedback(error.message, "error");
        setProviderRowBusy(row, false);
      }
    });

    controls.append(input, saveButton, deleteButton);
    row.append(head, controls);
    providerKeyList.appendChild(row);
  }
}

function applyProfilePayload(payload) {
  state.profile = payload || null;
  const profile = payload?.profile;
  if (!profile) {
    resetProfileState();
    setTopbarIdentityLabel();
    return;
  }

  setProfileSectionVisibility(true);
  if (profileEmailPill) {
    profileEmailPill.textContent = profile.email || "Account";
  }

  if (profileDisplayNameInput) {
    profileDisplayNameInput.value = profile.display_name || profile.name || "";
  }
  if (profileHeadlineInput) {
    profileHeadlineInput.value = profile.headline || "";
  }
  if (profileCompanyInput) {
    profileCompanyInput.value = profile.company || "";
  }
  if (profileWebsiteInput) {
    profileWebsiteInput.value = profile.website || "";
  }
  if (profileTimezoneInput) {
    profileTimezoneInput.value = profile.timezone || "";
  }

  renderProviderKeyRows(normalizeProviderRecords(payload));
  setTopbarIdentityLabel();
}

async function bootstrapProfile() {
  if (!isAuthenticatedMode()) {
    resetProfileState();
    return;
  }

  setProfileSectionVisibility(true);
  setProfileFeedback("Loading profile...");

  try {
    const payload = await fetchProfileRequest();
    applyProfilePayload(payload);
    setProfileFeedback("");
  } catch (error) {
    setProfileFeedback(`Profile failed to load: ${error.message}`, "error");
  }
}

async function startWorkspaceSession() {
  resetWorkspaceState();
  resetProfileState();
  await bootstrapWorkspace();
}

async function ensureDefaultProject() {
  if (state.projects.length) {
    return;
  }
  const defaultProject = await createProjectRequest("New Project");
  state.projects = [defaultProject];
  clearProjectLayout(defaultProject.id); // LAYOUT-FIX: every newly created project starts without a saved layout snapshot
}

/**
 * Mark a project active and clear iterative edit state when switching conversations.
 *
 * @param {string} projectId
 * @returns {void}
 */
function setActiveProject(projectId) {
  const project = projectById(projectId);
  const previousProjectId = state.activeProject ?? state.activeProjectId; // LAYOUT-FIX: capture the old active project before switching
  if (previousProjectId && state.currentLayout) {
    saveProjectLayout(previousProjectId, state.currentLayout); // LAYOUT-FIX: preserve the old project's last layout before switching away
  }
  state.activeProjectId = project ? project.id : null;
  const newProjectId = state.activeProject ?? state.activeProjectId; // LAYOUT-FIX: resolve the newly selected project id
  const newLayout = loadProjectLayout(newProjectId); // LAYOUT-FIX: load the selected project's saved layout instead of clearing globally
  state.currentLayout = newLayout; // LAYOUT-FIX: currentLayout now points at the selected project's stored layout
  updateIterativeModeIndicator(); // LAYOUT-FIX: update editing-mode UI after switching projects
  activeProjectTitle.textContent = project ? project.name : "No project selected";
  chatSubtitle.textContent = project ? "Loading conversation..." : "No project selected";
  setBusy(state.busy);
  renderProjectList();
}

async function loadProjectConversation(projectId) {
  const payload = await fetchProjectMessages(projectId);
  applyConversationPayload(payload, { forceRender: true });
}

async function selectProject(projectId) {
  setActiveProject(projectId);
  try {
    await loadProjectConversation(projectId);
  } catch (error) {
    renderChatHistory([]);
    resetPreview();
    resetDxfRenderPreview({ projectId });
    appendMessage("assistant", `Failed to load project chat: ${error.message}`, {
      isError: true,
    });
  }
}

async function openProjectFromSidebar(projectId) {
  setWorkspaceMode("studio");
  setSidebarTab("chat");
  await selectProject(projectId);
  promptInput?.focus({ preventScroll: true });
}

async function renameProjectFlow(projectId) {
  const project = projectById(projectId);
  if (!project) {
    return;
  }

  const nextName = window.prompt("Rename project", project.name);
  if (nextName === null) {
    return;
  }
  const trimmedName = nextName.trim();
  if (!trimmedName) {
    return;
  }

  try {
    const updated = await renameProjectRequest(projectId, trimmedName);
    const index = state.projects.findIndex((item) => item.id === projectId);
    if (index >= 0) {
      state.projects[index] = updated;
    }
    if (state.activeProjectId === projectId) {
      activeProjectTitle.textContent = updated.name;
    }
    renderProjectList();
  } catch (error) {
    appendMessage("assistant", `Rename failed: ${error.message}`, { isError: true });
  }
}

async function deleteProjectFlow(projectId) {
  const project = projectById(projectId);
  if (!project) {
    return;
  }

  const confirmed = window.confirm(`Delete project "${project.name}"? This will delete its chat history.`);
  if (!confirmed) {
    return;
  }
  const deletedProjectId = projectId; // DELETE-FIX: keep a stable project id for cleanup and state updates after the confirmed delete succeeds

  try {
    await deleteProjectRequest(deletedProjectId);
    clearProjectLayout(deletedProjectId); // DELETE-FIX: remove the deleted project's saved layout from memory and browser storage
    state.projects = state.projects.filter((item) => item.id !== deletedProjectId);
    if (!state.projects.length) {
      await ensureDefaultProject();
    }

    const fallbackId = state.projects[0]?.id || null;
    if (state.activeProjectId === deletedProjectId) {
      setActiveProject(fallbackId);
      if (fallbackId) {
        await loadProjectConversation(fallbackId);
      }
      return;
    }

    renderProjectList();
  } catch (error) {
    appendMessage("assistant", `Delete failed: ${error.message}`, { isError: true });
  }
}

async function bootstrapWorkspace() {
  setStatus("Loading", "pending");
  resetPreview();
  setWorkspaceIdentityLabel();
  await loadModelCatalog();

  state.projectLayouts = readStoredProjectLayouts(); // LAYOUT-FIX: hydrate persisted per-project layouts before choosing the initial active project
  state.projects = await fetchProjects();
  await ensureDefaultProject();
  const validProjectIds = new Set( // LAYOUT-FIX: collect the live workspace project ids before pruning stale stored layouts
    state.projects
      .map((project) => String(project?.id || "").trim())
      .filter(Boolean)
  );
  const prunedProjectLayouts = {}; // LAYOUT-FIX: rebuild storage with only layouts that still belong to existing projects
  for (const [projectId, layout] of Object.entries(state.projectLayouts)) {
    if (!validProjectIds.has(projectId) || !layout || typeof layout !== "object" || Array.isArray(layout)) {
      continue; // LAYOUT-FIX: skip stale or malformed stored entries so deleted projects do not retain hidden layout state
    }
    prunedProjectLayouts[projectId] = layout; // LAYOUT-FIX: keep only valid layouts for projects that still exist in the workspace
  }
  state.projectLayouts = prunedProjectLayouts; // LAYOUT-FIX: replace the in-memory map with the pruned persisted project layouts
  writeStoredProjectLayouts(); // LAYOUT-FIX: save the pruned project layout map before the first project becomes active
  renderProjectList();

  const firstProjectId = state.projects[0]?.id || null;
  if (!firstProjectId) {
    setStatus("Error", "error");
    activeProjectTitle.textContent = "Failed to load";
    return;
  }

  await selectProject(firstProjectId);
  setStatus("Ready", "ready");
}

function stopPreviewPolling() {
  if (state.previewPollTimer) {
    window.clearInterval(state.previewPollTimer);
    state.previewPollTimer = null;
  }
}

function startPreviewPolling() {
  stopPreviewPolling();
  state.previewPollTimer = window.setInterval(async () => {
    if (!state.activeProjectId || state.previewPollInFlight) {
      return;
    }
    state.previewPollInFlight = true;
    try {
      const payload = await fetchProjectMessages(state.activeProjectId);
      const messages = payload.messages || [];
      if (messages.length !== state.serverMessageCount) {
        applyConversationPayload(payload, { forceRender: true });
      } else {
        applyConversationPayload(payload, { forceRender: false });
      }
    } catch (_error) {
      // polling is best-effort and should not break the UI
    } finally {
      state.previewPollInFlight = false;
    }
  }, 1400);
}

async function handleProfileSubmit(event) {
  event.preventDefault();
  if (!isAuthenticatedMode()) {
    setProfileFeedback("Sign in first to update profile.", "error");
    return;
  }
  if (!profileSaveButton) {
    return;
  }

  const payload = {
    display_name: profileDisplayNameInput?.value || "",
    headline: profileHeadlineInput?.value || "",
    company: profileCompanyInput?.value || "",
    website: profileWebsiteInput?.value || "",
    timezone: profileTimezoneInput?.value || "",
  };

  const previousLabel = profileSaveButton.textContent;
  profileSaveButton.disabled = true;
  profileSaveButton.textContent = "Saving...";
  setProfileFeedback("Updating profile...");

  try {
    const updated = await updateProfileRequest(payload);
    applyProfilePayload(updated);
    setProfileFeedback("Profile updated.");
  } catch (error) {
    setProfileFeedback(error.message, "error");
  } finally {
    profileSaveButton.disabled = false;
    profileSaveButton.textContent = previousLabel;
  }
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  if (_loginPending) {
    return;
  }
  const email = loginEmailInput.value.trim().toLowerCase();
  const password = loginPasswordInput.value;
  if (!email || !password) {
    setAuthFeedback("Email and password are required.", "error");
    return;
  }

  _loginPending = true;
  if (authLoginButton) {
    authLoginButton.disabled = true;
  }
  setAuthFeedback("Signing in...");
  try {
    const payload = await loginRequest({ email, password });
    applyAuthenticatedUser(payload.user);
    await startWorkspaceSession();
    setStatus("Ready", "ready");
    loginPasswordInput.value = "";
    setAuthFeedback("");
  } catch (error) {
    setAuthFeedback(error.message, "error");
  } finally {
    _loginPending = false;
    if (authLoginButton) {
      authLoginButton.disabled = false;
    }
  }
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  if (_registerPending) {
    return;
  }
  const name = registerNameInput.value.trim();
  const email = registerEmailInput.value.trim().toLowerCase();
  const password = registerPasswordInput.value;
  if (!name || !email || !password) {
    setAuthFeedback("Name, email, and password are required.", "error");
    return;
  }

  _registerPending = true;
  if (authRegisterButton) {
    authRegisterButton.disabled = true;
  }
  setAuthFeedback("Creating account...");
  try {
    const payload = await registerRequest({ name, email, password });
    applyAuthenticatedUser(payload.user);
    await startWorkspaceSession();
    setStatus("Ready", "ready");
    registerPasswordInput.value = "";
    setAuthFeedback("");
  } catch (error) {
    setAuthFeedback(error.message, "error");
  } finally {
    _registerPending = false;
    if (authRegisterButton) {
      authRegisterButton.disabled = false;
    }
  }
}

// FIX 1: double-submit guard
async function handleProjectCreateSubmit(event) {
  event.preventDefault();
  if (_projectCreatePending) {
    return;
  }
  const projectName = projectNameInput.value.trim();
  if (!projectName) {
    return;
  }

  _projectCreatePending = true;
  if (projectCreateButton) {
    projectCreateButton.disabled = true;
  }

  try {
    const createdProject = await createProjectRequest(projectName);
    state.projects.unshift(createdProject);
    clearProjectLayout(createdProject.id); // LAYOUT-FIX: every manually created project starts without a saved layout
    projectNameInput.value = "";
    state.projectSearchQuery = "";
    if (sidebarChatSearchInput) {
      sidebarChatSearchInput.value = "";
    }
    setSidebarTab("chat");
    await selectProject(createdProject.id);
  } catch (error) {
    appendMessage("assistant", `Project creation failed: ${error.message}`, { isError: true });
  } finally {
    _projectCreatePending = false;
    if (projectCreateButton) {
      projectCreateButton.disabled = state.busy;
    }
  }
}

async function handleLogout() {
  try {
    await logoutRequest();
  } catch (_error) {
    // best-effort logout
  }

  state.authMode = "unknown";
  state.authUser = null;
  state.userId = getOrCreateUserId();
  setTopbarIdentityLabel();
  setWorkspaceIdentityLabel();
  resetWorkspaceState();
  resetProfileState();
  if (!AUTH_UI_ENABLED) {
    await startWorkspaceSession();
    setStatus("Ready", "ready");
    setAuthFeedback("");
    return;
  }
  showAuthGate();
  void initializeGoogleAuth();
  setStatus("Signed out", "pending");
  setAuthFeedback("Sign in to continue.");
}

async function initializeApplication() {
  setTheme();
  updateThemeToggleButton();
  initializeWorkspaceLayout();
  setSidebarTab("chat");
  setWorkspaceMode("studio");
  resetDxfRenderPreview();
  setTopbarIdentityLabel();
  setWorkspaceIdentityLabel();
  showAuthCheckingState();
  setStatus("Loading", "pending");

  try {
    const payload = await fetchCurrentUser();
    applyAuthenticatedUser(payload.user);
    await startWorkspaceSession();
    setStatus("Ready", "ready");
    if (AUTH_UI_ENABLED) {
      void initializeGoogleAuth();
    }
  } catch (_error) {
    state.authMode = "unknown";
    state.authUser = null;
    state.userId = getOrCreateUserId();
    setTopbarIdentityLabel();
    setWorkspaceIdentityLabel();
    resetProfileState();
    if (!AUTH_UI_ENABLED) {
      await startWorkspaceSession();
      setStatus("Ready", "ready");
      setAuthFeedback("");
      return;
    }
    showAuthGate(resolvePreferredAuthTab());
    setStatus("Auth", "pending");
    setAuthFeedback(resolvePreferredAuthTab() === "register" ? "Create your account to continue." : "Sign in to load your account.");
    await initializeGoogleAuth();
  }
}

modelSelect.addEventListener("change", () => {
  if (modelPickerOptions) {
    const optionButtons = modelPickerOptions.querySelectorAll(".compact-model-option");
    for (const button of optionButtons) {
      button.classList.toggle("is-active", button.dataset.value === modelSelect.value);
    }
  }
  updateModelHint();
});

if (modelPickerTrigger) {
  modelPickerTrigger.addEventListener("click", () => {
    setModelMenuOpen(!modelMenuOpen);
  });
}

document.addEventListener("pointerdown", (event) => {
  if (!modelMenuOpen || !modelPicker) {
    return;
  }
  if (modelPicker.contains(event.target)) {
    return;
  }
  setModelMenuOpen(false);
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !modelMenuOpen) {
    return;
  }
  setModelMenuOpen(false);
  modelPickerTrigger?.focus({ preventScroll: true });
});

if (themeToggleButton) {
  themeToggleButton.addEventListener("click", () => {
    toggleTheme();
  });
}

if (togglePreviewButton) {
  togglePreviewButton.addEventListener("click", () => {
    togglePreviewVisibility();
  });
}

if (sidebarQuickHideButton) {
  sidebarQuickHideButton.addEventListener("click", () => {
    toggleSidebarVisibility();
  });
}

if (workspaceLeftResizer) {
  workspaceLeftResizer.addEventListener("pointerdown", (event) => {
    beginWorkspaceResize("left", event);
  });
}

if (workspaceRightResizer) {
  workspaceRightResizer.addEventListener("pointerdown", (event) => {
    beginWorkspaceResize("right", event);
  });
}

window.addEventListener("resize", () => {
  if (previewImage && previewImage.style.display === "block") {
    const fitted = getContainedImageSize(previewImage, previewCanvas);
    state.previewBaseWidth = fitted.width;
    state.previewBaseHeight = fitted.height;
    applyPreviewScale();
  }
  if (dxfRenderImage && dxfRenderImage.style.display === "block") {
    const fitted = getContainedImageSize(dxfRenderImage, dxfRenderCanvas);
    state.dxfRenderBaseWidth = fitted.width;
    state.dxfRenderBaseHeight = fitted.height;
    applyDxfRenderScale();
  }
  applyWorkspaceLayout({ persist: false });
  updateChatScrollBottomButton();
});

authLoginTab.addEventListener("click", () => {
  setAuthTab("login");
});

authRegisterTab.addEventListener("click", () => {
  setAuthTab("register");
});

if (sidebarChatTabButton) {
  sidebarChatTabButton.addEventListener("click", async () => {
    await createNewChatProject();
  });
}

if (sidebarProjectsTabButton) {
  sidebarProjectsTabButton.addEventListener("click", () => {
    setWorkspaceMode("studio");
    setSidebarTab("projects");
    sidebarChatSearchInput?.focus({ preventScroll: true });
  });
}

if (sidebarChatSearchInput) {
  sidebarChatSearchInput.addEventListener("focus", () => {
    setSidebarTab("projects");
  });

  sidebarChatSearchInput.addEventListener("input", () => {
    state.projectSearchQuery = sidebarChatSearchInput.value;
    setWorkspaceMode("studio");
    setSidebarTab("projects");
    renderProjectList();
  });

  sidebarChatSearchInput.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    if (!sidebarChatSearchInput.value) {
      return;
    }
    event.preventDefault();
    sidebarChatSearchInput.value = "";
    state.projectSearchQuery = "";
    setSidebarTab("chat");
    renderProjectList();
  });

  sidebarChatSearchInput.addEventListener("blur", () => {
    if (state.sidebarTab !== "projects") {
      return;
    }
    if (state.projectSearchQuery.trim()) {
      return;
    }
    setSidebarTab("chat");
  });
}

if (sidebarFocusChatButton) {
  sidebarFocusChatButton.addEventListener("click", () => {
    setWorkspaceMode("studio");
    setSidebarTab("chat");
    promptInput?.focus({ preventScroll: true });
    keepWorkspaceViewportStable();
  });
}

if (sidebarManageProjectsButton) {
  sidebarManageProjectsButton.addEventListener("click", () => {
    setWorkspaceMode("studio");
    setSidebarTab("projects");
    projectNameInput?.focus({ preventScroll: true });
  });
}

if (sidebarDxfUploadTriggerButton) {
  sidebarDxfUploadTriggerButton.addEventListener("click", () => {
    setSidebarTab("render");
    revealDxfRenderPanel({ scrollIntoView: true });
    keepWorkspaceViewportStable();
    if (state.dxfRenderFileToken) {
      updateStandaloneDxfRender({
        fileName: state.dxfRenderFileName || "generated_file.dxf",
        fileToken: state.dxfRenderFileToken,
        projectId: state.dxfRenderProjectId,
        source: state.dxfRenderSource || "chat",
      });
      dxfRenderRefreshButton?.focus({ preventScroll: true });
    }
  });
}

authLoginForm.addEventListener("submit", handleLoginSubmit);
authRegisterForm.addEventListener("submit", handleRegisterSubmit);
if (profileForm) {
  profileForm.addEventListener("submit", handleProfileSubmit);
}

if (topbarUserLabel) {
  topbarUserLabel.addEventListener("click", () => {
    if (!isAuthenticatedMode()) {
      return;
    }
    window.location.href = "/app/profile.html";
  });
}

topbarAuthButton.addEventListener("click", () => {
  showAuthGate("login");
  void initializeGoogleAuth();
  setAuthFeedback("");
});

topbarLogoutButton.addEventListener("click", () => {
  handleLogout();
});

projectCreateForm.addEventListener("submit", handleProjectCreateSubmit);

previewRefreshButton.addEventListener("click", async () => {
  if (!state.activeProjectId) {
    return;
  }
  try {
    const payload = await fetchProjectMessages(state.activeProjectId);
    applyConversationPayload(payload, { forceRender: true });
  } catch (error) {
    appendMessage("assistant", `Preview refresh failed: ${error.message}`, { isError: true });
  }
});

if (previewDownloadPngButton) {
  previewDownloadPngButton.addEventListener("click", () => {
    downloadDxfExport(state.lastPreviewFileToken, "image", previewExportBaseName());
  });
}

if (previewDownloadPdfButton) {
  previewDownloadPdfButton.addEventListener("click", () => {
    downloadDxfExport(state.lastPreviewFileToken, "pdf", previewExportBaseName());
  });
}

previewZoomInButton.addEventListener("click", () => {
  setPreviewScale(state.previewScale + 0.15);
});

previewZoomOutButton.addEventListener("click", () => {
  setPreviewScale(state.previewScale - 0.15);
});

previewZoomResetButton.addEventListener("click", () => {
  setPreviewScale(1);
});

previewCanvas.addEventListener(
  "wheel",
  (event) => {
    if (previewImage.style.display !== "block") {
      return;
    }
    if (!shouldZoomPreviewOnWheel(event)) {
      if (state.previewScale > 1.01) {
        const bounds = getPreviewPanBounds();
        const panSpeed = 0.6;
        let panX = -event.deltaX * panSpeed;
        let panY = -event.deltaY * panSpeed;

        const hasVerticalIntent = Math.abs(event.deltaY) > Math.abs(event.deltaX);
        if (hasVerticalIntent && bounds.maxPanY <= 0.5 && bounds.maxPanX > 0.5) {
          panX = -event.deltaY * panSpeed;
          panY = 0;
        }

        const canPanX = Math.abs(panX) > 0.1 && bounds.maxPanX > 0.5;
        const canPanY = Math.abs(panY) > 0.1 && bounds.maxPanY > 0.5;
        if (canPanX || canPanY) {
          event.preventDefault();
          panPreviewBy(canPanX ? panX : 0, canPanY ? panY : 0);
        }
      }
      return;
    }
    event.preventDefault();
    const delta = event.deltaY < 0 ? 0.08 : -0.08;
    setPreviewScale(state.previewScale + delta);
  },
  { passive: false }
);

previewCanvas.addEventListener("dblclick", () => {
  setPreviewScale(1);
});

previewCanvas.addEventListener("pointerdown", (event) => {
  beginCanvasPan("preview", event);
});

previewCanvas.addEventListener("pointermove", moveCanvasPan);
previewCanvas.addEventListener("pointerup", endCanvasPan);
previewCanvas.addEventListener("pointercancel", endCanvasPan);

if (dxfRenderRefreshButton) {
  dxfRenderRefreshButton.addEventListener("click", () => {
    if (!state.dxfRenderFileToken) {
      return;
    }
    updateStandaloneDxfRender({
      fileName: state.dxfRenderFileName || "generated_file.dxf",
      fileToken: state.dxfRenderFileToken,
      projectId: state.dxfRenderProjectId,
      source: state.dxfRenderSource || "chat",
    });
  });
}

if (dxfRenderDownloadPngButton) {
  dxfRenderDownloadPngButton.addEventListener("click", () => {
    downloadDxfExport(state.dxfRenderFileToken, "image", dxfRenderExportBaseName());
  });
}

if (dxfRenderDownloadPdfButton) {
  dxfRenderDownloadPdfButton.addEventListener("click", () => {
    downloadDxfExport(state.dxfRenderFileToken, "pdf", dxfRenderExportBaseName());
  });
}

if (dxfRenderZoomInButton) {
  dxfRenderZoomInButton.addEventListener("click", () => {
    setDxfRenderScale(state.dxfRenderScale + 0.15);
  });
}

if (dxfRenderZoomOutButton) {
  dxfRenderZoomOutButton.addEventListener("click", () => {
    setDxfRenderScale(state.dxfRenderScale - 0.15);
  });
}

if (dxfRenderZoomResetButton) {
  dxfRenderZoomResetButton.addEventListener("click", () => {
    setDxfRenderScale(1);
  });
}

if (dxfRenderCanvas) {
  dxfRenderCanvas.addEventListener(
    "wheel",
    (event) => {
      if (!dxfRenderImage || dxfRenderImage.style.display !== "block") {
        return;
      }
      if (!shouldZoomPreviewOnWheel(event)) {
        if (state.dxfRenderScale > 1.01) {
          const bounds = getDxfRenderPanBounds();
          const panSpeed = 0.6;
          let panX = -event.deltaX * panSpeed;
          let panY = -event.deltaY * panSpeed;

          const hasVerticalIntent = Math.abs(event.deltaY) > Math.abs(event.deltaX);
          if (hasVerticalIntent && bounds.maxPanY <= 0.5 && bounds.maxPanX > 0.5) {
            panX = -event.deltaY * panSpeed;
            panY = 0;
          }

          const canPanX = Math.abs(panX) > 0.1 && bounds.maxPanX > 0.5;
          const canPanY = Math.abs(panY) > 0.1 && bounds.maxPanY > 0.5;
          if (canPanX || canPanY) {
            event.preventDefault();
            panDxfRenderBy(canPanX ? panX : 0, canPanY ? panY : 0);
          }
        }
        return;
      }
      event.preventDefault();
      const delta = event.deltaY < 0 ? 0.08 : -0.08;
      setDxfRenderScale(state.dxfRenderScale + delta);
    },
    { passive: false }
  );

  dxfRenderCanvas.addEventListener("dblclick", () => {
    setDxfRenderScale(1);
  });

  dxfRenderCanvas.addEventListener("pointerdown", (event) => {
    beginCanvasPan("dxf", event);
  });
  dxfRenderCanvas.addEventListener("pointermove", moveCanvasPan);
  dxfRenderCanvas.addEventListener("pointerup", endCanvasPan);
  dxfRenderCanvas.addEventListener("pointercancel", endCanvasPan);
}

if (chatThread) {
  chatThread.addEventListener("scroll", () => {
    updateChatScrollBottomButton();
  }, { passive: true });
}

if (chatScrollBottomButton) {
  chatScrollBottomButton.addEventListener("click", () => {
    scrollChatToBottom({ behavior: "smooth" });
  });
}

promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

/**
 * Handle chat form submission for both generate and iterative edit flows.
 *
 * @param {SubmitEvent} event
 * @returns {Promise<void>}
 */
async function handleChatFormSubmit(event) {
  event.preventDefault();
  if (state.busy || !state.activeProjectId) {
    return;
  }

  const prompt = promptInput.value.trim();
  if (!prompt) {
    return;
  }

  appendMessage("user", prompt);
  promptInput.value = "";
  setBusy(true);
  setStatus("Generating", "pending");
  appendTypingIndicator();

  try {
    const response = await sendPrompt(state.activeProjectId, prompt);
    const requestMode = response?._requestMode === "iterate" ? "iterate" : "generate";
    removeTypingIndicator();
    if (requestMode === "generate") {
      syncCurrentLayoutFromResponse(response, requestMode); // LAYOUT-FIX: persist the top-level generate-dxf layout before refreshing chat history
      startPreviewPolling(); // LAYOUT-FIX: begin chat refresh polling only after the saved layout is available for iterative mode
      await loadProjectConversation(state.activeProjectId); // LAYOUT-FIX: refresh chat after layout persistence so the active project keeps its saved base layout
      setStatus("Ready", "ready");
      return;
    }

    if (Array.isArray(response?.error) && response.error.length) {
      appendMessage("assistant", `Update failed: ${response.error.join(" | ")}`, { isError: true });
      setStatus("Error", "error");
      return;
    }

    syncCurrentLayoutFromResponse(response, requestMode);
    appendIterativeResponseMessage(response);
    setStatus("Ready", "ready");
  } catch (error) {
    removeTypingIndicator();
    if (state.currentLayout) {
      appendMessage("assistant", `Update failed: ${error.message}`, { isError: true });
    } else {
      try {
        await loadProjectConversation(state.activeProjectId);
      } catch (_innerError) {
        appendMessage("assistant", `Generation failed: ${error.message}`, { isError: true });
      }
    }
    setStatus("Error", "error");
  } finally {
    stopPreviewPolling();
    removeTypingIndicator();
    setBusy(false);
  }
}

chatForm.addEventListener("submit", handleChatFormSubmit);

setupPanelSpotlight();
updateChatScrollBottomButton();
updateIterativeModeIndicator();

initializeApplication().catch((error) => {
  setStatus("Error", "error");
  renderChatHistory([]);
  setAuthFeedback(`Workspace failed to initialize: ${error.message}`, "error");
});
