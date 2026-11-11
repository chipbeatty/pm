# Frontend Guide

## Structure

- `src/app/` contains the Next.js App Router entry page, layout, global styles, and metadata.
- `src/components/` contains the Kanban board, columns, cards, and card-creation form.
- `src/lib/kanban.ts` defines the board/card/column types, initial demo data, card movement, and ID creation.
- `src/lib/api.ts` loads and saves a user's board through the FastAPI board API.
- `src/test/` contains Vitest setup.
- `tests/` contains Playwright browser tests.

`KanbanBoard` loads the persisted board after the client-side demo sign-in and saves manual board changes through `src/lib/api.ts`. The UI supports renaming fixed columns, creating, editing, and deleting cards, and moving cards with `@dnd-kit`. The sign-in gate is not backend authentication. Keep board operations in sync with the API's complete-board representation and cover behavior with tests.

## Commands

Run these from `frontend/`:

- `npm run dev` starts the Next.js development server.
- `npm run lint` runs ESLint.
- `npm run test:unit` runs Vitest.
- `npm run test:e2e` runs Playwright.
- `npm run test:all` runs unit and end-to-end tests.
- `npm run build` builds the frontend.

Use the existing TypeScript strict settings and `@/` alias for imports from `src/`. Follow the existing Tailwind CSS utility-class styling and CSS variables in `src/app/globals.css`.
