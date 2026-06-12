# Mini Issue Tracker

A small Jira/Linear-style issue tracker built for the QA Take-Home Assessment.

- **Backend**: FastAPI + SQLAlchemy + SQLite, JWT auth — entirely free, zero external services
- **Frontend**: React (Vite) SPA
- **Docs**: `docs/` contains the test strategy, test cases, bug report template, and system
  design write-up
- **Tests**: Pytest API test suite (`backend/app/tests/`), Playwright E2E suite (`frontend/e2e/`)

There are two ways to run this project:

1. **VS Code (no terminal needed)** — section 1 below. Best for day-to-day development and
   debugging.
2. **Docker Compose (one command)** — section 2 below. Best for a quick "just run it" check, and
   is what CI uses to verify the images build.

## 1. Running everything from VS Code

Open this `issue-tracker/` folder as your VS Code workspace folder (File → Open Folder).

### One-time setup (first time only)

Open the **Terminal → Run Task...** menu (or press `Ctrl+Shift+P` / `Cmd+Shift+P` and type
"Run Task") and run, in order:

1. **Backend: Install dependencies** — installs the Python packages listed in
   `backend/requirements.txt`
2. **Frontend: Install dependencies** — runs `npm install` for the React app

(These two steps use VS Code's Tasks runner, which opens a terminal panel for you — you don't
need to type any commands yourself, just click the task name.)

### Day-to-day: start the app

- Go to the **Run and Debug** panel (left sidebar, the play-button-with-bug icon).
- Choose **"Backend: FastAPI (uvicorn)"** from the dropdown at the top and press the green ▶
  Run/Debug button. This starts the API at http://localhost:8000 (interactive docs at
  http://localhost:8000/docs) and lets you set breakpoints in any `.py` file.
- Then run the **"Frontend: Start Dev Server"** task (Terminal → Run Task) to start the React
  app at http://localhost:5173.

The SQLite database file (`backend/issue_tracker.db`) is created automatically the first time
the backend starts — there's nothing to install or configure.

### Running the tests

- **Backend tests**: Run and Debug → **"Backend: Run all Pytest tests"** (or Terminal → Run Task
  → **"Backend: Run Pytest"**). All 39 tests run against an isolated in-memory SQLite database,
  so they don't touch `issue_tracker.db`.
- **Frontend E2E tests**: Terminal → Run Task → **"Frontend: Run Playwright E2E tests"**. The
  backend and frontend dev servers must already be running (see above).

## 2. Running everything with Docker

