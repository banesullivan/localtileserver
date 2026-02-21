FROM jupyter/base-notebook:python-3.12
LABEL maintainer="Bane Sullivan"
LABEL repo="https://github.com/banesullivan/localtileserver"

USER jovyan

WORKDIR /build-context

RUN python -m pip install --upgrade pip

COPY pyproject.toml README.md /build-context/
COPY localtileserver/ /build-context/localtileserver/
RUN pip install "/build-context[all,test]"

WORKDIR $HOME

COPY example.ipynb $HOME

ENV JUPYTER_ENABLE_LAB=yes

ARG LOCALTILESERVER_CLIENT_PREFIX='proxy/{port}'
ENV LOCALTILESERVER_CLIENT_PREFIX=$LOCALTILESERVER_CLIENT_PREFIX
