# Database services via Docker Compose
# GPU_VENDOR env var selects an optional overlay: 'nvidia' or 'amd' (default: CPU-only)
gpu_vendor = os.environ.get('GPU_VENDOR', '')
uv_extra = {'nvidia': 'gpu', 'amd': 'rocm'}.get(gpu_vendor, 'cpu')
compose_files = ['dev-environment/docker-compose.yaml']
if gpu_vendor == 'nvidia':
    compose_files.append('dev-environment/docker-compose.nvidia.yml')
elif gpu_vendor == 'amd':
    compose_files.append('dev-environment/docker-compose.amd.yml')
docker_compose(compose_files)

# Configure database resources
dc_resource('postgres-pgvector', labels=['databases'])

# not needed for now
#dc_resource('postgres-age', labels=['databases'])
#dc_resource('arcadedb', labels=['databases'])

# Configure LLM service
dc_resource('ollama', labels=['llm'])

local_resource(
    'backend',
    serve_cmd='cd python-server && GPU_VENDOR={} just dev'.format(gpu_vendor),
    # Tilt will automatically reload when these files change
    # fairly sure, that the --reload flag for uvicorn will handle this
    #deps=[
    #    'python-server/server.py',
    #    'python-server/loading_service_implementation.py',
    #    'python-server/bibliophage/',
    #],
    labels=['app'],
    resource_deps=['postgres-pgvector'],
    serve_env={
        'PYTHONUNBUFFERED': '1',  # Ensure logs appear immediately
        # Database connections (12-factor: config from environment)
        'VECTOR_DB_URL': 'postgresql://pgvector:pgvector_dev@localhost:5432/pgvector',
        # Ollama configuration
        'OLLAMA_URL': 'http://localhost:11435',
        'OLLAMA_DEFAULT_MODEL': 'mistral',
        # Optional: override defaults
        # 'EMBEDDING_MODEL_NAME': 'BAAI/bge-large-en-v1.5',
        # 'EMBEDDING_DEVICE': 'cuda',  # override auto-detection (cpu, cuda, mps, xpu)
        # 'LOG_LEVEL': 'INFO',
    },
    # do these make sense? currently, the API docs are empty
    # TODO: would be neat to actually have API docs here
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
    cmd='cd python-server && just gen-proto && cd ../web-ui && yarn api',
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
    'nuke containers&volumes',
    cmd='cd dev-environment && docker compose down -v',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['tools'],
)
