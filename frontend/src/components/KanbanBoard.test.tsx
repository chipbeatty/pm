import { afterEach, beforeEach, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

beforeEach(() => {
  let board: BoardData = structuredClone(initialData);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === "PUT") {
        board = JSON.parse(init.body as string) as BoardData;
      }
      return new Response(JSON.stringify(board), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    })
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const signIn = async () => {
  await userEvent.type(screen.getByLabelText("Username"), "user");
  await userEvent.type(screen.getByLabelText("Password"), "password");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
};

describe("KanbanBoard", () => {
  it("requires sign-in and renders five columns after valid credentials", async () => {
    render(<KanbanBoard />);
    expect(screen.queryByTestId(/column-/i)).not.toBeInTheDocument();

    await signIn();

    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    await signIn();
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    await userEvent.tab();
    await waitFor(() => {
      const putRequest = vi
        .mocked(fetch)
        .mock.calls.find(([, init]) => init?.method === "PUT");
      expect(putRequest).toBeDefined();
      expect(
        JSON.parse(putRequest?.[1]?.body as string).columns[0].title
      ).toBe("New Name");
    });
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    await signIn();
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("edits a card and persists the complete board", async () => {
    render(<KanbanBoard />);
    await signIn();
    const column = getFirstColumn();
    await userEvent.click(
      within(column).getByRole("button", { name: "Edit Align roadmap themes" })
    );
    const title = within(column).getByLabelText(
      "Title for Align roadmap themes"
    );
    await userEvent.clear(title);
    await userEvent.type(title, "Updated roadmap");
    await userEvent.click(within(column).getByRole("button", { name: "Save" }));

    expect(within(column).getByText("Updated roadmap")).toBeInTheDocument();
    const putRequest = vi
      .mocked(fetch)
      .mock.calls.find(([, init]) => init?.method === "PUT");
    expect(putRequest).toBeDefined();
    expect(JSON.parse(putRequest?.[1]?.body as string).cards["card-1"].title).toBe(
      "Updated roadmap"
    );
  });

  it("shows a visible error and keeps the board unchanged when saving fails", async () => {
    render(<KanbanBoard />);
    await signIn();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: "Database unavailable." }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const column = getFirstColumn();
    await userEvent.click(
      within(column).getByRole("button", { name: /add a card/i })
    );
    await userEvent.type(
      within(column).getByPlaceholderText("Card title"),
      "Unsaved card"
    );
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Board changes could not be saved: Database unavailable."
    );
    expect(within(column).queryByText("Unsaved card")).not.toBeInTheDocument();
  });

  it("rejects invalid credentials and returns to sign-in after logout", async () => {
    render(<KanbanBoard />);
    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Incorrect username or password."
    );
    expect(screen.queryByTestId(/column-/i)).not.toBeInTheDocument();

    await userEvent.clear(screen.getByLabelText("Password"));
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await userEvent.click(screen.getByRole("button", { name: "Sign out" }));

    expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
    expect(screen.queryByTestId(/column-/i)).not.toBeInTheDocument();
  });
});
