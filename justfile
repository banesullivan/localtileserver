# justfile for localtileserver
#
# All Python-touching recipes go through ``uv run`` so the tool
# versions come from the locked venv (see ``uv.lock``) instead of
# whatever ``pyenv``/system Python happens to be first on PATH. This
# keeps lint / typecheck / test results reproducible for contributors.

set dotenv-load := false
set shell := ["bash", "-euo", "pipefail", "-c"]

# Default: list available recipes
default:
    @just --list

# --- Variables ---
docker_image     := env("DOCKER_IMAGE", "localtileserver")
docker_image_jup := docker_image + "-jupyter"
port             := env("PORT", "8000")

# --- Development ---

# Sync UV env with all dev/test/doc dependencies
sync:
    uv sync --all-extras

# Sync deps and install pre-commit hooks (first-time setup)
install: sync
    uv run pre-commit install

# Run all pre-commit hooks
lint:
    uv run pre-commit run --all-files

# Auto-format and fix code
format:
    uv run ruff format localtileserver tests
    uv run ruff check --fix localtileserver tests

# Run tests with coverage
test:
    uv run pytest --cov=localtileserver

# Run module doctests
doctest:
    uv run pytest -v --doctest-modules localtileserver

# Run tests and generate HTML coverage report
coverage:
    uv run pytest --cov=localtileserver --cov-report=html
    @echo "Coverage report: htmlcov/index.html"

# Print scooby system report
report:
    uv run python -c "import localtileserver; print(localtileserver.Report())"

# --- Documentation ---

# Build Sphinx HTML documentation
docs:
    LOCALTILESERVER_BUILDING_DOCS=true uv run sphinx-build -M html doc/source doc/build

# Build docs with live tile server and serve locally
docs-serve tile_port="58998" doc_port="58999":
    #!/usr/bin/env bash
    set -euo pipefail
    rm -rf doc/build
    echo "Starting localtileserver on port {{ tile_port }} ..."
    LOCALTILESERVER_CORS_ALL=1 uv run python -m uvicorn localtileserver.web.wsgi:app \
        --host 0.0.0.0 --port {{ tile_port }} --log-level warning &
    TILE_PID=$!
    sleep 2
    echo "Tile server ready (PID $TILE_PID) at http://localhost:{{ tile_port }}"
    LOCALTILESERVER_BUILDING_DOCS=true \
    LOCALTILESERVER_CLIENT_HOST=http://localhost:{{ tile_port }} \
    uv run sphinx-build -M html doc/source doc/build
    BUILD_STATUS=$?
    if [ $BUILD_STATUS -ne 0 ]; then
        echo "Sphinx build failed (exit $BUILD_STATUS). Stopping tile server ..."
        kill $TILE_PID 2>/dev/null || true
        exit $BUILD_STATUS
    fi
    echo ""
    echo "============================================================"
    echo "  Docs:        http://localhost:{{ doc_port }}"
    echo "  Tile server: http://localhost:{{ tile_port }}"
    echo "  Press Ctrl-C to stop."
    echo "============================================================"
    echo ""
    trap "kill $TILE_PID 2>/dev/null; exit 0" INT TERM
    uv run python -m http.server -d doc/build/html {{ doc_port }}
    kill $TILE_PID 2>/dev/null || true

# --- Docker ---

# Build slim Docker image
build-slim:
    docker build -t {{ docker_image }} --target slim .

# Build Jupyter Docker image
build-jupyter:
    docker build -t {{ docker_image_jup }} --target jupyter .

# Build all Docker images
build: build-slim build-jupyter

# Run the slim Docker image
docker-run:
    docker run --rm -it -p {{ port }}:8000 {{ docker_image }}

# Run the Jupyter Docker image
jupyter:
    docker run --rm -it -p 8888:8888 {{ docker_image_jup }}

# --- Server ---

# Run local dev server with hot reload
serve:
    uv run uvicorn localtileserver.web.wsgi:app --host 0.0.0.0 --port {{ port }} --reload

# --- Cleanup ---

# Remove generated test images
clean-test-images:
    rm -rf tests/baseline/ tests/generated/

# Remove all build artifacts
clean: clean-test-images
    rm -rf dist/ build/ *.egg-info
    rm -rf doc/build
    rm -rf htmlcov/ .coverage
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