Requires only [Docker](https://www.docker.com/) (with Compose). From the `issue-tracker/` folder:

```bash
docker compose up --build
```

This single command:

- Builds and starts the **backend** (FastAPI + SQLite) at http://localhost:8000
  (docs at http://localhost:8000/docs), persisting the SQLite database in a named volume
  (`backend_data`) so data survives container restarts.
- Builds and starts the **frontend** (React, built and served via nginx) at http://localhost:80.
- Waits for the backend's `/health` check to pass before starting the frontend.

Stop everything with `Ctrl+C`, or `docker compose down` (add `-v` to also remove the database
volume).

## 3. Continuous Integration

`.github/workflows/ci.yml` runs automatically on every pull request (and push to `main`/`master`)
and includes three jobs:

- **Backend** — lint with `ruff` and run the full Pytest suite (39 tests)
- **Frontend** — lint with ESLint and build the production bundle
- **Docker** — build both the backend and frontend images, to catch Dockerfile breakage early

## 4. Project Structure

```
issue-tracker/
├── .vscode/
│   ├── launch.json     # Run/Debug configs (backend server, pytest)
│   └── tasks.json       # One-click tasks (install, run, test)
├── .github/
│   └── workflows/
│       └── ci.yml        # Lint + test + build, on every PR
├── docker-compose.yml      # One command starts backend + frontend
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI app, middleware, error handlers, startup
│   │   ├── database.py    # settings, DB engine/session, logging
│   │   ├── models.py        # SQLAlchemy models (User, Project, Issue)
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── security.py        # password hashing, JWT, auth dependency
│   │   ├── routers.py          # all API routes (auth, projects, issues, dashboard)
│   │   └── tests/                # Pytest API test suite (39 tests)
│   ├── requirements.txt
│   ├── pyproject.toml      # ruff lint config
│   ├── Dockerfile
│   ├── .dockerignore
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/          # Login, Register, Dashboard, ProjectPage
│   │   ├── components/      # NavBar, IssueForm, IssueRow, ProtectedRoute
│   │   ├── context/          # AuthContext
│   │   └── api.js
│   ├── e2e/                   # Playwright E2E tests
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── .dockerignore
│   └── .env.example
└── docs/
    ├── test-strategy.md
    ├── test-cases.md
    ├── bug-report-template.md
    └── system-design.md
```

The backend was deliberately consolidated from ~17 small files into 6 focused modules
(`main.py`, `database.py`, `models.py`, `schemas.py`, `security.py`, `routers.py`) to make it
easy to navigate while keeping clear separation of concerns. All QA artifacts (test strategy,
test cases, bug report template, Pytest suite, Playwright suite) are unchanged from the original
build.

## 5. Configuration

Both `backend/.env.example` and `frontend/.env.example` show the available settings. Copy them
to `.env` if you want to override defaults (optional — the app works out of the box):

```bash
# backend/.env.example
DATABASE_URL=sqlite:///./issue_tracker.db
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
PASSWORD_MIN_LENGTH=8
CORS_ORIGINS=http://localhost:5173
```

```bash
# frontend/.env.example
VITE_API_URL=http://localhost:8000
```

## 6. API Overview

All endpoints (except `/health`, `/auth/register`, `/auth/login`) require an
`Authorization: Bearer <token>` header. Errors are returned as `{"error": "..."}`.

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Log in, returns a JWT |
| POST | `/auth/logout` | Log out (stateless; client discards token) |
| GET | `/auth/me` | Current user info |
| GET | `/auth/users` | List users (for assignee dropdowns) |
| GET | `/projects` | List the current user's projects |
| POST | `/projects` | Create a project |
| GET | `/projects/{id}` | Get a project |
| PATCH | `/projects/{id}` | Update a project |
| POST | `/projects/{id}/archive` | Archive a project |
| POST | `/projects/{id}/unarchive` | Unarchive a project |
| GET | `/issues` | List issues (filters: `project_id`, `search`, `status`, `priority`, `assignee_id`) |
| POST | `/issues` | Create an issue |
| GET | `/issues/{id}` | Get an issue |
| PATCH | `/issues/{id}` | Update an issue (status, assignee, etc.) |
| DELETE | `/issues/{id}` | Delete an issue |
| GET | `/dashboard/stats` | Aggregate stats (total/open/completed issues, total projects) |

Full interactive docs (generated by FastAPI) are available at `/docs` once the backend is
running.

## 7. Assumptions

- **SQLite for everything**: this project uses a single SQLite file (`issue_tracker.db`,
  created automatically) for the running app, and an isolated in-memory SQLite database for
  tests. This keeps the whole project free, dependency-free, and runnable from VS Code with no
  database server to install.
- **Schema management**: tables are created via `Base.metadata.create_all()` on application
  startup rather than through Alembic migrations. For a take-home project this avoids the
  overhead of a migration framework while still giving a working schema out of the box. A
  production deployment would use Alembic for versioned, reversible migrations, and likely a
  server-based database (e.g. PostgreSQL).
- **Single-owner projects**: each project has a single `owner`. Issues within a project can be
  assigned to *any* registered user (not just project "members"), since the assessment doesn't
  define a project-membership/sharing model. This is documented as a known limitation in
  `docs/bug-report-template.md`'s example.
- **Logout is stateless**: JWTs are not server-side revoked on logout; the client simply
  discards the token. Token lifetime is controlled by `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60).
- **Archiving vs. deleting projects**: "archive" is a soft state (`is_archived` flag) and is the
  primary way to remove a project from the active view. Hard-deleting a project (and cascading
  to its issues) is supported at the model level but not exposed via a dedicated endpoint, to
  avoid accidental data loss in normal usage.
- **Search**: issue title search uses a case-insensitive `ILIKE`/`LIKE` match, sufficient for the
  expected data volumes of this assessment.
