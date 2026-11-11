# Backend Guide

## Structure

- `app/main.py` defines the FastAPI application and API routes, then serves the static site from `static/`.
- `static/` contains the temporary scaffold page. Later, the production Next.js static export will replace this content.
- `tests/` contains pytest tests for API and static-serving behavior.
- `pyproject.toml` and `uv.lock` define the backend project and its reproducible dependencies; manage dependencies with `uv`.

Run backend tests from the repository root with `uv run --directory backend pytest`. The local Docker setup is defined by the root `Dockerfile` and `compose.yaml`; use the scripts in `scripts/` to start and stop it.
