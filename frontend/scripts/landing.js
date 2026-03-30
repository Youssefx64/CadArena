const headline = document.getElementById("dynamic-headline");
const headlineHost = document.getElementById("dynamic-headline-host");
const yearLabel = document.getElementById("year-label");
const topNav = document.querySelector(".top-nav");
const scrollProgress = document.getElementById("scroll-progress");
const promptCards = Array.from(document.querySelectorAll(".prompt-card"));
const revealNodes = Array.from(document.querySelectorAll(".reveal"));
const statNodes = Array.from(document.querySelectorAll(".stat-value"));
const orbOne = document.getElementById("orb-one");
const orbTwo = document.getElementById("orb-two");
const scrollToTopButton = document.getElementById("scroll-to-top");
const themeToggleButton = document.getElementById("landing-theme-toggle");
const landingAuthLinks = document.getElementById("landing-auth-links");
const landingLoginLink = document.getElementById("landing-login-link");
const landingRegisterLink = document.getElementById("landing-register-link");
const landingOpenStudioLink = document.getElementById("landing-open-studio-link");
const landingUserMenu = document.getElementById("landing-user-menu");
const landingUserTrigger = document.getElementById("landing-user-trigger");
const landingUserAvatar = document.getElementById("landing-user-avatar");
const landingUserDropdown = document.getElementById("landing-user-dropdown");
const landingUserLogoutButton = document.getElementById("landing-user-logout-btn");
const navSectionLinks = Array.from(document.querySelectorAll('.nav-links a[href^="#"]'));
const navSections = navSectionLinks
  .map((link) => {
    const href = link.getAttribute("href");
    if (!href || !href.startsWith("#")) {
      return null;
    }
    const section = document.querySelector(href);
    if (!section) {
      return null;
    }
    return { link, section };
  })
  .filter(Boolean);

const rotatingLines = [
  "Generate build-ready DXF.",
  "Preview layouts in real time.",
  "Manage every project conversation.",
  "Switch models and iterate faster.",
];

const THEME_STORAGE_KEY = "cadarena_theme";
const AUTH_VISITED_STORAGE_KEY = "cadarena_auth_visited";
const AUTH_KNOWN_ACCOUNT_STORAGE_KEY = "cadarena_has_registered_account";
const DEFAULT_PROFILE_AVATAR = "/static/assets/cadarena-mark.svg";

let lineIndex = 0;
let frameId = null;
let landingUserMenuOpen = false;
let landingUserMenuHideTimer = null;
/* FIX 5: RAF scroll handler */
let _scrollRAF = null;

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

function inferLandingAuthAction() {
  const visitedBefore = readStoredFlag(AUTH_VISITED_STORAGE_KEY);
  const hasKnownAccount = readStoredFlag(AUTH_KNOWN_ACCOUNT_STORAGE_KEY);
  if (!visitedBefore) {
    return "login";
  }
  return hasKnownAccount ? "login" : "register";
}

