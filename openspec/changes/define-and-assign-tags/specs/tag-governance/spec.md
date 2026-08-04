## Purpose

Defines how tag names and their values are created, renamed, colored, and removed — the governance layer that determines which tag names exist, since every other capability that assigns a tag to a document depends on the tag name already existing here.

## ADDED Requirements

### Requirement: Tag names are created explicitly
A tag name SHALL only come into existence through an explicit creation action in this capability. No other capability (document creation, document update, or PDF ingestion) SHALL create a new tag name as a side effect of assigning a value.

#### Scenario: Creating a new tag name
- **WHEN** a client creates a tag with a name that does not already exist
- **THEN** the system creates the tag and it becomes available for value assignment

#### Scenario: Assigning to an unknown tag name is rejected
- **WHEN** a client attempts to assign a value under a tag name that does not exist
- **THEN** the system rejects the request without creating the tag

### Requirement: Tag values are created implicitly on assignment
Unlike tag names, a tag value SHALL be created automatically the first time it is assigned to a document under an existing tag, without requiring a separate creation step. This capability SHALL also allow a value to be created explicitly, ahead of any document using it.

#### Scenario: Assigning an unseen value auto-creates it
- **WHEN** a client assigns a value to a document under an existing tag, and that value does not yet exist under that tag
- **THEN** the system creates the value and records the assignment in the same operation

#### Scenario: Explicitly seeding a value
- **WHEN** a client creates a value under an existing tag without assigning it to any document
- **THEN** the value exists and is available for assignment and for autocomplete, even though no document currently carries it

### Requirement: Tags and values can be renamed
A tag name or a tag value SHALL be renameable. A rename that collides with another existing name or value in the same scope SHALL be rejected without altering either the source or the colliding target.

#### Scenario: Renaming a tag
- **WHEN** a client renames a tag to a name that is not already in use
- **THEN** the tag's name changes and all existing value and document associations are preserved unchanged

#### Scenario: Renaming into a collision
- **WHEN** a client renames a tag or a value to a name or value that already exists
- **THEN** the system rejects the rename and leaves both the source and the colliding target unchanged

### Requirement: Tags and values can be deleted
Deleting a tag SHALL remove the tag, all of its values, and every document's assignment to it. Deleting a single value SHALL remove that value and every document's assignment to it, without affecting the tag's other values.

#### Scenario: Deleting a tag
- **WHEN** a client deletes a tag
- **THEN** the tag, its values, and all document assignments to it are removed, and documents that had other tags remain otherwise unaffected

#### Scenario: Deleting a single value
- **WHEN** a client deletes one value under a tag
- **THEN** that value and every document's assignment to it are removed, other values under the same tag are unaffected, and documents keep any other tag or value assignments they had

### Requirement: Tags and values expose usage counts
Listing tags SHALL report, per tag, the number of distinct values it has and the number of documents that carry it. Listing a tag's values SHALL report, per value, the number of documents that carry it. This SHALL be sufficient for a caller to show the impact of a deletion before it happens, without an additional request.

#### Scenario: Listing tags shows impact
- **WHEN** a client lists tags
- **THEN** each returned tag includes its value count and the number of documents that carry it

#### Scenario: Listing values shows impact
- **WHEN** a client lists a tag's values
- **THEN** each returned value includes the number of documents that carry it

### Requirement: Tags support a display color
A tag SHALL support an optional display color, independent of its name and values, settable and changeable at any time.

#### Scenario: Setting a tag's color
- **WHEN** a client sets or changes a tag's color
- **THEN** subsequent reads of that tag return the new color, and no document association is affected

### Requirement: Merging tags or values is not provided by this capability
The system SHALL NOT provide an operation that combines two tag names, or two values under the same tag, into one.

#### Scenario: No merge operation exists
- **WHEN** a client looks for a way to combine two tags or two values into one
- **THEN** no such operation exists in this capability; resolving a duplicate requires reassigning affected documents by hand and deleting the redundant tag or value
