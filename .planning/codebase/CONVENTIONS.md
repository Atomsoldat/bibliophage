# Coding Conventions

**Analysis Date:** 2026-06-07

## Python Backend

### Linting & Formatting
- **Linter:** Ruff with `select = ["ALL"]` — nearly all rules enabled
- **Config:** `python-server/ruff.toml`
- **Ignored rules:** `D` (docstrings — relaxed for now), `E501` (line length), `FIX001` (TODO markers used for documentation), `D203/D211/D212` (docstring formatting conflicts), `COM812` (trailing comma — formatter handles this)
- **Test-specific:** `S101` ignored in tests (allows `assert` statements)
- **Type checking:** `ty` (Pyright-based) via `just types`
- **Dead code:** `vulture` via `just lint`
- **Dependency check:** `deptry` via `just lint`
- **Run all:** `just lint` runs ruff, ty, deptry, vulture in sequence

### Singleton Pattern
All shared resources are initialized once and accessed via module-level singletons:

```python
# python-server/src/embeddings.py — lazy singleton
_model = None
def get_embeddings_model():
    global _model
    if _model is None:
        _model = HuggingFaceEmbeddings(...)
    return _model
```

Applied to: `postgres_db.py` (DB pool), `embeddings.py` (embedding model), `llm_access.py` (Ollama client), `config.py` (settings).

### Service Implementation Pattern
Each Connect RPC service follows the same structure:

```python
# {domain}_service_implementation.py
class {Domain}ServiceImplementation:
    async def method_name(self, request, context):
        # 1. Validate/extract from protobuf request
        # 2. Call DB/model/external service
        # 3. Convert result to protobuf response
        # 4. Return response
```

- Services registered in `server.py` as Connect RPC handlers on FastAPI
- Proto converters in `proto_converters.py` handle Protobuf ↔ Python dict mapping

### Error Handling
- `try/except` with `logger.exception()` for service methods
- Per-module loggers: `logger = logging.getLogger(__name__)`
- No custom exception hierarchy — uses standard Python exceptions

### Configuration
- Pydantic Settings (`BaseSettings`) reads from environment variables
- Nested config classes: `DatabaseConfig`, `EmbeddingConfig`, `OllamaConfig`, `AppConfig`
- `.env.example` documents all variables with defaults

## TypeScript / Vue Frontend

### Linting
- **Config:** `@antfu/eslint-config` — opinionated, Vue-compatible
- **File:** `web-ui/eslint.config.mjs`
- **Custom rules:** `vue/v-bind-style: 'longform'` — uses `v-bind:xyz` instead of `:xyz`
- **Excluded:** `src/bibliophage/**` (generated protobuf code)

### State Management
- **Pinia stores** in `web-ui/src/stores/` (recently migrated from composables)
- 5 stores: `documents`, `chat`, `console`, `editorWindows`, `graph`
- Composables (`use*.ts`) handle API communication, stores handle state

### Component Patterns
- **Views** are page-level components routed via Vue Router
- **Components** are reusable UI building blocks
- **Composables** encapsulate API client logic with `useXxxApi()` pattern
- Uses `<script setup>` syntax with TypeScript

### Styling
- **Tailwind CSS v4** with **DaisyUI v5** component library
- **Sass** for custom styles where needed
- No CSS modules — utility-first approach

### API Communication
- **Connect RPC** (not standard gRPC) via `@connectrpc/connect-web`
- Generated TypeScript clients from `.proto` definitions
- Composables wrap Connect RPC calls: `useDocumentApi()`, `useChatApi()`, etc.

## Cross-Cutting

### Generated Code
- Protobuf-generated code is **committed to git** in both `python-server/src/bibliophage/` and `web-ui/src/bibliophage/`
- Regenerate with `tilt trigger api` after `.proto` changes
- Both linters exclude generated code directories

### Versioning
- **Cocogitto** for conventional commits (`cog.toml`)
- 4 packages tracked: `api/`, `flansch/`, `python-server/`, `web-ui/`
- Auto-generated `CHANGELOG.md`

### Task Running
- **Python:** `just` (justfile) — `just dev`, `just tests`, `just lint`
- **Frontend:** `yarn` scripts — `yarn dev`, `yarn build`, `yarn lint`
- **Orchestration:** `tilt up` starts everything

---

*Conventions analysis: 2026-06-07*
