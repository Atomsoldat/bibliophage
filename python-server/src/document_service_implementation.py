import logging
import uuid
from datetime import datetime, timezone

from google.protobuf import timestamp_pb2

import bibliophage.v1alpha2.document_pb2 as api
from database import get_database

logger = logging.getLogger(__name__)


class DocumentServiceImplementation:
    def __init__(self):
        """Initialize the document service with database repository."""
        self.db = get_database()
        logger.info("Document service initialized with database repository")
    # TODO: figure out where the type of ctx is defined, we  don't use it in the loading service either
    async def store_document(
        self, request: api.StoreDocumentRequest, ctx,
    ) -> api.StoreDocumentResponse:
        logger.info(
            f"Received StoreDocumentRequest for document: {request.document.name}",
        )

        # Generate document ID and store in database
        document_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        await self.db.store_document(
            document_id=document_id,
            name=request.document.name,
            content=request.document.content,
            doc_type=request.document.type,
            tags=list(request.document.tags) if request.document.tags else [],
            created_at=now,
        )

        # Create response with stored document metadata
        stored_document = api.Document()
        stored_document.CopyFrom(request.document)
        stored_document.id = document_id

        # Set timestamps
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(now)
        stored_document.created_at.CopyFrom(timestamp)
        stored_document.updated_at.CopyFrom(timestamp)

        # Set character count
        stored_document.character_count = len(request.document.content)

        return api.StoreDocumentResponse(
            success=True,
            message=f"Document '{stored_document.name}' stored successfully",
            document=stored_document,
        )

    async def get_document(
        self, request: api.GetDocumentRequest, ctx,
    ) -> api.GetDocumentResponse:
        logger.info(f"Received GetDocumentRequest for ID: {request.id}")

        # Retrieve document from database
        doc_data = await self.db.get_document_by_id(request.id)

        if doc_data is None:
            return api.GetDocumentResponse(
                success=False,
                message=f"Document with ID {request.id} not found",
            )

        # Convert database document to protobuf Document
        document = api.Document()
        document.id = doc_data['_id']
        document.name = doc_data['name']
        document.content = doc_data['content']
        document.type = doc_data['type']
        document.character_count = doc_data['character_count']
        document.tags.extend(doc_data.get('tags', []))

        # Set timestamps
        created_timestamp = timestamp_pb2.Timestamp()
        created_timestamp.FromDatetime(doc_data['created_at'])
        document.created_at.CopyFrom(created_timestamp)

        updated_timestamp = timestamp_pb2.Timestamp()
        updated_timestamp.FromDatetime(doc_data['updated_at'])
        document.updated_at.CopyFrom(updated_timestamp)

        return api.GetDocumentResponse(
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
        self, request: api.UpdateDocumentRequest, ctx,
    ) -> api.UpdateDocumentResponse:
        logger.info(f"Received UpdateDocumentRequest for ID: {request.document.id}")

        # Update document in database
        doc_data = await self.db.update_document(
            document_id=request.document.id,
            name=request.document.name if request.document.name else None,
            content=request.document.content if request.document.content else None,
            doc_type=request.document.type if request.document.type else None,
            tags=list(request.document.tags) if request.document.tags else None,
        )

        if doc_data is None:
            return api.UpdateDocumentResponse(
                success=False,
                message=f"Document with ID {request.document.id} not found",
            )

        # Convert updated database document to protobuf Document
        updated_document = api.Document()
        updated_document.id = doc_data['_id']
        updated_document.name = doc_data['name']
        updated_document.content = doc_data['content']
        updated_document.type = doc_data['type']
        updated_document.character_count = doc_data['character_count']
        updated_document.tags.extend(doc_data.get('tags', []))

        # Set timestamps
        created_timestamp = timestamp_pb2.Timestamp()
        created_timestamp.FromDatetime(doc_data['created_at'])
        updated_document.created_at.CopyFrom(created_timestamp)

        updated_timestamp = timestamp_pb2.Timestamp()
        updated_timestamp.FromDatetime(doc_data['updated_at'])
        updated_document.updated_at.CopyFrom(updated_timestamp)

        return api.UpdateDocumentResponse(
            success=True,
            message=f"Document '{updated_document.name}' updated successfully",
            document=updated_document,
        )

    async def search_documents(
        self, request: api.SearchDocumentsRequest, ctx,
    ) -> api.SearchDocumentsResponse:
        logger.info("Received SearchDocumentsRequest")

        # TODO: Implement actual document search
        # When implementing, create DocumentListItem instances with snippets:
        # snippet = full_content[:200] + "..." if len(full_content) > 200 else full_content
        # list_item = api.DocumentListItem(
        #     id=doc.id,
        #     name=doc.name,
        #     content_snippet=snippet,
        #     type=doc.type,
        #     created_at=doc.created_at,
        #     updated_at=doc.updated_at,
        #     tags=doc.tags,
        #     character_count=doc.character_count
        # )
        return api.SearchDocumentsResponse(
            success=False,
            message="Search not yet implemented",
            documents=[],  # This will be a list of DocumentListItem, not Document
            total_count=0,
            page_number=request.page_number,
            has_more=False,
        )

    async def delete_document(
        self, request: api.DeleteDocumentRequest, ctx,
    ) -> api.DeleteDocumentResponse:
        logger.info(f"Received DeleteDocumentRequest for ID: {request.id}")

        # Delete document from database
        deleted = await self.db.delete_document(request.id)

        if not deleted:
            return api.DeleteDocumentResponse(
                success=False,
                message=f"Document with ID {request.id} not found",
            )

        return api.DeleteDocumentResponse(
            success=True,
            message=f"Document with ID {request.id} deleted successfully",
        )
