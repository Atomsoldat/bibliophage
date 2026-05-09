"""Pytest configuration and shared fixtures for integration tests.

This module provides reusable fixtures for test data setup and teardown,
ensuring tests are isolated and idempotent.

Fixtures:
    - sample_pdf: Generates an examplaric PDF from markdown to be used by other tests
    - document_client: Configured DocumentServiceClient for test operations
    - embedding_client: Configured EmbeddingServiceClient for test operations
    - pdf_client: Configured PdfServiceClient for test operations
    - test_document: Creates and cleans up a test document automatically
    - embedded_document: Creates a document and embeds it, cleans up both
    - token_embedded_document: Creates a document with token-based embeddings
"""

import logging
import os

import pytest

import bibliophage.v1alpha3.document_pb2 as doc_api
import bibliophage.v1alpha3.embedding_pb2 as emb_api
from bibliophage.v1alpha3.document_connect import DocumentServiceClient
from bibliophage.v1alpha3.embedding_connect import EmbeddingServiceClient
from bibliophage.v1alpha3.pdf_connect import PdfServiceClient

logger = logging.getLogger(__name__)

# Test configuration - can be overridden via environment variable
TEST_SERVER_URL = os.getenv("TEST_SERVER_URL", "http://localhost:8000")


# this decorator allows tests to use this function as an argument
# the function is automatically called and returns the path to our pdf
# tmp_path is a fixture built into pytest, which handles the creation and cleanup for us
@pytest.fixture
def sample_pdf(tmp_path):
    """Generate PDF from markdown fixture."""
    fixture_dir = Path(__file__).parent / "data"
    md_file = fixture_dir / "bestiary_sample.md"
    pdf_file = tmp_path / "bestiary_sample.pdf"

    subprocess.run(["pandoc", str(md_file), "-o", str(pdf_file)], check=True)
    return pdf_file


@pytest.fixture
async def document_client():
    """Provide a DocumentServiceClient for tests.

    Yields:
        DocumentServiceClient: Connected client instance

    Note:
        The client connection is automatically cleaned up after the test.

    """
    async with DocumentServiceClient(TEST_SERVER_URL) as client:
        yield client


@pytest.fixture
async def embedding_client():
    """Provide an EmbeddingServiceClient for tests.

    Yields:
        EmbeddingServiceClient: Connected client instance

    Note:
        The client connection is automatically cleaned up after the test.

    """
    async with EmbeddingServiceClient(TEST_SERVER_URL) as client:
        yield client


@pytest.fixture
async def pdf_client():
    """Provide a PdfServiceClient for tests.

    Yields:
        PdfServiceClient: Connected client instance

    Note:
        The client connection is automatically cleaned up after the test.

    """
    async with PdfServiceClient(TEST_SERVER_URL) as client:
        yield client


@pytest.fixture
async def test_document(document_client):
    """Create a test document and automatically clean it up after the test.

    This fixture follows the setup-yield-teardown pattern:
    1. Setup: Creates a document via DocumentService
    2. Yield: Provides the document to the test
    3. Teardown: Deletes the document (even if test fails)

    Args:
        document_client: The DocumentServiceClient fixture

    Yields:
        Document: The created test document with id, name, content, etc.

    Example:
        @pytest.mark.asyncio
        async def test_something(test_document):
            # Document already exists, just use it
            assert test_document.id is not None
            # Automatic cleanup happens after test

    """
    # Setup: Create test document
    doc_request = doc_api.StoreDocumentRequest()
    doc_request.document.name = "Test Document (auto-cleanup)"
    doc_request.document.systems.append("Test System")
    doc_request.document.type = doc_api.NOTE
    doc_request.document.source_type = doc_api.GM_NOTES
    doc_request.document.content = (
        "# Test Content\n"
        "This is a test document created by pytest fixtures.\n\n"
        "## Section 1\n"
        "Some test content here.\n\n"
        "## Section 2\n"
        "More test content."
    )

    response = await document_client.store_document(doc_request)
    document = response.document

    # Yield to test
    yield document

    # Teardown: Clean up the document
    try:
        delete_request = doc_api.DeleteDocumentRequest()
        delete_request.id = document.id
        await document_client.delete_document(delete_request)
        logger.debug(f"Cleaned up test document {document.id}")
    except Exception as e:
        logger.warning(
            f"Failed to cleanup test document {document.id}: {e}",
            exc_info=True,
        )


@pytest.fixture
async def embedded_document(test_document, embedding_client):
    """Create a test document with embeddings, clean up both after test.

    This fixture builds on test_document by adding embeddings to it.
    Cleanup is handled in reverse order: embeddings first, then document
    (via test_document's teardown).

    Args:
        test_document: The test_document fixture (provides base document)
        embedding_client: The EmbeddingServiceClient fixture

    Yields:
        tuple[Document, EmbedDocumentResponse]: The document and embedding response

    Example:
        @pytest.mark.asyncio
        async def test_search(embedded_document):
            document, embed_response = embedded_document
            # Document is already embedded, test search functionality
            assert embed_response.embedding_status.is_embedded == True

    """
    # Setup: Embed the test document
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.config.max_heading_level = 2

    embed_response = await embedding_client.embed_document(emb_request)

    # Yield to test
    yield (test_document, embed_response)

    # Teardown: Clean up embeddings
    try:
        delete_request = emb_api.DeleteEmbeddingsRequest()
        delete_request.document_id = test_document.id
        await embedding_client.delete_embeddings(delete_request)
        logger.debug(f"Cleaned up embeddings for document {test_document.id}")
    except Exception as e:
        logger.warning(
            f"Failed to cleanup embeddings for {test_document.id}: {e}",
            exc_info=True,
        )


# Alternative fixture with different embedding strategy
@pytest.fixture
async def token_embedded_document(test_document, embedding_client):
    """Create a test document with token-based embeddings.

    Similar to embedded_document but uses TOKEN_BASED strategy instead
    of MARKDOWN_STRUCTURE. Useful for testing different chunking strategies.

    Args:
        test_document: The test_document fixture
        embedding_client: The EmbeddingServiceClient fixture

    Yields:
        tuple[Document, EmbedDocumentResponse]: The document and embedding response

    """
    # Setup: Embed with token-based strategy
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.TOKEN_BASED
    emb_request.config.max_chunk_size = 512

    embed_response = await embedding_client.embed_document(emb_request)

    # Yield to test
    yield (test_document, embed_response)

    # Teardown: Clean up embeddings
    try:
        delete_request = emb_api.DeleteEmbeddingsRequest()
        delete_request.document_id = test_document.id
        await embedding_client.delete_embeddings(delete_request)
        logger.debug(f"Cleaned up embeddings for document {test_document.id}")
    except Exception as e:
        logger.warning(
            f"Failed to cleanup embeddings for {test_document.id}: {e}",
            exc_info=True,
        )
