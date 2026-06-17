# CVApplier — Status

Estado de la implementación actual. **Esta es la v0.1 funcional**, suficiente para validar el concepto end-to-end.

## ✅ Implementado y verificado

### Backend (`backend/`)
- **34/34 tests pasan** (`pytest` desde `backend/`)
- Smoke test en vivo: `POST /auth/register` → 200, `GET /auth/me` → 200, `PATCH /profile` → 200, `GET /profile` → 200
- Auth: register, login, refresh con rotation y reuse detection, logout, me
- Profile: get, patch, put
- Settings: get, patch (con cifrado Fernet de API keys, validación de modelos por provider)
- LLM Gateway: LiteLLM con DeepSeek (default), OpenAI, Anthropic, Ollama, custom
- Mapping Service: orquestador learned → heuristics → custom_answers → LLM con rate limit
- Heuristic engine: type-based + keyword (EN + ES)
- Mapping prompts: con defense contra prompt injection
- CVs: upload, list, get, download, set primary, delete (cifrado AES-256-GCM envelope)
- Sessions: list, detail
- Feedback: batch endpoint
- Users GDPR: export, hard delete con cascada
- WebSocket `/ws/fill` con cascade y progress streaming
- Workers: learning aggregation con promotion + decay, CV parser (stub)
- Health y metrics Prometheus
- Exception hierarchy con handler global

### Extensión (`extension/`)
- Manifest V3 con permisos correctos
- Build con esbuild → `dist/` listo para "Load unpacked"
- `typecheck` pasa (TypeScript strict)
- **UI popup con epic-design en azul** (6 depth layers, gradientes, sparkles, glassmorphism, animaciones GPU-only, `prefers-reduced-motion` safe)
- 4 vistas: Login, Main, Fill, Settings (con tabs)
- Banner in-page con Shadow DOM y estilos blue gradient
- Content script: detección de forms, extracción de campos, inyección con React controlled input bypass
- Background service worker: auth, message routing, token storage
- Iconos PNG azules (placeholders generados)
- WebSocket client hacia backend con progress en vivo

## ⏳ Pendiente (no bloquea el demo)

### v0.2
- CV parser real con `unstructured` + LLM structuring (hoy es stub)
- Local engine en la extensión: embeddings Transformers.js en WASM (hoy solo heuristics del backend)
- Nginx + certbot + Dockerfile de producción
- docker-compose.prod.yml
- E2E tests con Playwright contra portales reales (Greenhouse, Workday, Lever demo)
- Multi-CVs por usuario con auto-selección
- Cover letter generation con LLM

### v1.1+
- Field-level encryption en profile
- Redis rate limit (multi-instancia)
- Offscreen document para el modelo de embeddings
- OAuth login (Google, Microsoft)
- Email verification
- 2FA TOTP
- Firefox extension
- LinkedIn Easy Apply adapter

## 🚀 Cómo arrancar

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edita .env: JWT_SECRET (32+ chars), FERNET_KEY (Fernet.generate_key()), CV_MASTER_KEY (32 chars)
# Opcional: arranca Mongo y MinIO
docker run -d -p 27017:27017 --name cv-mongo mongo:7
docker run -d -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin minio/minio server /data --console-address :9001
uvicorn cvapplier.main:app --reload --port 8000
```

### Extensión
```bash
cd extension
npm install
npm run build
# Abre chrome://extensions, activa Developer mode, "Load unpacked" -> dist/
```

## 🎨 Diseño UI (epic-design, azul)

La popup aplica la **6-layer depth system** del skill `epic-design`:

- **depth-0**: gradient backdrop con 3 radial-gradients azules
- **depth-1**: 3 blobs con `filter: blur(40px)` y animación `drift` 18s
- **depth-2**: grid sutil enmascarado
- **depth-3**: contenido principal con glassmorphism (`backdrop-filter: blur(20px)`)
- **depth-4**: texto y badges
- **depth-5**: sparkles con animación `twinkle`

Paleta:
- `--blue-500: #3b82f6` (primary)
- `--blue-700: #1d4ed8` (hover)
- `--blue-800: #1e40af` (deep accents)
- `--blue-950: #172554` (text on light bg)

Tokens en `extension/popup.html` líneas 12-35.

## 📂 Estructura del proyecto

```
CV-applier/
├── README.md                          # overview
├── STATUS.md                          # este archivo
├── docs/superpowers/
│   ├── specs/2026-06-17-cvapplier-design.md   # diseño completo
│   └── plans/2026-06-17-cvapplier-backend.md  # plan de implementación
├── backend/                           # FastAPI + Mongo + S3 + LiteLLM
│   ├── src/cvapplier/                 # package
│   │   ├── core/                      # config, security, db, storage, exceptions
│   │   ├── models/                    # Beanie Documents
│   │   ├── schemas/                   # Pydantic DTOs, uno por fichero
│   │   ├── repositories/              # data access
│   │   ├── services/                  # use cases
│   │   ├── api/v1/                    # HTTP controllers
│   │   ├── workers/                   # background jobs
│   │   ├── utils/                     # PII redactor, time helpers
│   │   └── main.py                    # FastAPI app factory
│   ├── scripts/                       # seed_learned_mappings.py
│   └── tests/                         # 34 tests
└── extension/                         # Chrome MV3
    ├── manifest.json
    ├── popup.html + popup.js          # epic-design UI en azul
    ├── src/                           # TS sources (background, content, types)
    ├── public/icons/                  # PNGs
    └── dist/                          # build output
```

## 🔐 Notas de seguridad

- API keys LLM cifradas con Fernet
- CVs cifrados con AES-256-GCM envelope (HKDF per user)
- JWT access 15min, refresh 30d con rotation + reuse detection
- Passwords argon2id, mínimo 12 chars
- PII redactor en logs y Sentry
- WS /ws/fill autenticado por access token en query

## 📊 Métricas de éxito v1.0 (target)

- 70%+ campos auto-rellenados sin edición
- Latencia end-to-end < 2s con LLM, < 300ms sin LLM
- Coste LLM medio < $0.01 por sesión
- 0 PII leaks en logs
- 80%+ test coverage
