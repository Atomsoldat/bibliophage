## MODIFIED Requirements

### Requirement: Document type is recorded as a tag
A document's type SHALL be represented as a tag named `document_type` with a single value drawn from an open vocabulary (e.g. `note`, `rulebook`, `session_log`), stored and queried through the same generic tag mechanism used for every other document facet. The system SHALL NOT expose a dedicated `type` field, column, or enum for this purpose — this includes `Metadata.publication_type` and `Pdf`/`PdfListItem.type`, which are retired in favor of this tag.

#### Scenario: Storing a document with a type
- **WHEN** a client creates or updates a document and includes a tag named `document_type` with one value
- **THEN** the system stores that value as the document's type via the standard tag storage path, with no separate type column or field involved

#### Scenario: Retrieving a document's type
- **WHEN** a client fetches a document
- **THEN** the document's type is present among its tags as the `document_type` tag, not as a distinct field

#### Scenario: Document created without a type
- **WHEN** a client creates a document without a `document_type` tag
- **THEN** the system stores the document successfully with no `document_type` tag present (the field is no longer required/NOT NULL)

#### Scenario: No dedicated publication-type or PDF-type field exists
- **WHEN** a client builds a request to create, update, or list a document, or to load or list a PDF
- **THEN** no `publication_type` field exists on `Metadata`, and no `type` field exists on `Pdf` or `PdfListItem` — the only way to express a document's kind is the `document_type` tag
