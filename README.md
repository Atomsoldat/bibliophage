# Bibliophage

The idea behind Bibliophage is that it loads RPG rulebook PDFs into a PostgreSQL vector database and then provides RAG capabilities based on the information stored in those books. The application uses Python and LangChain for PDF processing and embeddings, with gRPC for service communication. Eventually this will expand into a GM toolbox with session notes, content generation, and reference lookup. Or whatever else i come up with. Or it will end up collecting dust somewhere on my hard drive, we will see...

Currently, there's a rudimentary web-ui talking to a backend service, that handles all the funny ML bits. This is a work in progress and may change at any moment, just in case this was not clear enough.

## Quick Start

First start the server in one shell window
```bash
cd python-server

# Install dependencies
pixi install

# Generate Python gRPC code from proto file
pixi run generate-proto

# Run the gRPC server 
# the runscript currently fetches the DB password from my own environment
# you will need to adjust that, if you want to do anything with it
pixi run server
```

In another shell window, start the web-ui

```bash
cd django

# Install dependencies
pixi install

pixi run setup-and-run
```


## Database
PostgreSQL with pgvector at `vectordb.bibliophage.irminsul`, database `vectors`, user `bibliophage`.
