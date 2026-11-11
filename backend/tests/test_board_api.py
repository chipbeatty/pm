import sqlite3
from contextlib import closing
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import connect
from app.main import create_app

USER_ID = "user-1"
BOARD_URL = f"/api/users/{USER_ID}/board"


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "data" / "kanban.sqlite3"


@pytest.fixture
def client(database_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(database_path)) as test_client:
        yield test_client


def test_initializes_and_seeds_database(client: TestClient, database_path: Path) -> None:
    response = client.get(BOARD_URL)

    assert database_path.exists()
    assert response.status_code == 200
    board = response.json()
    assert board["id"] == "board-1"
    assert [column["id"] for column in board["columns"]] == [
        "col-backlog",
        "col-discovery",
        "col-progress",
        "col-review",
        "col-done",
    ]
    assert len(board["cards"]) == 8
    assert board["columns"][0]["cardIds"] == ["card-1", "card-2"]


def test_replaces_board_for_rename_card_edits_and_card_order(
    client: TestClient,
) -> None:
    board = client.get(BOARD_URL).json()
    board["columns"][0]["title"] = "Ideas"
    board["columns"][0]["cardIds"] = ["card-2"]
    board["columns"][1]["cardIds"] = []
    board["columns"][3]["cardIds"] = ["card-1", "card-6"]
    board["columns"][4]["cardIds"].append("card-9")
    board["cards"]["card-2"]["title"] = "Review customer signals"
    board["cards"]["card-2"]["details"] = "Review support and sales feedback."
    board["cards"].pop("card-3")
    board["cards"]["card-9"] = {
        "id": "card-9",
        "title": "Plan release",
        "details": "Prepare the release checklist.",
    }

    response = client.put(BOARD_URL, json=board)

    assert response.status_code == 200
    assert response.json() == board
    assert client.get(BOARD_URL).json() == board


def test_rejects_invalid_card_membership_without_changing_board(
    client: TestClient,
) -> None:
    original = client.get(BOARD_URL).json()
    invalid_board = {**original, "columns": [*original["columns"]]}
    invalid_board["columns"][0] = {
        **invalid_board["columns"][0],
        "cardIds": ["card-1", "card-1", "card-2"],
    }

    response = client.put(BOARD_URL, json=invalid_board)

    assert response.status_code == 422
    assert client.get(BOARD_URL).json() == original


def test_rejects_board_id_mismatch(client: TestClient) -> None:
    board = client.get(BOARD_URL).json()
    board["id"] = "another-board"

    response = client.put(BOARD_URL, json=board)

    assert response.status_code == 409


def test_unknown_user_has_no_board(client: TestClient) -> None:
    response = client.get("/api/users/unknown-user/board")

    assert response.status_code == 404


def test_user_board_persists_when_app_is_recreated(database_path: Path) -> None:
    with TestClient(create_app(database_path)) as first_client:
        board = first_client.get(BOARD_URL).json()
        board["columns"][0]["title"] = "Persistent title"
        board["columns"][1]["cardIds"].remove("card-3")
        board["cards"].pop("card-3")
        assert first_client.put(BOARD_URL, json=board).status_code == 200

    with TestClient(create_app(database_path)) as restarted_client:
        response = restarted_client.get(BOARD_URL)

    assert response.status_code == 200
    assert response.json()["columns"][0]["title"] == "Persistent title"
    assert "card-3" not in response.json()["cards"]


def test_board_reads_are_scoped_to_user_id(
    client: TestClient, database_path: Path
) -> None:
    with connect(database_path) as connection:
        connection.execute(
            "INSERT INTO users (id, username) VALUES ('user-2', 'second')"
        )
        connection.execute(
            "INSERT INTO boards (id, user_id) VALUES ('board-2', 'user-2')"
        )
        connection.executemany(
            """
            INSERT INTO board_columns (board_id, id, title, position)
            VALUES ('board-2', ?, ?, ?)
            """,
            [
                ("col-backlog", "Other backlog", 0),
                ("col-discovery", "Other discovery", 1),
                ("col-progress", "Other progress", 2),
                ("col-review", "Other review", 3),
                ("col-done", "Other done", 4),
            ],
        )

    response = client.get("/api/users/user-2/board")

    assert response.status_code == 200
    assert response.json()["id"] == "board-2"
    assert response.json()["columns"][0]["title"] == "Other backlog"
    assert response.json()["cards"] == {}

    second_board = response.json()
    second_board["columns"][0]["cardIds"] = ["card-1"]
    second_board["cards"]["card-1"] = {
        "id": "card-1",
        "title": "Second user's card",
        "details": "Card IDs are scoped to a board.",
    }
    update = client.put("/api/users/user-2/board", json=second_board)

    assert update.status_code == 200
    assert client.get(BOARD_URL).json()["cards"]["card-1"]["title"] == (
        "Align roadmap themes"
    )


def test_database_enables_foreign_key_constraints(database_path: Path) -> None:
    create_app(database_path)
    with closing(connect(database_path)) as connection, connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO boards (id, user_id) VALUES ('invalid', 'missing-user')"
            )
