import logging
from typing import Any

from google.protobuf import timestamp_pb2

import bibliophage.v1alpha3.document_pb2 as document_api
import bibliophage.v1alpha3.embedding_pb2 as embedding_api
from postgres_db import get_postgres_db

logger = logging.getLogger(__name__)


def _row_to_proto_document(
    row: dict[str, Any],
    proto_class: type = document_api.Document,
) -> document_api.Document | document_api.DocumentListItem:
    """Convert a DB row from the documents table to a proto Document or DocumentListItem.

    Handles column renames (document_id→id, title→name, document_type→type),
    enum string→proto lookups, metadata JSONB→proto, and timestamp conversion.
    """
    proto = proto_class()
    proto.id = str(row["document_id"])
    proto.name = row["title"]
    proto.character_count = row["character_count"]

    # Content field: Document has full content, DocumentListItem has content_snippet
    if proto_class == document_api.Document:
        proto.content = row["content"]
    else:
        proto.content_snippet = row.get("content_snippet", "")

    # Enum fields — stored as their proto name strings in DB
    proto.type = getattr(
        document_api, row["document_type"], document_api.DOCUMENT_TYPE_UNSPECIFIED,
    )
    source_type_str = row.get("source_type", "SOURCE_TYPE_UNSPECIFIED")
    proto.source_type = getattr(
        document_api, source_type_str, document_api.SOURCE_TYPE_UNSPECIFIED,
    )

    # TODO: systems are not yet stored — junction table not wired up
    proto.systems.extend(row.get("systems", []))

    # Metadata JSONB → proto
    metadata_dict = row.get("metadata") or {}
    if metadata_dict:
        metadata = document_api.Metadata()
        metadata.file_size = metadata_dict.get("file_size", 0)
        if "publication_type" in metadata_dict:
            metadata.publication_type = metadata_dict["publication_type"]
        if "pdf" in metadata_dict:
            pdf = metadata_dict["pdf"]
            pdf_data = document_api.PdfData(
                loading_batch_count=pdf.get("loading_batch_count", 0),
                vector_chunk_count=pdf.get("vector_chunk_count", 0),
                page_count=pdf.get("page_count", 0),
            )
            metadata.pdf.CopyFrom(pdf_data)
        proto.metadata.CopyFrom(metadata)

    # TODO: tags are not yet stored — junction table not wired up
    for tag_data in row.get("tags", []):
        tag = document_api.Tag()
        tag.name = tag_data.get("name", "")
        tag.values.extend(tag_data.get("values", []))
        proto.tags.append(tag)

    # Timestamps
    created_ts = timestamp_pb2.Timestamp()
    created_ts.FromDatetime(row["created_at"])
    proto.created_at.CopyFrom(created_ts)

    updated_ts = timestamp_pb2.Timestamp()
    updated_ts.FromDatetime(row["updated_at"])
    proto.updated_at.CopyFrom(updated_ts)

    return proto


