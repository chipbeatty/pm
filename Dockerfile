FROM ghcr.io/astral-sh/uv:0.13.7 AS uv

FROM node:24-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

COPY --from=uv /uv /uvx /bin/

WORKDIR /app/backend

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --compile-bytecode

COPY backend/app ./app
COPY --from=frontend-builder /app/frontend/out ./static

ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
