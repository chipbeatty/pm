from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Project Management API")


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI!"}


static_directory = Path(__file__).parent.parent / "static"
app.mount("/", StaticFiles(directory=static_directory, html=True), name="frontend")
