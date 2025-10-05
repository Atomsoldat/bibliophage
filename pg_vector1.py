from langchain_postgres.vectorstores import PGVector
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import logging
import os
import sys


class PdfProcessor:
    def __init__(self, pdf_path, name):
        self.pdf_path = pdf_path
        self.name = name

    def ingest_pdf(self, chunk_size, chunk_overlap):
        loader = PyPDFLoader(self.pdf_path)
        # as far as i know, this loads individual pages
        documents = loader.load()
        print(f'PDF "documents" loaded: {len(documents)}')

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        docs = text_splitter.split_documents(documents)

        for doc in docs:
            doc.metadata.update({"source": self.pdf_path})
        return docs


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


bestiary_pdf_path = "pdfs/pf1e/bestiary_bonus.pdf"
bestiary_name = "Bonus Bestiary PF1E"

bestiary = PdfProcessor(bestiary_pdf_path, bestiary_name)


print(os.getenv("PG_CONNECTION_STRING"))


# PG_CONNECTION_STRING - "postgresql+psycopg://user:pass@localhost:5432/db"
env_var_connection_string_name = "PG_CONNECTION_STRING"
if env_var_connection_string_name not in os.environ:
    logging.error(f"{env_var_connection_string_name} environment variable is not set.")
    sys.exit(1)
pgvector = PGVector(
    connection=os.getenv(env_var_connection_string_name),
    embeddings=HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5"),
)

documents = bestiary.ingest_pdf(chunk_size=600, chunk_overlap=50)

# Store Chunks in Vector DB
pgvector.add_documents(documents)
