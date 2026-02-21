FROM python:3.12-slim
LABEL maintainer="Bane Sullivan"
LABEL repo="https://github.com/banesullivan/localtileserver"

WORKDIR /build-context

RUN python -m pip install --upgrade pip

COPY pyproject.toml README.md /build-context/
COPY localtileserver/ /build-context/localtileserver/
RUN pip install "/build-context[colormaps]"

ENTRYPOINT ["uvicorn", "localtileserver.web.wsgi:app", "--host=0.0.0.0", "--port=8000"]
# docker run --rm -it -p 8000:8000 localtileserver
