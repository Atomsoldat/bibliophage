#!/bin/bash

# This script is meant for debugging and quick one-off executions of python code

# Keep all __pycache__ dirs out of the source tree, mirrored under one root.
export PYTHONPYCACHEPREFIX="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.pycache"

# Source environment variables from .env.example
if [ -f .env.example ]; then
    set -a  # Automatically export all variables
    source .env.example
    set +a
fi

# Override with .env if it exists (for local development)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Check if a parameter was provided (e.g., a Python file to run)
if [ -n "$1" ]; then
    # Run the provided Python file with all arguments
    python "$@"
else
    # Default: start the uvicorn web server
    # https://uvicorn.dev/settings/#configuration-methods
    # -- reload enables hot reloading
    python -m uvicorn \
        --reload \
        src.server:api_server
fi
