# Project Management MVP

## Run locally

Requires Docker with Compose.

- macOS or Linux: `./scripts/start.sh` and `./scripts/stop.sh`
- Windows: run `scripts\start.bat` and `scripts\stop.bat`

Open [http://localhost:8000](http://localhost:8000). Set `PORT` to use a different local port.

## Backend tests

Run from the repository root:

```sh
uv run --directory backend pytest
```
