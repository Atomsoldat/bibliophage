import logging
import uuid
from datetime import UTC, datetime

from google.protobuf import timestamp_pb2

import bibliophage.v1alpha3.document_pb2 as document_api
import bibliophage.v1alpha3.embedding_pb2 as embedding_api
import vector_operations
from document_database_pg import get_document_db

logger = logging.getLogger(__name__)


class DocumentServiceImplementation:
    def __init__(self):
        """Initialize the document service with database repository."""
        self.db = get_document_db()
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

        # Generate document ID and store in database
        document_id = str(uuid.uuid4())
        now = datetime.now(UTC)

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

        await self.db.store_document(
            document_id=document_id,
            name=request.document.name,
            systems=list(request.document.systems),
            source_type=source_type,
            content=request.document.content,
            doc_type=doc_type,
            tags=tags,
            created_at=now,
            metadata=metadata,
        )

        # Create response with stored document metadata
        stored_document = document_api.Document()
        stored_document.CopyFrom(request.document)
        stored_document.id = document_id

        # Set timestamps
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(now)
        stored_document.created_at.CopyFrom(timestamp)
        stored_document.updated_at.CopyFrom(timestamp)

        # Set character count
        stored_document.character_count = len(request.document.content)

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

        # Convert database document to protobuf Document
        document = document_api.Document()
        document.id = doc_data["_id"]
        document.name = doc_data["name"]
        document.content = doc_data["content"]
        document.type = getattr(document_api, doc_data["type"], document_api.DOCUMENT_TYPE_UNSPECIFIED)
        document.character_count = doc_data["character_count"]

        # Add systems array
        document.systems.extend(doc_data.get("systems", []))

        # Convert source_type string to enum
        source_type_str = doc_data.get("source_type", "SOURCE_TYPE_UNSPECIFIED")
        document.source_type = getattr(
            document_api, source_type_str, document_api.SOURCE_TYPE_UNSPECIFIED,
        )

        # Convert metadata if present
        if "metadata" in doc_data:
            metadata = document_api.Metadata()
            metadata.file_size = doc_data["metadata"].get("file_size", 0)

            if "publication_type" in doc_data["metadata"]:
                metadata.publication_type = doc_data["metadata"]["publication_type"]

            if "pdf" in doc_data["metadata"]:
                pdf_data = document_api.PdfData()
                pdf_data.loading_batch_count = doc_data["metadata"]["pdf"].get(
                    "loading_batch_count", 0,
                )
                pdf_data.vector_chunk_count = doc_data["metadata"]["pdf"].get(
                    "vector_chunk_count", 0,
                )
                pdf_data.page_count = doc_data["metadata"]["pdf"].get("page_count", 0)
                metadata.pdf.CopyFrom(pdf_data)

            document.metadata.CopyFrom(metadata)

        # Convert dict tags to protobuf tags
        for tag_data in doc_data.get("tags", []):
            tag = document_api.Tag()
            tag.name = tag_data.get("name", "")
            tag.values.extend(tag_data.get("values", []))
            document.tags.append(tag)

        # Set timestamps
        created_timestamp = timestamp_pb2.Timestamp()
        created_timestamp.FromDatetime(doc_data["created_at"])
        document.created_at.CopyFrom(created_timestamp)

        updated_timestamp = timestamp_pb2.Timestamp()
        updated_timestamp.FromDatetime(doc_data["updated_at"])
        document.updated_at.CopyFrom(updated_timestamp)

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
        logger.info(f"Received UpdateDocumentRequest for ID: {request.document.id}")

        # Validate systems array if provided (must have at least one value)
        systems = None
        if request.document.systems:
            if len(request.document.systems) == 0:
                return document_api.UpdateDocumentResponse(
                    success=False,
                    message="Document must belong to at least one system",
                )
            systems = list(request.document.systems)

        # Convert protobuf tags to dict format for database storage if provided
        tags = None
        if request.document.tags:
            tags = []
            for tag in request.document.tags:
                tags.append({"name": tag.name, "values": list(tag.values)})

        # Convert enum to string name for database storage if provided
        doc_type = None
        if (
            request.document.type
            and request.document.type != document_api.DOCUMENT_TYPE_UNSPECIFIED
        ):
            doc_type = document_api.DocumentType.Name(request.document.type)

        # Convert source_type enum to string if provided
        source_type = None
        if (
            request.document.source_type
            and request.document.source_type != document_api.SOURCE_TYPE_UNSPECIFIED
        ):
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

        # Update document in database
        doc_data = await self.db.update_document(
            document_id=request.document.id,
            name=request.document.name if request.document.name else None,
            systems=systems,
            source_type=source_type,
            content=request.document.content if request.document.content else None,
            doc_type=doc_type,
            tags=tags,
            metadata=metadata,
        )

        if doc_data is None:
            return document_api.UpdateDocumentResponse(
                success=False,
                message=f"Document with ID {request.document.id} not found",
            )

        # Lifecycle hook: Mark embeddings as stale if content changed
        # This signals that the document has been modified and embeddings need re-generation
        if request.document.content:
            await self.db.mark_embeddings_stale(request.document.id)
            logger.info(
                f"Marked embeddings as stale for document {request.document.id} due to content update",
            )

        # Convert updated database document to protobuf Document
        updated_document = document_api.Document()
        updated_document.id = doc_data["_id"]
        updated_document.name = doc_data["name"]
        updated_document.content = doc_data["content"]
        updated_document.type = getattr(
            document_api, doc_data["type"], document_api.DOCUMENT_TYPE_UNSPECIFIED,
        )
        updated_document.character_count = doc_data["character_count"]

        # Add systems array
        updated_document.systems.extend(doc_data.get("systems", []))

        # Convert source_type string to enum
        source_type_str = doc_data.get("source_type", "SOURCE_TYPE_UNSPECIFIED")
        updated_document.source_type = getattr(
            document_api, source_type_str, document_api.SOURCE_TYPE_UNSPECIFIED,
        )

        # Convert metadata if present
        if "metadata" in doc_data:
            metadata = document_api.Metadata()
            metadata.file_size = doc_data["metadata"].get("file_size", 0)

            if "publication_type" in doc_data["metadata"]:
                metadata.publication_type = doc_data["metadata"]["publication_type"]

            if "pdf" in doc_data["metadata"]:
                pdf_data = document_api.PdfData()
                pdf_data.loading_batch_count = doc_data["metadata"]["pdf"].get(
                    "loading_batch_count", 0,
                )
                pdf_data.vector_chunk_count = doc_data["metadata"]["pdf"].get(
                    "vector_chunk_count", 0,
                )
                pdf_data.page_count = doc_data["metadata"]["pdf"].get("page_count", 0)
                metadata.pdf.CopyFrom(pdf_data)

            updated_document.metadata.CopyFrom(metadata)

        # Convert dict tags to protobuf tags
        for tag_data in doc_data.get("tags", []):
            tag = document_api.Tag()
            tag.name = tag_data.get("name", "")
            tag.values.extend(tag_data.get("values", []))
            updated_document.tags.append(tag)

        # Set timestamps
        created_timestamp = timestamp_pb2.Timestamp()
        created_timestamp.FromDatetime(doc_data["created_at"])
        updated_document.created_at.CopyFrom(created_timestamp)

        updated_timestamp = timestamp_pb2.Timestamp()
        updated_timestamp.FromDatetime(doc_data["updated_at"])
        updated_document.updated_at.CopyFrom(updated_timestamp)

        return document_api.UpdateDocumentResponse(
            success=True,
            message=f"Document '{updated_document.name}' updated successfully",
            document=updated_document,
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
                    document_api.DocumentType.Name(t) for t in request.filter.type_filters
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

        # Fetch chunk boundaries for all documents to populate embedding status
        document_ids = [doc["_id"] for doc in documents]
        chunk_boundaries_map = {}
        for doc_id in document_ids:
            boundaries_doc = await self.db.get_chunk_boundaries(doc_id)
            if boundaries_doc:
                chunk_boundaries_map[doc_id] = boundaries_doc

        # Convert database documents to DocumentListItem protobuf objects
        document_list_items = []
        for doc_data in documents:
            list_item = document_api.DocumentListItem()
            list_item.id = doc_data["_id"]
            list_item.name = doc_data["name"]
            list_item.content_snippet = doc_data.get("content_snippet", "")
            list_item.type = getattr(
                document_api, doc_data["type"], document_api.DOCUMENT_TYPE_UNSPECIFIED,
            )
            list_item.character_count = doc_data["character_count"]

            # Add systems array
            list_item.systems.extend(doc_data.get("systems", []))

            # Convert source_type string to enum
            source_type_str = doc_data.get("source_type", "SOURCE_TYPE_UNSPECIFIED")
            list_item.source_type = getattr(
                document_api, source_type_str, document_api.SOURCE_TYPE_UNSPECIFIED,
            )

            # Convert metadata if present
            if "metadata" in doc_data:
                metadata = document_api.Metadata()
                metadata.file_size = doc_data["metadata"].get("file_size", 0)

                if "publication_type" in doc_data["metadata"]:
                    metadata.publication_type = doc_data["metadata"]["publication_type"]

                if "pdf" in doc_data["metadata"]:
                    pdf_data = document_api.PdfData()
                    pdf_data.loading_batch_count = doc_data["metadata"]["pdf"].get(
                        "loading_batch_count", 0,
                    )
                    pdf_data.vector_chunk_count = doc_data["metadata"]["pdf"].get(
                        "vector_chunk_count", 0,
                    )
                    pdf_data.page_count = doc_data["metadata"]["pdf"].get(
                        "page_count", 0,
                    )
                    metadata.pdf.CopyFrom(pdf_data)

                list_item.metadata.CopyFrom(metadata)

            # Set timestamps
            created_timestamp = timestamp_pb2.Timestamp()
            created_timestamp.FromDatetime(doc_data["created_at"])
            list_item.created_at.CopyFrom(created_timestamp)

            updated_timestamp = timestamp_pb2.Timestamp()
            updated_timestamp.FromDatetime(doc_data["updated_at"])
            list_item.updated_at.CopyFrom(updated_timestamp)

            # Add tags (tags are stored as dicts in the database)
            for tag_data in doc_data.get("tags", []):
                tag = document_api.Tag()
                tag.name = tag_data.get("name", "")
                tag.values.extend(tag_data.get("values", []))
                list_item.tags.append(tag)

            # Populate embedding status if chunk boundaries exist
            doc_id = doc_data["_id"]
            if doc_id in chunk_boundaries_map:
                boundaries_data = chunk_boundaries_map[doc_id]
                embedding_status = embedding_api.EmbeddingStatus()
                embedding_status.is_embedded = boundaries_data.get(
                    "embedding_status", {},
                ).get("is_embedded", False)
                embedding_status.embeddings_current = boundaries_data.get(
                    "embedding_status", {},
                ).get("embeddings_current", False)
                embedding_status.total_chunks = len(
                    boundaries_data.get("chunk_boundaries", []),
                )

                if "embedding_status" in boundaries_data and "embedded_at" in boundaries_data["embedding_status"]:
                    embedded_timestamp = timestamp_pb2.Timestamp()
                    embedded_timestamp.FromDatetime(
                        boundaries_data["embedding_status"]["embedded_at"],
                    )
                    embedding_status.embedded_at.CopyFrom(embedded_timestamp)

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
                message=f"Document with ID {request.id} not found",
            )

        # Lifecycle hooks: Cascade deletion to related data
        # 1. Delete chunk boundaries from FerretDB
        await self.db.delete_chunk_boundaries(request.id)
        logger.info(f"Deleted chunk boundaries for document {request.id}")

        # 2. Delete vector embeddings from pgvector
        deleted_chunks = await vector_operations.delete_document_chunks(request.id)
        logger.info(f"Deleted {deleted_chunks} vector chunks for document {request.id}")

        return document_api.DeleteDocumentResponse(
            success=True,
            message=f"Document with ID {request.id} deleted successfully",
        )
