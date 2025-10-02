#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") [--major] [--push]

Create a new git tag. By default increments the minor version (e.g. 0.1 -> 0.2).
Use --major to increment the major version (e.g. 0.1 -> 1.0).
The script prints the proposed tag and asks for confirmation before creating it.

Options:
  --major    Increment the major version (minor resets to 0)
  --push     Push the created tag to 'origin' after creation
  -h, --help Show this help and exit
EOF
}

INCREMENT_MAJOR=false
PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --major) INCREMENT_MAJOR=true; shift ;;
    --push) PUSH=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

# ensure we're in a git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository." >&2
  exit 1
fi

# find latest semver-like tag (v?MAJOR.MINOR)
latest_tag=$(git tag --list | grep -E '^v?[0-9]+\.[0-9]+$' | sort -V | tail -n1 || true)

if [[ -z "$latest_tag" ]]; then
  # No tags yet
  if [[ "$INCREMENT_MAJOR" = true ]]; then
    new_major=1
    new_minor=0
  else
    new_major=0
    new_minor=1
  fi
  prefix=""
else
  # keep prefix if present (v)
  if [[ "$latest_tag" =~ ^v ]]; then
    prefix="v"
    numeric=${latest_tag#v}
  else
    prefix=""
    numeric=$latest_tag
  fi
  IFS='.' read -r major minor <<<"$numeric"
  major=${major:-0}
  minor=${minor:-0}

  if [[ "$INCREMENT_MAJOR" = true ]]; then
    new_major=$((major + 1))
    new_minor=0
  else
    new_major=$major
    new_minor=$((minor + 1))
  fi
fi

proposed_tag="${prefix}${new_major}.${new_minor}"

echo "Latest tag: ${latest_tag:-<none>}"
echo "Proposed tag: ${proposed_tag}"

read -r -p "Create tag ${proposed_tag}? [y/N] " confirm
case "$confirm" in
  [yY]|[yY][eE][sS])
    git tag -a "$proposed_tag" -m "Release $proposed_tag"
    echo "Created tag $proposed_tag"
    if [[ "$PUSH" = true ]]; then
      git push origin "$proposed_tag"
      echo "Pushed tag $proposed_tag to origin"
    else
      echo "To push the tag: git push origin $proposed_tag"
    fi
    ;;
  *)
    echo "Aborted. No tag created."
    exit 0
    ;;
esac
