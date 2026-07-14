<!-- refreshed: 2026-06-07 -->
# Architecture

**Analysis Date:** 2026-06-07

## System Overview

Bibliophage is a RAG (Retrieval-Augmented Generation) system for RPG rulebook PDFs. It ingests PDFs via Docling, chunks and embeds them into vector storage (pgvector), stores structured documents in PostgreSQL, and streams LLM responses from Ollama with automatic context retrieval.

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Web UI (Vue 3 + Pinia)                       │
│              `web-ui/src/` (views, stores, composables)          │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/Connect RPC
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐
│ PdfService    │ │ Document   │ │ Chat        │
│ (LoadPdf)     │ │ Service    │ │ Service     │
│               │ │ (CRUD)     │ │ (Stream)    │
└────────┬──────┘ └─────┬──────┘ └──────┬──────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼──────────────────────────────────────┐
│       PostgreSQL (Schema + pgvector)           │
│       `python-server/src/db_schema/`           │
├──────────────────────────────────────────────┤
│ documents (title, content, source_type)       │
│ document_chunks (content, embedding, vector)  │
│ systems, tags (mapping tables)                │
│ graph_edges (experimental)                    │
└────────────────────────────────────────────────┘
                         │
                         │
                    ┌────▼────┐
                    │ Ollama   │
                    │ (LLM)    │
                    └──────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| PdfService | PDF ingestion via Docling pipeline | `python-server/src/loading_service_implementation.py` |
| DocumentService | Document CRUD and search in PostgreSQL | `python-server/src/document_service_implementation.py` |
| EmbeddingService | Chunking and vector embedding generation | `python-server/src/embedding_service_implementation.py` |
| ChatService | RAG orchestration and streaming LLM responses | `python-server/src/chat_service_implementation.py` |
| GraphService | Graph database proxy to ArcadeDB (experimental) | `flansch/src/server/graph.go` |
| Web UI | Frontend for upload, document library, chat, and graph views | `web-ui/src/` |

## Pattern Overview

**Overall:** Service-oriented architecture (SOA) with Connect RPC-based service communication. Each backend service is independently deployable via ASGI (Asynchronous Server Gateway Interface) and mounts as a sub-application on the FastAPI server.

**Key Characteristics:**
- Protobuf-first API design with Connect RPC (HTTP-based, not gRPC)
- Singleton pattern for database clients, embedding models, and LLM instances
- Server-streaming RPC for real-time LLM token delivery (ChatService)
- Document authority weighting for context prioritization in LLM prompts
- PostgreSQL as single source of truth (no FerretDB)

## Layers

**API Layer (Proto definitions):**
- Purpose: Define service contracts and message types
- Location: `api/bibliophage/v1alpha3/`
- Contains: `.proto` files for PdfService, DocumentService, EmbeddingService, ChatService, GraphService
- Depends on: Google Protobuf
- Used by: Python backend (generates `*_pb2.py`, `*_connect.py`), TypeScript frontend (generates `*.ts`)

**Service Implementation Layer:**
- Purpose: Implement business logic for each RPC service
- Location: `python-server/src/*_service_implementation.py` and `flansch/src/server/`
- Contains: Service classes with async RPC methods
- Depends on: Database, embeddings, LLM client, chunking strategies
- Used by: FastAPI router (via proto-generated ASGI wrappers)

**Infrastructure Layer:**
- Purpose: Database access, embeddings, LLM communication, configuration
- Location: `python-server/src/` (postgres_db.py, embeddings.py, llm_access.py, config.py, etc.)
- Contains: Connection pools, singleton clients, schema management
- Depends on: External services (PostgreSQL, Ollama, HuggingFace)
- Used by: Service implementations

**Frontend Layer:**
- Purpose: User interface for uploading, browsing, chatting, and graph exploration
- Location: `web-ui/src/`
- Contains: Vue components, Pinia stores, composables (API client wrappers)
- Depends on: Connect RPC transport, backend APIs
- Used by: Browser

## Data Flow

### Primary Request Path: Chat with Vector Retrieval

1. User sends chat message in UI (`web-ui/src/views/Chat.vue`)
2. `useChatApi()` composable calls `ChatService.streamChat()` RPC
3. `ChatServiceImplementation.stream_chat()` processes request:
   - Fetches context documents if provided (`_fetch_context_documents`)
   - Performs vector similarity search via `db.search_similar()` (if auto-retrieval enabled)
   - Builds LLM message chain from user query + retrieved chunks + conversation history
   - Yields metadata chunk with context info
4. `LLMClient.astream()` streams tokens from Ollama via LangChain
5. Frontend receives token stream and appends to message in `useChatStore`

**Files involved:**
- Frontend entry: `web-ui/src/views/Chat.vue`
- API composable: `web-ui/src/composables/useChatApi.ts`
- Backend RPC: `python-server/src/bibliophage/v1alpha3/chat_connect.py` (auto-generated)
- Implementation: `python-server/src/chat_service_implementation.py` (lines 44-100+)
- LLM: `python-server/src/llm_access.py`
- DB: `python-server/src/postgres_db.py` (search_similar method)

### Secondary Flow: PDF Upload & Chunking

1. User uploads PDF in `web-ui/src/views/PdfUpload.vue`
2. `LoadPdfRequest` sent to `PdfService.loadPdf()` RPC
3. `LoadingServiceImplementation.load_pdf()` orchestrates:
   - Validates PDF and systems array
   - Processes PDF via `DoclingPipeline.process_pdf()` (batched OCR, layout, table detection)
   - Extracts markdown-formatted content
   - Stores as Document in PostgreSQL via `db.store_document()`
   - Returns `LoadPdfResponse` with document ID
