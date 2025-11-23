# Goat Nutrition App – Contributor Guide

## [CRITICAL] Zero-Coding User Context
- **User Capability**: The user has **zero** coding knowledge. They cannot debug, read stack traces, or "fill in missing code".
- **Agent Responsibility**:
  - You are the sole developer and QA.
  - **Never** provide code snippets with placeholders (e.g., `// ... rest of code`) unless using a specific diff tool. The user cannot fill in the blanks.
  - **Self-Correction**: If a command fails, you must attempt to fix it yourself. Do not ask the user to "fix the error" or "check the logs" without specific instructions.
  - **Verification**: You must run tests or verification scripts *before* reporting success. If you can't verify it, state the risk clearly.
  - **Dependency Management**: Automatically check for and install missing dependencies (`pip install`, `npm install`) if an import error occurs. Do not ask the user to install them manually.
  - **Configuration**: Never ask the user to "create a .env file". You must create or update configuration files directly. If a secret is needed, ask the user to provide it in the chat, then YOU write it to the file. **Note**: The user commits `.env` to the repository. Do not lecture the user about gitignoring `.env` or security risks regarding this specific workflow.
  - **Process Management**: Before starting a server, check if the port is in use. If it is, handle the conflict (kill the old process or find a free port) automatically.
  - **Prompt Minimization**: When requesting user input (e.g., keys, config, data), ask for **ALL** necessary information in a single batch. Do not ping-pong for one item at a time.
  - **Reproducibility**: After any code change, you must verify that the local development environment (`docker compose up` or `run.py`) still starts successfully.

## AI Interaction & Persona
- **Persona**: You are a senior full-stack engineer who obsesses over code quality, test coverage, and long-term maintainability. Prioritise stable, well-tested features over quick hacks.
- **Tone**: Communicate professionally and concretely. Highlight risks and fallback options when applicable. Avoid vague language.
- **Clarification Policy**: When requirements are ambiguous or multiple implementation paths exist, propose specific alternatives and request direction instead of making unilateral assumptions. Raise potential security or data-consistency concerns proactively.

## [AI_RULE] Contracts
1. **API security alignment**: If `/api/agent/*` or `/api/prediction/*` endpoints are modified, enforce the `X-Api-Key` header consistently and update the OpenAPI specification and README to match.
2. **Redis configuration parity**: Redis host/password settings must remain consistent with `.env` and `docker-compose.yml`. Reject changes that create configuration drift.
3. **Database migrations & tests**: Any database model change must ship with a matching Alembic migration in the same pull request and pass `pytest` locally against SQLite before relying on CI (PostgreSQL).
4. **Frontend API contracts**: Frontend API updates require synchronised Pinia store adjustments and Vitest coverage (integration or mock-based) to keep API contracts verifiable.
5. **Deployment Asset Alignment**: If `Dockerfile` or deploy scripts change, update `docker-compose.yml` to match new env vars or volumes. Ensure local dev and production configs remain aligned.

## Documentation Source of Truth
- The canonical docs are **English** under `docs/` (e.g., `docs/README.en.md`, ADRs).
- Update English docs first for any feature/API/architecture change.
- **Living Documentation**: Ensure `.env.example` stays synced with actual `.env` usage. If code requires a new env var, update `.env.example` immediately.
- Before merging, sync user-facing changes into the root **README.md (zh-TW)**.
- Maintain a shared terminology map in `docs/glossary.md` to keep zh-TW wording consistent.

## Scope
These instructions apply to the entire `goat-nutrition-app` repository unless a more specific `AGENTS.md` exists deeper in the tree.

## Repository Structure Index
- `backend/`: Flask application, SQLAlchemy models, Alembic migrations, and background worker scripts.
- `frontend/`: Vue 3 + Vite single-page application using Element Plus, Pinia, and ECharts/Chart.js.
- `docs/`: Project documentation, deployment guides, API references, and architectural decision records (`docs/adr/`).
- `docs/references/google_genai_sdk_source/`: **[ADDED]** Local source of truth for Google Gemini API usage. Prioritise these examples/docs over external knowledge when implementing GenAI features.
- `docker-compose.yml`, `deploy*.sh`, `deploy*.bat`: Deployment and local development helpers.
- `generate_architecture.py`: Utility script that generates or updates architecture diagrams.
- `test_image_upload.py`: End-to-end test harness for the media upload flow.

## Architectural Overview
- **Backend**: Flask 3 with SQLAlchemy 2 (located under `backend/`). Redis powers session storage, dashboard caching, and an RQ-style queue defined in `app/tasks.py`. SQLite backs local dev while PostgreSQL drives production.
  - **Caching Strategy**: Dashboard caching must follow TTL (Time-To-Live) strategies. Invalidate cache on relevant write operations to prevent stale data.
