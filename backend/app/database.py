import sqlite3
from contextlib import closing
from pathlib import Path

from app.board import COLUMN_IDS

DEFAULT_USER_ID = "user-1"
DEFAULT_BOARD_ID = "board-1"
DEFAULT_USERNAME = "user"

INITIAL_CARDS = (
    (
        "card-1",
        "col-backlog",
        "Align roadmap themes",
        "Draft quarterly themes with impact statements and metrics.",
        0,
    ),
    (
        "card-2",
        "col-backlog",
        "Gather customer signals",
        "Review support tags, sales notes, and churn feedback.",
        1,
    ),
    (
        "card-3",
        "col-discovery",
        "Prototype analytics view",
        "Sketch initial dashboard layout and key drill-downs.",
        0,
    ),
    (
        "card-4",
        "col-progress",
        "Refine status language",
        "Standardize column labels and tone across the board.",
        0,
    ),
    (
        "card-5",
        "col-progress",
        "Design card layout",
        "Add hierarchy and spacing for scanning dense lists.",
        1,
    ),
    (
        "card-6",
        "col-review",
        "QA micro-interactions",
        "Verify hover, focus, and loading states.",
        0,
    ),
    (
        "card-7",
        "col-done",
        "Ship marketing page",
        "Final copy approved and asset pack delivered.",
        0,
    ),
    (
        "card-8",
        "col-done",
        "Close onboarding sprint",
        "Document release notes and share internally.",
        1,
    ),
)

INITIAL_COLUMN_TITLES = (
    "Backlog",
    "Discovery",
    "In Progress",
    "Review",
    "Done",
)


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS boards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE
                    REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS board_columns (
                board_id TEXT NOT NULL
                    REFERENCES boards(id) ON DELETE CASCADE,
                id TEXT NOT NULL CHECK (id IN (
                    'col-backlog',
                    'col-discovery',
                    'col-progress',
                    'col-review',
                    'col-done'
                )),
                title TEXT NOT NULL,
                position INTEGER NOT NULL CHECK (position BETWEEN 0 AND 4),
                PRIMARY KEY (board_id, id),
                UNIQUE (board_id, position)
            );

            CREATE TABLE IF NOT EXISTS cards (
                id TEXT NOT NULL,
                board_id TEXT NOT NULL
                    REFERENCES boards(id) ON DELETE CASCADE,
                column_id TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT NOT NULL,
                position INTEGER NOT NULL CHECK (position >= 0),
                FOREIGN KEY (board_id, column_id)
                    REFERENCES board_columns(board_id, id) ON DELETE RESTRICT,
                PRIMARY KEY (board_id, id),
                UNIQUE (board_id, column_id, position)
            );
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
            (DEFAULT_USER_ID, DEFAULT_USERNAME),
        )
        board_created = connection.execute(
            "INSERT OR IGNORE INTO boards (id, user_id) VALUES (?, ?)",
            (DEFAULT_BOARD_ID, DEFAULT_USER_ID),
        ).rowcount == 1
        if board_created:
            for position, (column_id, title) in enumerate(
                zip(COLUMN_IDS, INITIAL_COLUMN_TITLES, strict=True)
            ):
                connection.execute(
                    """
                    INSERT INTO board_columns (board_id, id, title, position)
                    VALUES (?, ?, ?, ?)
                    """,
                    (DEFAULT_BOARD_ID, column_id, title, position),
                )
            connection.executemany(
                """
                INSERT INTO cards
                    (id, board_id, column_id, title, details, position)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (card_id, DEFAULT_BOARD_ID, column_id, title, details, position)
                    for card_id, column_id, title, details, position in INITIAL_CARDS
                ),
            )
