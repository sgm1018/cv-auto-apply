/// <reference types="chrome" />
import type { ExtractedField, FieldValue } from "./types.js";

const API_BASE = "http://localhost:8000";
const BANNER_ID = "__cvapplier_banner__";

interface FormDetection {
  form: HTMLFormElement;
  fields: ExtractedField[];
  detectedAt: number;
}

// Detect form on page
function detectForms(): FormDetection[] {
  const out: FormDetection[] = [];
  for (const form of document.querySelectorAll<HTMLFormElement>("form")) {
    if (form.dataset.cvapplierSeen) continue;
    const fields = extractFields(form);
    if (shouldSuggest(fields)) {
      form.dataset.cvapplierSeen = "1";
      out.push({ form, fields, detectedAt: Date.now() });
    }
  }
  return out;
}

function shouldSuggest(fields: ExtractedField[]): boolean {
  if (fields.length < 3) return false;
  // Heuristic: at least one field whose label/type hints at a job-application concept
  const hints = ["name", "email", "phone", "resume", "cv", "first name", "last name", "nombre", "correo", "telefono", "linkedin"];
  for (const f of fields) {
    const hay = `${f.label ?? ""} ${f.name ?? ""} ${f.placeholder ?? ""}`.toLowerCase();
    if (hints.some((h) => hay.includes(h))) return true;
  }
  return false;
}

function extractFields(form: HTMLFormElement): ExtractedField[] {
  const out: ExtractedField[] = [];
  let idx = 0;
  for (const el of form.querySelectorAll<HTMLElement>("input, select, textarea")) {
    if ((el as HTMLInputElement).type === "hidden") continue;
    if ((el as HTMLInputElement).type === "submit") continue;
    const label = resolveLabel(el);
    out.push({
      field_id: stableId(el, idx++),
      tag: el.tagName.toLowerCase() === "input" ? "input" : (el.tagName.toLowerCase() as any),
      type: (el as HTMLInputElement).type ?? undefined,
      name: (el as HTMLInputElement).name || undefined,
      id: el.id || undefined,
      label: label ?? undefined,
      placeholder: (el as HTMLInputElement).placeholder || undefined,
      required: (el as HTMLInputElement).required || false,
      current_value: (el as HTMLInputElement).value || undefined,
    });
  }
  return out;
}

function stableId(el: HTMLElement, idx: number): string {
  if (el.id) return `id:${el.id}`;
  if ((el as HTMLInputElement).name) return `name:${(el as HTMLInputElement).name}`;
  return `idx:${idx}`;
}

function resolveLabel(el: HTMLElement): string | null {
  // 1. <label for="id">
  if (el.id) {
    const lab = document.querySelector(`label[for="${cssEscape(el.id)}"]`);
    if (lab?.textContent) return lab.textContent.trim();
  }
  // 2. parent <label>
  let p: HTMLElement | null = el.parentElement;
  while (p) {
    if (p.tagName === "LABEL" && p.textContent) return p.textContent.trim();
    p = p.parentElement;
  }
  // 3. aria-label
  const aria = el.getAttribute("aria-label");
  if (aria) return aria;
  // 4. placeholder
  const ph = el.getAttribute("placeholder");
  if (ph) return ph;
  return null;
}

