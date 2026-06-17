// Popup state
const state = {
  authenticated: false,
  email: null,
  settings: null,
  fillSession: null,
  fields: [],
};

// View management
function showView(name) {
  for (const v of ["login", "register", "main", "fill", "settings"]) {
    const el = document.getElementById("view-" + v);
    if (el) el.classList.toggle("active", v === name);
  }
}

// Tab management
function activateTab(name) {
  for (const t of document.querySelectorAll(".tab")) {
    t.classList.toggle("active", t.dataset.tab === name);
  }
  for (const p of ["profile", "general", "llm", "cvs", "account"]) {
    const el = document.getElementById("tab-" + p);
    if (el) el.classList.toggle("hidden", p !== name);
  }
  if (name === "profile") {
    loadProfile();
  }
  if (name === "cvs") {
    loadCVs();
  }
}

// Toast
function toast(message, kind) {
  kind = kind || "";
  const el = document.createElement("div");
  el.className = "toast" + (kind ? " " + kind : "");
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(function () { el.remove(); }, 3500);
}

// Send to background
function send(msg) {
  return new Promise(function (resolve) {
    chrome.runtime.sendMessage(msg, function (response) { resolve(response); });
  });
}

// ---------- BOOTSTRAP ----------
async function boot() {
  const auth = await send({ type: "AUTH_STATE" });
  if (auth && auth.authenticated) {
    state.authenticated = true;
    state.email = auth.email;
    await loadSettings();
    showView("main");
  } else {
    showView("login");
  }
  wireEvents();
  await maybeTriggerFillFromContent();
}

async function maybeTriggerFillFromContent() {
  // Check if the banner button was clicked (TRIGGER_FILL)
  let pending = false;
  try {
    const res = await send({ type: "PENDING_FILL_CHECK" });
    pending = !!(res && res.pending);
  } catch (_e) { /* ignore */ }
  const forms = await scanCurrentTabForForms();
  if (forms && forms.length > 0) {
    showFormDetectedCard(true);
    if (pending) {
      startFillSession(forms[0]);
    }
  } else {
    showFormDetectedCard(false);
  }
}

async function scanCurrentTabForForms() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab = tabs[0];
  if (!tab || !tab.id) return [];
  try {
    const result = await chrome.tabs.sendMessage(tab.id, { type: "GET_FORMS" });
    if (result && result.forms && result.forms.length > 0) {
      return result.forms;
    }
  } catch (_e) {
    // No content script on this tab
  }
  return [];
}

function showFormDetectedCard(visible) {
  const card = document.getElementById("form-detected-card");
  if (card) card.classList.toggle("hidden", !visible);
}

async function loadSettings() {
  const res = await send({ type: "AUTH_STATE" });
  if (!res || !res.authenticated) return;
  const token = await getToken();
  const settings = await fetch("http://localhost:8000/api/v1/settings", {
    headers: { Authorization: "Bearer " + token },
  }).then(function (r) { return r.json(); });
  state.settings = settings;
  applySettingsToUI();
}

function applySettingsToUI() {
  if (!state.settings) return;
  const s = state.settings;
  const langEl = document.getElementById("set-language");
  if (langEl) langEl.value = s.language;
  const modeEl = document.getElementById("set-mode");
  if (modeEl) modeEl.value = s.autofill_mode;
  const limitEl = document.getElementById("set-limit");
  if (limitEl) limitEl.value = String(s.llm_daily_limit);
  const provEl = document.getElementById("set-provider");
  if (provEl) provEl.value = s.llm_provider;
  const modelEl = document.getElementById("set-model");
  if (modelEl) modelEl.value = s.llm_model;
  const ollamaEl = document.getElementById("set-ollama");
  if (ollamaEl) ollamaEl.value = s.ollama_base_url || "";
  const endpEl = document.getElementById("set-endpoint");
  if (endpEl) endpEl.value = s.custom_endpoint || "";
  const keyStatus = document.getElementById("set-key-status");
  if (keyStatus) keyStatus.textContent = s.llm_api_key_set ? "(set)" : "";
  const emailDisplay = document.getElementById("set-email-display");
  if (emailDisplay) emailDisplay.textContent = "Signed in as: " + (state.email || "—");
  // Toggle conditional fields
  const ollamaVisible = s.llm_provider === "ollama";
  const customVisible = s.llm_provider === "custom";
  const fieldOllama = document.getElementById("field-ollama-url");
  if (fieldOllama) fieldOllama.classList.toggle("hidden", !ollamaVisible);
  const fieldCustom = document.getElementById("field-custom-endpoint");
  if (fieldCustom) fieldCustom.classList.toggle("hidden", !customVisible);
  const userEmail = document.getElementById("user-email");
  if (userEmail) userEmail.textContent = (state.email && state.email.split("@")[0]) || "there";
}

async function getToken() {
  const stored = await chrome.storage.session.get("accessToken");
  return stored.accessToken || "";
}

