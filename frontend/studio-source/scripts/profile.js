const THEME_STORAGE_KEY = "cadarena_theme";
const DEFAULT_PROFILE_AVATAR = "/static/assets/cadarena-mark.svg";
const MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024;

const themeToggleButton = document.getElementById("profile-theme-toggle");
const profileUserAvatar = document.getElementById("profile-user-avatar");
const profileUserName = document.getElementById("profile-user-name");
const openStudioButton = document.getElementById("profile-open-studio-btn");
const logoutButton = document.getElementById("profile-logout-btn");

const profileForm = document.getElementById("profile-form");
const profileDisplayNameInput = document.getElementById("profile-display-name-input");
const profileHeadlineInput = document.getElementById("profile-headline-input");
const profileCompanyInput = document.getElementById("profile-company-input");
const profileWebsiteInput = document.getElementById("profile-website-input");
const profileTimezoneInput = document.getElementById("profile-timezone-input");
const profileSaveButton = document.getElementById("profile-save-btn");
const profileEmailPill = document.getElementById("profile-email-pill");
const profileFeedback = document.getElementById("profile-feedback");
const profileAvatarImage = document.getElementById("profile-avatar-image");
const profileAvatarInput = document.getElementById("profile-avatar-input");
const profileAvatarUploadButton = document.getElementById("profile-avatar-upload-btn");
const profileAvatarRemoveButton = document.getElementById("profile-avatar-remove-btn");

const providerKeyList = document.getElementById("provider-key-list");

const state = {
  currentUser: null,
  profilePayload: null,
};

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
    // best effort
  }
  updateThemeToggleButton();
}

function toggleTheme() {
  setTheme();
}

function setFeedback(message, tone = "info") {
  if (!profileFeedback) {
    return;
  }
  profileFeedback.textContent = message || "";
  profileFeedback.classList.toggle("error", tone === "error");
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

async function apiFetch(url, options = {}) {
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
    throw new Error(parseErrorMessage(response.status, payload));
  }

  return payload;
}

async function fetchCurrentUser() {
  return apiFetch("/api/v1/auth/me");
}

async function fetchProfile() {
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

async function uploadProfileAvatarRequest(file) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch("/api/v1/profile/me/avatar", {
    method: "POST",
    body: formData,
  });
}

async function deleteProfileAvatarRequest() {
  return apiFetch("/api/v1/profile/me/avatar", {
    method: "DELETE",
  });
}

async function logoutRequest() {
  return apiFetch("/api/v1/auth/logout", {
    method: "POST",
  });
}

