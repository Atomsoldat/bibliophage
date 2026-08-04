## Purpose

Defines how a document's kind (note, rulebook, session log, etc.) is recorded and set, using the general-purpose tag system instead of a dedicated enum field, so the vocabulary of types can grow without an API/schema change.

## ADDED Requirements

### Requirement: Document type is recorded as a tag
A document's type SHALL be represented as a tag named `document_type` with a single value drawn from an open vocabulary (e.g. `note`, `rulebook`, `session_log`), stored and queried through the same generic tag mechanism used for every other document facet. The system SHALL NOT expose a dedicated `type` field, column, or enum for this purpose.

#### Scenario: Storing a document with a type
- **WHEN** a client creates or updates a document and includes a tag named `document_type` with one value
- **THEN** the system stores that value as the document's type via the standard tag storage path, with no separate type column or field involved

#### Scenario: Retrieving a document's type
- **WHEN** a client fetches a document
- **THEN** the document's type is present among its tags as the `document_type` tag, not as a distinct field

#### Scenario: Document created without a type
- **WHEN** a client creates a document without a `document_type` tag
- **THEN** the system stores the document successfully with no `document_type` tag present (the field is no longer required/NOT NULL)

### Requirement: PDF ingestion does not infer a document type
The system SHALL NOT infer or assign a `document_type` tag automatically during PDF ingestion. A `document_type` tag is only present on an ingested document if the user explicitly included it among the upload's tags. The PDF's declared type string SHALL continue to independently determine the document's `source_type` (authority weighting) exactly as before — that inference is unrelated to and unaffected by this requirement.

#### Scenario: Ingesting a PDF without an explicit document_type tag
- **WHEN** a PDF is ingested and the upload's tags do not include a `document_type` tag
- **THEN** the stored document has no `document_type` tag, regardless of the PDF's declared type string

#### Scenario: Ingesting a PDF with an explicit document_type tag
- **WHEN** a PDF is ingested and the upload's tags include a `document_type` tag with a value chosen by the user
- **THEN** the stored document has that `document_type` tag, stored exactly as provided, unmodified by any classification logic

#### Scenario: Source type authority weighting is unaffected
- **WHEN** a PDF is ingested whose declared type string contains "rulebook", "core", "supplement", "expansion", "adventure", "bestiary", or "monster"
- **THEN** the stored document's `source_type` is derived from that string exactly as before (e.g. `CORE` for "rulebook"/"core", `SUPPLEMENT` for the others), independent of whether a `document_type` tag is present

### Requirement: Document type filtering is not provided by this capability
The system SHALL NOT provide a dedicated document-type search/filter field (equivalent to the former `type_filters`). Filtering documents by type is out of scope for this capability and deferred to the general tag-filtering capability.

#### Scenario: Searching without a type filter field
- **WHEN** a client searches for documents
- **THEN** no request field exists for filtering specifically by document type; filtering by the `document_type` tag is unavailable until tag-based filtering is implemented as a separate capability
