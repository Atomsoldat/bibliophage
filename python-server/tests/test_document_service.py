"""Tests for DocumentService v1alpha2 implementation."""


import pytest
from unittest.mock import AsyncMock

import bibliophage.v1alpha2.document_pb2 as api
from document_service_implementation import DocumentServiceImplementation


@pytest.fixture
def document_service(mock_database):
    """Create a DocumentServiceImplementation instance for testing.

    The mock_database fixture from conftest.py is automatically applied,
    so this service will use the mocked database.
    """
    return DocumentServiceImplementation()


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    doc = api.Document()
    doc.name = "Test Document"
    doc.content = "This is test content for the document."
    doc.type = api.DocumentType.NOTE
    return doc


@pytest.mark.asyncio
async def test_store_document_assigns_id(document_service, sample_document):
    """Test that store_document assigns a UUID to the document."""
    request = api.StoreDocumentRequest(document=sample_document)

    response = await document_service.store_document(request, None)

    assert response.success is True
    assert response.document.id != ""
    assert len(response.document.id) == 36  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx


@pytest.mark.asyncio
async def test_store_document_sets_timestamps(document_service, sample_document):
    """Test that store_document sets created_at and updated_at timestamps."""
    request = api.StoreDocumentRequest(document=sample_document)

    response = await document_service.store_document(request, None)

    assert response.document.HasField("created_at")
    assert response.document.HasField("updated_at")
    # Both timestamps should be approximately now
    assert response.document.created_at.seconds > 0
    assert response.document.updated_at.seconds > 0


@pytest.mark.asyncio
async def test_store_document_sets_character_count(document_service, sample_document):
    """Test that store_document calculates character count correctly."""
    request = api.StoreDocumentRequest(document=sample_document)

    response = await document_service.store_document(request, None)

    assert response.document.character_count == len(sample_document.content)


@pytest.mark.asyncio
async def test_store_document_preserves_name_and_content(document_service, sample_document):
    """Test that store_document preserves the document name and content."""
    request = api.StoreDocumentRequest(document=sample_document)

    response = await document_service.store_document(request, None)

    assert response.document.name == sample_document.name
    assert response.document.content == sample_document.content


@pytest.mark.asyncio
async def test_store_document_preserves_type(document_service, sample_document):
    """Test that store_document preserves the document type."""
    request = api.StoreDocumentRequest(document=sample_document)

    response = await document_service.store_document(request, None)

    assert response.document.type == sample_document.type


@pytest.mark.asyncio
async def test_store_document_preserves_tags(document_service):
    """Test that store_document preserves tags."""
    doc = api.Document()
    doc.name = "Tagged Document"
    doc.content = "Content with tags"

    # Add tags
    tag1 = doc.tags.add()
    tag1.name = "genre"
    tag1.values.extend(["fantasy", "adventure"])

    tag2 = doc.tags.add()
    tag2.name = "world"
    tag2.values.append("forgotten-realms")

    request = api.StoreDocumentRequest(document=doc)
    response = await document_service.store_document(request, None)

    assert len(response.document.tags) == 2
    assert response.document.tags[0].name == "genre"
    assert list(response.document.tags[0].values) == ["fantasy", "adventure"]
    assert response.document.tags[1].name == "world"
    assert list(response.document.tags[1].values) == ["forgotten-realms"]


@pytest.mark.asyncio
async def test_update_document_updates_timestamp(document_service, sample_document):
    """Test that update_document updates the updated_at timestamp."""
    # First store a document
    sample_document.id = "test-id-123"
    sample_document.content = "Original content"

    request = api.UpdateDocumentRequest(document=sample_document)
    response = await document_service.update_document(request, None)

    assert response.success is True
    assert response.document.HasField("updated_at")


@pytest.mark.asyncio
async def test_update_document_updates_character_count(document_service):
    """Test that update_document recalculates character count."""
    doc = api.Document()
    doc.id = "test-id-123"
    doc.name = "Updated Document"
    doc.content = "New content with different length"

    request = api.UpdateDocumentRequest(document=doc)
    response = await document_service.update_document(request, None)

    assert response.document.character_count == len(doc.content)


# TODO: Update these tests to work with the new database-backed implementation
# The tests below need to be updated because we've implemented actual database operations.

@pytest.mark.asyncio
async def test_get_document_not_implemented(document_service):
    """Test that get_document returns not implemented message."""
    request = api.GetDocumentRequest(id="test-id-123")

    response = await document_service.get_document(request, None)

    assert response.success is False
    assert "not yet implemented" in response.message.lower()


@pytest.mark.asyncio
async def test_search_documents_not_implemented(document_service):
    """Test that search_documents returns empty results.

    Note: response.documents will be a list of DocumentListItem (not Document)
    when this is fully implemented.
    """
    request = api.SearchDocumentsRequest(
        name_query="test",
        page_size=10,
        page_number=0,
    )

    response = await document_service.search_documents(request, None)

    assert response.success is True
    assert len(response.documents) == 0
    assert response.total_count == 0
    assert response.has_more is False


@pytest.mark.asyncio
async def test_delete_document_not_implemented(document_service):
    """Test that delete_document returns not implemented message."""
    request = api.DeleteDocumentRequest(id="test-id-123")

    response = await document_service.delete_document(request, None)

    assert response.success is True
    assert "not yet implemented" in response.message.lower()


@pytest.mark.asyncio
async def test_store_document_with_all_document_types(document_service):
    """Test storing documents with different document types."""
    types_to_test = [
        api.DocumentType.NOTE,
        api.DocumentType.LORE_FRAGMENT,
        api.DocumentType.CHARACTER,
        api.DocumentType.LOCATION,
        api.DocumentType.OBJECT,
        api.DocumentType.QUEST,
        api.DocumentType.SESSION_LOG,
    ]

    for doc_type in types_to_test:
        doc = api.Document()
        doc.name = f"Test {doc_type}"
        doc.content = f"Content for {doc_type}"
        doc.type = doc_type

        request = api.StoreDocumentRequest(document=doc)
        response = await document_service.store_document(request, None)

        assert response.success is True
        assert response.document.type == doc_type
