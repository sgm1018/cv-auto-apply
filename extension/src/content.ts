/// <reference types="chrome" />
import type { ExtractedField, FieldValue } from "./types.js";

const API_BASE = "http://localhost:8000";
const BANNER_ID = "__cvapplier_banner__";

interface FormDetection {
  form: HTMLElement;
  fields: ExtractedField[];
  detectedAt: number;
}

const FIELD_HINTS = [
  "name", "email", "phone", "resume", "cv", "first name", "last name",
  "nombre", "apellido", "apellidos", "correo", "telefono", "teléfono",
  "linkedin", "github", "portfolio", "location", "address", "dirección",
  "direccion", "ciudad", "pais", "país", "country", "city",
];

const FORM_LIKE_ATTRS = /form|application|apply|questionnaire/i;
const FORM_LIKE_TAGS = new Set(["div", "section", "article", "fieldset", "main", "aside", "form"]);

// ── Detection ──────────────────────────────────────────────────────

function detectForms(): FormDetection[] {
  const out: FormDetection[] = [];

  // Strategy 1: native <form> elements
  for (const form of document.querySelectorAll<HTMLFormElement>("form")) {
    if (form.dataset.cvapplierSeen) continue;
    const fields = extractFields(form);
    if (shouldSuggest(fields)) {
      form.dataset.cvapplierSeen = "1";
      out.push({ form, fields, detectedAt: Date.now() });
    }
  }

  // Strategy 2: SPA containers that look like forms (no <form> tag)
  for (const container of findFormContainers()) {
    if (container.dataset.cvapplierSeen) continue;
    if (container.tagName === "FORM") continue; // already handled above
    const fields = extractFields(container);
    if (shouldSuggest(fields)) {
      container.dataset.cvapplierSeen = "1";
      out.push({ form: container, fields, detectedAt: Date.now() });
    }
  }

  return out;
}

function findFormContainers(): HTMLElement[] {
  const inputs = document.querySelectorAll<HTMLElement>(
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="image"]), select, textarea',
  );
  if (inputs.length < 3) return [];

  const groups = new Map<HTMLElement, HTMLElement[]>();
  for (const el of inputs) {
    const container = findFormAncestor(el);
    if (!container) continue;
    if (!groups.has(container)) groups.set(container, []);
    groups.get(container)!.push(el);
  }

  return Array.from(groups.entries())
    .filter(([, els]) => els.length >= 3)
    .map(([c]) => c);
}

function findFormAncestor(el: HTMLElement): HTMLElement | null {
  let cur: HTMLElement | null = el.parentElement;
  while (cur && cur !== document.body && cur !== document.documentElement) {
    if (
      (cur.dataset.formId) ||
      (cur.dataset.testid && /form/i.test(cur.dataset.testid)) ||
      (cur.getAttribute("role") === "form") ||
      (cur.className && typeof cur.className === "string" && FORM_LIKE_ATTRS.test(cur.className)) ||
      (cur.id && FORM_LIKE_ATTRS.test(cur.id))
    ) {
      return cur;
    }
    cur = cur.parentElement;
  }
  // Fallback: closest block-level ancestor with ≥ 3 visible inputs
  cur = el.parentElement;
  while (cur && cur !== document.body && cur !== document.documentElement) {
    if (FORM_LIKE_TAGS.has(cur.tagName.toLowerCase())) {
      const childInputs = cur.querySelectorAll<HTMLElement>(
        'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="image"]), select, textarea',
      );
      if (childInputs.length >= 3) return cur;
    }
    cur = cur.parentElement;
  }
  return null;
}

function shouldSuggest(fields: ExtractedField[]): boolean {
  if (fields.length < 3) return false;
  for (const f of fields) {
    const hay = `${f.label ?? ""} ${f.name ?? ""} ${f.placeholder ?? ""}`.toLowerCase();
    if (FIELD_HINTS.some((h) => hay.includes(h))) return true;
  }
  return false;
}

