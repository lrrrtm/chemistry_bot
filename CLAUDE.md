# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chemistry Bot is a full-stack educational platform for Russian chemistry exam (EGE) preparation. It consists of three runtimes that share a single MySQL database:

1. **Telegram Bot** (`tgbot/`) — student-facing interface built with aiogram 3.x
2. **FastAPI backend** (`api/`) — REST API for the admin panel, also serves the React SPA
3. **React frontend** (`frontend/`) — admin panel built with React 19, TypeScript, Vite, Tailwind CSS, and Radix UI

## Commands

### Frontend

```bash
cd frontend
npm run dev        # Dev server on port 5173 (proxies /api to port 8000)
npm run build      # Production build → frontend/dist/ (served by FastAPI)
npm run lint       # ESLint
npx tsc --noEmit   # Type-check without emitting
```

### Backend / Bot

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload          # API on port 8000
python tgbot/start.py                  # Telegram bot (long-polling)
pytest tests/ -v                       # Run all tests
pytest tests/test_auth_service.py -v   # Run a single test file
```

### Docker

```bash
docker compose up                                                               # All services (bot, api, db, backup)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d         # Production
```

## Architecture

### Data flow

- **Students** interact through the Telegram bot; the bot queries MySQL directly via `db/crud.py`.
- **Admins** use the React panel → FastAPI REST API → MySQL.
- FastAPI serves the React SPA: every non-`/api` route returns `frontend/dist/index.html`.
- A background scheduler (`utils/backup_job.py` via APScheduler) periodically uploads DB dumps to Yandex Disk.

### Backend structure

`api/routers/` contains one sub-package per domain, each with `router.py`, `schemas.py`, and `service.py`:

| Package | Purpose |
|---|---|
| `auth/` | JWT login, password recovery |
| `pool/` | Question bank CRUD |
| `topics/` | Topic management |
| `users/` | Student user management |
| `student/` | Student work retrieval and stats |
| `hand_works/` | Admin-created custom assignments |
| `images/` | Image upload/serve |
| `backup/` | DB backup and restore via Yandex Disk |
| `ege/` | EGE score conversion table |

Database access is centralised in `db/crud.py`. Session management uses a context-manager pattern (`get_session()`) with auto-commit/rollback. Non-destructive column migrations run automatically in `db/database.py::run_migrations()` at startup — add new columns there when extending models in `db/models.py`.

### Telegram bot structure

`tgbot/handlers/` contains one module per conversation flow. Multi-step flows use aiogram FSM states defined in `tgbot/states/`. All user-visible strings live in `tgbot/lexicon/` (Russian). Keyboard layouts are in `tgbot/keyboards/`.

### Frontend structure

`frontend/src/pages/admin/` holds all admin views; `frontend/src/pages/student/` has the public stats page (`ViewStats.tsx`) accessible via a shareable UUID token. Auth state is managed by the `useAuth()` hook. Protected routes are wrapped in `RequireAuth`. Radix UI primitives + Tailwind are the component foundation.

## Environment

Copy `.env.dist` to `.env` and fill in:

- `BOT_API_KEY`, `ADMIN_ID`, `DEVELOPER_ID`, `FBACK_GROUP_ID` — Telegram credentials
- `PANEL_PASSWORD` — Admin panel login password
- `DB_*` — MySQL connection (host is `db` inside Docker, `localhost` for local dev)
- `APP_PORT` — Exposed port (default `3003`)
- `ROOT_FOLDER` — Absolute path to the project root on the host

## CI/CD

GitHub Actions (`.github/workflows/deploy.yml`) on push to `master`:
1. Runs `pytest` and frontend lint/type-check/build
2. Builds and pushes a Docker image to GHCR
3. SSHes into production, pulls the image, and restarts containers
