# CVApplier

Auto-fill job application forms on any website. FastAPI backend + Chrome extension (MV3) with local heuristics, embeddings, and LLM fallback.

## Architecture

```
+------------------+       +----------------------+
|  Chrome Ext      |       |  FastAPI Backend     |
|  (Svelte 5)      | <---> |  (Python 3.12)       |
|                  |  WS   |                      |
|  - local engine  |       |  - mapping service   |
|  - banner (SDOM) |       |  - LLM gateway       |
|  - popup (UI)    |       |  - learning service  |
+------------------+       +----------------------+
                                       |
                                       v
                                +--------------+
                                |  MongoDB 7   |
                                +--------------+
                                +--------------+
                                |  S3/MinIO    |
                                |  (CV files)  |
                                +--------------+
```

Full design: `docs/superpowers/specs/2026-06-17-cvapplier-design.md`
Backend plan: `docs/superpowers/plans/2026-06-17-cvapplier-backend.md`

## Components

- `backend/` — FastAPI + Beanie + LiteLLM. See `backend/README.md`.
- `extension/` — WXT + Svelte 5 + TypeScript. See `extension/README.md`.
- `docs/` — Specs, plans, ADRs.

## Local development (quick start)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env: set MONGO_URI, S3_*, JWT_SECRET, FERNET_KEY, CV_MASTER_KEY
docker run -d --name cv-mongo -p 27017:27017 mongo:7
docker run -d --name cv-minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address :9001
uvicorn cvapplier.main:app --reload --port 8000
```

### Extension

```bash
cd extension
npm install
npm run dev
# Load unpacked in chrome://extensions -> .output/chrome-mv3
```

## Status

This is an early-stage build. See `STATUS.md` for what is implemented and what remains.
