## MODIFIED Requirements

### Requirement: Document type is recorded as a tag
A document's type SHALL be represented as one or more tags named `document_type`, each with a value drawn from an open vocabulary (e.g. `note`, `rulebook`, `session_log`), stored and queried through the same generic tag mechanism used for every other document facet. The system SHALL NOT expose a dedicated `type` field, column, or enum for this purpose — this includes `Metadata.publication_type` and `Pdf`/`PdfListItem.type`, which are retired in favor of this tag. Every document SHALL have at least one `document_type` value at all times; a document with no `document_type` tag explicitly set is assigned one automatically rather than left untyped.

#### Scenario: Storing a document with a type
- **WHEN** a client creates or updates a document and includes one or more `document_type` tag values
- **THEN** the system stores those values as the document's type(s) via the standard tag storage path, with no separate type column or field involved

#### Scenario: Retrieving a document's type
- **WHEN** a client fetches a document
- **THEN** the document's type(s) are present among its tags as `document_type` tag values, not as a distinct field

#### Scenario: Document created without an explicit type
- **WHEN** a client creates a document without including a `document_type` tag
- **THEN** the system assigns a `document_type` value automatically — an avenue-of-ingress-appropriate default where one reasonably exists, or `"generic"` otherwise — rather than storing the document with no `document_type` tag

#### Scenario: Document tagged with more than one type
- **WHEN** a client creates or updates a document with more than one `document_type` value
- **THEN** the system stores all of the given values, with no restriction to a single value

## REMOVED Requirements

### Requirement: PDF ingestion does not infer a document type
**Reason**: This constraint kept the `publication_type`/`Pdf.type`-to-tag migration honest — during that transition, ingestion was deliberately barred from inventing `document_type` values so migrated data wouldn't be silently overwritten with a guess. `document_type` is now mandatory rather than an optional migration artifact (see "Document type is recorded as a tag" above), so avenue-of-ingress-based inference is desired behavior, not a migration risk.
**Migration**: PDF ingestion without an explicit `document_type` tag now falls under "Document created without an explicit type" above — it receives an avenue-appropriate default (or `"generic"`) instead of being left untyped.
