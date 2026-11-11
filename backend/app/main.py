import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.board import BoardData
from app.database import initialize_database
from app.repository import get_board, replace_board


def create_app(database_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management API")
    resolved_database_path = database_path or Path(
        os.environ.get(
            "KANBAN_DB_PATH",
            str(Path(__file__).parent.parent / "data" / "kanban.sqlite3"),
        )
    )
    initialize_database(resolved_database_path)

    @app.get("/api/hello")
    def hello() -> dict[str, str]:
        return {"message": "Hello from FastAPI!"}

    @app.get("/api/users/{user_id}/board", response_model=BoardData)
    def read_board(user_id: str) -> BoardData:
        board = get_board(resolved_database_path, user_id)
        if board is None:
            raise HTTPException(status_code=404, detail="User board not found.")
        return board

    @app.put("/api/users/{user_id}/board", response_model=BoardData)
    def update_board(user_id: str, board_data: BoardData) -> BoardData:
        result = replace_board(resolved_database_path, user_id, board_data)
        if result is True:
            updated_board = get_board(resolved_database_path, user_id)
            if updated_board is None:
                raise HTTPException(status_code=404, detail="User board not found.")
            return updated_board
        if result is False:
            raise HTTPException(
                status_code=409,
                detail="Board ID does not match the user's board.",
            )
        raise HTTPException(status_code=404, detail="User board not found.")

    static_directory = Path(__file__).parent.parent / "static"
    app.mount("/", StaticFiles(directory=static_directory, html=True), name="frontend")
    return app


app = create_app()
