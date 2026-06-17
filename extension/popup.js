/// <reference types="chrome" />
/* eslint-disable @typescript-eslint/no-explicit-any */

// Popup state
const state = {
  authenticated: false,
  email: null as string | null,
  settings: null as any,
  fillSession: null as any,
  fields: [] as any[],
};

// View management
function showView(name: "login" | "main" | "fill" | "settings") {
  for (const v of ["login", "main", "fill", "settings"] as const) {
    document.getElementById(`view-${v}`)?.classList.toggle("active", v === name);
  }
}

// Tab management
function activateTab(name: "general" | "llm" | "account") {
  for (const t of document.querySelectorAll<HTMLElement>(".tab")) {
    t.classList.toggle("active", t.dataset.tab === name);
  }
  for (const p of ["general", "llm", "account"] as const) {
    document.getElementById(`tab-${p}`)?.classList.toggle("hidden", p !== name);
  }
}

// Toast
function toast(message: string, kind: "ok" | "err" | "" = "") {
  const el = document.createElement("div");
  el.className = "toast" + (kind ? ` ${kind}` : "");
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// Send to background
function send<T = any>(msg: any): Promise<T> {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(msg, (response) => resolve(response as T));
  });
}

// ---------- BOOTSTRAP ----------
async function boot() {
  const auth = await send({ type: "AUTH_STATE" });
  if (auth?.authenticated) {
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
  // Get the active tab and ask the content script for forms
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  try {
    const result = await chrome.tabs.sendMessage(tab.id, { type: "GET_FORMS" });
    if (result?.forms?.length > 0) {
      startFillSession(result.forms[0]);
    }
  } catch {
    // No content script on this tab; stay on main view
  }
}

async function loadSettings() {
  const res = await send({ type: "AUTH_STATE" });
  if (!res?.authenticated) return;
  const settings = await fetch("http://localhost:8000/api/v1/settings", {
    headers: { Authorization: `Bearer ${await getToken()}` },
  }).then((r) => r.json());
  state.settings = settings;
  applySettingsToUI();
}

function applySettingsToUI() {
  if (!state.settings) return;
  const s = state.settings;
  (document.getElementById("set-language") as HTMLSelectElement).value = s.language;
  (document.getElementById("set-mode") as HTMLSelectElement).value = s.autofill_mode;
  (document.getElementById("set-limit") as HTMLInputElement).value = String(s.llm_daily_limit);
  (document.getElementById("set-provider") as HTMLSelectElement).value = s.llm_provider;
  (document.getElementById("set-model") as HTMLInputElement).value = s.llm_model;
  (document.getElementById("set-ollama") as HTMLInputElement).value = s.ollama_base_url ?? "";
  (document.getElementById("set-endpoint") as HTMLInputElement).value = s.custom_endpoint ?? "";
  (document.getElementById("set-key-status") as HTMLElement).textContent =
    s.llm_api_key_set ? "(set)" : "";
  (document.getElementById("set-email-display") as HTMLElement).textContent =
    `Signed in as: ${state.email ?? "—"}`;
  // Toggle conditional fields
  const ollamaVisible = s.llm_provider === "ollama";
  const customVisible = s.llm_provider === "custom";
  document.getElementById("field-ollama-url")?.classList.toggle("hidden", !ollamaVisible);
  document.getElementById("field-custom-endpoint")?.classList.toggle("hidden", !customVisible);
  (document.getElementById("user-email") as HTMLElement).textContent =
    state.email?.split("@")[0] ?? "there";
}

async function getToken(): Promise<string> {
  const stored = await chrome.storage.session.get("accessToken");
  return stored.accessToken ?? "";
}

// ---------- EVENTS ----------
function wireEvents() {
  // Login
  document.getElementById("login-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = (document.getElementById("email") as HTMLInputElement).value;
    const password = (document.getElementById("password") as HTMLInputElement).value;
    const btn = (e.target as HTMLFormElement).querySelector("button[type=submit]") as HTMLButtonElement;
    btn.disabled = true;
    const res = await send({ type: "AUTH_LOGIN", email, password });
    btn.disabled = false;
    if (res?.ok) {
      state.authenticated = true;
      state.email = email;
      await loadSettings();
      showView("main");
      toast("Signed in", "ok");
    } else {
      toast(res?.error ?? "Login failed", "err");
    }
  });

  // Main -> Settings
  document.getElementById("goto-settings")?.addEventListener("click", () => {
    showView("settings");
    activateTab("general");
  });

  // Settings -> Back
  document.getElementById("settings-back")?.addEventListener("click", () => {
    showView(state.fillSession ? "fill" : "main");
  });

  // Tabs
  for (const t of document.querySelectorAll<HTMLElement>(".tab")) {
    t.addEventListener("click", () => activateTab(t.dataset.tab as any));
  }

  // Provider change -> show/hide conditional fields
  document.getElementById("set-provider")?.addEventListener("change", (e) => {
    const v = (e.target as HTMLSelectElement).value;
    document.getElementById("field-ollama-url")?.classList.toggle("hidden", v !== "ollama");
    document.getElementById("field-custom-endpoint")?.classList.toggle("hidden", v !== "custom");
  });

  // Save general settings
  document.getElementById("set-language")?.addEventListener("change", () => saveSettings());
  document.getElementById("set-mode")?.addEventListener("change", () => saveSettings());
  document.getElementById("set-limit")?.addEventListener("change", () => saveSettings());

  // Save LLM settings
  document.getElementById("set-save-llm")?.addEventListener("click", () => saveLLMSettings());

  // Test connection
  document.getElementById("set-test")?.addEventListener("click", async () => {
    const out = document.getElementById("set-test-result")!;
    out.textContent = "Testing...";
    const token = await getToken();
    const res = await fetch("http://localhost:8000/api/v1/settings/llm/test", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    out.textContent = data.ok ? "✓ " + data.message : "✗ " + data.message;
    out.style.color = data.ok ? "#047857" : "#b91c1c";
  });

  // Logout
  document.getElementById("set-logout")?.addEventListener("click", async () => {
    await send({ type: "AUTH_LOGOUT" });
    state.authenticated = false;
    state.email = null;
    state.settings = null;
    showView("login");
    toast("Signed out", "ok");
  });

  // Fill apply
  document.getElementById("fill-apply")?.addEventListener("click", async () => {
    if (!state.fillSession) return;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) return;
    await chrome.tabs.sendMessage(tab.id, {
      type: "APPLY_MAPPING",
      mapping: state.fillSession.mapping,
    });
    toast("Applied to page", "ok");
    showView("main");
  });

  // Fill cancel
  document.getElementById("fill-cancel")?.addEventListener("click", () => {
    state.fillSession = null;
    showView("main");
  });

  // Footer help
  document.getElementById("footer-help")?.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: "http://localhost:8000/docs" });
  });
}