4. (Separate flow) Frontend calls `EmbeddingService.generateChunks()` to create chunks
5. Chunks are embedded via HuggingFace embeddings and stored in `document_chunks` table with vectors

**Files involved:**
- Frontend: `web-ui/src/views/PdfUpload.vue`
- RPC impl: `python-server/src/loading_service_implementation.py`
- Docling: `python-server/src/docling_pipeline.py`
- DB schema: `python-server/src/db_schema/documents.sql`, `vectors.sql`

### State Management: Frontend

**Chat state** (Pinia store):
- Stores messages, selected context documents, retrieved chunks
- Tracks streaming state (message ID, isStreaming flag)
- Provides actions for appending tokens, toggling docs, clearing messages

**Document state:**
- Stores list of documents from library search
- Tracks selection for bulk operations

**Editor windows state:**
- Manages open editor modals (text editor, chunk editor)

**Graph store:**
- Manages graph visualization state and node relationships

## Key Abstractions

**DocumentContext (Authority-Aware):**
- Purpose: Wraps document content with metadata for LLM ranking
- Location: `python-server/src/llm_access.py` (lines 46-60)
- Pattern: Dataclass with computed `authority_weight` property
- Used in: Chat context building (sorts documents by source_type authority)

**ChunkBoundary:**
- Purpose: Defines start/end positions for text chunks without storing content
- Location: Auto-generated from `api/bibliophage/v1alpha3/embedding.proto`
- Pattern: Used for proposing chunks before generation/storage
- Example: `ChunkBoundary(start=0, end=200, strategy=MARKDOWN_STRUCTURE)`

**Service Singleton Pattern:**
- Purpose: Ensure single instance of expensive resources (DB pools, embedding models, LLM clients)
- Examples:
  - `postgres_db.get_postgres_db()` → `BibliophageDatabase` singleton
  - `embeddings.get_embeddings_model()` → HuggingFaceEmbeddings singleton
  - `llm_access.get_llm_client()` → LLMClient singleton
- Location: `python-server/src/*` (module-level `_instance` variables with getter functions)

**Chunking Strategies:**
- Purpose: Abstract different approaches to splitting document content
- Location: `python-server/src/chunking_strategies.py`
- Strategies: `MARKDOWN_STRUCTURE` (heading-level), `TOKEN_BASED` (token count)

## Entry Points

**Backend HTTP Server:**
- Location: `python-server/src/server.py` (line 57: `api_server`)
- Triggers: `uvicorn server:api_server` command
- Responsibilities:
  - Configure CORS middleware
  - Initialize database schema on startup
  - Mount all service ASGI applications
  - Handle graceful shutdown

**Frontend Entry:**
- Location: `web-ui/src/main.ts` (line 25: `app.mount('#app')`)
- Triggers: Vite dev server or production build
- Responsibilities:
  - Create Vue app instance
  - Install Pinia store
  - Install Vue Router
  - Mount to DOM

**Service Registration:**
- Location: `python-server/src/server.py` (lines 88-94)
- Services mounted: PdfService, DocumentService, ChatService, EmbeddingService, GraphService

## Architectural Constraints

- **Threading:** Python backend is async (uvicorn + asyncio). No explicit worker threads; embedding/LLM calls may use internal threading.
- **Global state:** Singletons for database, embeddings model, LLM client (initialized once per process, safe due to async context)
- **Circular imports:** Handled via late imports (e.g., `from postgres_db import get_postgres_db()` in service implementations to avoid import-time connection attempts)
- **Vector storage:** pgvector HNSW index for O(log n) similarity search. Embeddings are 1024-dimensional (BAAI/bge-large-en-v1.5)
- **Message streaming:** Connect RPC server-streaming for real-time token delivery (ChatService only)
- **Document authority:** Enum-based source types (`RULEBOOK`, `GM_NOTES`, `PLAYER_NOTES`, etc.) with fixed weight multipliers for context ranking

## Error Handling

**Strategy:** Async/await with try-catch blocks at RPC method level. Errors converted to response proto messages (success=false, message="...").

**Patterns:**
- Validation errors return early with `message` field explaining the issue
- Database errors logged and caught, returned as failed RPC response
- Vector search errors don't crash—missing vectors simply omit that document from results
- LLM streaming errors yield ERROR chunk type, then DONE

**Example from ChatService (lines 58-91):**
```python
try:
    context_documents = await self._fetch_context_documents(...)
    retrieved_chunks = await self._fetch_retrieved_chunks(...)
except Exception as e:
    logger.error(...)
    yield api.ChatResponseChunk(
        type=api.ChunkType.ERROR,
        content=str(e)
    )
```

## Cross-Cutting Concerns

**Logging:**
- Approach: Python logging module with stdout handler
- Level: INFO (configurable)
- Pattern: Log service initialization, RPC requests, chunk generation, DB operations

**Validation:**
- Request validation: Protobuf field presence checks (`HasField`), enum validation
- Schema validation: PostgreSQL constraints (NOT NULL, CHECK, REFERENCES)
- Example: `if not request.pdf.systems: return error_response`

**Authentication:**
- Current: None (all endpoints open, suitable for local/internal use)
- CORS: Wildcard (`allow_origins=["*"]`) for local browser access

**Observability:**
- Structured logs with timing information
- Token counts returned in metadata chunks for chat responses
- Document authority scores visible in context metadata

---

*Architecture analysis: 2026-06-07*