// ---------- CVs ----------
async function parseCV(cvId, token) {
  const res = await fetch("http://localhost:8000/api/v1/cvs/" + cvId + "/parse", {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok || data.parse_status === "failed") {
    var msg = data.parse_error || "Parse failed";
    if (msg.indexOf("Authentication") >= 0 || msg.indexOf("InvalidKey") >= 0) {
      msg = "Missing or invalid API key \u2014 set it in Settings \u2192 LLM";
    }
    toast(msg, "err");
  }
}

async function loadCVs() {
  const list = document.getElementById("cv-list");
  if (!list) return;
  list.innerHTML = '<p class="muted" style="padding: 12px 0; text-align: center;">Loading\u2026</p>';
  try {
    const token = await getToken();
    const res = await fetch("http://localhost:8000/api/v1/cvs", {
      headers: { Authorization: "Bearer " + token },
    });
    if (!res.ok) {
      list.innerHTML = '<p class="muted" style="padding: 12px 0; text-align: center; color:#b91c1c;">Failed to load CVs</p>';
      return;
    }
    const cvs = await res.json();
    renderCVs(cvs);
  } catch (_e) {
    list.innerHTML = '<p class="muted" style="padding: 12px 0; text-align: center; color:#b91c1c;">Cannot reach server</p>';
  }
}

function renderCVs(cvs) {
  const list = document.getElementById("cv-list");
  if (!list) return;
  if (!cvs || cvs.length === 0) {
    list.innerHTML = '<p class="muted" style="padding: 12px 0; text-align: center;">No CVs yet. Upload your first one above.</p>';
    return;
  }
  list.innerHTML = cvs.map(function (cv) {
    const sizeKb = Math.round(cv.size_bytes / 1024);
    const primaryBadge = cv.is_primary
      ? '<span class="badge learned">primary</span>'
      : "";
    const statusBadge = cv.parse_status === "done"
      ? '<span class="badge local">parsed</span>'
      : cv.parse_status === "failed"
        ? '<span class="badge err">parse error</span>'
        : '<span class="badge skip">pending</span>';
    const primaryBtn = cv.is_primary
      ? ""
      : '<button class="link-btn" data-action="primary" data-id="' + cv.cv_id + '" style="font-size:12px;">Set primary</button>';
    // Parse action button
    var parseBtn = "";
    var previewHtml = "";
    if (cv.parse_status === "pending" || cv.parse_status === "failed") {
      parseBtn = '<button class="link-btn" data-action="parse" data-id="' + cv.cv_id + '" style="font-size:12px; color:var(--blue-600);">Parse</button>';
    } else if (cv.parse_status === "done" && cv.parsed_data) {
      var fields = [];
      var d = cv.parsed_data;
      if (d.first_name || d.last_name) fields.push(d.first_name + " " + d.last_name);
      if (d.email) fields.push(d.email);
      if (d.phone) fields.push(d.phone);
      if (d.skills && d.skills.length) fields.push("Skills: " + d.skills.length);
      if (d.work_experience && d.work_experience.length) fields.push("Exp: " + d.work_experience.length + " positions");
      if (d.education && d.education.length) fields.push("Edu: " + d.education.length);
      previewHtml =
        '<div style="margin-top:8px; padding:8px; background:var(--ink-100); border-radius:8px; font-size:11px; color:var(--ink-700);">' +
          '<div style="font-weight:600; margin-bottom:4px;">\u2713 Profile updated from this CV</div>' +
          fields.map(function (f) { return '<div style="margin:2px 0;">\u2022 ' + escapeHtml(f) + '</div>'; }).join("") +
        '</div>';
    }
    return (
      '<div class="card" style="padding:10px 12px; margin-bottom:8px;">' +
        '<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">' +
          '<div style="flex:1; min-width:0;">' +
            '<div style="font-weight:600; font-size:13px; word-break:break-all;">' + escapeHtml(cv.filename) + '</div>' +
            '<div class="muted" style="font-size:11px; margin-top:2px;">' + sizeKb + ' KB \u00b7 ' + escapeHtml(cv.mime_type) + '</div>' +
            '<div style="margin-top:6px; display:flex; gap:4px; flex-wrap:wrap;">' + primaryBadge + statusBadge + '</div>' +
            previewHtml +
          '</div>' +
          '<div style="display:flex; flex-direction:column; gap:4px; align-items:flex-end;">' +
            parseBtn +
            primaryBtn +
            '<button class="link-btn" data-action="delete" data-id="' + cv.cv_id + '" style="font-size:12px; color:#b91c1c;">Delete</button>' +
          '</div>' +
        '</div>' +
      '</div>'
    );
  }).join("");
}

// ---------- EVENTS ----------
function wireEvents() {
  // Password eye toggle (delegated)
  document.addEventListener("click", function (e) {
    var btn = e.target;
    if (!(btn instanceof HTMLElement)) return;
    if (btn.dataset.toggle) {
      var input = document.getElementById(btn.dataset.toggle);
      if (!input) return;
      if (input.type === "password") {
        input.type = "text";
        btn.innerHTML = "&#128064;";
      } else {
        input.type = "password";
        btn.innerHTML = "&#128065;";
      }
    }
  });

  // Login
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      const btn = e.target.querySelector("button[type=submit]");
      btn.disabled = true;
      const res = await send({ type: "AUTH_LOGIN", email: email, password: password });
      btn.disabled = false;
      if (res && res.ok) {
        state.authenticated = true;
        state.email = email;
        await loadSettings();
        showView("main");
        toast("Signed in", "ok");
      } else {
        toast((res && res.error) || "Login failed", "err");
      }
    });
  }

  // Login -> Register
  const gotoSignup = document.getElementById("goto-signup");
  if (gotoSignup) {
    gotoSignup.addEventListener("click", function () {
      showView("register");
    });
  }

  // Register -> Login
  const gotoLogin = document.getElementById("goto-login");
  if (gotoLogin) {
    gotoLogin.addEventListener("click", function () {
      showView("login");
    });
  }

  // Register form
  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const email = document.getElementById("reg-email").value;
      const password = document.getElementById("reg-password").value;
      const confirm = document.getElementById("reg-confirm").value;
      if (password !== confirm) {
        toast("Passwords do not match", "err");
        return;
      }
      const btn = e.target.querySelector("button[type=submit]");
      btn.disabled = true;
      try {
        const res = await fetch("http://localhost:8000/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email, password: password, language: "en", consent_terms: true }),
        });
        const data = await res.json();
        if (res.ok) {
          await chrome.storage.session.set({ accessToken: data.access_token, refreshToken: data.refresh_token });
          state.authenticated = true;
          state.email = email;
          await loadSettings();
          showView("main");
          toast("Account created", "ok");
        } else {
          toast(data.detail || data.message || "Registration failed", "err");
        }
      } catch (err) {
        toast("Cannot reach server: " + err.message, "err");
      } finally {
        btn.disabled = false;
      }
    });
  }

  // Main -> Settings
  const gotoSettings = document.getElementById("goto-settings");
  if (gotoSettings) {
    gotoSettings.addEventListener("click", function () {
      showView("settings");
      activateTab("profile");
    });
  }

  // Main: trigger fill (from form-detected card)
  const triggerFillBtn = document.getElementById("trigger-fill-btn");
  if (triggerFillBtn) {
    triggerFillBtn.addEventListener("click", async function () {
      const forms = await scanCurrentTabForForms();
      if (!forms || forms.length === 0) {
        toast("No form detected now", "err");
        return;
      }
      startFillSession(forms[0]);
    });
  }

  // Main: manual scan
  const scanFormBtn = document.getElementById("scan-form-btn");
  if (scanFormBtn) {
    scanFormBtn.addEventListener("click", async function () {
      scanFormBtn.disabled = true;
      scanFormBtn.textContent = "Scanning...";
      const forms = await scanCurrentTabForForms();
      scanFormBtn.disabled = false;
      scanFormBtn.textContent = "Scan this page";
      if (forms && forms.length > 0) {
        showFormDetectedCard(true);
        toast("Form found \u2014 click Review and apply", "ok");
      } else {
        showFormDetectedCard(false);
        toast("No form detected on this page", "err");
      }
    });
  }

  // Settings -> Back
  const settingsBack = document.getElementById("settings-back");
  if (settingsBack) {
    settingsBack.addEventListener("click", function () {
      showView(state.fillSession ? "fill" : "main");
    });
  }

  // Tabs
  for (const t of document.querySelectorAll(".tab")) {
    t.addEventListener("click", function () { activateTab(t.dataset.tab); });
  }

  // Provider change
  const setProvider = document.getElementById("set-provider");
  if (setProvider) {
    setProvider.addEventListener("change", function (e) {
      const v = e.target.value;
      const fieldOllama = document.getElementById("field-ollama-url");
      if (fieldOllama) fieldOllama.classList.toggle("hidden", v !== "ollama");
      const fieldCustom = document.getElementById("field-custom-endpoint");
      if (fieldCustom) fieldCustom.classList.toggle("hidden", v !== "custom");
    });
  }

  // Save general settings
  const setLanguage = document.getElementById("set-language");
  if (setLanguage) setLanguage.addEventListener("change", function () { saveSettings(); });
  const setMode = document.getElementById("set-mode");
  if (setMode) setMode.addEventListener("change", function () { saveSettings(); });
  const setLimit = document.getElementById("set-limit");
  if (setLimit) setLimit.addEventListener("change", function () { saveSettings(); });

  // Save LLM settings
  const setSaveLlm = document.getElementById("set-save-llm");
  if (setSaveLlm) setSaveLlm.addEventListener("click", function () { saveLLMSettings(); });

  // Save profile
  const pfSave = document.getElementById("pf-save");
  if (pfSave) pfSave.addEventListener("click", async function () { await saveProfile(); });

  // CV source selector in profile tab
  const pfSourceCv = document.getElementById("pf-source-cv");
  if (pfSourceCv) {
    pfSourceCv.addEventListener("change", async function () {
      var cvId = pfSourceCv.value;
      if (!cvId) return;
      var token = await getToken();
      if (!token) return;
      await switchProfileCV(cvId, token);
    });
  }

  // Add education entry
  var pfEduAdd = document.getElementById("pf-edu-add");
  if (pfEduAdd) {
    pfEduAdd.addEventListener("click", function () {
      var current = collectEduCards();
      current.push({ institution: "", degree: null, field: null, start_date: null, end_date: null });
      renderEduCards(current);
    });
  }

  // Add certification entry
  var pfCertAdd = document.getElementById("pf-cert-add");
  if (pfCertAdd) {
    pfCertAdd.addEventListener("click", function () {
      var current = collectCertCards();
      current.push({ name: "", issuer: null, issue_date: null });
      renderCertCards(current);
    });
  }

  // Delegated delete for education/certification cards
  var pfEduCards = document.getElementById("pf-edu-cards");
  if (pfEduCards) {
    pfEduCards.addEventListener("click", function (e) {
      var btn = e.target;
      if (!(btn instanceof HTMLElement)) return;
      if (btn.dataset.action === "del-edu") {
        var current = collectEduCards();
        var card = btn.closest(".card");
        if (card && card.dataset.eduIdx !== undefined) {
          var idx = parseInt(card.dataset.eduIdx, 10);
          current.splice(idx, 1);
        }
        renderEduCards(current);
      }
    });
  }
  var pfCertCards = document.getElementById("pf-cert-cards");
  if (pfCertCards) {
    pfCertCards.addEventListener("click", function (e) {
      var btn = e.target;
      if (!(btn instanceof HTMLElement)) return;
      if (btn.dataset.action === "del-cert") {
        var current = collectCertCards();
        var card = btn.closest(".card");
        if (card && card.dataset.certIdx !== undefined) {
          var idx = parseInt(card.dataset.certIdx, 10);
          current.splice(idx, 1);
        }
        renderCertCards(current);
      }
    });
  }

  // Test connection
  const setTest = document.getElementById("set-test");
  if (setTest) {
    setTest.addEventListener("click", async function () {
      const out = document.getElementById("set-test-result");
      out.textContent = "Testing...";
      const token = await getToken();
      const keyEl = document.getElementById("set-key");
      const provEl = document.getElementById("set-provider");
      const modelEl = document.getElementById("set-model");
      const body = {};
      const key = keyEl ? keyEl.value : "";
      if (key) body.api_key = key;
      if (provEl && provEl.value) body.provider = provEl.value;
      if (modelEl && modelEl.value) body.model = modelEl.value;
      try {
        const res = await fetch("http://localhost:8000/api/v1/settings/llm/test", {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
          body: JSON.stringify(body),
        });
        const data = await res.json();
        out.textContent = data.ok ? "\u2713 " + data.message : "\u2717 " + data.message;
        out.style.color = data.ok ? "#047857" : "#b91c1c";
      } catch (_e) {
        out.textContent = "\u2717 Cannot reach server";
        out.style.color = "#b91c1c";
      }
    });
  }

  // CV upload
  const cvUploadBtn = document.getElementById("cv-upload-btn");
  if (cvUploadBtn) {
    cvUploadBtn.addEventListener("click", async function () {
      const fileInput = document.getElementById("cv-file-input");
      const status = document.getElementById("cv-upload-status");
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        status.textContent = "Pick a file first";
        status.style.color = "#b91c1c";
        return;
      }
      const file = fileInput.files[0];
      const btn = cvUploadBtn;
      btn.disabled = true;
      status.textContent = "Uploading...";
      status.style.color = "";
      try {
        const token = await getToken();
        const form = new FormData();
        form.append("file", file);
        const res = await fetch("http://localhost:8000/api/v1/cvs", {
          method: "POST",
          headers: { Authorization: "Bearer " + token },
          body: form,
        });
        if (res.ok) {
          const data = await res.json();
          status.textContent = "\u2713 " + file.name + " uploaded";
          status.style.color = "#047857";
          fileInput.value = "";
          await loadCVs();
          // Auto-parse if this is the first CV
          var cvs = [];
          try {
            const listRes = await fetch("http://localhost:8000/api/v1/cvs", {
              headers: { Authorization: "Bearer " + token },
            });
            cvs = await listRes.json();
          } catch (_e) { /* ignore */ }
          if (cvs.length <= 1) {
            toast("Only CV \u2014 auto-parsing\u2026", "ok");
            await parseCV(data.cv_id, token);
            await loadCVs();
          }
        } else {
          const body = await res.json().catch(function () { return {}; });
          status.textContent = "\u2717 " + (body.detail || "Upload failed");
          status.style.color = "#b91c1c";
        }
      } catch (e) {
        status.textContent = "\u2717 " + e.message;
        status.style.color = "#b91c1c";
      } finally {
        btn.disabled = false;
      }
    });
  }

  // CV list delegated handlers (primary/delete)
  const cvList = document.getElementById("cv-list");
  if (cvList) {
    cvList.addEventListener("click", async function (e) {
      const target = e.target;
      if (!(target instanceof HTMLElement)) return;
      const action = target.dataset.action;
      const cvId = target.dataset.id;
      if (!action || !cvId) return;
      const token = await getToken();
      try {
        if (action === "primary") {
          target.disabled = true;
          const res = await fetch("http://localhost:8000/api/v1/cvs/" + cvId + "/primary", {
            method: "PATCH",
            headers: { Authorization: "Bearer " + token },
          });
          if (res.ok) {
            toast("Primary CV updated", "ok");
            await loadCVs();
          } else {
            target.disabled = false;
            toast("Failed to set primary", "err");
          }
        } else if (action === "delete") {
          if (!confirm("Delete this CV?")) return;
          target.disabled = true;
          const res = await fetch("http://localhost:8000/api/v1/cvs/" + cvId, {
            method: "DELETE",
            headers: { Authorization: "Bearer " + token },
          });
          if (res.ok) {
            toast("CV deleted", "ok");
            await loadCVs();
          } else {
            target.disabled = false;
            toast("Delete failed", "err");
          }
        } else if (action === "parse") {
          target.disabled = true;
          target.textContent = "Parsing\u2026";
          await parseCV(cvId, token);
          target.disabled = false;
          target.textContent = "Parse";
          await loadCVs();
        }
      } catch (err) {
        toast("Error: " + err.message, "err");
        target.disabled = false;
      }
    });
  }

  // Logout
  const setLogout = document.getElementById("set-logout");
  if (setLogout) {
    setLogout.addEventListener("click", async function () {
      await send({ type: "AUTH_LOGOUT" });
      state.authenticated = false;
      state.email = null;
      state.settings = null;
      showView("login");
      toast("Signed out", "ok");
    });
  }

  // Fill apply
  const fillApply = document.getElementById("fill-apply");
  if (fillApply) {
    fillApply.addEventListener("click", async function () {
      if (!state.fillSession) return;
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const tab = tabs[0];
      if (!tab || !tab.id) return;
      await chrome.tabs.sendMessage(tab.id, {
        type: "APPLY_MAPPING",
        mapping: state.fillSession.mapping,
      });
      toast("Applied to page", "ok");
      showView("main");
    });
  }

  // Fill cancel
  const fillCancel = document.getElementById("fill-cancel");
  if (fillCancel) {
    fillCancel.addEventListener("click", function () {
      state.fillSession = null;
      showView("main");
    });
  }

  // Footer help
  const footerHelp = document.getElementById("footer-help");
  if (footerHelp) {
    footerHelp.addEventListener("click", function (e) {
      e.preventDefault();
      chrome.tabs.create({ url: "http://localhost:8000/docs" });
    });
  }
}

