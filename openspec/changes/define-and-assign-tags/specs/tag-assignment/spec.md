## Purpose

Defines how tag values attach to and detach from documents independent of editing a document's content or metadata, and establishes this as the exclusive mechanism for representing open-ended, per-document facets — no dedicated field per facet.

## ADDED Requirements

### Requirement: Tag assignment is independent of document content updates
Assigning or removing a tag value on a document SHALL NOT require sending or replacing the document's name, content, or metadata. Updating a document's name, content, or metadata SHALL NOT alter its tags.

#### Scenario: Assigning a tag does not touch content
- **WHEN** a client assigns a tag value to a document
- **THEN** the document's name, content, and metadata are unchanged

#### Scenario: Updating content does not touch tags
- **WHEN** a client updates a document's name, content, or metadata
- **THEN** the document's tag assignments are unchanged

### Requirement: Tag assignment applies to one or more documents atomically
A single assignment or removal request SHALL accept one or more target documents and apply the same tag/value change to all of them as one operation.

#### Scenario: Assigning to multiple documents
- **WHEN** a client assigns a tag value to several documents in one request
- **THEN** every specified document carries the assignment, and the request fails or succeeds as a whole rather than partially applying

### Requirement: Removing a tag value from a document
A client SHALL be able to remove one specific value of a tag from a document, or remove the tag entirely from a document (all of its values at once), without affecting the tag or value's existence for other documents.

#### Scenario: Removing one value
- **WHEN** a client removes one value of a tag from a document that has multiple values under that tag
- **THEN** that value's assignment is removed and the document's other values under the same tag remain

#### Scenario: Removing a whole tag from a document
- **WHEN** a client removes a tag from a document without specifying a value
- **THEN** every value-assignment of that tag on that document is removed, while the tag and its values remain available for other documents

### Requirement: Assignment requires an existing tag name
Assigning a value under a tag name that does not exist SHALL be rejected, consistent with tag names being created only through tag governance. Assigning a value that does not yet exist under an existing tag SHALL succeed and create the value.

#### Scenario: Assigning under an unknown tag name
- **WHEN** a client assigns a value under a tag name that has not been created
- **THEN** the system rejects the request and no assignment is recorded

#### Scenario: Assigning a new value under a known tag
- **WHEN** a client assigns a value that does not yet exist under an existing tag
- **THEN** the system creates the value and records the assignment

### Requirement: Tags are the exclusive representation of open-ended document facets
The system SHALL NOT expose a dedicated field for an open-ended, per-document facet, such as which RPG system or setting a document belongs to. Any such facet SHALL be represented as an ordinary tag, assigned through this capability like any other tag.

#### Scenario: No dedicated field for a document facet
- **WHEN** a client builds a request to create, update, or ingest a document
- **THEN** no request field exists for RPG-system/setting affiliation or any comparable open-ended facet; expressing it requires assigning a tag

#### Scenario: PDF ingestion accepts tags through the same mechanism
- **WHEN** a PDF is ingested with tags included in the upload
- **THEN** those tags are assigned to the resulting document through the same tag-assignment mechanism used for any other document, with no separate ingestion-specific tagging path
