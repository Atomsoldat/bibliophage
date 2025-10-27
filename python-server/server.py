import grpc
# futures has loads of stuff in it for parallel execution
from concurrent import futures
# reflection is used by clients to figure out what API endpoints there are
from grpc_reflection.v1alpha import reflection
from grpc_generated import api_pb2
from grpc_generated import api_pb2_grpc
import os
import sys
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector


class LoadingServiceServicer(api_pb2_grpc.LoadingServiceServicer):
    def LoadPDF(self, request, context):

        logging.info(f"Received LoadPdf request for file: {request.pdf_name}")
        
        # request will be the PdfLoadRequest from the client
        # we should access the fields in the request and do stuff with it
        # like setting metadata

        # https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.pdf.PyPDFLoader.html
        loader = PyPDFLoader(request.pdf_origin_path)

        # as far as i know, this loads individual pages
        documents = loader.load()
        logging.info(f'PDF "documents" loaded: {len(documents)}')

        chunk_size = request.chunk_size if request.HasField('chunk_size') else 600
        chunk_overlap = request.chunk_overlap if request.HasField('chunk_overlap') else 50
        # https://python.langchain.com/api_reference/text_splitters/character/langchain_text_splitters.character.RecursiveCharacterTextSplitter.html
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
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
        pgvector.add_documents(chunks)

        # when that's done, we return a PdfLoadResponse
        return api_pb2.PdfLoadResponse(
            success=True,
            message=f"PDF {request.pdf_name} loaded successfully",
            chunks_created=len(chunks),
            # TODO: uuid/md5sum
            # document_id="some-uuid"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # register our Servicer class at the grpc server
    # if a client requests a service that the Servicer can Service
    # the grpc server will send it that way
    api_pb2_grpc.add_LoadingServiceServicer_to_server(
        LoadingServiceServicer(), server
    )

    # Clients can use reflection to figure out which services the server offers through
    # another, standardised service
    # https://grpc.io/chunks/guides/reflection/
    # TODO: This may lower the security of a given API by allowing people to see which
    # services exist.  Although releasing the code to the public probably does the same
    # so i think this is not an issue to worry about atm
    #
    # apparently this bit where  we have to tell the reflection service
    # which services are floating around in our server is not necessary in the
    # implementation of other languages, so that is something to look forward to (:
    SERVICE_NAMES = (
        api_pb2.DESCRIPTOR.services_by_name["LoadingService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

# if our python file is executed as the main program
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    
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

    # done initialising, now we wait for someone to talk to us
    serve()
