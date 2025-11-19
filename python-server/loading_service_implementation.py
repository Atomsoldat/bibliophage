from bibliophage.v1alpha1.pdf_connect import LoadingService
import bibliophage.v1alpha1.pdf_pb2 as api

import logging
import traceback
import inspect

import os
import sys
from tempfile import NamedTemporaryFile

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector

logger = logging.getLogger(__name__)


# this class implements the interface that our generated connect RPC code defines
# it does that by having all the methods of the interface class
class LoadingServiceImplementation:
    # PG_CONNECTION_STRING - "postgresql+psycopg://user:pass@localhost:5432/db"
    # Define environment variable names
    env_var_connection_string_name = "PG_CONNECTION_STRING"
    
    # Retrieve environment variables
    if env_var_connection_string_name not in os.environ:
        logging.error(f"{env_var_connection_string_name} environment variable is not set.")
        sys.exit(1)

    # Initialise vector database connection
    pgvector = PGVector(
        connection=os.getenv(env_var_connection_string_name),
        embeddings=HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5"),
    )


    async def load_p_d_f(self, request: api.PdfLoadRequest, ctx):
        try:
            # TODO: actually do stuff with the request
            logger.info(f"Received LoadPdf request for file: {request.pdf_name}")

            # request will be the PdfLoadRequest from the client
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
                logger.info(f'Temporary file name: {tmp.name}')


                # https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.pdf.PyPDFLoader.html

                # access path on disk and try to  load
                #loader = PyPDFLoader(request.pdf_origin_path)
                # use transferred data in request
                loader = PyPDFLoader(tmp.name)
                documents = loader.load()

            # as far as i know, this loads individual pages
            logger.info(f'PDF "documents" loaded: {len(documents)}')

            chunk_size = request.chunk_size if request.HasField('chunk_size') else 600
            chunk_overlap = request.chunk_overlap if request.HasField('chunk_overlap') else 50
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
                chunk.metadata.update({"source": request.pdf_origin_path})
                chunk.metadata.update({"origin_path": request.pdf_origin_path})
                chunk.metadata.update({"system": request.pdf_system})
                chunk.metadata.update({"type": request.pdf_type})
                chunk.metadata.update({"page_count": len(documents)})
                chunk.metadata.update({"chunk_count": len(chunks)})
                # TODO: uuid/md5sum
            
            # Store Chunks in Vector DB
            self.pgvector.add_documents(chunks)

            # when that's done, we return a PdfLoadResponse
            return api.PdfLoadResponse(
                success=True,
                message=f"PDF {request.pdf_name} loaded successfully",
                chunks_created=len(chunks),
                # TODO: uuid/md5sum
                # document_id="some-uuid"
            )
        except Exception as e:
            logger.error(f"Exception: {e}\n{traceback.format_exc()}")
            raise