async function saveSettings() {
  const langEl = document.getElementById("set-language");
  const modeEl = document.getElementById("set-mode");
  const limitEl = document.getElementById("set-limit");
  const patch = {
    language: langEl ? langEl.value : "en",
    autofill_mode: modeEl ? modeEl.value : "review",
    llm_daily_limit: Number(limitEl ? limitEl.value : 100),
  };
  const token = await getToken();
  try {
    const res = await fetch("http://localhost:8000/api/v1/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify(patch),
    });
    if (res.ok) {
      state.settings = await res.json();
      flashStatus("Saved", "ok");
    } else {
      flashStatus("Save failed", "err");
    }
  } catch (_e) {
    flashStatus("Save failed", "err");
  }
}

async function saveLLMSettings() {
  const provEl = document.getElementById("set-provider");
  const modelEl = document.getElementById("set-model");
  const keyEl = document.getElementById("set-key");
  const ollamaEl = document.getElementById("set-ollama");
  const endpEl = document.getElementById("set-endpoint");
  const patch = {};
  if (provEl) patch.llm_provider = provEl.value;
  if (modelEl) patch.llm_model = modelEl.value;
  const key = keyEl ? keyEl.value : "";
  if (key) patch.llm_api_key = key;
  const ollama = ollamaEl ? ollamaEl.value : "";
  if (ollama) patch.ollama_base_url = ollama;
  const endpoint = endpEl ? endpEl.value : "";
  if (endpoint) patch.custom_endpoint = endpoint;
  const token = await getToken();
  try {
    const res = await fetch("http://localhost:8000/api/v1/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify(patch),
    });
    if (res.ok) {
      state.settings = await res.json();
      applySettingsToUI();
      if (keyEl) keyEl.value = "";
      flashStatus("Saved", "ok");
    } else {
      const body = await res.json().catch(function () { return {}; });
      flashStatus(body.message || "Save failed", "err");
    }
  } catch (_e) {
    flashStatus("Save failed", "err");
  }
}

