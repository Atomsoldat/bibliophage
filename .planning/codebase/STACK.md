# Technology Stack

**Analysis Date:** 2026-06-07

## Languages

**Primary:**
- Python 3.12 - Backend RAG service, data processing, embeddings, and LLM orchestration (`python-server/`)
- TypeScript 5.9.3 - Vue 3 frontend application (`web-ui/`)
- Protocol Buffers (v3) - API contracts for Connect RPC communication (`api/`)

**Secondary:**
- Go - Graph database proxy service to ArcadeDB (`flansch/`) — in development, not yet active

## Runtime

**Environment:**
- Python 3.12.x - Backend application server
- Node.js (via Yarn) - Frontend package manager and build tooling
- Docker - Service orchestration and development environment

**Package Managers:**
- **Python:** [uv](https://docs.astral.sh/uv/) 0.1+ - Fast Python package installer and resolver
  - Lockfile: `uv.lock` (deterministic, supports multiple Python indexes)
  - Supports CPU/GPU/ROCm variants via `--extra cpu|gpu|rocm` flag
- **JavaScript:** Yarn 4.11.0 (workspaces-capable)
  - Lockfile: `yarn.lock`

## Frameworks

**Backend Core:**
- FastAPI 0.128.0 - ASGI web framework for async HTTP APIs
- Connect RPC (Python 0.7.1, TypeScript 1.7.0) - Protocol Buffers over HTTP/2 for client-server communication (replaces gRPC)
- Uvicorn 0.40.0 - ASGI server for running FastAPI

**Frontend Core:**
- Vue 3.5.24 - Reactive UI framework
- Pinia 2.3.1 - State management store (migrated from Vuex/composables in May 2026)
- Vue Router 4.6.3 - Client-side routing
- Vite 7.2.4 - Frontend build tool and dev server with hot module replacement (HMR)

**Data Processing:**
- Docling 2.91.0 - PDF-to-structured-document pipeline with multi-format support
- LangChain 0.3.27+ ecosystem:
  - `langchain-huggingface` 0.3.1 - HuggingFace embeddings integration
  - `langchain-community` 0.3.31 - ChatOllama provider for LLM access
  - `langchain-postgres` 0.0.15 - PostgreSQL vector store adapter
- Sentence Transformers (via langchain-huggingface) - Embedding model: `BAAI/bge-large-en-v1.5` (default, configurable)
- PyMuPDF 1.26.1 - Alternative PDF text extraction utility
- PyPDF 6.6.0 - PDF text extraction and manipulation

**ML/Compute:**
- PyTorch 2.9.1+ - Tensor computation and model inference
  - CPU, CUDA 12.6 (NVIDIA), or ROCm 6.3 (AMD) variants
- torchvision 0.24+ - Computer vision utilities (required by Docling for document analysis)

## Key Dependencies

**Critical:**
- `psycopg[binary] 3.2.10` - PostgreSQL async driver with type safety
- `pgvector 0.3.5` - PostgreSQL pgvector extension Python client
- `grpcio 1.73.1, grpcio-tools 1.73.1` - Protocol Buffers compiler and gRPC tools (for protobuf generation)
- `pydantic-settings 2.12.0` - Typed environment variable configuration loader
- Ollama SDK - LLM inference engine (containerized, no Python package; accessed via HTTP REST API)

**Infrastructure:**
- `pymongo 4.16.0` - MongoDB/FerretDB document database driver (legacy; documents now stored in PostgreSQL)
- `psutil 7.2.1` - System resource monitoring

**Frontend Utilities:**
- `@bufbuild/protobuf` 1.10.1, `@bufbuild/protoc-gen-es` 1.10.1 - Protobuf runtime and code generator for TypeScript
- `@connectrpc/connect` 1.7.0, `@connectrpc/connect-web` 1.7.0, `@connectrpc/protoc-gen-connect-es` 1.7.0 - Connect RPC client and code generation
- `marked 17.0.1` - Markdown parser for chat message formatting
- `graphology 0.26.0, graphology-layout-forceatlas2 0.10.1, sigma 3.0.0` - Graph visualization libraries
- `@vueuse/core 14.1.0` - Composable utilities for Vue
- `@codemirror/*` (v6) - Code editor for chunk editing
- `@floating-ui/dom 1.7.4` - Floating element positioning
- Tailwind CSS 4.1.17, daisyUI 5.5.5 - Utility-first styling framework

**Development Tools:**
- Ruff 0.14.13 - Python linter and formatter
- Ty 0.0.13 - Python type checker
- Deptry 0.24.0 - Python dependency analyzer
- Vulture 2.14 - Dead Python code detector
- pytest 9.0.2, pytest-asyncio 1.3.0 - Python testing framework with async support
- coverage 7.13.1 - Code coverage measurement
- ESLint 9.39.2 (via @antfu/eslint-config) - JavaScript/TypeScript linter
- Knip 5.70.1 - Unused dependency detector
- vue-tsc 3.1.4 - TypeScript type checking for Vue files

## Configuration

**Environment:**
- Backend loads via `pydantic-settings` from:
  1. `.env` file (optional, local development)
  2. Environment variables (preferred for production)
- Frontend loads from (in order):
  1. Environment variable `VITE_BACKEND_HOST` (build-time)
  2. `/config.json` runtime file (optional)
  3. Hardcoded default: `http://localhost:8000`

**Key Configuration Variables:**
- `VECTOR_DB_URL` - PostgreSQL pgvector connection (required)
- `OLLAMA_URL` - Ollama HTTP endpoint (default: `http://localhost:11435`)
- `OLLAMA_DEFAULT_MODEL` - Default LLM model (default: `mistral`)
- `OLLAMA_TEMPERATURE` - LLM creativity parameter (default: 0.7)
- `OLLAMA_MAX_TOKENS` - Token generation limit (default: 2048)
- `OLLAMA_TIMEOUT` - Request timeout in seconds (default: 120)
- `EMBEDDING_MODEL_NAME` - HuggingFace model ID (default: `BAAI/bge-large-en-v1.5`)
- `EMBEDDING_DEVICE` - PyTorch device (empty = auto-detect: cuda > mps > xpu > cpu)
- `LOG_LEVEL` - Python logging level (default: INFO)

**Build:**
- `pyproject.toml` - Python project metadata and dependencies
- `package.json` - JavaScript project and build scripts
- `vite.config.ts` - Frontend build configuration (Vue, Tailwind, dev tools)
- `tsconfig.json` - TypeScript compilation settings
- `eslint.config.mjs` - Linting rules for frontend code

## Platform Requirements

**Development:**
- Docker and Docker Compose (for local services: PostgreSQL, Ollama, ArcadeDB)
- Tilt 0.23+ (Kubernetes-like local dev orchestrator)
- Python 3.12 with `uv` package manager
- Node.js 18+ with Yarn 4.11+
- GPU support optional (NVIDIA CUDA 12.6 or AMD ROCm 6.3)

**Production:**
- Docker container runtime for microservice deployment
- PostgreSQL 18+ with pgvector extension
- Ollama service (container or local binary)
- CORS-enabled reverse proxy for web UI → backend communication

**Deployment Target:**
- Platform-agnostic (Docker-based); tested on Linux, macOS
- Typical: Kubernetes cluster with containerized services or Docker Compose on single host

---

*Stack analysis: 2026-06-07*