function providerDisplayName(provider) {
  return provider
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function normalizeProviderRecords(payload) {
  const byProvider = new Map();
  const configured = Array.isArray(payload?.providers) ? payload.providers : [];
  const available = Array.isArray(payload?.available_providers) ? payload.available_providers : [];

  for (const item of configured) {
    if (!item || typeof item.provider !== "string") {
      continue;
    }
    byProvider.set(item.provider, {
      provider: item.provider,
      has_key: Boolean(item.has_key),
      masked_key: item.masked_key || null,
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

function buildAvatarUrl(profile) {
  const raw = typeof profile?.avatar_url === "string" ? profile.avatar_url.trim() : "";
  if (!raw) {
    return DEFAULT_PROFILE_AVATAR;
  }
  const stamp = typeof profile?.avatar_updated_at === "string" ? profile.avatar_updated_at.trim() : "";
  if (!stamp) {
    return raw;
  }
  const separator = raw.includes("?") ? "&" : "?";
  return `${raw}${separator}v=${encodeURIComponent(stamp)}`;
}

function setAvatarControlsBusy(busy) {
  if (profileAvatarUploadButton) {
    profileAvatarUploadButton.disabled = busy;
  }
  if (profileAvatarRemoveButton) {
    profileAvatarRemoveButton.disabled = busy;
  }
}

function updateAvatarUI(profile) {
  const avatarSrc = buildAvatarUrl(profile);
  const hasCustomAvatar = Boolean(profile?.avatar_url);

  if (profileAvatarImage) {
    profileAvatarImage.src = avatarSrc;
  }
  if (profileUserAvatar) {
    profileUserAvatar.src = avatarSrc;
  }
  if (profileAvatarRemoveButton) {
    profileAvatarRemoveButton.hidden = !hasCustomAvatar;
  }
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
    const row = document.createElement("details");
    row.className = "provider-key-row";
    row.dataset.provider = record.provider;

    const summary = document.createElement("summary");
    summary.className = "provider-key-summary";

    const summaryMain = document.createElement("div");
    summaryMain.className = "provider-key-summary-main";

    const title = document.createElement("strong");
    title.className = "provider-key-provider";
    title.textContent = providerDisplayName(record.provider);

    const status = document.createElement("span");
    status.className = `provider-key-status${record.has_key ? " configured" : ""}`;
    status.textContent = record.has_key && record.masked_key ? `Configured (${record.masked_key})` : "Not set";

    const chevron = document.createElement("span");
    chevron.className = "provider-key-chevron";
    chevron.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="m8 10 4 4 4-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    `;

    summaryMain.append(title, status);
    summary.append(summaryMain, chevron);

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
        setFeedback(`Enter ${providerDisplayName(record.provider)} API key first.`, "error");
        input.focus();
        return;
      }

      setProviderRowBusy(row, true);
      try {
        const payload = await upsertProviderApiKeyRequest(record.provider, apiKey);
        applyProfilePayload(payload);
        setFeedback(`${providerDisplayName(record.provider)} API key saved.`);
      } catch (error) {
        setFeedback(error.message, "error");
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
        setFeedback(`${providerDisplayName(record.provider)} API key removed.`);
      } catch (error) {
        setFeedback(error.message, "error");
        setProviderRowBusy(row, false);
      }
    });

    const panel = document.createElement("div");
    panel.className = "provider-key-panel";

    const hint = document.createElement("p");
    hint.className = "provider-key-hint";
    hint.textContent = "Stored securely for this user profile only.";

    controls.append(input, saveButton, deleteButton);
    panel.append(hint, controls);
    row.append(summary, panel);
    providerKeyList.append(row);
  }
}

function applyProfilePayload(payload) {
  state.profilePayload = payload || null;
  const profile = payload?.profile;

  if (!profile) {
    updateAvatarUI(null);
    return;
  }

  updateAvatarUI(profile);

  if (profileUserName) {
    profileUserName.textContent = (profile.display_name || profile.name || "User").trim() || "User";
  }

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
}

function redirectToLogin() {
  window.location.href = "/app/?auth=login";
}

async function handleProfileSubmit(event) {
  event.preventDefault();

  const payload = {
    display_name: profileDisplayNameInput?.value || "",
    headline: profileHeadlineInput?.value || "",
    company: profileCompanyInput?.value || "",
    website: profileWebsiteInput?.value || "",
    timezone: profileTimezoneInput?.value || "",
  };

  if (!profileSaveButton) {
    return;
  }

  const previousLabel = profileSaveButton.textContent;
  profileSaveButton.disabled = true;
  profileSaveButton.textContent = "Saving...";
  setFeedback("Updating profile...");

  try {
    const updatedPayload = await updateProfileRequest(payload);
    applyProfilePayload(updatedPayload);
    setFeedback("Profile updated.");
  } catch (error) {
    setFeedback(error.message, "error");
  } finally {
    profileSaveButton.disabled = false;
    profileSaveButton.textContent = previousLabel;
  }
}

async function handleLogout() {
  if (logoutButton) {
    logoutButton.disabled = true;
  }
  try {
    await logoutRequest();
  } catch (_error) {
    // best effort logout
  } finally {
    redirectToLogin();
  }
}

async function initializeProfilePage() {
  setTheme();
  updateThemeToggleButton();

  try {
    const userPayload = await fetchCurrentUser();
    state.currentUser = userPayload.user;
    if (!state.currentUser || !state.currentUser.id) {
      redirectToLogin();
      return;
    }

    if (profileUserName) {
      profileUserName.textContent = (state.currentUser.name || "User").trim() || "User";
    }
    updateAvatarUI(null);

    const payload = await fetchProfile();
    applyProfilePayload(payload);
    setFeedback("");
  } catch (_error) {
    redirectToLogin();
  }
}

if (themeToggleButton) {
  themeToggleButton.addEventListener("click", () => {
    toggleTheme();
  });
}

if (openStudioButton) {
  openStudioButton.addEventListener("click", () => {
    window.location.href = "/app/";
  });
}

if (logoutButton) {
  logoutButton.addEventListener("click", () => {
    handleLogout();
  });
}

if (profileForm) {
  profileForm.addEventListener("submit", handleProfileSubmit);
}

if (profileAvatarUploadButton && profileAvatarInput) {
  profileAvatarUploadButton.addEventListener("click", () => {
    profileAvatarInput.click();
  });

  profileAvatarInput.addEventListener("change", async () => {
    const [file] = profileAvatarInput.files || [];
    if (!file) {
      return;
    }

    if (file.type && !file.type.startsWith("image/")) {
      setFeedback("Please select an image file.", "error");
      profileAvatarInput.value = "";
      return;
    }
    if (file.size > MAX_PROFILE_IMAGE_BYTES) {
      setFeedback("Image is too large. Maximum size is 5 MB.", "error");
      profileAvatarInput.value = "";
      return;
    }

    setAvatarControlsBusy(true);
    setFeedback("Uploading profile image...");
    try {
      const payload = await uploadProfileAvatarRequest(file);
      applyProfilePayload(payload);
      setFeedback("Profile image updated.");
    } catch (error) {
      setFeedback(error.message, "error");
    } finally {
      setAvatarControlsBusy(false);
      profileAvatarInput.value = "";
    }
  });
}

if (profileAvatarRemoveButton) {
  profileAvatarRemoveButton.addEventListener("click", async () => {
    const confirmed = window.confirm("Remove your current profile image?");
    if (!confirmed) {
      return;
    }

    setAvatarControlsBusy(true);
    setFeedback("Removing profile image...");
    try {
      const payload = await deleteProfileAvatarRequest();
      applyProfilePayload(payload);
      setFeedback("Profile image removed.");
    } catch (error) {
      setFeedback(error.message, "error");
    } finally {
      setAvatarControlsBusy(false);
    }
  });
}

initializeProfilePage();