function extractFields(root: HTMLElement): ExtractedField[] {
  const out: ExtractedField[] = [];
  const seenRadioGroups = new Set<string>();
  let idx = 0;

  for (const el of root.querySelectorAll<HTMLElement>("input, select, textarea")) {
    if ((el as HTMLInputElement).type === "hidden") continue;
    if ((el as HTMLInputElement).type === "submit") continue;

    // Radio buttons: group by name, emit one field with options
    if ((el as HTMLInputElement).type === "radio") {
      const radioName = (el as HTMLInputElement).name;
      if (!radioName || seenRadioGroups.has(radioName)) continue;
      seenRadioGroups.add(radioName);
      const allRadios = root.querySelectorAll<HTMLInputElement>(`input[type="radio"][name="${cssEscape(radioName)}"]`);
      const label = resolveLabel(el);
      const options: Array<{ value: string; label: string }> = [];
      for (const r of allRadios) {
        const rLabel = resolveLabel(r) ?? r.value ?? "";
        options.push({ value: r.value, label: rLabel });
      }
      out.push({
        field_id: `name:${radioName}`,
        tag: "select",
        type: "radio",
        label: label ?? undefined,
        placeholder: undefined,
        required: el.getAttribute("required") !== null,
        options,
      });
      continue;
    }

    const label = resolveLabel(el);
    const fieldOptions = el instanceof HTMLSelectElement ? extractSelectOptions(el) : undefined;
    out.push({
      field_id: stableId(el, idx++),
      tag: el.tagName.toLowerCase() === "input" ? "input" : (el.tagName.toLowerCase() as any),
      type: (el as HTMLInputElement).type ?? undefined,
      name: (el as HTMLInputElement).name || undefined,
      id: el.id || undefined,
      label: label ?? undefined,
      placeholder: (el as HTMLInputElement).placeholder || undefined,
      required: (el as HTMLInputElement).required || false,
      options: fieldOptions,
      current_value: (el as HTMLInputElement).value || undefined,
    });
  }
  return out;
}

function extractSelectOptions(el: HTMLSelectElement): Array<{ value: string; label: string }> | undefined {
  if (el.tagName !== "SELECT" || !el.options || el.options.length === 0) return undefined;
  const opts: Array<{ value: string; label: string }> = [];
  for (const opt of el.options) {
    if (opt.value) opts.push({ value: opt.value, label: opt.textContent?.trim() || opt.value });
  }
  return opts.length > 0 ? opts : undefined;
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
function showBanner(_form: HTMLElement) {
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
    void triggerFill();
    hideBanner();
  });
  shadow.querySelector("#skip")?.addEventListener("click", hideBanner);
}

function hideBanner() {
  document.getElementById(BANNER_ID)?.remove();
}

async function triggerFill() {
  try {
    await chrome.runtime.sendMessage({ type: "TRIGGER_FILL" });
  } catch {
    // Fallback: try direct openPopup
    try { await chrome.action.openPopup(); } catch { /* ignore */ }
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
    let meta: Record<string, unknown> | null = null;
    if (typeof entry === "object" && entry !== null && "value" in (entry as object)) {
      raw = (entry as { value: unknown }).value;
    } else if (typeof entry === "object" && entry !== null) {
      raw = null;
      meta = entry as Record<string, unknown>;
    } else {
      raw = entry;
    }
    // Handle file (CV) fields
    if (meta && meta["__type"] === "cv_file" && el instanceof HTMLInputElement && el.type === "file") {
      try {
        const result = await chrome.runtime.sendMessage({
          type: "FETCH_CV_FILE",
          url: meta["url"] as string,
          filename: meta["filename"] as string,
          mimeType: meta["mime_type"] as string,
        });
        if (result && result.ok && result.base64) {
          const binary = atob(result.base64);
          const bytes = new Uint8Array(binary.length);
          for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
          }
          const file = new File([bytes], result.filename, { type: result.mimeType });
          const dt = new DataTransfer();
          dt.items.add(file);
          el.files = dt.files;
          el.dispatchEvent(new Event("change", { bubbles: true }));
        }
      } catch (_e) {
        // file download failed, skip
      }
      continue;
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
  // Polling fallback for slow SPAs that render in stages (1s, 2s, 4s, 8s)
  [1000, 2000, 4000, 8000].forEach((ms) => {
    setTimeout(() => {
      const found = detectForms();
      if (found.length > 0) {
        detectedForms.push(...found);
        showBanner(found[0].form);
      }
    }, ms);
  });
}

init();
