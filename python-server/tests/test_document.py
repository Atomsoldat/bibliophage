import pytest
from pathlib import Path
import bibliophage.v1alpha3.document_pb2 as doc_api
from bibliophage.v1alpha3.document_connect import DocumentServiceClient


@pytest.mark.asyncio
async def test_store_document_integration():
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
    async with DocumentServiceClient("http://localhost:8000") as client:
        response = await client.store_document(request)

    # Assert response
    assert response.success == True
    assert response.document.name == "Test Bestiary Note"
    assert response.document.character_count == len(markdown_content)
    assert len(response.document.id) > 0
