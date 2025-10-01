#!/bin/bash
docker login
if docker buildx inspect | grep -q "Endpoint:.*unix:///var/run/docker.sock" ; then
    echo "Builder exists already"
else
    echo "Builder does not exist - creating new one"
    docker buildx create --use default
fi
docker buildx build --platform linux/amd64,linux/arm64 -t jibby/home-dashboard:latest --push .