function cssEscape(s: string): string {
  return (window.CSS && CSS.escape) ? CSS.escape(s) : s.replace(/"/g, '\\"');
}

// Mount in-page banner
function showBanner(form: HTMLFormElement) {
  if (document.getElementById(BANNER_ID)) return;
  const host = document.createElement("div");
  host.id = BANNER_ID;
  host.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 2147483647;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  `;
  const shadow = host.attachShadow({ mode: "open" });
  shadow.innerHTML = `
    <style>
      :host { all: initial; }
      .card {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 20px; border-radius: 14px;
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #3b82f6 100%);
        color: white; box-shadow: 0 12px 36px rgba(37,99,235,0.45), 0 2px 8px rgba(0,0,0,0.12);
        animation: slideIn 0.5s cubic-bezier(0.16,1,0.3,1);
      }
      @keyframes slideIn {
        from { transform: translateY(20px) scale(0.96); opacity: 0; }
        to { transform: translateY(0) scale(1); opacity: 1; }
      }
      .icon {
        width: 36px; height: 36px; border-radius: 50%;
        background: rgba(255,255,255,0.15);
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
      }
      .text { font-size: 14px; line-height: 1.3; }
      .title { font-weight: 600; font-size: 15px; }
      .sub { opacity: 0.85; font-size: 12px; margin-top: 2px; }
      button {
        appearance: none; border: none; cursor: pointer; padding: 8px 14px;
        border-radius: 8px; font-size: 13px; font-weight: 600;
        transition: transform 0.15s ease;
      }
      button:hover { transform: translateY(-1px); }
      .primary { background: white; color: #1e40af; }
      .ghost { background: rgba(255,255,255,0.15); color: white; }
    </style>
    <div class="card">
      <div class="icon">CV</div>
      <div class="text">
        <div class="title">CVApplier ready</div>
        <div class="sub">Form detected — review and apply in one click</div>
      </div>
      <button class="primary" id="apply">Review & Apply</button>
      <button class="ghost" id="skip">Skip</button>
    </div>
  `;
  document.documentElement.appendChild(host);
  shadow.querySelector("#apply")?.addEventListener("click", () => {
    void openPopup();
    hideBanner();
  });
  shadow.querySelector("#skip")?.addEventListener("click", hideBanner);
}

function hideBanner() {
  document.getElementById(BANNER_ID)?.remove();
}

async function openPopup() {
  try {
    await chrome.action.openPopup();
  } catch {
    // openPopup not always available; user can click the icon manually
  }
}

// React-controlled input injection
function setReactValue(el: HTMLInputElement | HTMLTextAreaElement, value: string) {
  const proto = Object.getPrototypeOf(el) as object;
  const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
  setter?.call(el, value);
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
}

async function autofillFromMapping(mapping: Record<string, unknown>) {
  for (const el of document.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
    "input, textarea, select",
  )) {
    const key = el.id ? `id:${el.id}` : el.name ? `name:${el.name}` : null;
    if (!key) continue;
    const entry = mapping[key];
    if (entry === null || entry === undefined) continue;
    // Accept both shapes: flat value string OR object { value, source }
    let raw: unknown;
    if (typeof entry === "object" && entry !== null && "value" in (entry as object)) {
      raw = (entry as { value: unknown }).value;
    } else {
      raw = entry;
    }
    if (raw === null || raw === undefined || raw === "") continue;
    const value = String(raw);
    if (el instanceof HTMLSelectElement) {
      el.value = value;
      el.dispatchEvent(new Event("change", { bubbles: true }));
    } else {
      setReactValue(el as HTMLInputElement | HTMLTextAreaElement, value);
    }
  }
}

// Bootstrap
const detectedForms: FormDetection[] = [];

function debounce<T extends (...args: never[]) => unknown>(fn: T, ms: number): T {
  let t: ReturnType<typeof setTimeout> | null = null;
  return ((...args: never[]) => {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  }) as T;
}

// Message handler: popup asks to apply a mapping
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "APPLY_MAPPING") {
    void autofillFromMapping((msg.mapping ?? {}) as Record<string, unknown>);
    sendResponse({ ok: true });
    return true;
  }
  if (msg?.type === "GET_FORMS") {
    const forms = detectedForms.map((d) => ({
      domain: window.location.hostname,
      fields: d.fields,
    }));
    sendResponse({ forms });
    return true;
  }
  return false;
});

function init() {
  detectedForms.push(...detectForms());
  for (const d of detectedForms) showBanner(d.form);
  new MutationObserver(
    debounce(() => {
      const found = detectForms();
      if (found.length > 0) {
        detectedForms.push(...found);
        showBanner(found[0].form);
      }
    }, 500),
  ).observe(document.body, { childList: true, subtree: true });
}

init();
