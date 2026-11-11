#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

docker compose up --build --wait --wait-timeout 60
printf 'Project Management MVP is running at http://localhost:%s\n' "${PORT:-8000}"