async function loadProfile() {
  const token = await getToken();
  if (!token) return;
  try {
    // Load profile + CV list in parallel
    const [profRes, cvsRes] = await Promise.all([
      fetch("http://localhost:8000/api/v1/profile", {
        headers: { Authorization: "Bearer " + token },
      }),
      fetch("http://localhost:8000/api/v1/cvs", {
        headers: { Authorization: "Bearer " + token },
      }),
    ]);
    var p = {};
    if (profRes.ok) p = await profRes.json();
    var cvs = [];
    if (cvsRes.ok) cvs = await cvsRes.json();

    // Populate CV selector dropdown with parsed CVs
    var sourceSel = document.getElementById("pf-source-cv");
    var sourceLabel = document.getElementById("pf-source-label");
    if (sourceSel) {
      var parsedCVs = cvs.filter(function (c) { return c.parse_status === "done" && c.parsed_data; });
      sourceSel.innerHTML = '<option value="">-- No CV --</option>' +
        parsedCVs.map(function (c) {
          var sel = (p.source_cv_id && c.cv_id === p.source_cv_id) ? " selected" : "";
          return '<option value="' + c.cv_id + '"' + sel + '>' + escapeHtml(c.filename) + '</option>';
        }).join("");
      if (sourceLabel) {
        if (p.source_cv_id) {
          var srcCv = cvs.find(function (c) { return c.cv_id === p.source_cv_id; });
          sourceLabel.textContent = srcCv ? "Loaded from: " + srcCv.filename : "";
        } else {
          sourceLabel.textContent = "No CV selected \u2014 fill manually or parse a CV";
        }
      }
    }

    // Populate form fields
    var setField = function (id, val) {
      var el = document.getElementById(id);
      if (el) el.value = val || "";
    };
    setField("pf-first-name", p.first_name);
    setField("pf-last-name", p.last_name);
    setField("pf-email", p.email);
    setField("pf-phone", p.phone);
    setField("pf-linkedin", p.linkedin_url);
    setField("pf-github", p.github_url);
    setField("pf-portfolio", p.portfolio_url);
    setField("pf-summary", p.summary);
    if (p.skills && p.skills.length > 0) {
      setField("pf-skills", p.skills.join(", "));
    } else {
      setField("pf-skills", "");
    }
    // Location
    if (p.location) {
      setField("pf-city", p.location.city);
      setField("pf-region", p.location.region);
      setField("pf-country", p.location.country);
      setField("pf-country-code", p.location.country_code);
    }
    // Languages
    if (p.languages && p.languages.length > 0) {
      setField("pf-languages", p.languages.map(function (l) { return l.name + ": " + l.level; }).join(", "));
    } else {
      setField("pf-languages", "");
    }
    // Work experience textarea
    var expCount = document.getElementById("pf-exp-count");
    var expTextarea = document.getElementById("pf-exp-textarea");
    if (expTextarea && p.work_experience && p.work_experience.length > 0) {
      if (expCount) expCount.textContent = "(" + p.work_experience.length + ")";
      expTextarea.value = p.work_experience.map(function (e) {
        return [e.company || "", e.title || "", e.start_date || "", e.end_date || "", String(e.current || false), e.location || "", e.description || ""].join(" | ");
      }).join("\n");
    } else if (expTextarea) {
      if (expCount) expCount.textContent = "";
      expTextarea.value = "";
    }
    // Education cards
    renderEduCards(p.education || []);
    // Certifications cards
    renderCertCards(p.certifications || []);
  } catch (_e) { /* silent */ }
}

