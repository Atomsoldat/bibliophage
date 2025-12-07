import logging
import uuid
from datetime import datetime, timezone

import bibliophage.v1alpha2.document_pb2 as api
from google.protobuf import timestamp_pb2

logger = logging.getLogger(__name__)


class DocumentServiceImplementation:
    # TODO: figure out where the type of ctx is defined, we  don't use it in the loading service either
    async def store_document(
        self, request: api.StoreDocumentRequest, ctx
    ) -> api.StoreDocumentResponse:
        logger.info(
            f"Received StoreDocumentRequest for document: {request.document.name}"
        )

        # first we just pretend to do something with the request. later, we will actually store the document
        # for that, we need to just return a mock response
        # our frontend can then do stuff with that response, i.e. display a little animation or play a sound or whatnot

        # Create stored document with server-assigned fields
        stored_document = api.Document()
        stored_document.CopyFrom(request.document)
        stored_document.id = str(uuid.uuid4())

        # Set timestamps
        now = timestamp_pb2.Timestamp()
        now.FromDatetime(datetime.now(timezone.utc))
        stored_document.created_at.CopyFrom(now)
        stored_document.updated_at.CopyFrom(now)

        # Set character count
        stored_document.character_count = len(request.document.content)

        return api.StoreDocumentResponse(
            success=True,
            message=f"Document '{stored_document.name}' stored successfully",
            document=stored_document,
        )

    async def get_document(
        self, request: api.GetDocumentRequest, ctx
    ) -> api.GetDocumentResponse:
        logger.info(f"Received GetDocumentRequest for ID: {request.id}")

        # TODO: Implement actual document retrieval from storage
        return api.GetDocumentResponse(
            success=False,
            message="Document retrieval not yet implemented",
        )

    # TODO: We should have an update function that allows us to update a document by ID
    # This function should store previous versions of documents, so that people don't accidentally
    # Nuke their stuff
    # TODO: We may want to be able to clean up these old versions globally somehow
    # Or maybe we expire them after a certain time period?
    # But then what about losing the history of a document? That sounds pretty meh
    # Using git for this seems heavy...
    async def update_document(
        self, request: api.UpdateDocumentRequest, ctx
    ) -> api.UpdateDocumentResponse:
        logger.info(f"Received UpdateDocumentRequest for ID: {request.document.id}")

        # TODO: Implement actual document update in storage
        updated_document = api.Document()
        updated_document.CopyFrom(request.document)

        # Update timestamps
        now = timestamp_pb2.Timestamp()
        now.FromDatetime(datetime.now(timezone.utc))
        updated_document.updated_at.CopyFrom(now)

        # Update character count
        updated_document.character_count = len(request.document.content)

        return api.UpdateDocumentResponse(
            success=False,
            message=f"Document upate functionality not implemented yet; document '{updated_document.name}' not updated successfully",
            # TODO: should the response really contain the updated document? seems pretty redunant
            document=updated_document,
        )

    async def search_documents(
        self, request: api.SearchDocumentsRequest, ctx
    ) -> api.SearchDocumentsResponse:
        logger.info("Received SearchDocumentsRequest")

        # TODO: Implement actual document search
        return api.SearchDocumentsResponse(
            success=False,
            message="Search not yet implemented",
            documents=[],
            total_count=0,
            page_number=request.page_number,
            has_more=False,
        )

    async def delete_document(
        self, request: api.DeleteDocumentRequest, ctx
    ) -> api.DeleteDocumentResponse:
        logger.info(f"Received DeleteDocumentRequest for ID: {request.id}")

        # TODO: Implement actual document deletion
        return api.DeleteDocumentResponse(
            success=False,
            message="Document deletion not yet implemented",
        )