async function saveSettings() {
  const patch = {
    language: (document.getElementById("set-language") as HTMLSelectElement).value,
    autofill_mode: (document.getElementById("set-mode") as HTMLSelectElement).value,
    llm_daily_limit: parseInt((document.getElementById("set-limit") as HTMLInputElement).value, 10),
  };
  const token = await getToken();
  const res = await fetch("http://localhost:8000/api/v1/settings", {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(patch),
  });
  if (res.ok) {
    state.settings = await res.json();
    flashStatus("Saved", "ok");
  } else {
    flashStatus("Save failed", "err");
  }
}

async function saveLLMSettings() {
  const patch: any = {
    llm_provider: (document.getElementById("set-provider") as HTMLSelectElement).value,
    llm_model: (document.getElementById("set-model") as HTMLInputElement).value,
  };
  const key = (document.getElementById("set-key") as HTMLInputElement).value;
  if (key) patch.llm_api_key = key;
  const ollama = (document.getElementById("set-ollama") as HTMLInputElement).value;
  if (ollama) patch.ollama_base_url = ollama;
  const endpoint = (document.getElementById("set-endpoint") as HTMLInputElement).value;
  if (endpoint) patch.custom_endpoint = endpoint;
  const token = await getToken();
  const res = await fetch("http://localhost:8000/api/v1/settings", {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(patch),
  });
  if (res.ok) {
    state.settings = await res.json();
    applySettingsToUI();
    (document.getElementById("set-key") as HTMLInputElement).value = "";
    flashStatus("Saved", "ok");
  } else {
    const body = await res.json().catch(() => ({}));
    flashStatus(body.message ?? "Save failed", "err");
  }
}

