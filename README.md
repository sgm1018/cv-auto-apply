# SmartCVapply
<div align="center">
  <img width="120" height="120" alt="SmartCVapply logo" src="QuickApply_logo.png" />
</div>

<!-- DEMO VIDEO -->
<!--
  Replace with your screen recording link:
  https://github.com/user-attachments/assets/your-demo-video-id
-->
<p align="center">
  <strong>Auto-fill job applications with one keystroke.</strong><br />
  <em>Local heuristics · Embeddings · LLM fallback</em>
</p>

**Stop copy-pasting your CV into every application form.**

SmartCVapply is a Chrome extension backed by a Python API that detects job application forms on any website, maps every field to your profile data using a multi-stage resolution engine, and fills them automatically. You review before it applies.

Free. Open source. MIT licensed.

[Download for Chrome](https://chrome.google.com/webstore) · [View Source on GitHub](https://github.com/sgm1018/cv-auto-apply)

---

## What Is SmartCVapply?

Instead of showing you another empty form, SmartCVapply detects the form the moment you open it, resolves every field — first name, email, phone, LinkedIn, GitHub, skills, work history — against your stored profile and learned patterns, and presents a complete preview. You click Apply. It fills.

![Form detection and preview](docs/branding/screenshots/form-detected.svg)

---

## The Problem

Job applications are repetitive. Every platform — Greenhouse, Lever, Ashby, Workday, LinkedIn, and hundreds of custom ATS — asks for the same information but names fields differently, structures them in unique layouts, and often hides them inside SPAs with no `<form>` tag.

| Problem | What Happens |
|---|---|
| Manual repetition | Typing name, email, phone, LinkedIn, GitHub, skills into identical fields across 20+ tabs. |
| Inconsistent field naming | "First Name", "given-name", "fname", "nombre" — every site invents its own convention. |
| SPA complexity | React apps like AshbyHQ store form definitions in `window.__appData` — no `<form>` HTML element to detect. |
| CV re-upload | "Attach your CV" means finding the file, uploading it, and hoping the ATS parses it correctly every single time. |
| Language switching | English forms and Spanish forms require the same data — but the field names are completely different. |

SmartCVapply solves this with a **multi-stage resolution engine** that combines learned mappings, heuristic keyword matching (with English + Spanish support + accent normalization), an LLM gateway for ambiguous fields, and encrypted CV file relay — all from a keyboard-first popup.

---

## What Is It For?

Use SmartCVapply when you want to:

- Detect any job application form instantly, even inside SPAs.
- Preview every field the backend resolved before it touches the page.
- Trust that your CV file is uploaded automatically from encrypted storage — no digging for it.
- Store profile data once and reuse it across every application.
- Teach the system — corrections are learned and applied next time.
- Use your own LLM key (OpenAI, DeepSeek, Anthropic, Ollama) for fallback resolution on tricky fields.

![Field resolution preview](docs/branding/screenshots/fill-preview.svg)

---

## Features

### Multi-Stage Field Resolution

Every field goes through up to four stages until a value is found:

| Stage | Engine | Speed |
|---|---|---|
| 1 | Learned mappings (per-domain, per-user) | Instant |
| 2a | Local heuristic engine — 70+ keyword rules with accent normalization, word-boundary regex, and Spanish/English support | Instant |
| 2b | CV file sentinel — detects file inputs and auto-attaches the user's primary CV | Instant |
| 3 | Custom user answers (per field, per domain) | Instant |
| 4 | LLM fallback — configurable provider, daily limit, model selection | ~2–5s |

![Resolution pipeline](docs/branding/screenshots/resolution-pipeline.svg)

---

### Universal Form Detection

Two-strategy detection that works everywhere:

- **Native forms**: standard `<form>` elements with inputs, selects, radios, and textareas.
- **SPA containers**: detects form-like containers in React/Vue/Angular apps (AshbyHQ, Greenhouse, Lever) by scanning for common interaction patterns and polling for late-rendered fields.

![SPA form detection](docs/branding/screenshots/spa-detection.svg)

---

### Smart File Input Handling

When a form asks for a CV file, the backend detects the `type=file` input and sends back a signed URL pointing to the user's encrypted CV in Minio. The extension downloads it through the authenticated background script (no CORS issues) and sets it on the file input via `DataTransfer`. No manual file picking needed.

---

### Heuristic Engine With Accent Support

70+ keyword rules covering English and Spanish job application vocabulary:

```text
first_name, last_name, email, phone, linkedin_url, github_url,
portfolio_url, summary, skills, languages, location (city, region,
country, zip), address, full_name, cv_file, photo, salary,
availability, visa, gender, ethnicity, veteran, disability,
education, company, job_title, start_date, end_date, ...

Accent normalization: "teléfono" → "telefono", "dirección" → "direccion"
Word-boundary regex: "name" matches "Full Name" but NOT "surname"
```

---

### Keyboard-First Popup

The extension opens as a separate popup window (not `default_popup`) so it stays open while you interact with the page. Every action is one or two clicks away:

| Action | Flow |
|---|---|
| Detect form | Auto-detected on page load or manual "Scan" |
| Review fields | Popup shows every field with resolution source badge |
| Apply | One click fills every field and attaches the CV |
| Settings | API key, provider, model, profile data, CV management |

![Popup main view](docs/branding/screenshots/popup-main.svg)

---

### Onboarding Flow

New users go through a guided 3-step wizard:

1. **Set API key** — Test and save an LLM API key (encrypted at rest).
2. **Upload CV** — Upload a PDF/DOCX; the backend parses it and populates the profile.
3. **Review profile** — Confirm extracted personal info before applying.

Steps auto-detect completion and unlock the "Start applying" button.

![Onboarding flow](docs/branding/screenshots/onboarding.svg)

---

### Encrypted Storage

- **CV files** are encrypted with a user-derived key before being stored in Minio (S3-compatible). Decrypted on-the-fly during download.
- **API keys** are encrypted with a server-side Fernet key before being stored in MongoDB.
- **Profile data** is stored in a dedicated MongoDB collection, never shared.

---

### Configurable LLM Gateway

Bring your own model or provider:

| Provider | Default Model |
|---|---|
| DeepSeek | `deepseek-chat` |
| OpenAI | `gpt-4o-mini` |
| Anthropic | `claude-3-haiku` |
| Ollama (local) | Any local model |
| Custom endpoint | Any OpenAI-compatible API |

Daily call limits prevent runaway costs.

---

## Architecture

```
┌──────────────────────┐       ┌──────────────────────────┐
│   Chrome Extension   │       │    FastAPI Backend        │
│   (TypeScript)       │◄─────►│    (Python 3.12)          │
│                      │  WS   │                           │
│  content.ts          │       │  mapping_service.py       │
│  background.ts       │       │  heuristic_engine.py      │
│  popup.js            │       │  llm_service.py           │
│                      │       │  learning_service.py      │
└──────────────────────┘       │  onboarding_service.py    │
                               └───────────┬───────────────┘
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                       ┌──────────┐ ┌──────────┐ ┌──────────┐
                       │ MongoDB  │ │  Minio   │ │   LLM    │
                       │  (7)     │ │  (S3)    │ │ Provider │
                       └──────────┘ └──────────┘ └──────────┘
```

**Key services:**

| Service | Role |
|---|---|
| `heuristic_engine.py` | 70+ keyword rules, accent normalization, word-boundary regex, CV file sentinel |
| `mapping_service.py` | 4-stage cascade: learned → heuristics → custom → LLM |
| `llm_service.py` | Provider-agnostic gateway (LiteLLM) with daily limits |
| `learning_service.py` | Per-domain field mapping persistence |
| `onboarding_service.py` | Step tracking for new users |
| `profile_repository.py` | Profile upsert with nested model coercion |

---

## Quick Start

### Requirements

| Tool | Version |
|---|---|
| Python | 3.12+ |
| Node.js | 18+ |
| MongoDB | 7+ (Docker) |
| Minio | Latest (Docker) |

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env: set MONGO_URI, MINIO_*, JWT_SECRET, FERNET_KEY, CV_MASTER_KEY
```

Start infrastructure:

```bash
docker run -d --name cv-mongo -p 27017:27017 mongo:7
docker run -d --name cv-minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address :9001
```

Start the API:

```bash
uvicorn smartcvapply.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

### Extension

```bash
cd extension
npm install
npm run build
```

Load unpacked in `chrome://extensions` → point to `extension/dist/`.

### Verify

1. Open the extension popup.
2. Create an account.
3. Follow the onboarding wizard (API key → CV upload → profile review).
4. Navigate to any job application page (Greenhouse, Ashby, Lever, LinkedIn, etc.).
5. The popup detects the form automatically → click "Review and apply."

---

## Project Structure

```
smartcvapply/
├── backend/
│   ├── src/smartcvapply/
│   │   ├── api/v1/          # REST endpoints (auth, profile, cvs, settings, feedback)
│   │   ├── core/            # Config, security, Minio client
│   │   ├── models/          # Beanie ODM models (User, CV, Profile, etc.)
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic (heuristic, mapping, llm, learning, onboarding)
│   │   └── main.py          # FastAPI app factory
│   ├── tests/
│   └── pyproject.toml
├── extension/
│   ├── src/
│   │   ├── content.ts       # Form detection, field extraction, autofill
│   │   ├── background.ts    # Auth, file relay, tab management
│   │   └── types.ts         # Shared types
│   ├── popup.html           # Extension popup UI
│   ├── popup.js             # Popup logic
│   ├── manifest.json        # Chrome extension manifest
│   └── package.json
├── docs/
│   ├── branding/            # Logos, screenshots
│   └── superpowers/         # Design docs, specs, plans, ADRs
└── README.md
```

---

## Development

### Type checking

```bash
cd backend
mypy src/
```

### Linting

```bash
ruff check src/
```

### Tests

```bash
cd backend
pytest
```

### Extension watch mode

```bash
cd extension
npm run watch
```

---

## Status

This is an **active early-stage build**. See [`STATUS.md`](STATUS.md) for the current implementation state and roadmap.

---

## License

SmartCVapply is released under the **MIT License**.

Built by [@sgm1018](https://github.com/sgm1018).

## Star History

<a href="https://www.star-history.com/#sgm1018/cv-auto-apply&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=sgm1018/cv-auto-apply&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=sgm1018/cv-auto-apply&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=sgm1018/cv-auto-apply&type=Date" />
 </picture>
</a>
