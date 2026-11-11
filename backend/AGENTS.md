# Backend Guide

## Structure

- `app/main.py` creates the FastAPI application and defines API routes, then serves the static site from `static/`.
- `app/board.py` defines and validates the board API models.
- `app/database.py` creates the SQLite tables and seeds the initial user and board.
- `app/repository.py` reads and atomically replaces a user's board.
- `static/` contains the temporary scaffold page. Later, the production Next.js static export will replace this content.
- `tests/` contains pytest tests for API, board validation, persistence, and static-serving behavior.
- `pyproject.toml` and `uv.lock` define the backend project and its reproducible dependencies; manage dependencies with `uv`.

The default development database is `backend/data/kanban.sqlite3`; set `KANBAN_DB_PATH` to choose another path. Docker stores it at `/data/kanban.sqlite3` in the Compose named volume. The board API replaces a complete validated board atomically, so keep database writes inside transactions.

Run backend tests from the repository root with `uv run --directory backend pytest`. The local Docker setup is defined by the root `Dockerfile` and `compose.yaml`; use the scripts in `scripts/` to start and stop it.