function flashStatus(text: string, kind: "ok" | "err") {
  const el = document.getElementById("settings-status")!;
  el.textContent = text;
  el.style.color = kind === "ok" ? "#047857" : "#b91c1c";
  setTimeout(() => {
    el.textContent = "Saved";
    el.style.color = "";
  }, 2000);
}

// ---------- FILL SESSION ----------
async function startFillSession(forms: any[]) {
  // For v1: simplified — show a single-form preview
  const form = forms[0];
  state.fillSession = {
    domain: form.domain,
    fields: form.fields,
    mapping: {} as Record<string, any>,
  };
  state.fields = form.fields;
  showView("fill");
  (document.getElementById("fill-domain") as HTMLElement).textContent = form.domain;

  const list = document.getElementById("fill-list")!;
  list.innerHTML = form.fields
    .map(
      (f: any) =>
        `<div class="field-row" data-id="${f.field_id}">
          <span class="name">${escapeHtml(f.label || f.name || f.id)}</span>
          <span class="badge skip" data-status>pending</span>
        </div>`,
    )
    .join("");

  // Open WebSocket to backend
  const token = await getToken();
  if (!token) {
    toast("Please sign in first", "err");
    showView("main");
    return;
  }
  const ws = new WebSocket(`ws://localhost:8000/ws/fill?token=${encodeURIComponent(token)}`);
  ws.onopen = () => {
    ws.send(
      JSON.stringify({
        type: "FILL_REQUEST",
        url_hash: "local",
        domain: form.domain,
        fields: form.fields,
      }),
    );
  };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "FILL_PROGRESS") {
      const row = list.querySelector(`[data-id="${msg.field_id}"]`);
      if (row) {
        const badge = row.querySelector("[data-status]")!;
        badge.className = `badge ${msg.status}`;
        badge.textContent = msg.status;
      }
      updateProgress();
    } else if (msg.type === "FILL_COMPLETE") {
      state.fillSession.mapping = msg.mapping;
      (document.getElementById("fill-apply") as HTMLButtonElement).disabled = false;
      flashSummary(`Ready — ${Object.keys(msg.mapping).length} fields resolved`);
      ws.close();
    }
  };
  ws.onerror = () => {
    toast("Cannot reach backend", "err");
  };
  ws.onclose = () => {};
}

function updateProgress() {
  const total = state.fields.length;
  const resolved = state.fields.filter((f: any) => {
    const row = document.querySelector(`[data-id="${f.field_id}"]`);
    const badge = row?.querySelector("[data-status]") as HTMLElement | null;
    return badge && !["pending", "skipped", "error"].includes(badge.textContent ?? "");
  }).length;
  const pct = total > 0 ? Math.round((resolved / total) * 100) : 0;
  (document.getElementById("fill-progress") as HTMLElement).style.width = `${pct}%`;
  (document.getElementById("fill-summary") as HTMLElement).textContent =
    `Resolving ${resolved} / ${total} fields…`;
}

function flashSummary(text: string) {
  (document.getElementById("fill-summary") as HTMLElement).textContent = text;
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

boot().catch((e) => {
  console.error("boot error", e);
  toast("Init error: " + (e as Error).message, "err");
});
