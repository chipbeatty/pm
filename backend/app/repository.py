from contextlib import closing
from pathlib import Path

from app.board import BoardData
from app.database import connect


def get_board(database_path: Path, user_id: str) -> BoardData | None:
    with closing(connect(database_path)) as connection:
        board = connection.execute(
            "SELECT id FROM boards WHERE user_id = ?", (user_id,)
        ).fetchone()
        if board is None:
            return None

        columns = connection.execute(
            """
            SELECT id, title FROM board_columns
            WHERE board_id = ? ORDER BY position
            """,
            (board["id"],),
        ).fetchall()
        cards = connection.execute(
            """
            SELECT id, column_id, title, details FROM cards
            WHERE board_id = ? ORDER BY column_id, position
            """,
            (board["id"],),
        ).fetchall()

    card_data = {
        row["id"]: {
            "id": row["id"],
            "title": row["title"],
            "details": row["details"],
        }
        for row in cards
    }
    card_ids_by_column = {row["id"]: [] for row in columns}
    for row in cards:
        card_ids_by_column[row["column_id"]].append(row["id"])

    return BoardData(
        id=board["id"],
        columns=[
            {
                "id": row["id"],
                "title": row["title"],
                "cardIds": card_ids_by_column[row["id"]],
            }
            for row in columns
        ],
        cards=card_data,
    )


def replace_board(
    database_path: Path, user_id: str, board_data: BoardData
) -> bool | None:
    with closing(connect(database_path)) as connection:
        board = connection.execute(
            "SELECT id FROM boards WHERE user_id = ?", (user_id,)
        ).fetchone()
        if board is None:
            return None
        if board["id"] != board_data.id:
            return False

        with connection:
            for position, column in enumerate(board_data.columns):
                connection.execute(
                    """
                    UPDATE board_columns SET title = ?, position = ?
                    WHERE board_id = ? AND id = ?
                    """,
                    (column.title, position, board["id"], column.id),
                )

            connection.execute("DELETE FROM cards WHERE board_id = ?", (board["id"],))
            connection.executemany(
                """
                INSERT INTO cards (id, board_id, column_id, title, details, position)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        card_id,
                        board["id"],
                        column.id,
                        board_data.cards[card_id].title,
                        board_data.cards[card_id].details,
                        position,
                    )
                    for column in board_data.columns
                    for position, card_id in enumerate(column.cardIds)
                ),
            )

    return True
