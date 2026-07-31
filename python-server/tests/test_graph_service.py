"""Integration tests for the GraphService RPCs.

These talk to a running python-server via Connect RPC. Database-layer
behaviour (constraints, cascades) lives in test_graph_db.py; this file
focuses on the API surface: response shape, error mapping, and the
not-implemented stubs.
"""

import uuid

import pytest

import bibliophage.v1alpha3.document_pb2 as doc_api
import bibliophage.v1alpha3.graph_pb2 as graph_api


@pytest.mark.integration
async def test_create_edge_round_trip(graph_client, two_test_documents):
    a, b = two_test_documents

    response = await graph_client.create_edge(
        graph_api.CreateEdgeRequest(source_node_id=a.id, target_node_id=b.id),
    )

    assert response.success is True
    assert response.edge.id
    # Default relationship is RELATED, default directed is False
    assert response.edge.relationship == "RELATED"
    assert response.edge.directed is False
    # Endpoints are returned (canonical order for undirected, but we don't
    # assert the order here — see test_graph_db for that).
    assert {response.edge.node_a, response.edge.node_b} == {a.id, b.id}

    # Cleanup
    await graph_client.delete_edge(graph_api.DeleteEdgeRequest(id=response.edge.id))


@pytest.mark.integration
async def test_create_edge_missing_endpoint_fails(graph_client, two_test_documents):
    a, _ = two_test_documents
    bogus = str(uuid.uuid4())

    response = await graph_client.create_edge(
        graph_api.CreateEdgeRequest(source_node_id=a.id, target_node_id=bogus),
    )

    assert response.success is False
    assert "exist" in response.message.lower()


@pytest.mark.integration
async def test_create_edge_requires_both_endpoints(graph_client, two_test_documents):
    a, _ = two_test_documents

    response = await graph_client.create_edge(
        graph_api.CreateEdgeRequest(source_node_id=a.id, target_node_id=""),
    )

    assert response.success is False
    assert "required" in response.message.lower()


@pytest.mark.integration
async def test_get_neighbours_returns_edges_and_documents(
    graph_client, two_test_documents,
):
    a, b = two_test_documents

    edge_resp = await graph_client.create_edge(
        graph_api.CreateEdgeRequest(source_node_id=a.id, target_node_id=b.id),
    )
    try:
        response = await graph_client.get_neighbours(
            graph_api.GetNeighboursRequest(document_id=a.id),
        )

        assert response.success is True
        assert len(response.neighbours) == 1
        assert response.neighbours[0].id == b.id
        assert len(response.edges) == 1
        assert response.edges[0].id == edge_resp.edge.id
    finally:
        await graph_client.delete_edge(
            graph_api.DeleteEdgeRequest(id=edge_resp.edge.id),
        )


@pytest.mark.integration
async def test_get_neighbours_isolated_node(graph_client, test_document):
    response = await graph_client.get_neighbours(
        graph_api.GetNeighboursRequest(document_id=test_document.id),
    )

    assert response.success is True
    assert list(response.neighbours) == []
    assert list(response.edges) == []


@pytest.mark.integration
async def test_get_neighbours_requires_document_id(graph_client):
    response = await graph_client.get_neighbours(
        graph_api.GetNeighboursRequest(document_id=""),
    )
    assert response.success is False
    assert "required" in response.message.lower()


@pytest.mark.integration
async def test_list_edges_filters_to_subset(graph_client, document_client):
    # Build a 3-node graph: a-b, b-c. Listing edges within {a, b} must yield
    # only a-b. We create documents inline because we need three of them.
    docs = []
    for idx in range(3):
        request = doc_api.StoreDocumentRequest()
        request.document.name = f"Graph List Test {idx} (auto-cleanup)"
        request.document.systems.append("Test System")
        request.document.content = f"Graph list test document {idx}."
        response = await document_client.store_document(request)
        docs.append(response.document)
    a, b, c = docs

    edge_ab = await graph_client.create_edge(
        graph_api.CreateEdgeRequest(source_node_id=a.id, target_node_id=b.id),
    )
    edge_bc = await graph_client.create_edge(
        graph_api.CreateEdgeRequest(source_node_id=b.id, target_node_id=c.id),
    )

    try:
        response = await graph_client.list_edges(
            graph_api.ListEdgesRequest(document_ids=[a.id, b.id]),
        )
        assert response.success is True
        edge_ids = [e.id for e in response.edges]
        assert edge_ids == [edge_ab.edge.id]
    finally:
        await graph_client.delete_edge(
            graph_api.DeleteEdgeRequest(id=edge_ab.edge.id),
        )
        await graph_client.delete_edge(
            graph_api.DeleteEdgeRequest(id=edge_bc.edge.id),
        )
        for doc in docs:
            await document_client.delete_document(
                doc_api.DeleteDocumentRequest(id=doc.id),
            )


@pytest.mark.integration
async def test_delete_edge_returns_failure_for_missing(graph_client):
    response = await graph_client.delete_edge(
        graph_api.DeleteEdgeRequest(id=str(uuid.uuid4())),
    )
    assert response.success is False


@pytest.mark.integration
async def test_create_node_is_not_implemented(graph_client):
    """Documents are the source of truth for nodes — CreateNode is a stub."""
    response = await graph_client.create_node(
        graph_api.CreateNodeRequest(type_id="Character"),
    )
    assert response.success is False
    assert "DocumentService" in response.message


@pytest.mark.integration
async def test_delete_node_is_not_implemented(graph_client):
    response = await graph_client.delete_node(
        graph_api.DeleteNodeRequest(id="anything"),
    )
    assert response.success is False
    assert "DocumentService" in response.message
