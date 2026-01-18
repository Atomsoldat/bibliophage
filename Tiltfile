# Database services via Docker Compose
docker_compose('dev-environment/docker-compose.yaml')

# Configure database resources
dc_resource('postgres-pgvector', labels=['databases'])
dc_resource('postgres-documentdb', labels=['databases'])
dc_resource('postgres-age', labels=['databases'])
dc_resource('ferretdb', labels=['databases'])

# Configure LLM service
dc_resource('ollama', labels=['llm'])

local_resource(
    'backend',
    serve_cmd='cd python-server && pixi run dev',
    # Tilt will automatically reload when these files change
    # fairly sure, that the --reload flag for uvicorn will handle this
    #deps=[
    #    'python-server/server.py',
    #    'python-server/loading_service_implementation.py',
    #    'python-server/bibliophage/',
    #],
    labels=['app'],
    resource_deps=['postgres-pgvector', 'postgres-documentdb', 'ferretdb'],
    serve_env={
        'PYTHONPATH': 'src',
        'PYTHONUNBUFFERED': '1',  # Ensure logs appear immediately
        # Database connections (12-factor: config from environment)
        'VECTOR_DB_URL': 'postgresql://pgvector:pgvector_dev@localhost:5432/pgvector',
        'DOC_DB_URL': 'mongodb://postgres:ferretdb_dev@localhost:27017/',
        # Ollama configuration
        'OLLAMA_URL': 'http://localhost:11435',
        'OLLAMA_DEFAULT_MODEL': 'mistral',
        # Optional: override defaults
        # 'EMBEDDING_MODEL_NAME': 'BAAI/bge-large-en-v1.5',
        # 'LOG_LEVEL': 'INFO',
    },
    # do these make sense?
    #links=[
    #    link('http://localhost:8000', 'Backend API'),
    #    link('http://localhost:8000/docs', 'API Docs (FastAPI)'),
    #],
)

local_resource(
    'web-ui',
    serve_cmd='cd web-ui && yarn dev',
    # Vite has its own HMR, but Tilt needs to know when to restart the process
    deps=[
        'web-ui/src/',
        'web-ui/index.html',
        'web-ui/vite.config.ts',
        'web-ui/package.json',
    ],
    labels=['app'],
    links=[
        link('http://localhost:5173', 'Frontend UI'),
    ],
)

local_resource(
    'api',
    cmd='cd python-server && pixi run api && cd ../web-ui && yarn api',
    deps=['api/bibliophage/'],
    auto_init=False,  # Don't run automatically on startup
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['tools'],
)

local_resource(
    'api-format',
    cmd='buf format --write api',
    deps=['api/bibliophage/'],
    auto_init=False,  # Don't run automatically on startup
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['tools'],
)

local_resource(
    'ollama-pull-model',
    cmd='docker exec bibliophage-ollama ollama pull $MODEL',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['llm'],
    env={
        'MODEL': 'mistral',  # Default model, can be overridden
    },
)

local_resource(
    'nuke everything',
    cmd='docker compose down -v',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['tools'],
)
