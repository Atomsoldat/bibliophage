# Technical Concerns

**Analysis Date:** 2026-06-07

## Technical Debt

### High Priority

| Area | Issue | Location | Impact |
|------|-------|----------|--------|
| Dead dependency | FerretDB/MongoDB still referenced in Tiltfile and config | `Tiltfile:34`, `python-server/.env.example` | Confusion — documents now stored in PostgreSQL per project memory |
| Unused dependency | `pymongo` in `pyproject.toml` dependencies | `python-server/pyproject.toml` | Unnecessary install, potential security surface |
| No frontend tests | `@pinia/testing` installed but zero test files in `web-ui/` | `web-ui/` | No regression protection for UI |
| Legacy code | `werkbank/loading_service_implementation_legacy.py` with many TODOs | `werkbank/` | Legacy code may confuse contributors |

### Medium Priority

| Area | Issue | Location | Impact |
|------|-------|----------|--------|
| API version | Still on `v1alpha3` — indicates pre-stable API | `api/bibliophage/v1alpha3/` | API may change, breaking clients |
| Docstrings disabled | Ruff `D` rules entirely ignored | `python-server/ruff.toml` | No enforced documentation on public APIs |
| Line length | `E501` ignored — no line length limit | `python-server/ruff.toml` | Readability in narrow terminals |
| Graph DB commented out | ArcadeDB and AGE resources disabled in Tiltfile | `Tiltfile:14-15` | Flansch/graph features may be partially broken |

## Known Issues (from TODOs)

### Frontend TODOs
- Tag filtering not implemented (`web-ui/src/utils/protoHelpers.ts:28`)
- Bulk metadata edit only replaces, no append for tags (`web-ui/src/composables/useBulkMetadataEdit.ts:44`)
- Fetching entire documents when only metadata needed (`web-ui/src/composables/useBulkMetadataEdit.ts:46`)
- Hard-coded config values (`web-ui/src/composables/useConfig.ts:89`)
- Logger message types need cleanup (`web-ui/src/composables/useLogger.ts:67`)
- No confirmation dialog for unsaved editor changes (`web-ui/src/components/GlobalEditorWindows.vue:97`)
- PDF upload missing progress indicator (`web-ui/src/views/PdfUpload.vue:92`)
- PDF upload timeout handling unclear (`web-ui/src/views/PdfUpload.vue:131`)
- Multi-select for document systems not implemented (`web-ui/src/views/PdfUpload.vue:35`)

### Protobuf TODOs
- Document type flexibility under consideration (`document_pb.ts:13`)
- Authority weight calculation timing question (`document_pb.ts:523`)
- ChunkBoundary type derivation needed (`embedding_pb.ts:167`)
- Field naming alignment with database columns (`embedding_pb.ts:183`)

## Security Considerations

| Area | Concern | Severity |
|------|---------|----------|
| Database credentials | Hard-coded in Tiltfile for dev environment | Low (dev-only) |
| No auth | No authentication on any service endpoint | Medium — acceptable for local dev tool |
| PDF processing | Docling processes untrusted PDFs — potential for malformed input | Low |
| Ollama | LLM runs locally, no external API keys in production path | Low |

## Performance Concerns

| Area | Concern | Location |
|------|---------|----------|
| Embedding model | Loaded into memory on first use, stays resident | `python-server/src/embeddings.py` |
| Batch sizing | Dynamic calculator for GPU memory — complex logic | `python-server/src/batch_size_calculator.py` |
| PDF processing | Docling pipeline can be slow for large PDFs | `python-server/src/docling_pipeline.py` |
| Full document fetch | Bulk metadata edit fetches entire documents | `web-ui/src/composables/useBulkMetadataEdit.ts` |

## Fragile Areas

| Area | Why | Risk |
|------|-----|------|
| Proto generation | Manual `tilt trigger api` — easy to forget after `.proto` changes | Stale generated code |
| Graph service | Flansch is a git submodule, ArcadeDB disabled in Tiltfile | Feature may be broken/untested |
| Torch device detection | Multiple GPU vendor paths (CUDA/ROCm/MPS/XPU) with complex fallback | Edge cases on unusual hardware |
| FerretDB → PostgreSQL migration | References to MongoDB/FerretDB remain in codebase despite migration | Confusion, dead code |

## Missing Features (from ideas/ and notes/)

Based on files in `ideas/` and `notes/`:
- Multi-tenancy (`notes/TODO_TENANCY.md`)
- Flexible document types (`notes/TODO_FLEXIBLE_TYPES.md`)
- Desktop application (`notes/desktop_application.md`)
- Packaging/distribution (`notes/packaging.md`)
- Graph representation improvements (`notes/graph_representation.md`)

---

*Concerns analysis: 2026-06-07*
