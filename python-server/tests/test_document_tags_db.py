"""Tests for document tag storage against the real tags/tag_values schema.

These talk directly to Postgres (no python-server / RPC layer) and require
the dev-environment pgvector container to be running. They follow the
existing convention of marking DB-backed tests as `integration`
(see test_graph_db.py).
"""

import logging

import pytest

from db.postgres_db import BibliophageDatabase, close_database, get_postgres_db

logger = logging.getLogger(__name__)


@pytest.fixture
async def tag_db():
    """Initialise the database singleton with schema, yield it, then close."""
    db = get_postgres_db()
    await db.ensure_initialised()
    await db.initialise_schema()
    yield db
    await close_database()


async def _ensure_tag(db: BibliophageDatabase, title: str) -> None:
    """Create a tag if it doesn't already exist yet (tags are pre-declared)."""
    await db.execute(
        "INSERT INTO tags (title) VALUES (%(title)s) ON CONFLICT (title) DO NOTHING",
        {"title": title},
    )


@pytest.mark.integration
async def test_store_document_with_document_type_tag_round_trips(tag_db):
    await _ensure_tag(tag_db, "document_type")

    result = await tag_db.store_document(
        name="tag-round-trip",
        content="placeholder",
        tags=[{"name": "document_type", "values": ["rulebook"]}],
        metadata=None,
    )
    document_id = str(result["document_id"])

    try:
        doc = await tag_db.get_document_by_id(document_id)
        assert doc["tags"] == [{"name": "document_type", "values": ["rulebook"]}]
    finally:
        await tag_db.delete_document(document_id)


@pytest.mark.integration
async def test_store_document_without_document_type_tag_has_no_tags(tag_db):
    result = await tag_db.store_document(
        name="no-tags",
        content="placeholder",
        tags=[],
        metadata=None,
    )
    document_id = str(result["document_id"])

    try:
        doc = await tag_db.get_document_by_id(document_id)
        assert doc["tags"] == []
    finally:
        await tag_db.delete_document(document_id)


@pytest.mark.integration
async def test_store_document_with_multi_value_tag(tag_db):
    await _ensure_tag(tag_db, "genre")

    result = await tag_db.store_document(
        name="multi-value-tag",
        content="placeholder",
        tags=[{"name": "genre", "values": ["fantasy", "comedy"]}],
        metadata=None,
    )
    document_id = str(result["document_id"])

    try:
        doc = await tag_db.get_document_by_id(document_id)
        assert doc["tags"] == [{"name": "genre", "values": ["fantasy", "comedy"]}]
    finally:
        await tag_db.delete_document(document_id)


@pytest.mark.integration
async def test_store_document_with_valueless_tag(tag_db):
    await _ensure_tag(tag_db, "reviewed")

    result = await tag_db.store_document(
        name="valueless-tag",
        content="placeholder",
        tags=[{"name": "reviewed", "values": []}],
        metadata=None,
    )
    document_id = str(result["document_id"])

    try:
        doc = await tag_db.get_document_by_id(document_id)
        assert doc["tags"] == [{"name": "reviewed", "values": []}]
    finally:
        await tag_db.delete_document(document_id)


@pytest.mark.integration
async def test_store_document_unknown_tag_raises(tag_db):
    with pytest.raises(ValueError, match="Unknown tag"):
        await tag_db.store_document(
            name="unknown-tag-doc",
            content="placeholder",
            tags=[{"name": "not_a_real_tag", "values": ["x"]}],
            metadata=None,
        )


@pytest.mark.integration
async def test_update_document_replaces_tags(tag_db):
    await _ensure_tag(tag_db, "document_type")
    await _ensure_tag(tag_db, "genre")

    result = await tag_db.store_document(
        name="update-tags",
        content="placeholder",
        tags=[{"name": "document_type", "values": ["note"]}],
        metadata=None,
    )
    document_id = str(result["document_id"])

    try:
        await tag_db.update_document(
            document_id=document_id,
            name="update-tags",
            content="placeholder",
            tags=[{"name": "genre", "values": ["fantasy"]}],
            metadata=None,
        )

        doc = await tag_db.get_document_by_id(document_id)
        assert doc["tags"] == [{"name": "genre", "values": ["fantasy"]}]
    finally:
        await tag_db.delete_document(document_id)


@pytest.mark.integration
async def test_reusing_a_tag_value_across_documents(tag_db):
    """Two documents tagged genre=fantasy must not collide on the
    (tag_id, tag_value) UNIQUE constraint in tag_values — the second
    store should resolve to the same existing tag_value row, not fail."""
    await _ensure_tag(tag_db, "genre")

    first = await tag_db.store_document(
        name="shared-tag-value-1",
        content="placeholder",
        tags=[{"name": "genre", "values": ["fantasy"]}],
        metadata=None,
    )
    second = await tag_db.store_document(
        name="shared-tag-value-2",
        content="placeholder",
        tags=[{"name": "genre", "values": ["fantasy"]}],
        metadata=None,
    )

    try:
        doc1 = await tag_db.get_document_by_id(str(first["document_id"]))
        doc2 = await tag_db.get_document_by_id(str(second["document_id"]))
        assert doc1["tags"] == [{"name": "genre", "values": ["fantasy"]}]
        assert doc2["tags"] == [{"name": "genre", "values": ["fantasy"]}]
    finally:
        await tag_db.delete_document(str(first["document_id"]))
        await tag_db.delete_document(str(second["document_id"]))
