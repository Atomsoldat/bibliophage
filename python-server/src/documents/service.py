import logging

import bibliophage.v1alpha3.document_pb2 as document_api
import bibliophage.v1alpha3.embedding_pb2 as embedding_api
from db.postgres_db import get_postgres_db
from proto_converters import (
    datetime_to_proto_ts,
    metadata_proto_to_dict,
    row_to_proto_document,
)

logger = logging.getLogger(__name__)


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
            metadata = metadata_proto_to_dict(request.document.metadata)

        try:
            response = await self.db.store_document(
                name=request.document.name,
                systems=list(request.document.systems),
                source_type=source_type,
                content=request.document.content,
                doc_type=doc_type,
                tags=tags,
                metadata=metadata,
            )
        except ValueError as e:
            return document_api.StoreDocumentResponse(
                success=False,
                message=str(e),
            )

        # Create response with stored document metadata
        stored_document = document_api.Document()
        stored_document.CopyFrom(request.document)
        stored_document.id = response["document_id"]
        stored_document.character_count = response["character_count"]

        # Set timestamps — must use FromDatetime, not direct assignment
        created_ts = datetime_to_proto_ts(response["created_at"])
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

        document = row_to_proto_document(doc_data)

        return document_api.GetDocumentResponse(
            success=True,
            message=f"Document '{document.name}' retrieved successfully",
            document=document,
        )

    async def update_document(
        self,
        request: document_api.UpdateDocumentRequest,
        ctx,
    ) -> document_api.UpdateDocumentResponse:
        """Update a document by ID. Full replace strategy per D-01."""
        logger.info(f"Received UpdateDocumentRequest for ID: {request.document.id}")

        # Validate document ID is provided
        if not request.document.id:
            return document_api.UpdateDocumentResponse(
                success=False,
                message="Document ID is required",
            )

        # Convert protobuf tags to dict format for database storage
        tags = [
            {"name": tag.name, "values": list(tag.values)}
            for tag in request.document.tags
        ]

        # Convert enum to string name for database storage
        doc_type = document_api.DocumentType.Name(request.document.type)
        source_type = document_api.SourceType.Name(request.document.source_type)

        # Convert metadata if provided
        metadata = None
        if request.document.HasField("metadata"):
            metadata = metadata_proto_to_dict(request.document.metadata)

        try:
            result = await self.db.update_document(
                document_id=request.document.id,
                name=request.document.name,
                systems=list(request.document.systems),
                source_type=source_type,
                content=request.document.content,
                doc_type=doc_type,
                tags=tags,
                metadata=metadata,
            )
        except ValueError as e:
            return document_api.UpdateDocumentResponse(
                success=False,
                message=str(e),
            )

        if result is None:
            return document_api.UpdateDocumentResponse(
                success=False,
                message="Document not found",
            )

        # Re-fetch the full document so server-computed fields are accurate (D-03)
        doc_data = await self.db.get_document_by_id(request.document.id)
        proto_document = row_to_proto_document(doc_data)

        return document_api.UpdateDocumentResponse(
            success=True,
            message="Document updated successfully",
            document=proto_document,
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
            list_item = row_to_proto_document(doc_data, document_api.DocumentListItem)

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