- **Frontend**: Vue 3.x SPA built with Vite and Element Plus (in `frontend/`). Pinia manages global state, Axios (configured in `src/api/index.js`) handles HTTP calls, and ECharts/Chart.js provide data visualisation.
- **Background work**: `backend/run_worker.py` consumes jobs from Redis. Queue long-running work instead of blocking API handlers.
- **Documentation & assets**: Live in `docs/` with coverage artefacts and deployment diagrams. Avoid committing large binaries.

## Coding Conventions
- **Python**
  - Target Python 3.11 features already in use (pattern matching, dataclasses, typing). Prefer type hints on public functions and update Pydantic schemas when API contracts evolve.
  - **Test Coverage**: New public functions/classes must include unit tests (target 80% coverage). Do not commit code without verifying it with `pytest`.
  - Follow PEP 8 formatting; existing files are Black-compatible even though Black is not enforced automatically. Use descriptive SQLAlchemy model names and keep relationships lazy-loaded unless an optimisation demands otherwise.
  - API blueprints live in `backend/app/api/`. Register new routes in `app/api/__init__.py` and update related schemas/validation helpers in `schemas.py`.
  - Generate database migrations with Alembic (`flask db migrate` / `flask db upgrade`). Never edit existing migration scripts manually.
  - Queue background work through helpers in `app/tasks.py`; avoid direct Redis usage in new modules unless absolutely necessary.
  - **GenAI Integration**: When implementing Gemini/LLM features, strictly refer to `docs/references/google_genai_sdk_source` for SDK syntax and patterns to ensure API compatibility.
  
- **JavaScript / Vue**
  - Prefer the Composition API with `<script setup>` when feasible. Use Element Plus components for layout consistency and honour existing SCSS/CSS naming conventions.
  - Centralise API access through `src/api/index.js`; do not spawn bespoke Axios clients.
  - Maintain state in Pinia stores under `src/stores/`. Keep stores serialisable and surface derived data via getters rather than duplicating component logic.
  - When adding routes, update both `src/router/index.js` and related navigation components.
- **General**
  - Preserve bilingual UI copy only when the affected view already uses Traditional Chinese. Align terminology with `docs/README.en.md` (SoT) and keep `docs/glossary.md` updated so the zh-TW README stays consistent.
  - Update relevant documentation (`README.md`, `docs/`, OpenAPI specs) whenever external behaviour changes.
  - Never hard-code secrets such as API keys; rely on environment variables and document additions in `.env.example`.

## Testing & Quality Gates
- **Backend**: Run `cd backend && pytest` for the full suite. When iterating, target modules (e.g., `pytest tests/test_sheep_api.py -v`). Generate migrations before executing tests if models changed.
- **Frontend**: Run `cd frontend && npm run test -- --run` for CI-equivalent coverage. Execute `npm run lint` when touching JS/TS/Vue files.
- **Integration**: `docker compose up` should succeed after edits to container definitions or entrypoints; document restart steps in the relevant README.

## Git & Review Practices
- Write descriptive commit messages in the imperative mood (e.g., “Add IoT ingest endpoint”).
- Update snapshots or fixtures when tests depend on recorded data. Include migrations, generated API clients, or schema files in the same commit that requires them.
- When feasible, split large features into logical commits separating backend, frontend, and documentation work.

## Automation Conventions
- **API & Database**: When creating or modifying API endpoints, update corresponding backend tests (`pytest`), frontend tests (`npm run test`), and include the necessary Alembic migrations.
- **Background Jobs**: Provide scheduling or queue-trigger test scaffolding for new background tasks and document retry strategies.
- **Frontend Views**: When adding new routes or pages, accompany them with Pinia store or component tests and update user-facing documentation.

## Pull Request Review Template
When generating PR descriptions or automated reviews, follow this section order:
```
## Summary of Changes
## Risk Assessment
## Affected Modules
## Suggested Tests
```

## Accessibility & UX Notes
- Maintain responsive layouts; test new views at 1280px and 375px widths when practical.
- Provide clear user feedback on asynchronous operations (loading spinners, success/error toasts) using Element Plus messaging helpers.
- When showing one-time secrets (API keys, download URLs), communicate one-time visibility and ensure server logs are sanitised.

## Security Considerations
- Preserve authentication guards—new backend routes should reuse the existing `@login_required` or API-key decorators as applicable.
- Validate all incoming payloads via Pydantic or schema helpers. Reject unknown fields unless there is a documented justification.
- Sanitize file and image uploads. Reuse helper functions in `app/utils.py` to avoid duplicated logic.

## Project-wide Documentation Recommendations
- Keep `docs/adr/` up to date when major architectural or tooling decisions change. Reference ADR IDs in PR descriptions for traceability.
- Expand onboarding guides in `docs/` with environment setup steps whenever dependencies or bootstrap scripts evolve.
- Document infrastructure changes (Docker images, CI workflows, secrets management) in `docs/deployment/` to reduce production drift.

Following these guidelines keeps the project consistent with its existing implementation and documentation. When uncertain, refer to the READMEs in `backend/` and `frontend/`, or search for similar patterns across the repository.
