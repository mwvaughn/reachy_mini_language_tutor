async function fetchStatus() {
  try {
    const url = new URL("/status", window.location.origin);
    url.searchParams.set("_", Date.now().toString());
    const resp = await fetchWithTimeout(url, {}, 2000);
    if (!resp.ok) throw new Error("status error");
    return await resp.json();
  } catch (e) {
    return { has_key: false, error: true };
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchWithTimeout(url, options = {}, timeoutMs = 2000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

async function waitForStatus(timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (true) {
    try {
      const url = new URL("/status", window.location.origin);
      url.searchParams.set("_", Date.now().toString());
      const resp = await fetchWithTimeout(url, {}, 2000);
      if (resp.ok) return await resp.json();
    } catch (e) {}
    if (Date.now() >= deadline) return null;
    await sleep(500);
  }
}

async function waitForPersonalityData(timeoutMs = 15000) {
  const loadingText = document.querySelector("#loading p");
  let attempts = 0;
  const deadline = Date.now() + timeoutMs;
  while (true) {
    attempts += 1;
    try {
      const url = new URL("/personalities", window.location.origin);
      url.searchParams.set("_", Date.now().toString());
      const resp = await fetchWithTimeout(url, {}, 2000);
      if (resp.ok) return await resp.json();
    } catch (e) {}

    if (loadingText) {
      loadingText.textContent = attempts > 8 ? "Starting backend…" : "Loading…";
    }
    if (Date.now() >= deadline) return null;
    await sleep(500);
  }
}

async function validateKey(key) {
  const body = { openai_api_key: key };
  const resp = await fetch("/validate_api_key", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.error || "validation_failed");
  }
  return data;
}

async function saveKey(key) {
  const body = { openai_api_key: key };
  const resp = await fetch("/openai_api_key", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.error || "save_failed");
  }
  return await resp.json();
}

// ---------- SuperMemory API ----------
async function getSupermemoryStatus() {
  try {
    const url = new URL("/supermemory_api_key/status", window.location.origin);
    url.searchParams.set("_", Date.now().toString());
    const resp = await fetchWithTimeout(url, {}, 2000);
    if (!resp.ok) throw new Error("status_error");
    return await resp.json(); // { has_key: bool }
  } catch (e) {
    return { has_key: false, error: true };
  }
}

async function saveSupermemoryKey(key) {
  const body = { supermemory_api_key: key };
  const resp = await fetch("/supermemory_api_key", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error("save_failed");
  return await resp.json();
}

// ---------- Idle Settings API ----------
async function getIdleSettings() {
  try {
    const url = new URL("/settings/idle", window.location.origin);
    url.searchParams.set("_", Date.now().toString());
    const resp = await fetchWithTimeout(url, {}, 2000);
    if (!resp.ok) throw new Error("fetch_failed");
    return await resp.json(); // { enable_idle_signals: bool, idle_signal_timeout: int }
  } catch (e) {
    // Return defaults on error
    return { enable_idle_signals: true, idle_signal_timeout: 300, error: true };
  }
}

async function saveIdleSettings(enableSignals, timeout) {
  const body = {
    enable_idle_signals: enableSignals,
    idle_signal_timeout: timeout,
  };
  const resp = await fetch("/settings/idle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.error || "save_failed");
  }
  return data;
}

function formatTimeout(seconds) {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// ---------- Personalities API ----------
async function getPersonalities() {
  const url = new URL("/personalities", window.location.origin);
  url.searchParams.set("_", Date.now().toString());
  const resp = await fetchWithTimeout(url, {}, 2000);
  if (!resp.ok) throw new Error("list_failed");
  return await resp.json();
}

async function applyPersonality(name, { persist = false } = {}) {
  // Send as query param to avoid any body parsing issues on the server
  const url = new URL("/personalities/apply", window.location.origin);
  url.searchParams.set("name", name || "");
  if (persist) {
    url.searchParams.set("persist", "1");
  }
  url.searchParams.set("_", Date.now().toString());
  const resp = await fetchWithTimeout(url, { method: "POST" }, 5000);
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.error || "apply_failed");
  }
  return await resp.json();
}

function show(el, flag) {
  if (!el) return;
  el.classList.toggle("hidden", !flag);
}

async function init() {
  const loading = document.getElementById("loading");
  const apiPanel = document.getElementById("api-panel");
  const openaiInputForm = document.getElementById("openai-input-form");
  const openaiConfigured = document.getElementById("openai-configured");
  const openaiInput = document.getElementById("openai-key");
  const saveOpenaiBtn = document.getElementById("save-openai-btn");
  const changeOpenaiBtn = document.getElementById("change-openai-btn");
  const openaiStatus = document.getElementById("openai-status");

  const supermemoryInputForm = document.getElementById("supermemory-input-form");
  const supermemoryConfigured = document.getElementById("supermemory-configured");
  const supermemoryInput = document.getElementById("supermemory-key");
  const saveSupermemoryBtn = document.getElementById("save-supermemory-btn");
  const changeSupermemoryBtn = document.getElementById("change-supermemory-btn");
  const supermemoryStatus = document.getElementById("supermemory-status");

  const personalityPanel = document.getElementById("personality-panel");
  const pSelect = document.getElementById("personality-select");
  const pApply = document.getElementById("apply-personality");
  const pPersist = document.getElementById("persist-personality");
  const pStatus = document.getElementById("personality-status");
  const startupLabel = document.getElementById("startup-label");

  const advancedPanel = document.getElementById("advanced-panel");
  const advancedToggle = document.getElementById("advanced-toggle");
  const advancedContent = document.getElementById("advanced-content");
  const enableIdleCheckbox = document.getElementById("enable-idle-signals");
  const timeoutSlider = document.getElementById("idle-timeout-slider");
  const timeoutValue = document.getElementById("timeout-value");
  const timeoutSetting = document.getElementById("timeout-setting");
  const saveAdvancedBtn = document.getElementById("save-advanced");
  const advancedStatus = document.getElementById("advanced-status");

  const gettingStartedPanel = document.getElementById("getting-started-panel");
  const gettingStartedToggle = document.getElementById("getting-started-toggle");
  const gettingStartedContent = document.getElementById("getting-started-content");

  show(loading, true);
  show(apiPanel, false);
  show(personalityPanel, false);
  show(advancedPanel, false);

  // Check OpenAI API key status
  const st = (await waitForStatus()) || { has_key: false };

  if (st.has_key) {
    // Key exists - show configured state
    show(openaiInputForm, false);
    show(openaiConfigured, true);

    // Load SuperMemory status (non-blocking)
    getSupermemoryStatus().then(smStatus => {
      if (smStatus.has_key) {
        show(supermemoryInputForm, false);
        show(supermemoryConfigured, true);
      } else {
        show(supermemoryInputForm, true);
        show(supermemoryConfigured, false);
      }
    }).catch(() => {
      // Silently fail - optional feature, default to input form
      show(supermemoryInputForm, true);
      show(supermemoryConfigured, false);
    });
  } else {
    // No key - show input form
    show(openaiInputForm, true);
    show(openaiConfigured, false);
  }

  show(apiPanel, true);
  show(gettingStartedPanel, true);

  // OpenAI key handlers
  changeOpenaiBtn.addEventListener("click", () => {
    show(openaiConfigured, false);
    show(openaiInputForm, true);
    openaiInput.value = "";
    openaiStatus.textContent = "";
  });

  openaiInput.addEventListener("input", () => {
    openaiInput.classList.remove("error");
  });

  saveOpenaiBtn.addEventListener("click", async () => {
    const key = openaiInput.value.trim();
    if (!key) {
      openaiStatus.textContent = "Please enter a valid key.";
      openaiStatus.className = "status-message status-error";
      openaiInput.classList.add("error");
      return;
    }

    openaiStatus.textContent = "Validating API key...";
    openaiStatus.className = "status-message status-info";
    openaiInput.classList.remove("error");

    try {
      const validation = await validateKey(key);
      if (!validation.valid) {
        openaiStatus.textContent = "Invalid API key. Please check and try again.";
        openaiStatus.className = "status-message status-error";
        openaiInput.classList.add("error");
        return;
      }

      openaiStatus.textContent = "Key valid! Saving...";
      openaiStatus.className = "status-message status-success";
      await saveKey(key);
      openaiStatus.textContent = "Saved. Reloading...";
      window.location.reload();
    } catch (e) {
      openaiInput.classList.add("error");
      openaiStatus.textContent = "Failed to validate/save key. Please try again.";
      openaiStatus.className = "status-message status-error";
    }
  });

  // SuperMemory key handlers
  changeSupermemoryBtn.addEventListener("click", () => {
    show(supermemoryConfigured, false);
    show(supermemoryInputForm, true);
    supermemoryInput.value = "";
    supermemoryStatus.textContent = "";
  });

  supermemoryInput.addEventListener("input", () => {
    supermemoryInput.classList.remove("error");
  });

  saveSupermemoryBtn.addEventListener("click", async () => {
    const key = supermemoryInput.value.trim();
    supermemoryStatus.textContent = "Saving...";
    supermemoryStatus.className = "status-message status-info";

    try {
      await saveSupermemoryKey(key);
      if (key) {
        supermemoryStatus.textContent = "Key saved successfully. Reloading...";
        supermemoryStatus.className = "status-message status-success";
        // Reload to show configured state
        setTimeout(() => window.location.reload(), 500);
      } else {
        supermemoryStatus.textContent = "Key removed (feature disabled)";
        supermemoryStatus.className = "status-message status-info";
        // Reload to show input form state
        setTimeout(() => window.location.reload(), 500);
      }
    } catch (e) {
      supermemoryStatus.textContent = "Failed to save key";
      supermemoryStatus.className = "status-message status-error";
    }
  });

  if (!st.has_key) {
    show(loading, false);
    return; // Stop here if no OpenAI key
  }

  // Wait for personality data
  const list = (await waitForPersonalityData()) || { choices: [] };
  if (!list.choices.length) {
    openaiStatus.textContent = "Backend not ready. Please retry shortly.";
    openaiStatus.className = "status-message status-warning";
    show(loading, false);
    return;
  }

  // Initialize personality dropdown
  const choices = Array.isArray(list.choices) ? list.choices : [];
  const DEFAULT_OPTION = choices[0] || "(built-in default)";
  const startupChoice = choices.includes(list.startup) ? list.startup : DEFAULT_OPTION;
  const currentChoice = choices.includes(list.current) ? list.current : startupChoice;

  function setStartupLabel(name) {
    const display = name && name !== DEFAULT_OPTION ? name : "Built-in default";
    startupLabel.textContent = `Launch on start: ${display}`;
  }

  pSelect.innerHTML = "";
  for (const n of choices) {
    const opt = document.createElement("option");
    opt.value = n;
    opt.textContent = n;
    pSelect.appendChild(opt);
  }
  if (choices.length) {
    const preferred = choices.includes(startupChoice) ? startupChoice : currentChoice;
    pSelect.value = preferred;
  }
  setStartupLabel(startupChoice);

  pApply.addEventListener("click", async () => {
    pStatus.textContent = "Applying...";
    pStatus.className = "status-message status-info";
    try {
      const res = await applyPersonality(pSelect.value);
      if (res.startup) setStartupLabel(res.startup);
      pStatus.textContent = res.status || "Applied.";
      pStatus.className = "status-message status-success";
    } catch (e) {
      pStatus.textContent = `Failed to apply: ${e.message}`;
      pStatus.className = "status-message status-error";
    }
  });

  pPersist.addEventListener("click", async () => {
    pStatus.textContent = "Saving for startup...";
    pStatus.className = "status-message status-info";
    try {
      const res = await applyPersonality(pSelect.value, { persist: true });
      if (res.startup) setStartupLabel(res.startup);
      pStatus.textContent = res.status || "Saved for startup.";
      pStatus.className = "status-message status-success";
    } catch (e) {
      pStatus.textContent = `Failed to persist: ${e.message}`;
      pStatus.className = "status-message status-error";
    }
  });

  show(personalityPanel, true);
  show(advancedPanel, true);

  // Advanced panel accordion
  let advancedLoaded = false;
  advancedToggle.addEventListener("click", async () => {
    const isExpanded = advancedToggle.getAttribute("aria-expanded") === "true";
    advancedToggle.setAttribute("aria-expanded", !isExpanded);
    advancedPanel.classList.toggle("panel-expanded");
    advancedContent.classList.toggle("panel-collapsed");

    // Lazy-load idle settings on first open
    if (!isExpanded && !advancedLoaded) {
      try {
        const settings = await getIdleSettings();
        enableIdleCheckbox.checked = settings.enable_idle_signals;
        timeoutSlider.value = settings.idle_signal_timeout;
        timeoutValue.textContent = formatTimeout(settings.idle_signal_timeout);

        // Update disabled state
        if (!settings.enable_idle_signals) {
          timeoutSetting.classList.add("setting-disabled");
          timeoutSlider.disabled = true;
        }

        advancedLoaded = true;
      } catch (e) {
        advancedStatus.textContent = "Failed to load settings. Using defaults.";
        advancedStatus.className = "status-message status-warning";
      }
    }
  });

  // Getting Started panel toggle
  gettingStartedToggle.addEventListener("click", () => {
    const isExpanded = gettingStartedToggle.getAttribute("aria-expanded") === "true";
    gettingStartedToggle.setAttribute("aria-expanded", !isExpanded);
    gettingStartedPanel.classList.toggle("panel-expanded");
    gettingStartedContent.classList.toggle("panel-collapsed");
  });

  // Idle timeout slider display update
  timeoutSlider.addEventListener("input", (e) => {
    const seconds = parseInt(e.target.value);
    timeoutValue.textContent = formatTimeout(seconds);
  });

  // Enable/disable timeout when toggle changes
  enableIdleCheckbox.addEventListener("change", (e) => {
    const enabled = e.target.checked;
    timeoutSetting.classList.toggle("setting-disabled", !enabled);
    timeoutSlider.disabled = !enabled;
  });

  // Save advanced settings
  saveAdvancedBtn.addEventListener("click", async () => {
    const enable = enableIdleCheckbox.checked;
    const timeout = parseInt(timeoutSlider.value);

    advancedStatus.textContent = "Saving...";
    advancedStatus.className = "status-message status-info";

    try {
      await saveIdleSettings(enable, timeout);
      advancedStatus.textContent = "Settings saved successfully";
      advancedStatus.className = "status-message status-success";

      // Auto-dismiss after 3 seconds
      setTimeout(() => {
        advancedStatus.textContent = "";
      }, 3000);
    } catch (e) {
      if (e.message === "timeout_out_of_range") {
        advancedStatus.textContent = "Timeout must be between 30 and 900 seconds";
      } else {
        advancedStatus.textContent = "Failed to save settings";
      }
      advancedStatus.className = "status-message status-error";
    }
  });

  show(loading, false);
}

window.addEventListener("DOMContentLoaded", init);
