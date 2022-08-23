#!/bin/sh

docker tag svs-tileserver ghcr.io/supervisionearth/tileserver:latest
docker push ghcr.io/supervisionearth/tileserver:latest