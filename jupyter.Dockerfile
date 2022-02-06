FROM jupyter/base-notebook:python-3.9.7
LABEL maintainer="Bane Sullivan"
LABEL repo="https://github.com/banesullivan/localtileserver"

USER jovyan

WORKDIR /build-context

RUN python -m pip install --upgrade pip

COPY requirements.txt /build-context/
COPY requirements_jupyter.txt /build-context/
RUN pip install -r requirements_jupyter.txt

RUN pip install jupyter-server-proxy

COPY setup.py /build-context/
COPY MANIFEST.in /build-context/
COPY localtileserver/ /build-context/localtileserver/
RUN python setup.py bdist_wheel
RUN pip install dist/localtileserver*.whl

WORKDIR $HOME

COPY example.ipynb $HOME

ENV JUPYTER_ENABLE_LAB=yes

ARG LOCALTILESERVER_CLIENT_PORT=8888
ENV LOCALTILESERVER_CLIENT_PORT=$LOCALTILESERVER_CLIENT_PORT
ARG LOCALTILESERVER_CLIENT_HOST=127.0.0.1
ENV LOCALTILESERVER_CLIENT_HOST=$LOCALTILESERVER_CLIENT_HOST
ARG LOCALTILESERVER_CLIENT_PREFIX='proxy/{port}'
ENV LOCALTILESERVER_CLIENT_PREFIX=$LOCALTILESERVER_CLIENT_PREFIX