async function switchProfileCV(cvId, token) {
  try {
    var res = await fetch("http://localhost:8000/api/v1/profile/from-cv/" + cvId, {
      method: "PUT",
      headers: { Authorization: "Bearer " + token },
    });
    if (res.ok) {
      toast("Profile loaded from CV", "ok");
      await loadProfile();
    } else {
      var data = await res.json().catch(function () { return {}; });
      toast(data.detail || "Failed to load CV data", "err");
    }
  } catch (_e) {
    toast("Cannot reach server", "err");
  }
}

async function saveProfile() {
  var token = await getToken();
  if (!token) { toast("Please sign in first", "err"); return; }
  var getStr = function (id) {
    var el = document.getElementById(id);
    return el ? el.value.trim() : "";
  };
  var skillsStr = getStr("pf-skills");
  var skills = skillsStr ? skillsStr.split(",").map(function (s) { return s.trim(); }).filter(Boolean) : [];
  var langStr = getStr("pf-languages");
  var languages = langStr ? langStr.split(",").map(function (s) { return s.trim(); }).filter(Boolean).map(function (entry) {
    var parts = entry.split(":");
    return { name: (parts[0] || "").trim(), level: (parts[1] || "native").trim() };
  }) : [];
  var sourceSel = document.getElementById("pf-source-cv");

  // Parse work experience textarea
  var expText = getStr("pf-exp-textarea");
  var workExperience = expText ? expText.split("\n").map(function (line) {
    var parts = line.split("|").map(function (s) { return s.trim(); });
    if (!parts[0] && !parts[1]) return null;
    return {
      company: parts[0] || "",
      title: parts[1] || "",
      start_date: parts[2] || null,
      end_date: parts[3] || null,
      current: parts[4] === "true",
      location: parts[5] || null,
      description: parts[6] || null,
    };
  }).filter(Boolean) : [];

  // Collect from education cards
  var education = collectEduCards();

  // Collect from certification cards
  var certifications = collectCertCards();

  var body = {
    first_name: getStr("pf-first-name") || null,
    last_name: getStr("pf-last-name") || null,
    email: getStr("pf-email") || null,
    phone: getStr("pf-phone") || null,
    linkedin_url: getStr("pf-linkedin") || null,
    github_url: getStr("pf-github") || null,
    portfolio_url: getStr("pf-portfolio") || null,
    summary: getStr("pf-summary") || null,
    skills: skills,
    languages: languages,
    location: {
      city: getStr("pf-city") || null,
      region: getStr("pf-region") || null,
      country: getStr("pf-country") || null,
      country_code: getStr("pf-country-code") || null,
    },
    work_experience: workExperience,
    education: education,
    certifications: certifications,
    source_cv_id: sourceSel ? sourceSel.value || null : null,
  };
  var statusEl = document.getElementById("pf-status");
  try {
    var res = await fetch("http://localhost:8000/api/v1/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      if (statusEl) { statusEl.textContent = "\u2713 Profile saved"; statusEl.style.color = "#047857"; }
    } else {
      var data = await res.json().catch(function () { return {}; });
      if (statusEl) { statusEl.textContent = "\u2717 " + (data.message || "Save failed"); statusEl.style.color = "#b91c1c"; }
    }
  } catch (_e) {
    if (statusEl) { statusEl.textContent = "\u2717 Cannot reach server"; statusEl.style.color = "#b91c1c"; }
  }
}

