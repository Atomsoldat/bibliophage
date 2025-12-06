import logging

from bibliophage.v1alpha1.pdf_connect import LoadingService
import bibliophage.v1alpha1.document_pb2 as api

logger = logging.getLogger(__name__)


class DocumentServiceImplementation:
    # TODO: figure out where the type of ctx is defined, we  don't use it in the loading service either
    async def store_document(
        self, request: api.DocumentStoreRequest, ctx
    ) -> api.DocumentStoreResponse:
        logger.info(
            f"Received DocumentStoreRequest for document: {request.document_name}"
        )

        # first we just pretend to do something with the request. later, we will actually store the document
        # for that, we need to just return a mock response
        # our frontend can then do stuff with that response, i.e. display a little animation or play a sound or whatnot
        return api.DocumentStoreResponse(
            success=True,
            message=f"Document {request.document_name} loaded successfully",
        )

    # TODO: We should have an update function that allows us to update a document by ID
    # This function should store previous versions of documents, so that people don't accidentally
    # Nuke their stuff
    # TODO: We may want to be able to clean up these old versions globally somehow
    # Or maybe we expire them after a certain time period?
    # But then what about losing the history of a document? That sounds pretty meh
    # Using git for this seems heavy...
