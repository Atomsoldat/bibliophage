import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bibliophage.v1alpha2.document_connect import DocumentServiceASGIApplication
from bibliophage.v1alpha2.pdf_connect import PdfServiceASGIApplication
from document_service_implementation import DocumentServiceImplementation
from loading_service_implementation import LoadingServiceImplementation


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(asctime)s %(name)s  %(message)s",
        stream=sys.stdout,
    )


configure_logging()


# this is the core of our API application,
# https://fastapi.tiangolo.com/reference/fastapi/
# when we run `uvicorn server:api_server`, we are effectively telling uvicorn
# look in the module "server", which corresponds to `server.py` and from that module
# import `api_server` and execute `uvicorn.run(api_server)`
# where uvicorn will look for this object depends on the python path but we are keeping
# it simple for now and run everything from the same directory
# TODO: We can make  all kinds of configurations for this API, e.g.
# for interactive API documentation
# https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI--example
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
pdf_service = LoadingServiceImplementation()
document_service = DocumentServiceImplementation()


# toss our instantiated implementation into the generated wrapper so we don't need to think about
# how all the communication works
pdf_service_endpoint = PdfServiceASGIApplication(service=pdf_service)
document_service_endpoint = DocumentServiceASGIApplication(service=document_service)


# Apply CORS directly to the mounted app
pdf_service_endpoint_cors = CORSMiddleware(
    app=pdf_service_endpoint,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_service_endpoint_cors = CORSMiddleware(
    app=document_service_endpoint,
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
    pdf_service_endpoint.path,
    pdf_service_endpoint_cors,
)

# TODO: is mounting multiple services  done using multiple invocations of mount?
api_server.mount(
    document_service_endpoint.path,
    document_service_endpoint_cors,
)
