import bibliophage.v1alpha2.pdf_pb2 as api

import logging
import traceback
import uuid
from datetime import datetime, timezone

import os
import sys
from tempfile import NamedTemporaryFile

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector
from google.protobuf import timestamp_pb2

logger = logging.getLogger(__name__)


# this class implements the interface that our generated connect RPC code defines
# it does that by having all the methods of the interface class
class LoadingServiceImplementation:
    # PG_CONNECTION_STRING - "postgresql+psycopg://user:pass@localhost:5432/db"
    # Define environment variable names
    env_var_connection_string_name = "PG_CONNECTION_STRING"

    # Retrieve environment variables
    if env_var_connection_string_name not in os.environ:
        logging.error(
            f"{env_var_connection_string_name} environment variable is not set."
        )
        sys.exit(1)

    # Initialise vector database connection
    pgvector = PGVector(
        connection=os.getenv(env_var_connection_string_name),
        embeddings=HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5"),
    )

    # TODO: figure out why we can use ctx without a type  here, also we should probably prevent that
    async def load_pdf(self, request: api.LoadPdfRequest, ctx):
        try:
            # TODO: actually do stuff with the request
            logger.info(f"Received LoadPdf request for file: {request.pdf.name}")

            # request will be the LoadPdfRequest from the client
            # we should access the fields in the request and do stuff with it
            # like setting metadata

            pdf_bytes = request.file_data

            # store transmitted data in a temporary file
            # `with` will always run the cleanup functions of the file object we create
            # https://docs.python.org/3/reference/compound_stmts.html#index-18
            # https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers
            with NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
                tmp.write(pdf_bytes)
                tmp.flush()
                logger.info(f"Temporary file name: {tmp.name}")

                # https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.pdf.PyPDFLoader.html

                # access path on disk and try to  load
                # loader = PyPDFLoader(request.pdf.origin_path)
                # use transferred data in request
                loader = PyPDFLoader(tmp.name)
                documents = loader.load()

            # as far as i know, this loads individual pages
            logger.info(f'PDF "documents" loaded: {len(documents)}')

            chunk_size = request.chunking_config.chunk_size if request.HasField("chunking_config") and request.chunking_config.chunk_size > 0 else 600
            chunk_overlap = request.chunking_config.chunk_overlap if request.HasField("chunking_config") and request.chunking_config.chunk_overlap > 0 else 50

            # https://python.langchain.com/api_reference/text_splitters/character/langchain_text_splitters.character.RecursiveCharacterTextSplitter.html
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            # TODO: perhaps we can send some kind of progress indicator to the user here?
            chunks = text_splitter.split_documents(documents)

            # it seems weird to attach information like the original PDF path to  every chunk
            # TODO: we probably just want to have a separate, regular table containing the origin information and
            # then we can reference that table
            for chunk in chunks:
                chunk.metadata.update({"source": request.pdf.origin_path})
                chunk.metadata.update({"origin_path": request.pdf.origin_path})
                chunk.metadata.update({"system": request.pdf.system})
                chunk.metadata.update({"type": request.pdf.type})
                chunk.metadata.update({"page_count": len(documents)})
                chunk.metadata.update({"chunk_count": len(chunks)})
                # TODO: uuid/md5sum

            # Store Chunks in Vector DB
            self.pgvector.add_documents(chunks)

            # Create response with stored PDF metadata
            stored_pdf = api.Pdf()
            stored_pdf.CopyFrom(request.pdf)
            stored_pdf.id = str(uuid.uuid4())
            stored_pdf.page_count = len(documents)
            stored_pdf.chunk_count = len(chunks)
            stored_pdf.file_size = len(pdf_bytes)

            # Set timestamps
            now = timestamp_pb2.Timestamp()
            now.FromDatetime(datetime.now(timezone.utc))
            stored_pdf.created_at.CopyFrom(now)
            stored_pdf.updated_at.CopyFrom(now)

            # when that's done, we return a LoadPdfResponse
            return api.LoadPdfResponse(
                success=True,
                message=f"PDF {request.pdf.name} loaded successfully",
                # Returning the pdf here makes no sense to me
                pdf=stored_pdf,
                # TODO: uuid/md5sum
                # document_id="some-uuid"
            )
        except Exception as e:
            logger.error(f"Exception: {e}\n{traceback.format_exc()}")
            raise

    async def search_pdfs(
        self, request: api.SearchPdfsRequest, ctx
    ) -> api.SearchPdfsResponse:
        logger.info("Received SearchPdfsRequest")

        # TODO: Implement actual PDF search
        # When implementing, create PdfListItem instances from Pdf metadata:
        # list_item = api.PdfListItem(
        #     id=pdf.id,
        #     name=pdf.name,
        #     system=pdf.system,
        #     type=pdf.type,
        #     page_count=pdf.page_count,
        #     origin_path=pdf.origin_path,
        #     created_at=pdf.created_at,
        #     updated_at=pdf.updated_at,
        #     file_size=pdf.file_size,
        #     chunk_count=pdf.chunk_count,
        #     tags=pdf.tags
        # )
        return api.SearchPdfsResponse(
            success=False,
            message="Search not yet implemented",
            pdfs=[],  # This will be a list of PdfListItem, not Pdf
            total_count=0,
            page_number=request.page_size if request.page_number else 0,
            has_more=False,
        )

    async def get_pdf(
        self, request: api.GetPdfRequest, ctx
    ) -> api.GetPdfResponse:
        logger.info(f"Received GetPdfRequest for ID: {request.id}")

        # TODO: Implement actual PDF retrieval
        return api.GetPdfResponse(
            success=False,
            message="PDF retrieval not yet implemented",
        )