class DocumentServiceImplementation:
    def __init__(self):
        """Initialize the document service with database repository."""
        self.db = get_postgres_db()
        logger.info("Document service initialized with database repository")

    # TODO: figure out where the type of ctx is defined, we  don't use it in the loading service either
    async def store_document(
        self,
        request: document_api.StoreDocumentRequest,
        ctx,
    ) -> document_api.StoreDocumentResponse:
        logger.info(
            f"Received StoreDocumentRequest for document: {request.document.name}",
        )

        # Validate systems array (must have at least one value)
        if not request.document.systems:
            return document_api.StoreDocumentResponse(
                success=False,
                message="Document must belong to at least one system",
            )

        # Convert protobuf tags to dict format for database storage
        tags = []
        for tag in request.document.tags:
            tags.append({"name": tag.name, "values": list(tag.values)})

        # Convert enum to string name for database storage
        doc_type = document_api.DocumentType.Name(request.document.type)

        # Convert source_type enum to string
        source_type = document_api.SourceType.Name(request.document.source_type)

        # Convert metadata if provided
        metadata = None
        if request.document.HasField("metadata"):
            metadata = {
                "file_size": request.document.metadata.file_size,
            }
            if request.document.metadata.HasField("publication_type"):
                metadata["publication_type"] = (
                    request.document.metadata.publication_type
                )
            if request.document.metadata.HasField("pdf"):
                metadata["pdf"] = {
                    "loading_batch_count": request.document.metadata.pdf.loading_batch_count,
                    "vector_chunk_count": request.document.metadata.pdf.vector_chunk_count,
                    "page_count": request.document.metadata.pdf.page_count,
                }

        response = await self.db.store_document(
            name=request.document.name,
            systems=list(request.document.systems),
            source_type=source_type,
            content=request.document.content,
            doc_type=doc_type,
            tags=tags,
            metadata=metadata,
        )

        # Create response with stored document metadata
        stored_document = document_api.Document()
        stored_document.CopyFrom(request.document)
        stored_document.id = response["document_id"]
        stored_document.character_count = response["character_count"]

        # Set timestamps — must use FromDatetime, not direct assignment
        created_ts = timestamp_pb2.Timestamp()
        created_ts.FromDatetime(response["created_at"])
        stored_document.created_at.CopyFrom(created_ts)
        stored_document.updated_at.CopyFrom(created_ts)

        return document_api.StoreDocumentResponse(
            success=True,
            message=f"Document '{stored_document.name}' stored successfully",
            document=stored_document,
        )

    async def get_document(
        self,
        request: document_api.GetDocumentRequest,
        ctx,
    ) -> document_api.GetDocumentResponse:
        logger.info(f"Received GetDocumentRequest for ID: {request.id}")

        # Retrieve document from database
        doc_data = await self.db.get_document_by_id(request.id)

        if doc_data is None:
            return document_api.GetDocumentResponse(
                success=False,
                message=f"Document with ID {request.id} not found",
            )

        document = _row_to_proto_document(doc_data)

        return document_api.GetDocumentResponse(
            success=True,
            message=f"Document '{document.name}' retrieved successfully",
            document=document,
        )

    # TODO: We should have an update function that allows us to update a document by ID
    # This function should store previous versions of documents, so that people don't accidentally
    # Nuke their stuff
    # TODO: We may want to be able to clean up these old versions globally somehow
    # Or maybe we expire them after a certain time period?
    # But then what about losing the history of a document? That sounds pretty meh
    # Using git for this seems heavy...
    async def update_document(
        self,
        request: document_api.UpdateDocumentRequest,
        ctx,
    ) -> document_api.UpdateDocumentResponse:
        """Update a document by ID.

        TODO: Re-implement against PostgreSQL. Pseudocode below.

        Conversion helpers to extract from this method and get_document / search_documents:
        - _row_to_proto_document(row) — maps DB row to document_api.Document
          handles column renames (document_id→id, title→name, document_type→type),
          enum lookups, metadata JSONB→proto, and timestamp conversion
        - _proto_to_update_params(proto) — maps document_api.Document fields to
          a dict of DB column names and values, only including fields that are
          actually set on the proto (partial update semantics)

        Pseudocode:
        1. params = _proto_to_update_params(request.document)
           — skip unset fields (empty strings, UNSPECIFIED enums)
           — convert enums to string names (DocumentType.Name, SourceType.Name)
           — convert metadata proto to JSONB dict
           — if content changed, update character_count and content_snippet too

        2. if not params:
               return error "no fields to update"

        3. updated_row = await self.db.update_document(request.document.id, params)
           — db.update_document builds: UPDATE documents SET col1=%(col1)s, ...
             WHERE document_id = %(document_id)s RETURNING *
           — single query, no ORM, uses psycopg sql.SQL + sql.Identifier for
             dynamic column names so we don't need to enumerate every combination

        4. if updated_row is None:
               return error "not found"

        5. TODO: if "content" in params, flag embeddings as stale or re-embed

        6. TODO: handle systems (delete + re-insert into map_documents_to_systems)
           and tags (delete + re-insert into map_documents_to_tags) within a
           db.transaction() alongside the document UPDATE

        7. document = _row_to_proto_document(updated_row)
           return UpdateDocumentResponse(success=True, document=document)
        """
        raise NotImplementedError(
            "UpdateDocument is not yet implemented against PostgreSQL. "
            "See pseudocode in docstring for implementation plan."
        )

    async def search_documents(
        self,
        request: document_api.SearchDocumentsRequest,
        ctx,
    ) -> document_api.SearchDocumentsResponse:
        logger.info("Received SearchDocumentsRequest")

        # Extract filter parameters if filter is provided
        name_query = None
        content_query = None
        type_filters = None
        system_filters = None
        tag_filters = None

        if request.HasField("filter"):
            # Extract search parameters from filter
            name_query = (
                request.filter.name_query
                if request.filter.HasField("name_query")
                else None
            )
            content_query = (
                request.filter.content_query
                if request.filter.HasField("content_query")
                else None
            )

            # Convert DocumentType enums to strings for database query
            # Repeated fields don't have presence in proto3 - check if non-empty instead
            if request.filter.type_filters:
                type_filters = [
                    document_api.DocumentType.Name(t)
                    for t in request.filter.type_filters
                ]

            # Extract system filters (matches ANY)
            if request.filter.system_filters:
                system_filters = list(request.filter.system_filters)

            # Extract tag filters (must match ALL)
            if request.filter.tag_filters:
                tag_filters = []
                for tag_filter in request.filter.tag_filters:
                    tag_filters.append(
                        {
                            "name": tag_filter.name,
                            "value": tag_filter.value,
                        },
                    )

        # Set page size with a reasonable default
        page_size = request.page_size if request.page_size > 0 else 50
        page_number = max(request.page_number, 0)

        # Call database search method
        documents, total_count = await self.db.search_documents(
            name_query=name_query,
            content_query=content_query,
            type_filters=type_filters,
            system_filters=system_filters,
            tag_filters=tag_filters,
            page_size=page_size,
            page_number=page_number,
        )

        # Convert database documents to DocumentListItem protobuf objects
        document_list_items = []
        for doc_data in documents:
            list_item = _row_to_proto_document(doc_data, document_api.DocumentListItem)

            # Populate embedding status from document_chunks table
            doc_id = str(doc_data["document_id"])
            chunk_count = await self.db.get_chunk_count(doc_id)
            if chunk_count > 0:
                embedding_status = embedding_api.EmbeddingStatus(
                    is_embedded=True,
                    # TODO: embeddings_current is always True — we don't track
                    # whether content changed since last embedding
                    embeddings_current=True,
                    total_chunks=chunk_count,
                )
                list_item.embedding_status.CopyFrom(embedding_status)

            document_list_items.append(list_item)

        # Calculate if there are more results
        has_more = (page_number + 1) * page_size < total_count
        return document_api.SearchDocumentsResponse(
            success=True,
            message=f"Found {total_count} document(s)",
            matches=document_list_items,
            total_count=total_count,
            page_number=page_number,
            has_more=has_more,
        )

    async def delete_document(
        self,
        request: document_api.DeleteDocumentRequest,
        ctx,
    ) -> document_api.DeleteDocumentResponse:
        logger.info(f"Received DeleteDocumentRequest for ID: {request.id}")

        # Delete document from database
        deleted = await self.db.delete_document(request.id)

        if not deleted:
            return document_api.DeleteDocumentResponse(
                success=False,
                message=f"Document with ID {request.id} could not be deleted",
            )

        # Chunk deletion is handled by ON DELETE CASCADE on document_chunks FK
        return document_api.DeleteDocumentResponse(
            success=True,
            message=f"Document with ID {request.id} deleted successfully",
        )
