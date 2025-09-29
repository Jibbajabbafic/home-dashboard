#!/bin/bash
docker login
if docker buildx ls | grep -q desktop-linux; then
    echo "Builder exists already"
else
    echo "Builder does not exist - creating new one"
    docker buildx create --use desktop-linux
fi
docker buildx build --platform linux/amd64,linux/arm64 -t jibby/home-dashboard:latest --push .