function currentTheme() {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function updateThemeToggleButton() {
  if (!themeToggleButton) {
    return;
  }
  const label = "Toggle mode";
  themeToggleButton.setAttribute("aria-label", label);
  themeToggleButton.title = label;
}

function setTheme(theme) {
  const normalized = theme === "dark" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", normalized);
  try {
    localStorage.setItem(THEME_STORAGE_KEY, normalized);
  } catch (_error) {
    // best effort persistence
  }
  updateThemeToggleButton();
}

function toggleTheme() {
  setTheme(currentTheme() === "dark" ? "light" : "dark");
}

function buildLandingAvatarUrl(profileRecord) {
  const raw = typeof profileRecord?.avatar_url === "string" ? profileRecord.avatar_url.trim() : "";
  if (!raw) {
    return DEFAULT_PROFILE_AVATAR;
  }
  const normalized = /^https?:\/\//i.test(raw) ? raw : raw.startsWith("/") ? raw : `/${raw}`;
  const stamp = typeof profileRecord?.avatar_updated_at === "string" ? profileRecord.avatar_updated_at.trim() : "";
  if (!stamp) {
    return normalized;
  }
  const separator = normalized.includes("?") ? "&" : "?";
  return `${normalized}${separator}v=${encodeURIComponent(stamp)}`;
}

function applyLandingIdentity(user, profileRecord = null) {
  if (!landingUserTrigger || !landingUserAvatar) {
    return;
  }
  const displayName = String(profileRecord?.display_name || user?.name || "Account").trim() || "Account";
  const avatarUrl = buildLandingAvatarUrl(profileRecord);
  landingUserAvatar.src = avatarUrl;
  landingUserAvatar.alt = `${displayName} profile image`;
  landingUserTrigger.setAttribute("aria-label", `${displayName} account menu`);
  landingUserTrigger.title = displayName;
}

function setLandingUserMenuOpen(nextOpen) {
  if (!landingUserMenu || !landingUserTrigger || !landingUserDropdown || landingUserMenu.hidden) {
    landingUserMenuOpen = false;
    return;
  }
  if (landingUserMenuHideTimer) {
    window.clearTimeout(landingUserMenuHideTimer);
    landingUserMenuHideTimer = null;
  }
  const shouldOpen = Boolean(nextOpen);
  if (landingUserMenuOpen === shouldOpen && shouldOpen === landingUserDropdown.classList.contains("is-open")) {
    return;
  }
  landingUserMenuOpen = shouldOpen;
  landingUserTrigger.setAttribute("aria-expanded", String(landingUserMenuOpen));
  if (landingUserMenuOpen) {
    landingUserDropdown.hidden = false;
    window.requestAnimationFrame(() => {
      if (landingUserMenuOpen) {
        landingUserDropdown.classList.add("is-open");
      }
    });
    return;
  }
  landingUserDropdown.classList.remove("is-open");
  landingUserMenuHideTimer = window.setTimeout(() => {
    if (!landingUserMenuOpen) {
      landingUserDropdown.hidden = true;
    }
    landingUserMenuHideTimer = null;
  }, 180);
}

function closeLandingUserMenu() {
  setLandingUserMenuOpen(false);
}

function setLandingAuthState({ isAuthenticated, user = null, profileRecord = null }) {
  const unauthAction = inferLandingAuthAction();
  if (isAuthenticated) {
    markKnownAccount();
  }
  if (landingAuthLinks) {
    landingAuthLinks.hidden = isAuthenticated;
  }
  if (landingLoginLink) {
    landingLoginLink.hidden = isAuthenticated || unauthAction !== "login";
  }
  if (landingRegisterLink) {
    landingRegisterLink.hidden = isAuthenticated || unauthAction !== "register";
  }
  if (landingOpenStudioLink) {
    landingOpenStudioLink.hidden = false;
  }
  if (landingUserMenu) {
    landingUserMenu.hidden = !isAuthenticated;
  }

  if (isAuthenticated) {
    applyLandingIdentity(user, profileRecord);
    setLandingUserMenuOpen(false);
  } else {
    closeLandingUserMenu();
    if (landingUserAvatar) {
      landingUserAvatar.src = DEFAULT_PROFILE_AVATAR;
      landingUserAvatar.alt = "Profile image";
    }
    if (landingUserTrigger) {
      landingUserTrigger.setAttribute("aria-label", "Open account menu");
      landingUserTrigger.title = "Account";
    }
  }
}

async function landingApiFetch(url, options = {}) {
  const response = await fetch(url, {
    credentials: "include",
    ...options,
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch (_error) {
    payload = null;
  }
  if (!response.ok) {
    const message = payload && typeof payload.detail === "string" ? payload.detail : `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return payload;
}

async function syncLandingAuthState() {
  try {
    const authPayload = await landingApiFetch("/api/v1/auth/me");
    let profileRecord = null;
    try {
      const profilePayload = await landingApiFetch("/api/v1/profile/me");
      profileRecord = profilePayload?.profile || null;
    } catch (_error) {
      profileRecord = null;
    }
    setLandingAuthState({
      isAuthenticated: true,
      user: authPayload?.user || null,
      profileRecord,
    });
  } catch (_error) {
    setLandingAuthState({ isAuthenticated: false });
  } finally {
    markAuthVisited();
  }
}

async function handleLandingLogout() {
  const logoutButtons = [landingUserLogoutButton].filter(Boolean);
  if (!logoutButtons.length) {
    return;
  }
  const previousLabels = logoutButtons.map((button) => button.textContent);
  for (const button of logoutButtons) {
    button.disabled = true;
    button.textContent = "Signing out...";
  }
  closeLandingUserMenu();
  try {
    await landingApiFetch("/api/v1/auth/logout", { method: "POST" });
  } catch (_error) {
    // best effort logout
  } finally {
    for (const [index, button] of logoutButtons.entries()) {
      button.disabled = false;
      button.textContent = previousLabels[index] || "Logout";
    }
    setLandingAuthState({ isAuthenticated: false });
  }
}

function rotateHeadline() {
  if (!headline) {
    return;
  }

  lineIndex = (lineIndex + 1) % rotatingLines.length;
  headline.style.opacity = "0";
  headline.style.transform = "translateY(8px)";

  window.setTimeout(() => {
    headline.textContent = rotatingLines[lineIndex];
    headline.style.opacity = "1";
    headline.style.transform = "translateY(0)";
  }, 180);
}

function stabilizeHeadlineHeight() {
  if (!headline || !headlineHost) {
    return;
  }

  const hostWidth = headlineHost.clientWidth;
  if (hostWidth <= 0) {
    return;
  }

  const styles = window.getComputedStyle(headline);
  const probe = document.createElement("span");
  probe.style.position = "fixed";
  probe.style.visibility = "hidden";
  probe.style.pointerEvents = "none";
  probe.style.left = "0";
  probe.style.top = "0";
  probe.style.width = `${hostWidth}px`;
  probe.style.display = "inline-block";
  probe.style.font = styles.font;
  probe.style.fontWeight = styles.fontWeight;
  probe.style.letterSpacing = styles.letterSpacing;
  probe.style.lineHeight = styles.lineHeight;
  probe.style.whiteSpace = "normal";
  probe.style.wordBreak = "normal";
  probe.style.textTransform = styles.textTransform;
  probe.style.setProperty("text-wrap", styles.getPropertyValue("text-wrap") || "normal");

  document.body.appendChild(probe);
  let maxHeight = 0;
  for (const line of rotatingLines) {
    probe.textContent = line;
    const height = probe.getBoundingClientRect().height;
    if (height > maxHeight) {
      maxHeight = height;
    }
  }
  probe.remove();

  if (maxHeight > 0) {
    headlineHost.style.minHeight = `${Math.ceil(maxHeight)}px`;
  }
}

function activatePrompt(targetCard) {
  for (const card of promptCards) {
    const isActive = card === targetCard;
    card.classList.toggle("active", isActive);
    card.setAttribute("aria-pressed", isActive ? "true" : "false");
  }
}

function updateTopNav() {
  if (!topNav) {
    return;
  }
  topNav.classList.toggle("is-scrolled", window.scrollY > 8);
}

function setActiveSectionLink(activeSectionId) {
  for (const item of navSections) {
    const isActive = item.section.id === activeSectionId;
    item.link.classList.toggle("is-active", isActive);
    if (isActive) {
      item.link.setAttribute("aria-current", "true");
    } else {
      item.link.removeAttribute("aria-current");
    }
  }
}

function detectActiveSectionId() {
  if (!navSections.length) {
    return null;
  }

  const probeY = window.scrollY + window.innerHeight * 0.34;
  let activeId = navSections[0].section.id;

  for (const item of navSections) {
    const sectionTop = item.section.offsetTop;
    if (probeY >= sectionTop - 110) {
      activeId = item.section.id;
    }
  }

  const scrollBottom = document.documentElement.scrollHeight - window.innerHeight - 4;
  if (window.scrollY >= scrollBottom) {
    activeId = navSections[navSections.length - 1].section.id;
  }

  return activeId;
}

function updateActiveSectionByScroll() {
  const activeId = detectActiveSectionId();
  if (activeId) {
    setActiveSectionLink(activeId);
  }
}

function updateScrollProgress() {
  if (!scrollProgress) {
    return;
  }

  const doc = document.documentElement;
  const scrollHeight = doc.scrollHeight - doc.clientHeight;
  const progress = scrollHeight <= 0 ? 0 : window.scrollY / scrollHeight;
  scrollProgress.style.transform = `scaleX(${Math.max(0, Math.min(1, progress))})`;
}

function updateScrollToTopButton() {
  if (!scrollToTopButton) {
    return;
  }
  scrollToTopButton.classList.toggle("is-visible", window.scrollY > 320);
}

function animateStat(targetNode) {
  const target = Number(targetNode.dataset.target || "0");
  if (!Number.isFinite(target) || target <= 0) {
    return;
  }

  const startTime = performance.now();
  const duration = 950;

  function step(timestamp) {
    const elapsed = timestamp - startTime;
    const ratio = Math.min(elapsed / duration, 1);
    const eased = 1 - (1 - ratio) * (1 - ratio);
    targetNode.textContent = `${Math.round(target * eased)}`;

    if (ratio < 1) {
      requestAnimationFrame(step);
    }
  }

  requestAnimationFrame(step);
}

function setupRevealObserver() {
  if (revealNodes.length === 0) {
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) {
          continue;
        }

        entry.target.classList.add("in");

        if (entry.target.matches(".stat-card")) {
          const stat = entry.target.querySelector(".stat-value");
          if (stat && stat.dataset.animated !== "true") {
            stat.dataset.animated = "true";
            animateStat(stat);
          }
        }

        observer.unobserve(entry.target);
      }
    },
    { threshold: 0.15 },
  );

  for (const [index, node] of revealNodes.entries()) {
    node.style.transitionDelay = `${Math.min(index * 45, 280)}ms`;
    observer.observe(node);
  }
}

function setupSectionSpy() {
  if (!navSections.length) {
    return;
  }

  for (const item of navSections) {
    item.link.addEventListener("click", () => {
      setActiveSectionLink(item.section.id);
    });
  }

  updateActiveSectionByScroll();
}

function handlePointerMove(event) {
  const { innerWidth, innerHeight } = window;
  const x = (event.clientX / innerWidth - 0.5) * 2;
  const y = (event.clientY / innerHeight - 0.5) * 2;

  if (frameId) {
    cancelAnimationFrame(frameId);
  }

  frameId = requestAnimationFrame(() => {
    if (orbOne) {
      orbOne.style.transform = `translate(${x * -14}px, ${y * -10}px)`;
    }
    if (orbTwo) {
      orbTwo.style.transform = `translate(${x * 16}px, ${y * 12}px)`;
    }
  });
}

if (headline) {
  headline.style.transition = "opacity 0.2s ease, transform 0.2s ease";
  window.setInterval(rotateHeadline, 2800);
  stabilizeHeadlineHeight();
}

for (const [index, card] of promptCards.entries()) {
  card.addEventListener("mouseenter", () => activatePrompt(card));
  card.addEventListener("focus", () => activatePrompt(card));
  card.addEventListener("click", () => activatePrompt(card));

  if (index === 0) {
    activatePrompt(card);
  }
}

if (statNodes.length > 0) {
  for (const stat of statNodes) {
    stat.textContent = "0";
  }
}

updateThemeToggleButton();

if (themeToggleButton) {
  themeToggleButton.addEventListener("click", () => {
    toggleTheme();
  });
}

if (landingUserLogoutButton) {
  landingUserLogoutButton.addEventListener("click", () => {
    handleLandingLogout();
  });
}

if (landingUserTrigger) {
  landingUserTrigger.addEventListener("click", (event) => {
    event.stopPropagation();
    setLandingUserMenuOpen(!landingUserMenuOpen);
  });
}

if (landingUserDropdown) {
  landingUserDropdown.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

document.addEventListener("click", () => {
  closeLandingUserMenu();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeLandingUserMenu();
  }
});

setupRevealObserver();
setupSectionSpy();
window.addEventListener("scroll", () => {
  if (_scrollRAF) {
    return;
  }
  _scrollRAF = window.requestAnimationFrame(() => {
    updateTopNav();
    updateScrollProgress();
    updateScrollToTopButton();
    updateActiveSectionByScroll();
    _scrollRAF = null;
  });
}, { passive: true });
window.addEventListener("resize", () => {
  updateScrollProgress();
  updateActiveSectionByScroll();
  stabilizeHeadlineHeight();
});
window.addEventListener("pointermove", handlePointerMove, { passive: true });

updateTopNav();
updateScrollProgress();
updateScrollToTopButton();
updateActiveSectionByScroll();
syncLandingAuthState();

if (document.fonts?.ready) {
  document.fonts.ready.then(() => {
    stabilizeHeadlineHeight();
  });
}

if (yearLabel) {
  yearLabel.textContent = `© ${new Date().getFullYear()} CadArena`;
}
