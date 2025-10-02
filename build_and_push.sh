#!/bin/bash
set -euo pipefail

docker login

if docker buildx inspect | grep -q "Endpoint:.*unix:///var/run/docker.sock" ; then
    echo "Builder exists already"
else
    echo "Builder does not exist - creating new one"
    docker buildx create --use default
fi

# Resolve a short git SHA (prefer CI env var)
GIT_SHA="${GIT_SHA:-${GITHUB_SHA:-}}"
if [ -z "$GIT_SHA" ]; then
  if git rev-parse --git-dir >/dev/null 2>&1; then
    GIT_SHA="$(git rev-parse --short=8 HEAD)"
    # Mark dirty state if desired
    if ! git diff --quiet --ignore-submodules --; then
      GIT_SHA="${GIT_SHA}-dirty"
    fi
  else
    GIT_SHA="local"
  fi
fi

IMAGE="jibby/home-dashboard"
TAG_SHA="${IMAGE}:${GIT_SHA}"
TAG_LATEST="${IMAGE}:latest"

echo "Building and pushing ${TAG_SHA} and ${TAG_LATEST}..."

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${TAG_SHA}" \
  -t "${TAG_LATEST}" \
  --label "org.opencontainers.image.revision=${GIT_SHA}" \
  --push .