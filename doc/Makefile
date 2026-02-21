# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Tile-server settings for interactive docs (overridable)
TILE_SERVER_PORT ?= 58998
TILE_SERVER_HOST ?= 0.0.0.0
DOC_SERVER_PORT  ?= 58999

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile serve-html

# Build docs with a local tile server and then serve everything so
# interactive widgets work when browsing locally.
#
# Usage:
#   make serve-html                          # default ports
#   make serve-html TILE_SERVER_PORT=9000    # custom tile server port
#   make serve-html DOC_SERVER_PORT=8080     # custom doc server port
#
# How it works:
#   1. Starts localtileserver (uvicorn) in the background with CORS enabled
#      so that the static HTML can fetch tiles cross-origin.
#   2. Sets LOCALTILESERVER_BUILDING_DOCS=true so example data paths resolve
#      to remote GitHub URLs (the server fetches them via GDAL VSI).
#   3. Sets LOCALTILESERVER_CLIENT_HOST so tile URLs in rendered widgets
#      point to the local server instead of the public demo server.
#   4. Builds the Sphinx HTML documentation.
#   5. Serves the built HTML on DOC_SERVER_PORT (blocking – Ctrl-C to stop).
serve-html:
	@echo "Cleaning previous build ..."; \
	rm -rf "$(BUILDDIR)"; \
	echo "Starting localtileserver on port $(TILE_SERVER_PORT) ..."; \
	LOCALTILESERVER_CORS_ALL=1 python -m uvicorn localtileserver.web.wsgi:app \
		--host $(TILE_SERVER_HOST) --port $(TILE_SERVER_PORT) \
		--log-level warning & \
	TILE_PID=$$!; \
	sleep 2; \
	echo "Tile server ready (PID $$TILE_PID) at http://localhost:$(TILE_SERVER_PORT)"; \
	LOCALTILESERVER_BUILDING_DOCS=true \
	LOCALTILESERVER_CLIENT_HOST=http://localhost:$(TILE_SERVER_PORT) \
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O); \
	BUILD_STATUS=$$?; \
	if [ $$BUILD_STATUS -ne 0 ]; then \
		echo "Sphinx build failed (exit $$BUILD_STATUS). Stopping tile server ..."; \
		kill $$TILE_PID 2>/dev/null || true; \
		exit $$BUILD_STATUS; \
	fi; \
	echo ""; \
	echo "============================================================"; \
	echo "  Docs:        http://localhost:$(DOC_SERVER_PORT)"; \
	echo "  Tile server: http://localhost:$(TILE_SERVER_PORT)"; \
	echo "  Press Ctrl-C to stop."; \
	echo "============================================================"; \
	echo ""; \
	trap "kill $$TILE_PID 2>/dev/null; exit 0" INT TERM; \
	python -m http.server -d $(BUILDDIR)/html $(DOC_SERVER_PORT); \
	kill $$TILE_PID 2>/dev/null || true

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
