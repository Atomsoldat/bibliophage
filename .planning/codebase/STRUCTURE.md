# Directory Structure

**Analysis Date:** 2026-06-07

## Repository Layout

```
bibliophage/
├── api/                          # Protobuf API definitions (source of truth)
│   └── bibliophage/v1alpha3/     # Current API version
│       ├── document.proto        # Document CRUD service
│       ├── embedding.proto       # Embedding/chunking service
│       ├── chat.proto            # RAG chat service
│       ├── pdf.proto             # PDF ingestion service
│       └── graph.proto           # Graph database service
├── python-server/                # Python backend (FastAPI + Connect RPC)
│   ├── src/                      # Source code
│   │   ├── server.py             # Entry point — registers all services
│   │   ├── config.py             # Pydantic Settings config from env vars
│   │   ├── postgres_db.py        # PostgreSQL/pgvector singleton client
│   │   ├── embeddings.py         # HuggingFace embedding model singleton
│   │   ├── llm_access.py         # Ollama LLM client singleton
│   │   ├── *_service_implementation.py  # Connect RPC service handlers
│   │   ├── proto_converters.py   # Protobuf ↔ Python dict converters
│   │   ├── chunking_strategies.py # Text chunking (markdown/token-based)
│   │   ├── docling_pipeline.py   # PDF processing via Docling
│   │   ├── batch_size_calculator.py # Dynamic batch sizing for embeddings
│   │   ├── pdf_outline_inspector.py # PDF TOC extraction
│   │   └── bibliophage/          # Generated protobuf Python code (committed)
│   ├── tests/                    # pytest tests
│   │   ├── conftest.py           # Shared fixtures
│   │   ├── test_*.py             # Test files
│   │   └── data/                 # Test fixture data
│   ├── pyproject.toml            # Dependencies, tool config (uv)
│   ├── ruff.toml                 # Linter config
│   └── justfile                  # Task runner commands
├── web-ui/                       # Vue 3 frontend
│   ├── src/
│   │   ├── main.ts               # App entry point
│   │   ├── App.vue               # Root component
│   │   ├── router/index.ts       # Vue Router config
│   │   ├── views/                # Page-level components
│   │   │   ├── Library.vue       # Document management
│   │   │   ├── Chat.vue          # RAG chat interface
│   │   │   ├── PdfUpload.vue     # PDF ingestion
│   │   │   ├── Chunks.vue        # Chunk viewer/editor
│   │   │   ├── GraphView.vue     # Graph visualization (sigma.js)
│   │   │   ├── Settings.vue      # App settings
│   │   │   ├── Home.vue          # Landing page
│   │   │   └── Sandbox.vue       # Dev playground
│   │   ├── components/           # Reusable UI components
│   │   ├── composables/          # Vue composables (API clients, utilities)
│   │   ├── stores/               # Pinia state stores
│   │   │   ├── documents.ts      # Document state
│   │   │   ├── chat.ts           # Chat state
│   │   │   ├── console.ts        # Console/log state
│   │   │   ├── editorWindows.ts  # Editor window state
│   │   │   └── graph.ts          # Graph visualization state
│   │   ├── utils/protoHelpers.ts # Protobuf utility functions
│   │   └── bibliophage/          # Generated protobuf TS code (committed)
│   ├── package.json              # Dependencies (yarn)
│   ├── vite.config.ts            # Vite bundler config
│   └── eslint.config.mjs         # Linter config
├── flansch/                      # Go graph service (ArcadeDB proxy, git submodule)
├── dev-environment/              # Docker Compose files for services
│   ├── docker-compose.yaml       # Base: PostgreSQL, FerretDB, Ollama
│   ├── docker-compose.nvidia.yml # NVIDIA GPU overlay
│   └── docker-compose.amd.yml    # AMD GPU overlay
├── docs/                         # Developer documentation
├── notes/                        # Design notes, TODOs, architecture thinking
├── ideas/                        # Feature ideas and problem tracking
├── pdfs/                         # Sample RPG rulebook PDFs for testing
├── werkbank/                     # Experimental code / legacy implementations
├── Tiltfile                      # Dev orchestration (Tilt)
├── cog.toml                      # Cocogitto conventional commit config
└── CLAUDE.md                     # AI assistant instructions
```

## Key Locations

| What | Where |
|------|-------|
| API definitions | `api/bibliophage/v1alpha3/*.proto` |
| Backend entry point | `python-server/src/server.py` |
| Service implementations | `python-server/src/*_service_implementation.py` |
| Database access | `python-server/src/postgres_db.py` |
| Config | `python-server/src/config.py` |
| Frontend entry | `web-ui/src/main.ts` |
| Routes | `web-ui/src/router/index.ts` |
| State management | `web-ui/src/stores/*.ts` |
| API clients | `web-ui/src/composables/use*Api.ts` |
| Generated protobuf (Python) | `python-server/src/bibliophage/v1alpha3/` |
| Generated protobuf (TS) | `web-ui/src/bibliophage/v1alpha3/` |
| Docker services | `dev-environment/docker-compose.yaml` |
| Dev orchestration | `Tiltfile` |

## Naming Conventions

### Python Backend
- **Files:** `snake_case.py` — service files named `{domain}_service_implementation.py`
- **Classes:** `PascalCase` — `DatabaseConfig`, `EmbeddingServiceImplementation`
- **Functions:** `snake_case` — `get_embeddings_model()`, `embed_document()`
- **Constants:** `UPPER_SNAKE` — `AUTHORITY_WEIGHTS`

### TypeScript Frontend
- **Files:** `PascalCase.vue` for components, `camelCase.ts` for utilities
- **Composables:** `use{Name}.ts` — `useDocumentApi.ts`, `useChatApi.ts`
- **Stores:** `{name}.ts` in `stores/` — `documents.ts`, `chat.ts`
- **Components:** `PascalCase.vue` — `DocumentTable.vue`, `BaseCard.vue`

### API (Protobuf)
- **Package:** `bibliophage.v1alpha3` — versioned API namespace
- **Services:** `PascalCase` — `DocumentService`, `EmbeddingService`
- **Messages:** `PascalCase` — `StoreDocumentRequest`, `EmbedDocumentResponse`
- **Fields:** `snake_case` — `document_id`, `chunk_text`

## Where to Add New Code

| New thing | Location | Pattern to follow |
|-----------|----------|-------------------|
| New API endpoint | `api/bibliophage/v1alpha3/` + regen | Existing `.proto` files |
| New backend service | `python-server/src/{name}_service_implementation.py` | `document_service_implementation.py` |
| New frontend view | `web-ui/src/views/{Name}.vue` + add route | `Library.vue` |
| New frontend component | `web-ui/src/components/{Name}.vue` | `BaseCard.vue` |
| New API composable | `web-ui/src/composables/use{Name}Api.ts` | `useDocumentApi.ts` |
| New Pinia store | `web-ui/src/stores/{name}.ts` | `documents.ts` |
| New backend test | `python-server/tests/test_{name}.py` | `test_proto_converters.py` |
| New Docker service | `dev-environment/docker-compose.yaml` + Tiltfile | Existing services |

---

*Structure analysis: 2026-06-07*
