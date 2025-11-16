import os
import sys
import logging

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector

from fastapi import FastAPI
from grpc_generated.api_connect import LoadingServiceASGIApplication
from loading_service_implementation import LoadingServiceImplementation



# this is the core of our API application,
# https://fastapi.tiangolo.com/reference/fastapi/
# when we run `uvicorn server:api_server`, we are effectively telling uvicorn
# look in the module "server", which corresponds to `server.py` and from that module
# import `api_server` and execute `uvicorn.run(api_server)`
# where uvicorn will look for this object depends on the python path but we are keeping
# it simple for now and run everything from the same directory
api_server = FastAPI()

# instantiate each of our Service Implementations of the Service Interfaces generated for us
loading_service = LoadingServiceImplementation()

# ASGI (Asynchronous Server Gateway Interface) is a python concept for 
# how web applications can talk to web servers
# https://asgi.readthedocs.io/en/latest/
# in this case, Connect RPC uses it as a standard for talking to Connect Servers
# the protoc plugin generated ASGI application wrappers for us, that do all the
# ASGI stuff without us having to use our poor brains too much
# that's different from how it works with gRPC, but let's just go with it

# toss our instantiated implementation into the generated wrapper so we don't need to think about
# how all the communication works
loading_app = LoadingServiceASGIApplication(loading_service)

# mount the ConnectRPC wrapped application
api_server.mount(loading_app.path, loading_app)