function flashStatus(text, kind) {
  const el = document.getElementById("settings-status");
  if (!el) return;
  el.textContent = text;
  el.style.color = kind === "ok" ? "#047857" : "#b91c1c";
  setTimeout(function () {
    el.textContent = "Saved";
    el.style.color = "";
  }, 2000);
}

// ---------- FILL SESSION ----------
async function startFillSession(form) {
  state.fillSession = {
    domain: form.domain,
    fields: form.fields,
    mapping: {},
  };
  state.fields = form.fields;
  showView("fill");
  const domainEl = document.getElementById("fill-domain");
  if (domainEl) domainEl.textContent = form.domain;

  const list = document.getElementById("fill-list");
  if (!list) return;
  list.innerHTML = form.fields
    .map(function (f) {
      return (
        "<div class=\"field-row\" data-id=\"" + f.field_id + "\">" +
          "<span class=\"name\">" + escapeHtml(f.label || f.name || f.id) + "</span>" +
          "<span class=\"badge skip\" data-status>pending</span>" +
        "</div>"
      );
    })
    .join("");

  // Open WebSocket to backend
  const token = await getToken();
  if (!token) {
    toast("Please sign in first", "err");
    showView("main");
    return;
  }
  const ws = new WebSocket("ws://localhost:8000/api/v1/ws/fill?token=" + encodeURIComponent(token));
  ws.onopen = function () {
    ws.send(
      JSON.stringify({
        type: "FILL_REQUEST",
        url_hash: "local",
        domain: form.domain,
        fields: form.fields,
      }),
    );
  };
  ws.onmessage = function (ev) {
    const msg = JSON.parse(ev.data);
    if (msg.type === "FILL_PROGRESS") {
      const row = list.querySelector("[data-id=\"" + msg.field_id + "\"]");
      if (row) {
        const badge = row.querySelector("[data-status]");
        if (badge) {
          badge.className = "badge " + msg.status;
          badge.textContent = msg.status;
        }
      }
      updateProgress();
    } else if (msg.type === "FILL_COMPLETE") {
      state.fillSession.mapping = msg.mapping;
      const fillApply = document.getElementById("fill-apply");
      if (fillApply) fillApply.disabled = false;
      flashSummary("Ready — " + Object.keys(msg.mapping).length + " fields resolved");
      ws.close();
    }
  };
  ws.onerror = function () {
    toast("Cannot reach backend", "err");
  };
}

