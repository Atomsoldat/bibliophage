import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import db.postgres_db as postgres_db
from bibliophage.v1alpha3.chat_connect import ChatServiceASGIApplication
from bibliophage.v1alpha3.document_connect import DocumentServiceASGIApplication
from bibliophage.v1alpha3.embedding_connect import EmbeddingServiceASGIApplication
from bibliophage.v1alpha3.graph_connect import GraphServiceASGIApplication
from bibliophage.v1alpha3.pdf_connect import PdfServiceASGIApplication
from chat.service import ChatServiceImplementation
from documents.service import DocumentServiceImplementation
from embeddings.service import EmbeddingServiceImplementation
from graph.service import GraphServiceImplementation
from ingestion.service import LoadingServiceImplementation


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(asctime)s %(name)s  %(message)s",
        stream=sys.stdout,
    )


configure_logging()


# Initialise database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    db = postgres_db.get_postgres_db()
    await db.ensure_initialised()
    await db.initialise_schema()
    yield
    # clean up before shutdown
    await postgres_db.close_database()


# this is the core of our API application,
# https://fastapi.tiangolo.com/reference/fastapi/
# when we run `uvicorn server:api_server`, we are effectively telling uvicorn
# look in the module "server", which corresponds to `server.py` and from that module
# import `api_server` and execute `uvicorn.run(api_server)`
# where uvicorn will look for this object depends on the python path but we are keeping
# it simple for now and run everything from the same directory
# uvicorn is just the ASGI server; it parses bytes, builds the scope dict,
# and hands the request to api_server. It has no opinions about CORS or routing.
#   uvicorn docs: https://www.uvicorn.org/
# TODO: We can make  all kinds of configurations for this API, e.g.
# for interactive API documentation
# https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI--example
api_server = FastAPI(lifespan=lifespan)

# CORS, so Vue can call the server
# https://fastapi.tiangolo.com/tutorial/cors/
# Browsers will ask a server they talk to whether that server likes the idea of being
# talked to by a client from a given origin
# this prevents malicious websites from hijacking a user's browser and talking to the backend
# i suppose it would not be great if someone could have his LLM API Tokens stolen
# Background reading:
#   MDN's CORS overview (start here if you've never seen this before):
#     https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
#   The actual living standard (the W3C/Fetch spec defining preflight, etc.):
#     https://fetch.spec.whatwg.org/#http-cors-protocol
#   Starlette's CORSMiddleware reference (every keyword arg below is documented here):
#     https://www.starlette.io/middleware/#corsmiddleware
#   FastAPI's middleware mechanics (explains what add_middleware actually does):
#     https://fastapi.tiangolo.com/advanced/middleware/
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
# toss our instantiated implementation into the generated wrapper so we don't need to think about
# how all the communication works
service_endpoints = [
    PdfServiceASGIApplication(service=LoadingServiceImplementation()),
    DocumentServiceASGIApplication(service=DocumentServiceImplementation()),
    ChatServiceASGIApplication(service=ChatServiceImplementation()),
    EmbeddingServiceASGIApplication(service=EmbeddingServiceImplementation()),
    GraphServiceASGIApplication(service=GraphServiceImplementation()),
]

# ASGI (Asynchronous Server Gateway Interface) is a python concept for
# how web applications can talk to web servers
# https://asgi.readthedocs.io/en/latest/
# in this case, Connect RPC uses it as a standard for talking to Connect Servers
# the protoc plugin generated ASGI application wrappers for us, that do all the
# ASGI stuff without us having to use our poor brains too much
# that's different from how it works with gRPC, but let's just go with it


# mount the ConnectRPC wrapped application
# Mounted sub-apps inherit the parent's middleware stack — the top-level
# add_middleware(CORSMiddleware, ...) above is what serves CORS responses
# for requests routed here
#   FastAPI sub-applications:
#     https://fastapi.tiangolo.com/advanced/sub-applications/
#   Starlette routing / Mount (the layer under FastAPI's .mount()):
#     https://www.starlette.io/routing/#submounting-routes
for endpoint in service_endpoints:
    api_server.mount(endpoint.path, endpoint)
