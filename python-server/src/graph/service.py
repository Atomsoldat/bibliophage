"""Graph service implementation.

Implements the GraphService RPCs against PostgreSQL (the `graph_edges` table).
Nodes are documents — there is no separate node table — so CreateNode and
DeleteNode are intentionally not implemented here; callers should use
DocumentService instead.

The web-ui's expected call pattern is:
    GetNeighbours(pinnedDocId) → render inner circle
    GetNeighbours(otherId)     → expand on TAB
    CreateEdge / DeleteEdge    → user-initiated edits
    ListEdges                  → fill in edges between already-loaded nodes
"""

import logging
from typing import Any

import psycopg

import bibliophage.v1alpha3.document_pb2 as document_api
import bibliophage.v1alpha3.graph_pb2 as graph_api
from db.postgres_db import get_postgres_db
from proto_converters import row_to_proto_document

logger = logging.getLogger(__name__)

_NOT_IMPLEMENTED_MSG = (
    "Nodes are documents in this build — use DocumentService.StoreDocument / "
    "DeleteDocument instead of GraphService.CreateNode / DeleteNode."
)


def _row_to_proto_edge(row: dict[str, Any]) -> graph_api.Edge:
    """Convert a graph_edges row to a proto Edge."""
    return graph_api.Edge(
        id=str(row["edge_id"]),
        relationship=row["relationship"],
        directed=row["directed"],
        node_a=str(row["source_id"]),
        node_b=str(row["target_id"]),
    )


class GraphServiceImplementation:
    """Implementation of the GraphService RPC interface."""

    def __init__(self):
        self.db = get_postgres_db()
        logger.info("Graph service initialised")

    # ── unimplemented: documents are the source of truth for nodes ──────

    async def create_node(
        self,
        request: graph_api.CreateNodeRequest,
        ctx,
    ) -> graph_api.CreateNodeResponse:
        return graph_api.CreateNodeResponse(success=False, message=_NOT_IMPLEMENTED_MSG)

    async def delete_node(
        self,
        request: graph_api.DeleteNodeRequest,
        ctx,
    ) -> graph_api.DeleteNodeResponse:
        return graph_api.DeleteNodeResponse(success=False, message=_NOT_IMPLEMENTED_MSG)

    # ── edges ───────────────────────────────────────────────────────────

    async def create_edge(
        self,
        request: graph_api.CreateEdgeRequest,
        ctx,
    ) -> graph_api.CreateEdgeResponse:
        logger.info(
            "CreateEdge: %s → %s (%s)",
            request.source_node_id, request.target_node_id, request.relationship,
        )

        if not request.source_node_id or not request.target_node_id:
            return graph_api.CreateEdgeResponse(
                success=False, message="source_node_id and target_node_id are required",
            )

        relationship = request.relationship or "RELATED"

        try:
            row = await self.db.create_edge(
                source_id=request.source_node_id,
                target_id=request.target_node_id,
                relationship=relationship,
                directed=request.directed,
            )
        except psycopg.errors.ForeignKeyViolation as err:
            # One of the endpoints isn't a real document.
            return graph_api.CreateEdgeResponse(
                success=False, message=f"endpoint does not exist: {err}",
            )
        except psycopg.errors.UniqueViolation:
            return graph_api.CreateEdgeResponse(
                success=False, message="edge already exists",
            )
        except psycopg.errors.CheckViolation as err:
            # Self-loop, or a directed-only insert we missed canonicalising.
            return graph_api.CreateEdgeResponse(
                success=False, message=f"invalid edge: {err}",
            )

        return graph_api.CreateEdgeResponse(
            success=True, message="edge created", edge=_row_to_proto_edge(row),
        )

    async def delete_edge(
        self,
        request: graph_api.DeleteEdgeRequest,
        ctx,
    ) -> graph_api.DeleteEdgeResponse:
        logger.info("DeleteEdge: %s", request.id)
        deleted = await self.db.delete_edge(request.id)
        if not deleted:
            return graph_api.DeleteEdgeResponse(
                success=False, message=f"edge {request.id} not found",
            )
        return graph_api.DeleteEdgeResponse(success=True, message="edge deleted")

    # ── reads ───────────────────────────────────────────────────────────

    async def get_neighbours(
        self,
        request: graph_api.GetNeighboursRequest,
        ctx,
    ) -> graph_api.GetNeighboursResponse:
        logger.info("GetNeighbours: %s", request.document_id)

        if not request.document_id:
            return graph_api.GetNeighboursResponse(
                success=False, message="document_id is required",
            )

        neighbour_rows, edge_rows = await self.db.get_neighbours(request.document_id)

        response = graph_api.GetNeighboursResponse(
            success=True,
            message=f"{len(neighbour_rows)} neighbour(s)",
        )
        for row in neighbour_rows:
            response.neighbours.append(
                row_to_proto_document(row, document_api.DocumentListItem),
            )
        for row in edge_rows:
            response.edges.append(_row_to_proto_edge(row))
        return response

    async def list_edges(
        self,
        request: graph_api.ListEdgesRequest,
        ctx,
    ) -> graph_api.ListEdgesResponse:
        logger.info("ListEdges: %d node(s)", len(request.document_ids))

        edge_rows = await self.db.list_edges_between(list(request.document_ids))

        response = graph_api.ListEdgesResponse(
            success=True, message=f"{len(edge_rows)} edge(s)",
        )
        for row in edge_rows:
            response.edges.append(_row_to_proto_edge(row))
        return response
