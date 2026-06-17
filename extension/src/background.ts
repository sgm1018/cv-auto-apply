/// <reference types="chrome"/>
import type { Message, Profile, Settings } from "./types.js";

const API_BASE = "http://localhost:8000";
const SIDEBAR_WIDTH = 420;

let accessToken: string | null = null;
let refreshToken: string | null = null;
let cachedProfile: Profile | null = null;
let cachedSettings: Settings | null = null;

async function openSidebar(pendingFill = false) {
  if (pendingFill) {
    await chrome.storage.session.set({ pendingFill: true });
  }
  // Close any existing popup window first
  const existing = await chrome.windows.getAll({ windowTypes: ["popup"] });
  for (const w of existing) {
    try { await chrome.windows.remove(w.id!); } catch { /* ignore */ }
  }
  // Get screen dimensions from the last focused (main) window
  let w = 1024;
  let h = 900;
  let l = 0;
  try {
    const main = await chrome.windows.getLastFocused();
    w = main.width ?? 1024;
    h = main.height ?? 900;
    l = main.left ?? 0;
  } catch { /* use defaults */ }
  chrome.windows.create({
    url: chrome.runtime.getURL("popup.html"),
    type: "popup",
    width: SIDEBAR_WIDTH,
    height: h,
    top: 0,
    left: l + w - SIDEBAR_WIDTH,
    focused: true,
  });
}

// Extension icon clicked → open sidebar
chrome.action.onClicked.addListener(() => {
  void openSidebar(false);
});

async function loadTokens() {
  const stored = await chrome.storage.session.get(["accessToken", "refreshToken"]);
  accessToken = stored.accessToken ?? null;
  refreshToken = stored.refreshToken ?? null;
}

async function saveTokens() {
  await chrome.storage.session.set({ accessToken, refreshToken });
}

async function apiFetch<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  if (!accessToken) await loadTokens();
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (!headers.has("Content-Type") && init.body && typeof init.body === "string") {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (res.status === 401 && refreshToken) {
    await refreshAccessToken();
    return apiFetch(path, init);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.message ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function refreshAccessToken(): Promise<void> {
  if (!refreshToken) throw new Error("No refresh token");
  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) throw new Error("Refresh failed");
  const data = await res.json();
  accessToken = data.access_token;
  refreshToken = data.refresh_token;
  await saveTokens();
}

async function getSettings(): Promise<Settings> {
  cachedSettings = await apiFetch<Settings>("/api/v1/settings");
  return cachedSettings;
}

async function getProfile(): Promise<Profile | null> {
  try {
    cachedProfile = await apiFetch<Profile>("/api/v1/profile");
    return cachedProfile;
  } catch (e) {
    if ((e as Error).message.includes("404")) return null;
    throw e;
  }
}

async function patchSettings(patch: Partial<Settings>): Promise<Settings> {
  cachedSettings = await apiFetch<Settings>("/api/v1/settings", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
  return cachedSettings;
}

// Message router
chrome.runtime.onMessage.addListener((msg: Message, _sender, sendResponse) => {
  (async () => {
    try {
      switch (msg.type) {
        case "AUTH_LOGIN": {
          const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: msg.email, password: msg.password }),
          });
          if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw new Error(body.message ?? "Login failed");
          }
          const data = await res.json();
          accessToken = data.access_token;
          refreshToken = data.refresh_token;
          await saveTokens();
          sendResponse({ ok: true, user_id: data.user_id });
          break;
        }
        case "AUTH_LOGOUT": {
          await chrome.storage.session.clear();
          accessToken = null;
          refreshToken = null;
          cachedProfile = null;
          cachedSettings = null;
          sendResponse({ ok: true });
          break;
        }
        case "AUTH_STATE": {
          await loadTokens();
          if (!accessToken) {
            sendResponse({ authenticated: false });
            return;
          }
          try {
            const me = await apiFetch<{ user_id: string; email: string; language: string }>("/api/v1/auth/me");
            sendResponse({ authenticated: true, ...me });
          } catch {
            sendResponse({ authenticated: false });
          }
          break;
        }
        case "SETTINGS_UPDATE": {
          const settings = await patchSettings(msg.patch);
          sendResponse({ ok: true, settings });
          break;
        }
        case "PROFILE_UPDATED": {
          cachedProfile = null;
          sendResponse({ ok: true });
          break;
        }
        case "TRIGGER_FILL": {
          // Banner button clicked → open sidebar with fill signal
          void openSidebar(true);
          sendResponse({ ok: true });
          break;
        }
        case "PENDING_FILL_CHECK": {
          const stored = await chrome.storage.session.get("pendingFill");
          if (stored.pendingFill) {
            await chrome.storage.session.remove("pendingFill");
            sendResponse({ pending: true });
          } else {
            sendResponse({ pending: false });
          }
          break;
        }
        default:
          sendResponse({ ok: false, error: "unknown message" });
      }
    } catch (e) {
      sendResponse({ ok: false, error: (e as Error).message });
    }
  })();
  return true; // async response
});

chrome.runtime.onInstalled.addListener(() => {
  console.log("[CVApplier] extension installed");
});
