# Bibliophage

The idea behind Bibliophage is that it loads RPG rulebook PDFs into a PostgreSQL vector database and then provides RAG capabilities based on the information stored in those books. The application uses Python and LangChain for PDF processing and embeddings, with  Connect RPC for service communication. Eventually this will expand into a GM toolbox with session notes, content generation, and reference lookup. Or whatever else i come up with. Or it will end up collecting dust somewhere on my hard drive, we will see...

Currently, there's a rudimentary web-ui which is in the process of being hooked up to a backend service, that handles all the funny ML bits. This is a work in progress and may change at any moment, just in case this was not clear enough.

## Quick Start

First start the server in one shell window
```bash
cd python-server

# Install dependencies
pixi install

# execute
pixi run dev
```

In another shell window, start the web-ui

```bash
cd web-ui

# Install dependencies
yarn install

# execute
yarn dev
```

## Connect RPC API

The components of this service communicate via the Connect RPC protocol

```bash
make api
```

## Database
PostgreSQL with pgvector at `vectordb.bibliophage.irminsul`, database `vectors`, user `bibliophage`.
