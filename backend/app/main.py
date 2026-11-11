import os
from typing import Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.ai_service import AnthropicError, check_connectivity, generate_board_response
from app.board import BoardData
from app.database import initialize_database
from app.repository import get_board, replace_board


class AIBoardRequest(BaseModel):
    user_id: str
    board: BoardData
    message: str
    history: list[dict[str, str]] | None = None


def create_app(database_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
    )
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

    @app.get("/api/ai/health")
    def ai_health() -> dict[str, str]:
        try:
            result = check_connectivity()
            return {
                "status": "ok",
                "model": result["model"],
                "answer": result["answer"],
            }
        except AnthropicError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/api/ai/board")
    def ai_board(request: AIBoardRequest) -> dict[str, Any]:
        try:
            result = generate_board_response(request.board, request.message, request.history)
            if request.user_id:
                saved = replace_board(resolved_database_path, request.user_id, result["board"])
                if saved is None:
                    raise HTTPException(status_code=404, detail="User board not found.")
                if saved is False:
                    raise HTTPException(
                        status_code=409,
                        detail="Board ID does not match the user's board.",
                    )
            return result
        except AnthropicError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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
