import os
import sys
import logging

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bibliophage.v1alpha1.pdf_connect import LoadingServiceASGIApplication
from loading_service_implementation import LoadingServiceImplementation



# this is the core of our API application,
# https://fastapi.tiangolo.com/reference/fastapi/
# when we run `uvicorn server:api_server`, we are effectively telling uvicorn
# look in the module "server", which corresponds to `server.py` and from that module
# import `api_server` and execute `uvicorn.run(api_server)`
# where uvicorn will look for this object depends on the python path but we are keeping
# it simple for now and run everything from the same directory
api_server = FastAPI()

# CORS, so Vue can call the server
# https://fastapi.tiangolo.com/tutorial/cors/
# Browsers will ask a server they talk to whether that server likes the idea of being
# talked to by a client from a given origin
# this prevents malicious websites from hijacking a user's browser and talking to the backend
# i suppose it would not be great if someone could have his LLM API Tokens stolen
# TODO: Would be neat to have this set up properly anyway as a finger exercise
# TODO: Think about whether we want to  restrict and/or configure this somehow
api_server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# instantiate each of our Service Implementations of the Service Interfaces generated for us
loading_service = LoadingServiceImplementation()



# toss our instantiated implementation into the generated wrapper so we don't need to think about
# how all the communication works
loading_service_endpoint = LoadingServiceASGIApplication(service=loading_service)


# Apply CORS directly to the mounted app
loading_service_endpoint_cors = CORSMiddleware(
    app=loading_service_endpoint,
    allow_origins=["*"],            
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ASGI (Asynchronous Server Gateway Interface) is a python concept for 
# how web applications can talk to web servers
# https://asgi.readthedocs.io/en/latest/
# in this case, Connect RPC uses it as a standard for talking to Connect Servers
# the protoc plugin generated ASGI application wrappers for us, that do all the
# ASGI stuff without us having to use our poor brains too much
# that's different from how it works with gRPC, but let's just go with it


# mount the ConnectRPC wrapped application
api_server.mount(
    loading_service_endpoint.path,
    loading_service_endpoint_cors,
)

