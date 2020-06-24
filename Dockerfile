FROM python:3.6-slim

RUN set -ex \
    && apt update \
    && pip install --no-cache-dir --upgrade pip

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app

COPY . /app

ENTRYPOINT ./entrypoint
