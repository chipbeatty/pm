import type { BoardData } from "@/lib/kanban";

const API_ORIGIN =
  process.env.NODE_ENV === "development" ? "http://localhost:8000" : "";

const boardUrl = (userId: string) =>
  `${API_ORIGIN}/api/users/${encodeURIComponent(userId)}/board`;

const readBoardResponse = async (response: Response): Promise<BoardData> => {
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.detail ?? `Board request failed (${response.status}).`);
  }
  return result;
};

export const getBoard = async (userId: string): Promise<BoardData> =>
  readBoardResponse(await fetch(boardUrl(userId)));

export const saveBoard = async (
  userId: string,
  board: BoardData
): Promise<BoardData> =>
  readBoardResponse(
    await fetch(boardUrl(userId), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(board),
    })
  );
