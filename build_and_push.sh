#!/bin/bash
set -euo pipefail

DRY_RUN=false

# Simple CLI parsing for --dry-run / -n
for arg in "$@"; do
  case "$arg" in
    --dry-run|-n)
      DRY_RUN=true
      ;;
    --help|-h)
      echo "Usage: $0 [--dry-run|-n]"
      exit 0
      ;;
  esac
done

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

# If HEAD is exactly at a tag, prefer that tag as a release tag
GIT_TAG=""
if git rev-parse --git-dir >/dev/null 2>&1; then
  if git describe --tags --exact-match >/dev/null 2>&1; then
    GIT_TAG=$(git describe --tags --exact-match)
  fi
fi

if [ -n "$GIT_TAG" ]; then
  TAG_RELEASE="${IMAGE}:${GIT_TAG}"
else
  TAG_RELEASE=""
fi

# Prepare a human-readable list of tags that will be pushed
if [ -n "${TAG_RELEASE}" ]; then
  DISPLAY_TAGS="${TAG_SHA}, ${TAG_RELEASE}, ${TAG_LATEST}"
else
  DISPLAY_TAGS="${TAG_SHA}, ${TAG_LATEST}"
fi

if [ "${DRY_RUN}" = true ]; then
  echo "Dry run: building ${DISPLAY_TAGS} (push skipped)"
else
  echo "Building and pushing ${DISPLAY_TAGS}..."
fi

# Build an array of -t tags to pass to docker. This avoids complex inline quoting
# and prevents mismatched quotes when TAG_RELEASE is empty.
DOCKER_TAGS=("-t" "${TAG_SHA}")
if [ -n "${TAG_RELEASE}" ]; then
  DOCKER_TAGS+=("-t" "${TAG_RELEASE}")
fi
DOCKER_TAGS+=("-t" "${TAG_LATEST}")

# Ensure we're logged in (will use cached login if already done)
docker login

# Run the build; push only when not a dry run
if [ "${DRY_RUN}" = true ]; then
  docker buildx build \
    --platform linux/amd64,linux/arm64 \
    "${DOCKER_TAGS[@]}" \
    --label "org.opencontainers.image.revision=${GIT_SHA}" \
    .
  echo "Dry run complete. Image(s) were built locally but not pushed."
else
  docker buildx build \
    --platform linux/amd64,linux/arm64 \
    "${DOCKER_TAGS[@]}" \
    --label "org.opencontainers.image.revision=${GIT_SHA}" \
    --push .
fi