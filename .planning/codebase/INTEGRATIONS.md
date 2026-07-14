# External Integrations

**Analysis Date:** 2026-06-07

## APIs & External Services

**LLM Inference:**
- Ollama - Local LLM model server for RPG rulebook Q&A
  - SDK/Client: LangChain `ChatOllama` (via `langchain-community`)
  - Connection: HTTP REST API at `http://localhost:11435` (configurable via `OLLAMA_URL`)
  - Authentication: None (local/trusted network)
  - Models: `mistral` (default), customizable per request
  - Purpose: Streaming chat responses with RAG context

**Embedding Models:**
- HuggingFace Model Hub - Pre-trained embedding models
  - SDK/Client: `langchain_huggingface.HuggingFaceEmbeddings`
  - Model: `BAAI/bge-large-en-v1.5` (default, configurable via `EMBEDDING_MODEL_NAME`)
  - Local inference: Models downloaded on first use and cached
  - No API key required — runs locally after download
  - Purpose: Document chunking and vector embeddings for semantic search

**Protocol Buffer Compilation:**
- Buf CLI - Protocol Buffers schema tooling (used in development)
  - Location: `api/bibliophage/` directory
  - Triggered via: `tilt trigger api` (runs `just gen-proto` + TypeScript codegen)
  - Purpose: Generate Python and TypeScript service stubs from `.proto` files

## Data Storage

**Databases:**

**PostgreSQL + pgvector (Primary Vector Store):**
- Type: PostgreSQL 18+ with pgvector extension
- Port: 5432
- Connection: `postgresql+psycopg://pgvector:pgvector_dev@localhost:5432/pgvector` (dev)
- Client: `psycopg[binary] 3.2.10` (async driver)
- Vector ORM: `langchain-postgres` for semantic search (LangChain integration)
- Purpose: Document chunk embeddings, semantic search, vector similarity
- Schema: Custom; initialized on startup via `postgres_db.py` -> `initialise_schema()`

**PostgreSQL (Document Storage - Current Authority):**
- Type: PostgreSQL (same instance as pgvector)
- Purpose: Structured document metadata, chunks, source type authority weights
- Migration Status: Documents migrated from FerretDB (June 2026); stored in PostgreSQL
- Note: Documents were previously stored in FerretDB/MongoDB, now consolidated to PostgreSQL

**File Storage:**
- Type: Local filesystem only
- Location: Relative to backend working directory
- Uploaded PDFs: Stored temporarily during processing
- Purpose: PDF ingestion via Docling pipeline

**Caching:**
- Type: None explicit (embedding models and LLM client cached as singletons in Python)
- Strategy: Application-level in-memory caching of initialized models (HuggingFaceEmbeddings, ChatOllama)

## Authentication & Identity

**Auth Provider:**
- Custom: None (no user authentication at application level)
- Strategy: All services trusted on local/internal network
- CORS: Configured to allow all origins (`allow_origins=["*"]` in FastAPI)
  - Purpose: Development convenience; production should restrict origins

## Monitoring & Observability

**Error Tracking:**
- Type: None (no external error tracking service integrated)
- Approach: Local logging only

**Logs:**
- Type: Console/stdout to application logs
- Format: `%(levelname)s: %(asctime)s %(name)s %(message)s`
- Configuration: `LOG_LEVEL` environment variable (default: INFO)
- Framework: Python standard `logging` module

## CI/CD & Deployment

**Hosting:**
- Development: Local via Docker Compose + Tilt
- Production: Docker container images (single backend instance or Kubernetes cluster)
- No automated CI/CD pipeline configured (no GitHub Actions or similar)

**CI Pipeline:**
- Type: Not detected
- Linting/Testing: Manual via `just` commands
  - `just lint` - Run all linters (Ruff, Ty, Deptry, Vulture)
  - `just tests` - Run pytest suite
  - `yarn lint` - ESLint for frontend

## Environment Configuration

**Required env vars (Backend):**
- `VECTOR_DB_URL` - PostgreSQL pgvector connection string (REQUIRED)
- `OLLAMA_URL` - Ollama API endpoint (default: `http://localhost:11435`)
- `OLLAMA_DEFAULT_MODEL` - LLM model to use (default: `mistral`)
- `EMBEDDING_MODEL_NAME` - HuggingFace model ID (default: `BAAI/bge-large-en-v1.5`)
- `GPU_VENDOR` - GPU variant for PyTorch: `''` (CPU), `'nvidia'` (CUDA), `'amd'` (ROCm)

**Optional env vars (Backend):**
- `EMBEDDING_DEVICE` - PyTorch device override (empty = auto-detect)
- `OLLAMA_TEMPERATURE` - LLM temperature (0.0-1.0)
- `OLLAMA_MAX_TOKENS` - Max generation tokens
- `OLLAMA_TIMEOUT` - Request timeout in seconds
- `LOG_LEVEL` - Python logging level

**Frontend env vars:**
- `VITE_BACKEND_HOST` - Backend API base URL (default: `http://localhost:8000`)

**Secrets location:**
- Development: `.env` file (git-ignored, see `.gitignore`)
- Production: Environment variables injected at container runtime
- No credential files stored in repository

## Webhooks & Callbacks

**Incoming:**
- Type: None detected

**Outgoing:**
- Type: None detected
- Note: Chat service streams responses to frontend via Connect RPC, not webhooks

## Document Authority Weights (RAG Ranking)

Source types affect how retrieved chunks are ranked in LLM context window:

| Source Type | Weight | Interpretation |
|-------------|--------|-----------------|
| `GM_NOTES` | 1.2 | Most authoritative (GM guidance) |
| `RULEBOOK` | 1.0 | Official rules baseline |
| `SUPPLEMENT` | 0.9 | Official supplements |
| `SESSION_LOG_RECORD` | 0.6 | Session history |
| `PLAYER_NOTES` | 0.5 | Player-contributed content |
| `GENERATED` | 0.3 | LLM-generated content (least authoritative) |
| `COMMUNITY` | 0.4 | Community contributions |

Implementation: `python-server/src/llm_access.py` lines 23-32 (`AUTHORITY_WEIGHTS` dict)

## Service Topology (Development)

```
┌─────────────────────────────────────────┐
│ Web UI (Vite dev server)                │
│ http://localhost:5173                   │
│ Vue 3 + Pinia stores                    │
└──────────────────┬──────────────────────┘
                   │ Connect RPC/HTTP
                   ▼
┌─────────────────────────────────────────┐
│ FastAPI Backend                         │
│ http://localhost:8000                   │
│ Uvicorn + Connect RPC services          │
└──┬──────────────┬──────────────┬────────┘
   │              │              │
   ▼              ▼              ▼
┌────────┐  ┌─────────┐  ┌──────────────┐
│ PG:    │  │ Ollama  │  │ HuggingFace  │
│5432    │  │:11435   │  │ (local cache)│
│pgvector│  │ LLM     │  │ Embeddings   │
└────────┘  └─────────┘  └──────────────┘
```

---

*Integration audit: 2026-06-07*
