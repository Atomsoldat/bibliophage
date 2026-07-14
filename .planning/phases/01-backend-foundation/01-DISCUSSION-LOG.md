# Phase 1: Backend Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-08
**Phase:** 1-Backend Foundation
**Areas discussed:** Update semantics, Systems/tags data model, Restructuring strategy, Ordering & dependencies

---

## Update Semantics

### Q1: Field handling strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Full replace | Client always sends the complete document. Backend replaces all fields. Simple, predictable. | ✓ |
| Mask-based partial | Add a FieldMask to the proto to specify which fields to update. More flexible but requires proto change. | |
| Ignore empty strings | Treat empty string as 'don't update'. Quick but prevents intentionally clearing a field. | |

**User's choice:** Full replace
**Notes:** None

### Q2: Embedding staleness on content change

| Option | Description | Selected |
|--------|-------------|----------|
| Flag stale | Set embeddings_current=false. Re-embedding happens separately. Keeps update fast. | ✓ |
| Re-embed inline | Trigger re-embedding inside the update call. Consistent but slow. | |

**User's choice:** Flag stale
**Notes:** None

### Q3: Response content

| Option | Description | Selected |
|--------|-------------|----------|
| Return full document | Re-fetch from DB so frontend gets server-set fields (updated_at, character_count). | ✓ |
| Success only | Just return success=true. Frontend keeps its local copy. | |

**User's choice:** Return full document
**Notes:** None

### Q4: Non-existent document ID

| Option | Description | Selected |
|--------|-------------|----------|
| Return error response | Set success=false with 'Document not found'. No upsert. | ✓ |
| Upsert | Create the document if it doesn't exist. | |

**User's choice:** Return error response
**Notes:** None

---

## Systems/Tags Data Model

### Q1: System resolution strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Upsert by title | Look up by title, create if not found. Simple for users. | |
| Must pre-exist | Only link to systems already in the table. Error if not found. | ✓ |
| Store as strings directly | Skip lookup table, store names in text[] column. | |

**User's choice:** Must pre-exist
**Notes:** None

### Q2: Unknown system handling

| Option | Description | Selected |
|--------|-------------|----------|
| Fail the whole operation | Return error if any system name can't be resolved. Strict. | ✓ |
| Skip unknown, warn | Store document but skip unrecognized systems with warning. | |
| Skip unknown, silent | Silently ignore unrecognized system names. | |

**User's choice:** Fail the whole operation
**Notes:** None

### Q3: Tag value storage

| Option | Description | Selected |
|--------|-------------|----------|
| Values as JSONB in info | Store tag values array as JSON in existing info column. No schema change. | ✓ |
| Add values column | Add text[] column to tags table. Cleaner but requires migration. | |
| Flatten to name:value pairs | Store each value as separate row. Simple to query but loses grouping. | |

**User's choice:** Values as JSONB in info
**Notes:** None

### Q4: Tag existence policy

| Option | Description | Selected |
|--------|-------------|----------|
| Upsert by name | Auto-create new tags when referenced. More fluid. | |
| Must pre-exist | Same strict rule as systems. Fail on unknown. | ✓ |

**User's choice:** Must pre-exist
**Notes:** Consistent with systems policy

---

## Restructuring Strategy

### Q1: Execution approach

| Option | Description | Selected |
|--------|-------------|----------|
| Big bang | Move all files in one commit. Update all imports. Clean break. | ✓ |
| Domain by domain | Move one domain at a time with __init__.py re-exports. | |
| You decide | Let the planner figure it out. | |

**User's choice:** Big bang
**Notes:** None

### Q2: Shared utilities location

| Option | Description | Selected |
|--------|-------------|----------|
| Keep at src/ root | proto_converters.py, config.py, server.py stay at root. Cross-cutting. | ✓ |
| Create shared/ package | Move into src/shared/. Cleaner root. | |
| Split converters per domain | Each domain gets its own converters.py. | |

**User's choice:** Keep at src/ root
**Notes:** None

### Q3: STRUCT-03 re-exports

| Option | Description | Selected |
|--------|-------------|----------|
| Skip re-exports | Big bang updates all imports. Re-exports would be dead code. | ✓ |
| Keep re-exports briefly | Add anyway for safety, remove in follow-up. | |

**User's choice:** Skip re-exports
**Notes:** None

---

## Ordering & Dependencies

### Q1: Workstream execution order

| Option | Description | Selected |
|--------|-------------|----------|
| Restructure first | Pure refactor first, then junction tables, then update_document. | ✓ |
| Fix bug first | Implement update_document first, then restructure. | |
| Interleave | Create db/ first, wire tables, then restructure rest. | |

**User's choice:** Restructure first
**Notes:** None

### Q2: Plan granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Separate plans | Three plans: (1) restructure, (2) junction tables, (3) update_document. | ✓ |
| Combined plan | One plan covers junction tables and update_document together. | |

**User's choice:** Separate plans
**Notes:** None

---

## Claude's Discretion

- Exact file-to-domain-package mapping (which files go into which domain directory)
- SQL query construction for junction table JOINs

## Deferred Ideas

None — discussion stayed within phase scope.
