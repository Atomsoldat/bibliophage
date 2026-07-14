# Testing Patterns

**Analysis Date:** 2026-06-07

## Test Framework

**Runner:** pytest 9.0.2+ (configured in `python-server/pyproject.toml`)

**Run Commands:**
```bash
cd python-server
just tests                                                        # All tests
just tests tests/test_embedding.py                                # Single file
just tests tests/test_embedding.py::test_embed_document_with_markdown_strategy  # Single test
just tests -k test_embed                                          # Pattern match
just coverage && just coverage-report                            # Coverage
```

## Test File Organization

**Location:** `python-server/tests/` (separate from source)

```
python-server/tests/
├── conftest.py                   # Shared fixtures (DB clients, test documents)
├── test_batch_size_calculator.py # Unit: batch sizing logic
├── test_document.py              # Integration: DocumentService CRUD
├── test_embedding.py             # Integration: EmbeddingService with DB
├── test_embeddings.py            # Unit: device detection, model loading
├── test_graph_db.py              # Integration: graph database operations
├── test_graph_service.py         # Integration: GraphService
├── test_pdf.py                   # Integration: PDF ingestion pipeline
├── test_proto_converters.py      # Unit: protobuf conversion functions
├── test_reconcile_embedding.py   # Integration: embedding reconciliation
└── data/
    └── bestiary_sample.md        # Test fixture data (converted to PDF)
```

**Frontend:** No test files exist in `web-ui/` — `@pinia/testing` is installed but unused.

## Test Markers

```python
@pytest.mark.unit          # Fast, no external dependencies
@pytest.mark.integration   # Requires running services (DB, Ollama)
@pytest.mark.slow          # Long-running tests
```

## Configuration

```toml
# pyproject.toml [tool.pytest.ini_options]
asyncio_mode = "auto"                    # Auto-runs async test functions
pythonpath = ["src"]                     # Import from src/ directly
testpaths = ["tests"]
addopts = ["-v", "--strict-markers", "--tb=short"]
log_cli = true
log_cli_level = "INFO"
```

## Fixture Patterns

**Setup-yield-teardown** for resource cleanup:

```python
# conftest.py — creates test document, cleans up after test
@pytest.fixture
async def test_document(document_client):
    doc_request = doc_api.StoreDocumentRequest()
    doc_request.document.name = "Test Document (auto-cleanup)"
    response = await document_client.store_document(doc_request)
    yield response.document
    # Teardown: delete even if test fails
    try:
        delete_request = doc_api.DeleteDocumentRequest()
        delete_request.id = response.document.id
        await document_client.delete_document(delete_request)
    except Exception as e:
        logger.warning(f"Failed to cleanup: {e}")
```

**Key fixtures from `conftest.py`:**
- `sample_pdf(tmp_path)` — generates PDF from markdown via pandoc
- `document_client()` — DocumentServiceClient instance
- `embedding_client()` — EmbeddingServiceClient instance
- `graph_client()` — GraphServiceClient instance
- `pdf_client()` — PdfServiceClient instance
- `test_document(document_client)` — creates + auto-cleans a document
- `embedded_document(test_document, embedding_client)` — document with embeddings

**Factory helper:**
```python
# test_proto_converters.py
def _make_row(**overrides):
    """Return a minimal complete row dict with overrides applied."""
    row = {"document_id": "11111111-...", "title": "Test Doc", ...}
    row.update(overrides)
    return row
```

## Mocking Policy

**Project rule: No mocking of databases or services.** Extract pure functions and test those directly. Integration tests use real running services.

**What IS mocked (sparingly):**
- Hardware detection: `monkeypatch.setattr(torch.cuda, "is_available", ...)`
- Module-level singletons via `monkeypatch`

**What is NOT mocked:**
- Database operations — use real fixtures with setup/teardown
- API clients — create real Connect RPC client instances
- Service implementations — test actual behavior

## Common Patterns

**Parameterized tests:**
```python
@pytest.mark.unit
@pytest.mark.parametrize("override", ["cpu", "cuda", "cuda:0", "mps", "xpu"])
def test_override_is_returned_verbatim(override):
    assert _resolve_embedding_device(override) == override
```

**Error testing:**
```python
@pytest.mark.unit
def test_invalid_nonempty_override_raises():
    with pytest.raises(ValueError, match="Unexpected value for embedding device"):
        _resolve_embedding_device("gpu")
```

**Async integration test:**
```python
@pytest.mark.integration
async def test_embed_document_with_markdown_strategy(test_document, embedding_client):
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    response = await embedding_client.embed_document(emb_request)
    assert response.success is True
```

## Coverage

```toml
# pyproject.toml [tool.coverage]
source = ["src"]
omit = ["tests/*", "src/bibliophage/*_pb2.py", "__init__.py"]
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]
show_missing = true
```

No enforced threshold. Run via `just coverage && just coverage-report`.

---

*Testing analysis: 2026-06-07*
