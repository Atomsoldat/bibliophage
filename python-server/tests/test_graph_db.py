"""Tests for the graph_edges database layer.

These talk directly to Postgres (no python-server / RPC layer) and require
the dev-environment pgvector container to be running. They follow the
existing convention of marking DB-backed tests as `integration`.
"""

import logging
import uuid

import psycopg
import pytest

from db.postgres_db import BibliophageDatabase, close_database, get_postgres_db

logger = logging.getLogger(__name__)


@pytest.fixture
async def graph_db():
    """Initialise the database singleton with schema, yield it, then close."""
    db = get_postgres_db()
    await db.ensure_initialised()
    await db.initialise_schema()
    yield db
    await close_database()


async def _make_document(db: BibliophageDatabase, name: str) -> str:
    """Insert a minimal document and return its id as a string."""
    result = await db.store_document(
        name=name,
        content="placeholder",
        tags=[],
        metadata=None,
    )
    return str(result["document_id"])


@pytest.fixture
async def two_documents(graph_db: BibliophageDatabase):
    """Provide two freshly-created document ids; clean both up after the test."""
    a = await _make_document(graph_db, "graph-test-A")
    b = await _make_document(graph_db, "graph-test-B")
    yield a, b
    await graph_db.delete_document(a)
    await graph_db.delete_document(b)


@pytest.mark.integration
async def test_create_edge_round_trip(graph_db, two_documents):
    a, b = two_documents

    edge = await graph_db.create_edge(a, b)

    assert edge["edge_id"] is not None
    # Default relationship and directionality
    assert edge["relationship"] == "RELATED"
    assert edge["directed"] is False
    # Undirected edges are stored in canonical order, regardless of input
    assert {str(edge["source_id"]), str(edge["target_id"])} == {a, b}
    assert str(edge["source_id"]) < str(edge["target_id"])

    neighbours, edges = await graph_db.get_neighbours(a)
    assert [str(n["document_id"]) for n in neighbours] == [b]
    assert [str(e["edge_id"]) for e in edges] == [str(edge["edge_id"])]


@pytest.mark.integration
async def test_create_edge_canonicalises_undirected(graph_db, two_documents):
    """Undirected edges should be stored in canonical order regardless of
    the order the caller passes them in. The DB CHECK enforces this; the
    method swaps so callers never trigger it."""
    a, b = sorted(two_documents)  # ensure a < b

    edge_forward = await graph_db.create_edge(a, b)
    # Same pair, reversed input order, different relationship to avoid the
    # UNIQUE constraint. The stored row should still have source < target.
    edge_backward = await graph_db.create_edge(b, a, relationship="OTHER")

    assert str(edge_forward["source_id"]) < str(edge_forward["target_id"])
    assert str(edge_backward["source_id"]) < str(edge_backward["target_id"])


@pytest.mark.integration
async def test_duplicate_undirected_edge_rejected(graph_db, two_documents):
    a, b = two_documents
    await graph_db.create_edge(a, b)

    with pytest.raises(psycopg.errors.UniqueViolation):
        await graph_db.create_edge(a, b)


@pytest.mark.integration
async def test_directed_edge_allowed_in_reverse(graph_db, two_documents):
    """A directed B→A is a different edge from A→B; both must be allowed."""
    a, b = sorted(two_documents)

    forward = await graph_db.create_edge(a, b, directed=True)
    reverse = await graph_db.create_edge(b, a, directed=True)

    # Stored exactly as passed in, no canonicalisation for directed edges
    assert (str(forward["source_id"]), str(forward["target_id"])) == (a, b)
    assert (str(reverse["source_id"]), str(reverse["target_id"])) == (b, a)


@pytest.mark.integration
async def test_self_edge_rejected(graph_db, two_documents):
    a, _ = two_documents
    with pytest.raises(psycopg.errors.CheckViolation):
        await graph_db.create_edge(a, a)


@pytest.mark.integration
async def test_delete_edge(graph_db, two_documents):
    a, b = two_documents
    edge = await graph_db.create_edge(a, b)

    deleted = await graph_db.delete_edge(str(edge["edge_id"]))
    assert deleted is True

    neighbours, _ = await graph_db.get_neighbours(a)
    assert neighbours == []

    # Deleting again is a no-op
    assert await graph_db.delete_edge(str(edge["edge_id"])) is False


@pytest.mark.integration
async def test_delete_document_cascades_to_edges(graph_db, two_documents):
    a, b = two_documents
    edge = await graph_db.create_edge(a, b)

    await graph_db.delete_document(a)

    # The edge is gone — verify via b's neighbourhood
    neighbours, edges = await graph_db.get_neighbours(b)
    assert neighbours == []
    assert edges == []
    # And directly:
    remaining = await graph_db.list_edges_between([b])
    assert remaining == []
    # Sanity: edge_id no longer exists
    assert await graph_db.delete_edge(str(edge["edge_id"])) is False


@pytest.mark.integration
async def test_get_neighbours_for_isolated_node(graph_db, two_documents):
    a, _ = two_documents
    neighbours, edges = await graph_db.get_neighbours(a)
    assert neighbours == []
    assert edges == []


@pytest.mark.integration
async def test_list_edges_between_filters_to_subset(graph_db):
    """list_edges_between only returns edges with both endpoints inside the set."""
    a = await _make_document(graph_db, "graph-test-list-A")
    b = await _make_document(graph_db, "graph-test-list-B")
    c = await _make_document(graph_db, "graph-test-list-C")

    try:
        ab = await graph_db.create_edge(a, b)
        await graph_db.create_edge(b, c)  # endpoint outside the set below

        result = await graph_db.list_edges_between([a, b])
        assert [str(e["edge_id"]) for e in result] == [str(ab["edge_id"])]

        # Empty input is a valid query
        assert await graph_db.list_edges_between([]) == []

        # A non-existent id is fine; just returns no rows
        assert await graph_db.list_edges_between([str(uuid.uuid4())]) == []
    finally:
        await graph_db.delete_document(a)
        await graph_db.delete_document(b)
        await graph_db.delete_document(c)
