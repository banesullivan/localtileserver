# Multi-stage Dockerfile for localtileserver
#
# Targets:
#   slim    - minimal server image (default)
#   jupyter - JupyterLab with localtileserver pre-installed
#
# Usage:
#   docker build -t localtileserver .                        # slim (default)
#   docker build -t localtileserver --target slim .          # slim (explicit)
#   docker build -t localtileserver-jupyter --target jupyter .
#
#   docker run --rm -it -p 8000:8000 localtileserver
#   docker run --rm -it -p 8888:8888 localtileserver-jupyter

# ---- shared base: install the package once ----
FROM python:3.12-slim AS base

LABEL maintainer="Bane Sullivan"
LABEL repo="https://github.com/banesullivan/localtileserver"

# libexpat1 is required at runtime by the GDAL bundled in the rasterio wheel
RUN apt-get update && apt-get install -y --no-install-recommends \
        libexpat1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build-context

RUN python -m pip install --upgrade --no-cache-dir pip

COPY pyproject.toml README.md /build-context/
COPY localtileserver/ /build-context/localtileserver/

# ---- slim: server-only image (default) ----
FROM base AS slim

RUN pip install --no-cache-dir "/build-context[colormaps]"

EXPOSE 8000
ENTRYPOINT ["uvicorn", "localtileserver.web.wsgi:app", "--host=0.0.0.0", "--port=8000"]

# ---- jupyter: full JupyterLab image ----
FROM base AS jupyter

RUN pip install --no-cache-dir "/build-context[all,test]" jupyterlab

ARG LOCALTILESERVER_CLIENT_PREFIX='proxy/{port}'
ENV LOCALTILESERVER_CLIENT_PREFIX=$LOCALTILESERVER_CLIENT_PREFIX
ENV JUPYTER_ENABLE_LAB=yes

WORKDIR /home

COPY example.ipynb /home/

EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
