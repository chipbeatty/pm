from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ColumnId = Literal[
    "col-backlog",
    "col-discovery",
    "col-progress",
    "col-review",
    "col-done",
]

COLUMN_IDS: tuple[ColumnId, ...] = (
    "col-backlog",
    "col-discovery",
    "col-progress",
    "col-review",
    "col-done",
)


class BoardCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^card-[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1)
    details: str


class BoardColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: ColumnId
    title: str = Field(min_length=1)
    cardIds: list[str] = Field(default_factory=list)


class BoardData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    columns: list[BoardColumn] = Field(min_length=5, max_length=5)
    cards: dict[str, BoardCard]

    @model_validator(mode="after")
    def validate_board_references(self) -> "BoardData":
        column_ids = [column.id for column in self.columns]
        if column_ids != list(COLUMN_IDS):
            raise ValueError("Board must contain the five fixed columns in order.")

        memberships = [
            card_id for column in self.columns for card_id in column.cardIds
        ]
        if len(memberships) != len(set(memberships)):
            raise ValueError("A card can belong to only one column.")
        if set(memberships) != set(self.cards):
            raise ValueError("Every card must appear in exactly one column.")
        if any(card_id != card.id for card_id, card in self.cards.items()):
            raise ValueError("Each card ID must match its key in the cards object.")

        return self
