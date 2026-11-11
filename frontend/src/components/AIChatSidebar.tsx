"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { askBoardAssistant, type ChatMessage } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type AIChatSidebarProps = {
  userId: string;
  board: BoardData;
  messages: ChatMessage[];
  onMessagesChange: (messages: ChatMessage[]) => void;
  onBoardUpdate: (board: BoardData) => void;
};

export const AIChatSidebar = ({
  userId,
  board,
  messages,
  onMessagesChange,
  onBoardUpdate,
}: AIChatSidebarProps) => {
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || isLoading) {
      return;
    }

    const nextUserMessage = { role: "user" as const, content: trimmed };
    const history = messages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    setDraft("");
    setError(null);
    setIsLoading(true);

    try {
      const response = await askBoardAssistant(userId, board, trimmed, history);
      onBoardUpdate(response.board);
      onMessagesChange([
        ...messages,
        nextUserMessage,
        {
          role: "assistant",
          content: response.assistant || response.message || "I updated the board.",
        },
      ]);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "The AI assistant could not respond."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside className="rounded-[28px] border border-[var(--stroke)] bg-white/90 p-4 shadow-[var(--shadow)] backdrop-blur">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[var(--gray-text)]">
            AI Assistant
          </p>
          <h2 className="mt-2 font-display text-xl font-semibold text-[var(--navy-dark)]">
            Board helper
          </h2>
        </div>
      </div>

      <div className="flex max-h-[560px] min-h-[280px] flex-col gap-3 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3">
        {messages.length === 0 ? (
          <p className="text-sm leading-6 text-[var(--gray-text)]">
            Ask the AI to add, edit, or move cards on the board.
          </p>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={message.role === "user" ? "ml-auto max-w-[85%] rounded-2xl bg-[var(--primary-blue)] px-3 py-2 text-sm text-white" : "mr-auto max-w-[85%] rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm leading-6 text-[var(--navy-dark)]"}
            >
              {message.content}
            </div>
          ))
        )}
        {isLoading && (
          <div className="mr-auto max-w-[85%] rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--gray-text)]">
            Thinking...
          </div>
        )}
        <div ref={endRef} />
      </div>

      {error && (
        <p role="alert" className="mt-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label className="sr-only" htmlFor="ai-message-input">
          Ask the AI assistant
        </label>
        <textarea
          id="ai-message-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={3}
          placeholder="Ask for a task, a change, or a move…"
          className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "Sending…" : "Send message"}
        </button>
      </form>
    </aside>
  );
};
