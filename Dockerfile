FROM python:3.8-slim

COPY requirements.txt /build-context/
WORKDIR /build-context

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY localtileserver/ /build-context/localtileserver/
COPY setup.py /build-context/
RUN python setup.py bdist_wheel
RUN pip install dist/localtileserver*.whl

ENTRYPOINT ["gunicorn", "--bind=0.0.0.0:8000", "localtileserver.tileserver.wsgi:app"]
# docker run --rm -it -p 8000:8000 localtileserver
