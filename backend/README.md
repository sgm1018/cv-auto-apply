# SmartCVapply Backend

FastAPI + MongoDB + S3 + LiteLLM backend for the SmartCVapply Chrome extension.

## Quick start

```bash
# 1. Create venv
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. Install
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# Edit .env: set JWT_SECRET, FERNET_KEY, CV_MASTER_KEY to real values

# 4. Run MongoDB and MinIO (Docker required)
docker run -d --name cv-mongo -p 27017:27017 mongo:7
docker run -d --name cv-minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address :9001

# 5. Run the API
uvicorn smartcvapply.main:app --reload --port 8000

# 6. (Optional) Seed the learned_mappings catalog
python -m scripts.seed_learned_mappings
```

## Layout

```
src/smartcvapply/
  core/          # config, security, db, storage, exceptions, logging, rate limit, deps
  models/        # Beanie Documents (User, Profile, CV, LearnedMapping, FillSession, FeedbackEvent)
  schemas/       # Pydantic DTOs, one per file
  repositories/  # Mongo data access
  services/      # use cases and orchestration (auth, profile, settings, mapping, llm, cv)
  api/v1/        # HTTP controllers (one per domain)
  workers/       # background jobs (cv_parser, learning)
scripts/         # one-off scripts (seed)
tests/           # pytest suite
```

## Layering rules

```
HTTP -> controller (parse, validate, return DTO)
     -> service (use case, orchestration, transactions)
     -> repository (Mongo / S3 access only)
     -> model
```

Controllers contain no business logic. Services contain no HTTP types. Repositories contain no business logic.

## Endpoints

| Method | Path | Auth |
|---|---|---|
| POST | `/api/v1/auth/register` | — |
| POST | `/api/v1/auth/login` | — |
| POST | `/api/v1/auth/refresh` | refresh |
| POST | `/api/v1/auth/logout` | user |
| GET | `/api/v1/auth/me` | user |
| GET/PUT/PATCH | `/api/v1/profile` | user |
| POST/GET | `/api/v1/cvs` | user |
| GET/DELETE/PATCH | `/api/v1/cvs/{id}` | user |
| GET | `/api/v1/settings` | user |
| PATCH | `/api/v1/settings` | user |
| POST | `/api/v1/settings/llm/test` | user |
| GET | `/api/v1/mappings/learned` | user |
| POST | `/api/v1/feedback/batch` | user |
| GET | `/api/v1/sessions` | user |
| GET | `/api/v1/sessions/{id}` | user |
| GET | `/api/v1/users/me/export` | user |
| DELETE | `/api/v1/users/me` | user |
| WS | `/ws/fill?token=...` | access JWT |
| GET | `/health` | — |
| GET | `/metrics` | — |

## Tests

```bash
pytest -v
```
