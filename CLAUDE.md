@AGENTS.md

## Current AI integration status

Anthropic board chat is implemented and was verified with a live browser request. After backend source changes, rebuild the Docker image with `docker compose up --build -d` so the container does not keep serving stale code. The local development container was stopped after verification; use `docker compose stop` to stop it.
