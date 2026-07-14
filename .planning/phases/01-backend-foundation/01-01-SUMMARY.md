---
phase: 01-backend-foundation
plan: "01"
subsystem: api
tags: [python, fastapi, refactor, domain-packages, restructure]

# Dependency graph
requires: []
provides:
  - Python server organized into domain packages (documents/, ingestion/, embeddings/, chat/, graph/, db/)
  - Each domain has service.py as its primary implementation file
  - db/schema/ holds all SQL DDL files, loadable via importlib.resources("db.schema")
affects: [01-02, 01-03, any future plan touching python-server/src/]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Domain package layout: src/{domain}/service.py for service implementations"
    - "Shared root files: server.py, config.py, proto_converters.py stay at src/ root"
    - "Empty __init__.py per D-11 (no backward-compat re-exports)"
    - "importlib.resources.files('db.schema') for SQL DDL access"

key-files:
  created:
    - python-server/src/documents/__init__.py
    - python-server/src/documents/service.py
    - python-server/src/ingestion/__init__.py
    - python-server/src/ingestion/service.py
    - python-server/src/ingestion/docling_pipeline.py
    - python-server/src/ingestion/batch_size_calculator.py
    - python-server/src/ingestion/pdf_outline_inspector.py
    - python-server/src/embeddings/__init__.py
    - python-server/src/embeddings/service.py
    - python-server/src/embeddings/model.py
    - python-server/src/embeddings/chunking.py
    - python-server/src/chat/__init__.py
    - python-server/src/chat/service.py
    - python-server/src/chat/llm_access.py
    - python-server/src/graph/__init__.py
    - python-server/src/graph/service.py
    - python-server/src/db/__init__.py
    - python-server/src/db/postgres_db.py
    - python-server/src/db/schema/__init__.py
    - python-server/src/db/schema/documents.sql
    - python-server/src/db/schema/vectors.sql
    - python-server/src/db/schema/graph.sql
  modified:
    - python-server/src/server.py
    - python-server/tests/test_embeddings.py
    - python-server/tests/test_batch_size_calculator.py
    - python-server/tests/test_graph_db.py
    - python-server/tests/test_reconcile_embedding.py

key-decisions:
  - "Big bang restructure (D-09): all 16 files moved in one shot, no phased migration"
  - "Empty __init__.py files (D-11): no backward-compat re-exports, imports updated directly"
  - "Shared files at root (D-10): server.py, config.py, proto_converters.py unchanged"
  - "importlib.resources package updated from 'db_schema' to 'db.schema'"
  - "chunking.py module imported as 'chunking_strategies' alias in embeddings/service.py to preserve call pattern"

patterns-established:
  - "Domain imports: from {domain}.{module} import ... (e.g. from db.postgres_db import get_postgres_db)"
  - "Intra-domain imports: fully qualified (e.g. from ingestion.docling_pipeline import DoclingPipeline)"
  - "Cross-domain imports: from db.postgres_db import ... (db is the shared data layer)"

requirements-completed: [STRUCT-01, STRUCT-02]

# Metrics
duration: 6min
completed: 2026-06-11
---

# Phase 1 Plan 01: Domain Restructure Summary

**Big-bang move of 16 Python source files into 6 domain packages (documents/, ingestion/, embeddings/, chat/, graph/, db/) with all imports updated — zero behavior change**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-11T01:50:28Z
- **Completed:** 2026-06-11T01:56:30Z
- **Tasks:** 2
- **Files modified:** 35 (22 moves + 13 import updates)

## Accomplishments

- All 16 source files moved to domain packages per the D-09 big-bang strategy
- All imports across 9 source files and 4 test files updated to new module paths
- db/schema/ SQL DDL files accessible via `importlib.resources.files("db.schema")`
- bibliophage/ generated proto directory left untouched
- server.py, config.py, proto_converters.py remain at src/ root per D-10

## Task Commits

1. **Task 1: Create domain packages and move files** - `17b71a2` (refactor)
2. **Task 2: Update all imports across source and test files** - `545000e` (refactor)

## Files Created/Modified

**Domain packages created (new):**
- `python-server/src/documents/service.py` - DocumentServiceImplementation (was document_service_implementation.py)
- `python-server/src/ingestion/service.py` - LoadingServiceImplementation (was loading_service_implementation.py)
- `python-server/src/ingestion/docling_pipeline.py` - DoclingPipeline (moved from root)
- `python-server/src/ingestion/batch_size_calculator.py` - calculate_batch_size (moved from root)
- `python-server/src/ingestion/pdf_outline_inspector.py` - PDF outline utilities (moved from root)
- `python-server/src/embeddings/service.py` - EmbeddingServiceImplementation (was embedding_service_implementation.py)
- `python-server/src/embeddings/model.py` - HuggingFace embeddings singleton (was embeddings.py)
- `python-server/src/embeddings/chunking.py` - Chunking strategies (was chunking_strategies.py)
- `python-server/src/chat/service.py` - ChatServiceImplementation (was chat_service_implementation.py)
- `python-server/src/chat/llm_access.py` - LLMClient singleton (was llm_access.py)
- `python-server/src/graph/service.py` - GraphServiceImplementation (was graph_service_implementation.py)
- `python-server/src/db/postgres_db.py` - BibliophageDatabase singleton (was postgres_db.py)
- `python-server/src/db/schema/` - SQL DDL files (was db_schema/)
- 7x empty `__init__.py` files for each package

**Root files modified (import updates):**
- `python-server/src/server.py` - Updated all service/db imports
- `python-server/tests/test_embeddings.py` - Updated embeddings module import
- `python-server/tests/test_batch_size_calculator.py` - Updated ingestion.batch_size_calculator
- `python-server/tests/test_graph_db.py` - Updated db.postgres_db import
- `python-server/tests/test_reconcile_embedding.py` - Updated embeddings.service import

## Decisions Made

- Used `import embeddings.chunking as chunking_strategies` alias in `embeddings/service.py` to preserve existing call pattern `chunking_strategies.get_strategy(...)` without touching implementation code
- Updated docstring usage example in `embeddings/chunking.py` for accuracy (was `from chunking_strategies import get_strategy`, updated to `from embeddings.chunking import get_strategy`)

## Deviations from Plan

None - plan executed exactly as written. The file mapping, import transformations, and `__init__.py` approach all matched the plan's action specifications.

## Issues Encountered

- `uv` and `just` are not available in the execution environment (they run inside Tilt-managed containers). Static import verification was performed instead:
  - Confirmed all import statements in modified files reference correct module paths
  - Confirmed no stale imports of old module names remain via grep across src/ and tests/
  - Confirmed `importlib.resources.files("db.schema")` path matches the new db/schema/__init__.py package location
- git user.email not configured in worktree — configured inline before first commit

## User Setup Required

None - no external service configuration required. This is a pure source restructure.

## Next Phase Readiness

- Plan 01-02 (Junction Tables) can proceed — it will work in `documents/service.py` and `db/postgres_db.py` which are now in their domain locations
- Plan 01-03 (Update Document) builds on 01-02 and uses the same domain structure
- All imports in the codebase now follow the `from {domain}.{module} import ...` pattern

---
*Phase: 01-backend-foundation*
*Completed: 2026-06-11*