function updateProgress() {
  const total = state.fields.length;
  var resolved = 0;
  for (var i = 0; i < state.fields.length; i++) {
    const f = state.fields[i];
    const row = document.querySelector("[data-id=\"" + f.field_id + "\"]");
    if (row) {
      const badge = row.querySelector("[data-status]");
      if (badge && ["pending", "skipped", "error"].indexOf(badge.textContent) === -1) {
        resolved++;
      }
    }
  }
  const pct = total > 0 ? Math.round((resolved / total) * 100) : 0;
  const progressFill = document.getElementById("fill-progress");
  if (progressFill) progressFill.style.width = pct + "%";
  const summary = document.getElementById("fill-summary");
  if (summary) summary.textContent = "Resolving " + resolved + " / " + total + " fields\u2026";
}

function flashSummary(text) {
  const el = document.getElementById("fill-summary");
  if (el) el.textContent = text;
}

function renderEduCards(items) {
  var container = document.getElementById("pf-edu-cards");
  var count = document.getElementById("pf-edu-count");
  if (!container) return;
  if (count) count.textContent = items.length > 0 ? "(" + items.length + ")" : "";
  container.innerHTML = items.map(function (e, i) {
    return (
      '<div class="card" style="padding:8px; margin-bottom:6px;" data-edu-idx="' + i + '">' +
        '<div class="cf-row">' +
          '<span class="cf-label">Institution</span>' +
          '<input class="cf-input pf-edu-inst" value="' + escapeHtml(e.institution || "") + '" placeholder="University" />' +
          '<button class="cf-del" data-action="del-edu">&times;</button>' +
        '</div>' +
        '<div class="cf-row">' +
          '<span class="cf-label">Degree</span>' +
          '<input class="cf-input pf-edu-degree" value="' + escapeHtml(e.degree || "") + '" placeholder="BSc" />' +
          '<span class="cf-label">Field</span>' +
          '<input class="cf-input pf-edu-field" value="' + escapeHtml(e.field || "") + '" placeholder="CS" />' +
        '</div>' +
        '<div class="cf-row">' +
          '<span class="cf-label">Start</span>' +
          '<input class="cf-input pf-edu-start" value="' + escapeHtml(e.start_date || "") + '" placeholder="YYYY" />' +
          '<span class="cf-label">End</span>' +
          '<input class="cf-input pf-edu-end" value="' + escapeHtml(e.end_date || "") + '" placeholder="YYYY" />' +
        '</div>' +
      '</div>'
    );
  }).join("");
}

