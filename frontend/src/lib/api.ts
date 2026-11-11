import type { BoardData } from "@/lib/kanban";

const API_ORIGIN =
  process.env.NODE_ENV === "development" ? "http://localhost:8000" : "";

const boardUrl = (userId: string) =>
  `${API_ORIGIN}/api/users/${encodeURIComponent(userId)}/board`;

const aiUrl = `${API_ORIGIN}/api/ai/board`;

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AIRequestResult = {
  assistant: string;
  message: string;
  board: BoardData;
  changes: Array<Record<string, unknown>>;
};

const readJsonResponse = async <T>(response: Response): Promise<T> => {
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.detail ?? `Request failed (${response.status}).`);
  }
  return result as T;
};

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

export const askBoardAssistant = async (
  userId: string,
  board: BoardData,
  message: string,
  history: Array<{ role: "user" | "assistant"; content: string }>
): Promise<AIRequestResult> =>
  readJsonResponse<AIRequestResult>(
    await fetch(aiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        board,
        message,
        history,
      }),
    })
  );
