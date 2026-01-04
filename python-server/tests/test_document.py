import logging
from pathlib import Path

import pytest

import bibliophage.v1alpha3.document_pb2 as doc_api

logger = logging.getLogger(__name__)


@pytest.mark.integration
async def test_store_document_integration(document_client):
    """Integration test: Store a markdown document via the Document service API."""
    # Read markdown content
    fixture_dir = Path(__file__).parent / "data"
    md_file = fixture_dir / "bestiary_sample.md"
    markdown_content = md_file.read_text()

    # Create request
    request = doc_api.StoreDocumentRequest()
    request.document.name = "Test Bestiary Note"
    request.document.systems.append("Fantasy RPG")
    # technically this is not a note, but we will go with it for now
    # since bestiaries would normally not show up in the journal
    request.document.type = doc_api.NOTE
    request.document.source_type = doc_api.GM_NOTES
    request.document.content = markdown_content

    # Call service
    response = await document_client.store_document(request)

    # Assert response
    assert response.success is True
    assert response.document.name == "Test Bestiary Note"
    assert response.document.character_count == len(markdown_content)
    assert len(response.document.id) > 0

    # Cleanup: Delete the document we created
    try:
        delete_request = doc_api.DeleteDocumentRequest()
        delete_request.id = response.document.id
        await document_client.delete_document(delete_request)
        logger.debug(f"Cleaned up document {response.document.id}")
    except Exception as e:
        logger.warning(f"Failed to cleanup document: {e}", exc_info=True)


@pytest.mark.integration
async def test_delete_document(test_document, document_client):
    """Test deleting a document."""
    # Delete the test document
    delete_request = doc_api.DeleteDocumentRequest()
    delete_request.id = test_document.id

    response = await document_client.delete_document(delete_request)

    # Assert deletion succeeded
    assert response.success is True
