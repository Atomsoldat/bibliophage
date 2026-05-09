"""Integration tests for the Embedding Service.

Tests cover embedding creation, deletion, and status verification using
pytest fixtures for automatic setup and teardown.
"""

import pytest

import bibliophage.v1alpha3.embedding_pb2 as emb_api


@pytest.mark.integration
async def test_embed_document_with_markdown_strategy(test_document, embedding_client):
    """Test embedding a document using MARKDOWN_STRUCTURE strategy.

    Verifies that:
    - Document can be successfully embedded
    - Embedding status is correctly set
    - Chunks are created from the markdown structure
    """
    # Embed the test document with markdown strategy
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.config.max_heading_level = 2

    response = await embedding_client.embed_document(emb_request)

    # Verify embedding succeeded
    assert response.success is True
    assert response.embedding_status.is_embedded is True
    assert response.embedding_status.embeddings_current is True
    assert response.embedding_status.total_chunks > 0


@pytest.mark.integration
async def test_embed_document_with_token_strategy(test_document, embedding_client):
    """Test embedding a document using TOKEN_BASED strategy.

    Verifies that token-based chunking works correctly.
    """
    # Embed the test document with token-based strategy
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.TOKEN_BASED
    emb_request.config.token_chunk_size = 512

    response = await embedding_client.embed_document(emb_request)

    # Verify embedding succeeded
    assert response.success is True
    assert response.embedding_status.is_embedded is True
    assert response.embedding_status.total_chunks > 0


@pytest.mark.integration
async def test_delete_embeddings(embedded_document, embedding_client):
    """Test deleting embeddings for a document.

    Verifies that:
    - Embeddings can be successfully deleted
    - The correct number of chunks are deleted
    """
    document, embed_response = embedded_document
    expected_chunks = embed_response.embedding_status.total_chunks

    # Delete embeddings
    delete_request = emb_api.DeleteEmbeddingsRequest()
    delete_request.document_id = document.id

    delete_response = await embedding_client.delete_embeddings(delete_request)

    # Verify deletion succeeded
    assert delete_response.success is True
    assert delete_response.chunks_deleted == expected_chunks


@pytest.mark.integration
async def test_re_embed_document_updates_chunks(test_document, embedding_client):
    """Test that re-embedding a document replaces old chunks.

    Verifies that embedding the same document twice doesn't duplicate chunks.
    """
    # First embedding
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.config.max_heading_level = 2

    first_response = await embedding_client.embed_document(emb_request)
    first_chunk_count = first_response.embedding_status.total_chunks

    # Second embedding (should replace, not duplicate)
    second_response = await embedding_client.embed_document(emb_request)
    second_chunk_count = second_response.embedding_status.total_chunks

    # Chunk counts should be the same (no duplicates)
    assert second_chunk_count == first_chunk_count
    assert second_response.embedding_status.embeddings_current is True
