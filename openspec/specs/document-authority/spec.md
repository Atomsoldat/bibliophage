# document-authority Specification

## Purpose

Defines how documents are treated when assembled into LLM context: with no source-authority classification, every document is weighted, ordered, and presented identically regardless of where it came from.

## Requirements

### Requirement: Documents carry no authority/trust classification
The system SHALL NOT expose a source-authority or trust-level field on documents (no `source_type` field, column, or enum). No document is more or less authoritative than another by virtue of a stored classification.

#### Scenario: Storing a document
- **WHEN** a client creates or updates a document
- **THEN** the system accepts the request with no source-authority field present or required

#### Scenario: Retrieving a document
- **WHEN** a client fetches a document
- **THEN** the returned document has no source-authority field

### Requirement: LLM context assembly treats all documents equally
When building context for LLM prompts (chat, generation, summarisation), the system SHALL NOT sort, weight, or label documents by source authority. All documents SHALL be presented with equal standing.

#### Scenario: Context ordering
- **WHEN** multiple documents are assembled into a single LLM context
- **THEN** their relative order is not determined by any authority ranking (whatever order they're supplied or retrieved in is preserved)

#### Scenario: Context formatting
- **WHEN** a document is formatted into the context prompt
- **THEN** its source attribution includes the document's name but no authority label (e.g. no "Official Rules" / "Player Notes" / "LLM-Generated" designation)

### Requirement: Chat responses report no per-document authority score
The system SHALL NOT include an authority score or weight for context documents in chat response metadata.

#### Scenario: Streaming chat metadata
- **WHEN** a chat response's metadata chunk lists the context documents used
- **THEN** each entry includes no authority score field
