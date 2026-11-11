import { expect, test } from "@playwright/test";
import { initialData, type BoardData } from "../src/lib/kanban";

test.beforeEach(async ({ page }) => {
  let board: BoardData = structuredClone(initialData);
  await page.route("**/api/users/user-1/board", async (route) => {
    if (route.request().method() === "PUT") {
      board = route.request().postDataJSON() as BoardData;
    }
    await route.fulfill({ json: board });
  });
});

const signIn = async (page: import("@playwright/test").Page) => {
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();
};

test("loads the kanban board", async ({ page }) => {
  const hydrationErrors: string[] = [];
  page.on("console", (message) => {
    if (
      message.type() === "error" &&
      message.text().includes("A tree hydrated")
    ) {
      hydrationErrors.push(message.text());
    }
  });

  await page.goto("/");
  await expect(page.getByLabel("Username")).toBeVisible();
  await signIn(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
  expect(hydrationErrors).toEqual([]);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
  await page.reload();
  await signIn(page);
  await expect(
    page.getByText("Playwright card", { exact: true })
  ).toBeVisible();
});

test("edits a card and persists its new details", async ({ page }) => {
  await page.goto("/");
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  await card.getByRole("button", { name: "Edit Align roadmap themes" }).click();
  await card.getByLabel("Title for Align roadmap themes").fill("Updated roadmap");
  await card
    .getByLabel("Details for Align roadmap themes")
    .fill("Updated project details.");
  await card.getByRole("button", { name: "Save" }).click();
  await expect(card.getByText("Updated roadmap")).toBeVisible();
  await page.reload();
  await signIn(page);
  await expect(page.getByTestId("card-card-1").getByText("Updated roadmap")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
  await page.reload();
  await signIn(page);
  await expect(
    page.getByTestId("column-col-review").getByTestId("card-card-1")
  ).toBeVisible();
});

test("rejects invalid credentials and clears sign-in on logout and refresh", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("invalid");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByText("Incorrect username or password.", { exact: true })
  ).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);

  await signIn(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByLabel("Username")).toBeVisible();

  await signIn(page);
  await page.reload();
  await expect(page.getByLabel("Username")).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
});
