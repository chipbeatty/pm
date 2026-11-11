# Project Plan

## Project decisions

- Frontend: Next.js, statically exported and served by the FastAPI application.
- Backend: Python with FastAPI; use `uv` for dependency management.
- Runtime: one Docker container for local use, with start and stop scripts for macOS, Windows, and Linux.
- Data: SQLite, initialized when the database does not exist. The schema supports multiple users, with one board per user.
- MVP sign-in: hardcoded username `user` and password `password`. Sign-in state is client-side and resets when the page is refreshed; it is a demo gate, not server-side authentication.
- AI: OpenRouter, using `openai/gpt-oss-120b`; keep the API key in the root `.env` and never expose it to the frontend.
- Board: a fixed set of columns whose names can be changed. Cards can be created, edited, deleted, reordered, and moved between columns.
- AI chat can create, edit, and move cards when requested.

## Part 1: Plan and frontend guidance

- [x] Review the existing project plan and project instructions.
- [x] Inspect the existing frontend and its test setup.
- [x] Record the frontend structure and working commands in `frontend/AGENTS.md`.
- [x] Expand this plan with implementation steps, tests, and success criteria for each part.
- [x] Have the user review and approve this plan before starting Part 2.

**Tests:** Documentation and instruction-file review; no code tests are needed.

**Success criteria:** Each part has actionable steps, relevant tests, and observable completion criteria. The user has approved this plan before implementation begins.

## Part 2: Docker and backend scaffold

- [x] Create the FastAPI backend entry point and a minimal example API route.
- [x] Add Docker configuration to install backend dependencies with `uv` and package the application.
- [x] Add start and stop scripts for macOS, Windows, and Linux that use the same container setup.
- [x] Serve a minimal example page at `/` and verify it can call the example API.
- [x] Document the minimum commands and required environment setup.

**Tests:** Backend unit test for the example API; build the Docker image; start the container and verify the page and API respond; check script syntax or invocation for each supported platform where runners are available.

**Success criteria:** A new developer can start the local container using the platform script, load `/`, call the example API, and stop the container. No API key is required for this part.

## Part 3: Serve the existing frontend

- [x] Configure the Next.js app for a static export compatible with FastAPI static-file serving.
- [x] Build and serve the frontend at `/`, retaining the current Kanban demo and styling.
- [x] Keep frontend assets and client-side routes working from the container.
- [x] Update the Docker build to produce and include the static frontend output.
- [x] Preserve the existing frontend unit and end-to-end tests, adapting only what the serving setup requires.

**Tests:** Frontend lint, unit tests, and Playwright tests; Docker build; container smoke test for `/`, static assets, and the example API route.

**Success criteria:** The container serves the existing interactive Kanban at `/`; the frontend and API are available from the same origin; the production image does not need a separate Next.js server.

## Part 4: Demo sign-in

- [x] Add a login screen that accepts only the MVP credentials `user` and `password`.
- [x] Gate the board behind client-side sign-in state.
- [x] Add a sign-out action that returns to the login screen.
- [x] Keep the behavior explicitly demo-only: reloading clears sign-in state; do not imply that this authenticates API requests.

**Tests:** Unit tests for valid and invalid credentials and sign-out; Playwright tests for login, board gating, logout, and sign-in reset after refresh.

**Success criteria:** The board is not shown before a successful login; the stated demo credentials work; invalid credentials do not unlock the board; sign-out and refresh return to the login screen.

## Part 5: Database model proposal

- [ ] Define a JSON schema describing users, each user's single board, the fixed board columns, and cards.
- [ ] Document SQLite table structure, keys, relationships, and how fixed columns and renamed titles are represented.
- [ ] Document database initialization and persistence expectations for local Docker use.
- [ ] Review the proposal with the user and obtain sign-off before implementing database access.

**Tests:** Validate the JSON schema and any example data against it; review that the proposed relationships enforce one board per user and preserve card ordering and column membership.

**Success criteria:** The schema and database approach are documented under `docs/`, account for all current board operations, and are approved before Part 6.

## Part 6: Persistent backend board API

- [ ] Initialize the SQLite database and create its schema when absent.
- [ ] Add API operations to read and update the signed-in demo user's board, including column renames and card create, edit, delete, and movement.
- [ ] Validate request data and return clear HTTP errors for invalid or missing resources.
- [ ] Keep database access and API behavior covered by focused backend tests.

**Tests:** Backend tests for first-run database creation, board reads and updates, each supported card/column operation, invalid input, and persistence across application restarts.

**Success criteria:** A newly started app has an initialized database and a usable board for the demo user; successful updates persist and are returned by subsequent reads; one user's data cannot be mistaken for another's.

## Part 7: Connect frontend to backend

- [ ] Replace in-memory-only board changes with calls to the same-origin backend API.
- [ ] Load the user's board after client-side demo sign-in and render persisted state.
- [ ] Wire manual board actions to persist column renames and card create, edit, delete, and movement.
- [ ] Show failures instead of silently presenting an unsaved change as successful.
- [ ] Keep the single-origin Docker deployment and static frontend constraints intact.

**Tests:** Frontend unit tests for API interactions and error states; Playwright integration tests for board load and each manual update; backend regression tests.

**Success criteria:** Manual board changes survive reloads; the displayed board reflects backend data; failed requests are visible and do not falsely appear saved.

## Part 8: OpenRouter connectivity

- [ ] Read the OpenRouter API key from the server-side root `.env` configuration.
- [ ] Add a minimal backend AI service using `openai/gpt-oss-120b`.
- [ ] Add a small connectivity check that asks the model a simple `2+2` question.
- [ ] Keep the key and provider request on the backend; do not include secrets in frontend assets, responses, logs, or committed files.

**Tests:** Unit tests with a mocked provider for request construction and error handling; a manual live `2+2` check when a valid key and network access are available.

**Success criteria:** With a valid key, the backend can make a live OpenRouter request and receive the expected answer; missing keys and provider errors are reported clearly; the secret remains server-side.

## Part 9: Structured AI board operations

- [ ] Send the current board, the user's question, and conversation history to the backend AI service.
- [ ] Define and validate a structured response containing assistant text and an optional set of board changes.
- [ ] Apply permitted create, edit, and move operations through the same persistence rules as manual API updates.
- [ ] Return the assistant response and resulting board state to the frontend.
- [ ] Handle malformed or rejected model output without applying partial or invalid board changes.

**Tests:** Unit tests using mocked model responses for text-only answers and each board operation; tests for invalid structured output, provider errors, and board-state validation; verify persisted results through the board API.

**Success criteria:** The backend supplies board context and conversation history, validates structured output, and persists valid requested changes while leaving the board unchanged for invalid output.

## Part 10: AI chat sidebar

- [ ] Add a sidebar chat interface to the board.
- [ ] Send user messages and conversation history to the backend AI endpoint.
- [ ] Display assistant replies and handle loading and request-error states.
- [ ] Refresh or replace board state when the backend reports an AI-applied update.
- [ ] Keep the sidebar usable alongside the board at supported viewport sizes.

**Tests:** Frontend unit tests for chat rendering and backend interaction; Playwright tests for sending a message, displaying a response, reflecting an AI board update, and showing errors; run the full backend and frontend suites.

**Success criteria:** The user can chat from the board, see the assistant response, and see valid AI board changes reflected without reloading. The full test suites pass, and the Dockerized app works end to end.
