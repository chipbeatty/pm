# Database Proposal

This four-table model, seed data, and named-volume persistence approach were approved before implementation. The JSON representation is described in [board.schema.json](./board.schema.json) and follows the current frontend board shape.

## SQLite tables

Use four normalized tables:

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE boards (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE board_columns (
    board_id TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
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

CREATE TABLE cards (
    id TEXT NOT NULL,
    board_id TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    column_id TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 0),
    FOREIGN KEY (board_id, column_id)
        REFERENCES board_columns(board_id, id) ON DELETE RESTRICT,
    PRIMARY KEY (board_id, id),
    UNIQUE (board_id, column_id, position)
);
```

The unique `boards.user_id` constraint enforces one board per user. The composite column key allows every board to use the same five stable column IDs. A column's ID identifies its fixed stage and its title is the user-editable label. Column `position` preserves the fixed order. Cards point to a column and use `position` for ordering within it; moving a card changes its column and position. Card IDs are unique within a board, allowing different users' boards to use the same local card IDs. Card updates and position changes should run in a database transaction, with positions reindexed atomically to satisfy the unique ordering constraint.

SQLite foreign-key enforcement must be enabled on every connection. The fixed set of columns is seeded in canonical order when a board is created. The application must create exactly one row for each of the five IDs and must not expose column creation or deletion. The DDL restricts the allowed IDs and positions but cannot alone guarantee that all five rows exist exactly once.

## JSON representation

The API representation keeps columns as an ordered array and cards as an object keyed by card ID, matching `BoardData` in the frontend. Each column's `cardIds` array determines the order of its cards. The schema requires five columns and restricts their IDs to the fixed set. Application validation must additionally ensure each column ID appears exactly once, every listed card exists, every card is listed in exactly one column, and each card object's `id` matches its object key.

Usernames are unique, and each user has one board in this representation. Authentication credentials are intentionally not stored in this database proposal: MVP sign-in is the client-only demo gate (`user` / `password`) and does not authenticate backend requests.

## Board API

- `GET /api/users/{user_id}/board` returns that user's board.
- `PUT /api/users/{user_id}/board` replaces the complete board atomically. The payload includes the board `id`, ordered columns, and cards. Renames, card creation/edit/deletion, movement, and reordering are represented in this replacement.
- Unknown user IDs return `404`; a payload whose board ID does not match that user's board returns `409`; invalid board structure returns `422`.

The user ID in the URL selects a board; it is not an authentication credential. This is consistent with the explicitly client-only demo login and is intended for local MVP use, not exposure to an untrusted network.

## Initialization, seed data, and local persistence

- On first startup, create the tables if absent.
- Create the demo user (`user-1`, username `user`), one board, the five fixed columns, and the current sample cards when the initial board is first created. Do not reseed cards on subsequent starts, because a deleted card must stay deleted.
- Store the SQLite file at `/data/kanban.sqlite3` inside the container.
- Mount a named Docker volume at `/data` so data survives container restarts and image rebuilds. Removing the Compose volume (for example with `docker compose down -v`) deletes the local database.
- Keep database files and credentials out of Git; do not put authentication or OpenRouter secrets in this schema.
