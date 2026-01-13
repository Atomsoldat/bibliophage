# Bibliophage

The idea behind Bibliophage is that it loads RPG rulebook PDFs into a PostgreSQL vector database and then provides RAG capabilities based on the information stored in those books. The application uses Python and LangChain for PDF processing and embeddings, with  Connect RPC for service communication. Eventually this will expand into a GM toolbox with session notes, content generation, and reference lookup. Or whatever else i come up with. Or it will end up collecting dust somewhere on my hard drive, we will see...

Currently, there's a rudimentary web-ui which is in the process of being hooked up to a backend service, that handles all the funny ML bits. This is a work in progress and may change at any moment, just in case this was not clear enough.

## Toolchain Requirements

- [Tilt](https://docs.tilt.dev/) - orchestration
- [Docker](https://docs.docker.com/engine/install/) - containerised services
- [Docker Compose](https://docs.docker.com/compose/install/) - container management
- [pixi](https://pixi.sh/latest/installation/) - Python dependency management
- [Yarn](https://yarnpkg.com/getting-started/install) - JavaScript dependency management

## Quick Start

```bash
# Start all services (databases, backend, web-ui)
tilt up
```

This starts:
- **PostgreSQL with pgvector** (localhost:5432) - vector embeddings storage
- **PostgreSQL with DocumentDB** (localhost:5433) - FerretDB backend
- **FerretDB** (localhost:27017) - MongoDB-compatible document storage
- **Python backend** - Connect RPC API server (depends on all databases)
- **Web UI** - Vue frontend (http://localhost:5173)

The Python backend requires all three databases to start successfully. Tilt manages these dependencies automatically.

Press `space` in the terminal to open the Tilt UI in your browser.

## Connect RPC API

The components communicate via Connect RPC. To regenerate the api code, trigger the `api` resource in the Tilt UI, or execute the following command:

```bash
tilt trigger api
```
