"""Tests for differential re-embedding (reconciliation).

Integration tests verify that embed_document with desired_boundaries correctly:
- Skips unchanged chunks
- Deletes orphaned chunks
- Embeds only new/modified boundaries

Unit tests verify the _diff_boundaries set logic in isolation.
"""

import pytest

import bibliophage.v1alpha3.embedding_pb2 as emb_api
from embedding_service_implementation import EmbeddingServiceImplementation


@pytest.mark.integration
async def test_reconcile_skips_unchanged_boundaries(embedded_document, embedding_client):
    """Sending the same boundaries back should skip all chunks (nothing to embed or delete)."""
    document, first_embed = embedded_document
    original_chunk_count = first_embed.embedding_status.total_chunks

    # Fetch the current boundaries
    get_request = emb_api.GetChunkBoundariesRequest()
    get_request.document_id = document.id
    boundaries_response = await embedding_client.get_chunk_boundaries(get_request)

    assert boundaries_response.success is True
    assert len(boundaries_response.boundaries) == original_chunk_count

    # Re-embed with the exact same boundaries (reconciliation should skip all)
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.desired_boundaries.extend(boundaries_response.boundaries)

    response = await embedding_client.embed_document(emb_request)

    assert response.success is True
    assert response.embedding_status.total_chunks == original_chunk_count
    assert "embedded 0" in response.message
    assert "deleted 0" in response.message


@pytest.mark.integration
async def test_reconcile_embeds_modified_boundary(embedded_document, embedding_client):
    """Changing one boundary's end position should re-embed only that chunk."""
    document, first_embed = embedded_document
    original_chunk_count = first_embed.embedding_status.total_chunks

    # Fetch the current boundaries
    get_request = emb_api.GetChunkBoundariesRequest()
    get_request.document_id = document.id
    boundaries_response = await embedding_client.get_chunk_boundaries(get_request)

    boundaries = list(boundaries_response.boundaries)
    assert len(boundaries) >= 2, "Need at least 2 chunks to test modification"

    # Modify the last boundary: shift char_end back by 1
    last = boundaries[-1]
    last.char_end = last.char_end - 1

    # Re-embed with modified boundaries
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.desired_boundaries.extend(boundaries)

    response = await embedding_client.embed_document(emb_request)

    assert response.success is True
    # Total chunks stays the same (1 deleted + 1 new = net zero change)
    assert response.embedding_status.total_chunks == original_chunk_count
    assert "embedded 1" in response.message
    assert "deleted 1" in response.message


@pytest.mark.integration
async def test_reconcile_deletes_orphaned_chunks(embedded_document, embedding_client):
    """Sending fewer boundaries than exist should delete the orphans."""
    document, first_embed = embedded_document
    original_chunk_count = first_embed.embedding_status.total_chunks

    # Fetch the current boundaries
    get_request = emb_api.GetChunkBoundariesRequest()
    get_request.document_id = document.id
    boundaries_response = await embedding_client.get_chunk_boundaries(get_request)

    boundaries = list(boundaries_response.boundaries)
    assert len(boundaries) >= 2, "Need at least 2 chunks to test deletion"

    # Drop the last boundary
    boundaries_without_last = boundaries[:-1]

    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.desired_boundaries.extend(boundaries_without_last)

    response = await embedding_client.embed_document(emb_request)

    assert response.success is True
    assert response.embedding_status.total_chunks == original_chunk_count - 1
    assert "embedded 0" in response.message
    assert "deleted 1" in response.message


@pytest.mark.integration
async def test_reconcile_against_unembedded_document(test_document, embedding_client):
    """Sending desired_boundaries for a never-embedded document should embed all of them."""
    # First, propose boundaries so we have something realistic to send
    propose_request = emb_api.ProposeChunksRequest()
    propose_request.document_id = test_document.id
    propose_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    propose_request.config.max_heading_level = 2

    proposal = await embedding_client.propose_chunks(propose_request)
    assert proposal.success is True

    boundaries = list(proposal.proposal.boundaries)
    assert len(boundaries) > 0

    # Embed with desired_boundaries on a document that has no existing chunks
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.desired_boundaries.extend(boundaries)

    response = await embedding_client.embed_document(emb_request)

    assert response.success is True
    assert response.embedding_status.total_chunks == len(boundaries)
    assert f"embedded {len(boundaries)}" in response.message
    assert "deleted 0" in response.message


# ── unit tests for _diff_boundaries ────────────────────────────────────


def _make_boundary(char_start, char_end):
    """Helper to create a ChunkBoundary proto with just positions."""
    return emb_api.ChunkBoundary(char_start=char_start, char_end=char_end)


def _make_db_row(chunk_id, start, end):
    """Helper to create a dict matching the shape returned by get_boundaries_for_document."""
    return {"chunk_id": chunk_id, "start_position": start, "end_position": end}


@pytest.mark.unit
def test_diff_no_changes():
    """Identical boundaries produce empty diff."""
    desired = [_make_boundary(0, 100), _make_boundary(100, 200)]
    current = [_make_db_row("a", 0, 100), _make_db_row("b", 100, 200)]

    diff = EmbeddingServiceImplementation._diff_boundaries(desired, current)

    assert diff.to_embed == []
    assert diff.to_delete == []


@pytest.mark.unit
def test_diff_one_modified():
    """Changing one boundary's end marks it for embed and the old one for delete."""
    desired = [_make_boundary(0, 100), _make_boundary(100, 250)]
    current = [_make_db_row("a", 0, 100), _make_db_row("b", 100, 200)]

    diff = EmbeddingServiceImplementation._diff_boundaries(desired, current)

    assert len(diff.to_embed) == 1
    assert diff.to_embed[0].char_end == 250
    assert diff.to_delete == ["b"]


@pytest.mark.unit
def test_diff_orphan_deleted():
    """Fewer desired boundaries means the extra existing chunk is orphaned."""
    desired = [_make_boundary(0, 100)]
    current = [_make_db_row("a", 0, 100), _make_db_row("b", 100, 200)]

    diff = EmbeddingServiceImplementation._diff_boundaries(desired, current)

    assert diff.to_embed == []
    assert diff.to_delete == ["b"]


@pytest.mark.unit
def test_diff_new_boundary_added():
    """A desired boundary with no match in current is new (embed it)."""
    desired = [_make_boundary(0, 100), _make_boundary(100, 200), _make_boundary(200, 300)]
    current = [_make_db_row("a", 0, 100), _make_db_row("b", 100, 200)]

    diff = EmbeddingServiceImplementation._diff_boundaries(desired, current)

    assert len(diff.to_embed) == 1
    assert diff.to_embed[0].char_start == 200
    assert diff.to_delete == []


@pytest.mark.unit
def test_diff_empty_current():
    """No existing chunks means everything is new."""
    desired = [_make_boundary(0, 100), _make_boundary(100, 200)]

    diff = EmbeddingServiceImplementation._diff_boundaries(desired, boundaries_current=[])

    assert len(diff.to_embed) == 2
    assert diff.to_delete == []


@pytest.mark.integration
async def test_full_embed_without_boundaries_still_works(test_document, embedding_client):
    """Embedding without desired_boundaries should still work (full embed path)."""
    emb_request = emb_api.EmbedDocumentRequest()
    emb_request.document_id = test_document.id
    emb_request.config.strategy = emb_api.MARKDOWN_STRUCTURE
    emb_request.config.max_heading_level = 2

    response = await embedding_client.embed_document(emb_request)

    assert response.success is True
    assert response.embedding_status.is_embedded is True
    assert response.embedding_status.total_chunks > 0
