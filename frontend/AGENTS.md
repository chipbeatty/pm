# Frontend Guide

## Structure

- `src/app/` contains the Next.js App Router entry page, layout, global styles, and metadata.
- `src/components/` contains the Kanban board, columns, cards, and card-creation form.
- `src/lib/kanban.ts` defines the board/card/column types, initial demo data, card movement, and ID creation.
- `src/test/` contains Vitest setup.
- `tests/` contains Playwright browser tests.

The current app is a client-side Kanban demo. `KanbanBoard` owns in-memory board state; the current UI supports renaming columns, moving cards with `@dnd-kit`, and adding or removing cards. Keep board operations in sync with `src/lib/kanban.ts` and cover behavior with tests. The project plan includes card editing and backend persistence as later work; do not assume those are already implemented.

## Commands

Run these from `frontend/`:

- `npm run dev` starts the Next.js development server.
- `npm run lint` runs ESLint.
- `npm run test:unit` runs Vitest.
- `npm run test:e2e` runs Playwright.
- `npm run test:all` runs unit and end-to-end tests.
- `npm run build` builds the frontend.

Use the existing TypeScript strict settings and `@/` alias for imports from `src/`. Follow the existing Tailwind CSS utility-class styling and CSS variables in `src/app/globals.css`.