function collectEduCards() {
  var cards = document.querySelectorAll("#pf-edu-cards .card");
  var result = [];
  for (var i = 0; i < cards.length; i++) {
    var c = cards[i];
    var inst = (c.querySelector(".pf-edu-inst") || {}).value || "";
    if (!inst) continue;
    result.push({
      institution: inst,
      degree: ((c.querySelector(".pf-edu-degree") || {}).value || "") || null,
      field: ((c.querySelector(".pf-edu-field") || {}).value || "") || null,
      start_date: ((c.querySelector(".pf-edu-start") || {}).value || "") || null,
      end_date: ((c.querySelector(".pf-edu-end") || {}).value || "") || null,
    });
  }
  return result;
}

function renderCertCards(items) {
  var container = document.getElementById("pf-cert-cards");
  var count = document.getElementById("pf-cert-count");
  if (!container) return;
  if (count) count.textContent = items.length > 0 ? "(" + items.length + ")" : "";
  container.innerHTML = items.map(function (c, i) {
    return (
      '<div class="card" style="padding:8px; margin-bottom:6px;" data-cert-idx="' + i + '">' +
        '<div class="cf-row">' +
          '<span class="cf-label">Name</span>' +
          '<input class="cf-input pf-cert-name" value="' + escapeHtml(c.name || "") + '" placeholder="AWS Solutions Architect" />' +
          '<button class="cf-del" data-action="del-cert">&times;</button>' +
        '</div>' +
        '<div class="cf-row">' +
          '<span class="cf-label">Issuer</span>' +
          '<input class="cf-input pf-cert-issuer" value="' + escapeHtml(c.issuer || "") + '" placeholder="Amazon" />' +
          '<span class="cf-label">Date</span>' +
          '<input class="cf-input pf-cert-date" value="' + escapeHtml(c.issue_date || "") + '" placeholder="YYYY-MM" />' +
        '</div>' +
      '</div>'
    );
  }).join("");
}

function collectCertCards() {
  var cards = document.querySelectorAll("#pf-cert-cards .card");
  var result = [];
  for (var i = 0; i < cards.length; i++) {
    var c = cards[i];
    var name = (c.querySelector(".pf-cert-name") || {}).value || "";
    if (!name) continue;
    result.push({
      name: name,
      issuer: ((c.querySelector(".pf-cert-issuer") || {}).value || "") || null,
      issue_date: ((c.querySelector(".pf-cert-date") || {}).value || "") || null,
    });
  }
  return result;
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

boot().catch(function (e) {
  console.error("boot error", e);
  toast("Init error: " + e.message, "err");
});
