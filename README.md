# xrayradar-server

Minimal FastAPI + Postgres backend for the `xrayradar` Python SDK.

## Test Coverage

![Backend Coverage](https://img.shields.io/badge/backend%20coverage-100%25-brightgreen?style=flat-square)
![Frontend Coverage](https://img.shields.io/badge/frontend%20coverage-98.93%25-brightgreen?style=flat-square)

**Current Coverage:**
- **Backend (Python)**: 100% - All tests passing ✓
- **Frontend (React)**: 98.93% - All tests passing ✓

> Coverage is automatically calculated in CI. To check locally:
> - **Backend**: From the `xrayradar-server` root directory, run:
>   ```bash
>   uv run pytest --cov=src/xrayradar_server --cov-report=term
>   ```
> - **Frontend**: From the `xrayradar-server` root directory, run:
>   ```bash
>   cd xrayradar-web && npm run test:coverage
>   ```

## Security

Security scanning is automated in CI and includes:
- **Backend**: `bandit` (static analysis) + `pip-audit` (dependency vulnerabilities)
- **Frontend**: `npm audit` (dependency vulnerabilities)

**Run security audit locally:**
```bash
./scripts/security_audit.sh
```

For detailed security practices and audit results, see [SECURITY.md](SECURITY.md).

## Run locally

1) Start Postgres:

```bash
docker compose up -d
```

2) (Optional) Build the marketing site (served by the backend in production)

```bash
cd xrayradar-web
npm install
npm run build
```
or 

```bash
cd xrayradar-web && npm ci && npm run build && cd ..
```

3) Run API:

```bash
uvicorn --app-dir src xrayradar_server.main:app --reload --port 8001 --env-file .env
```

If you prefer, you can also run with:

```bash
export XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar"
PYTHONPATH=src uvicorn xrayradar_server.main:app --reload --port 8001
```

### Run locally with Docker

This repo includes a multi-stage `Dockerfile` that builds the marketing site and serves it from the backend.

1) Start Postgres:

```bash
docker compose up -d
```

2) Build the backend image:

```bash
docker build -t xrayradar-server:local .
```

3) Run the container on the same Compose network so the hostname `db` resolves:

Make sure your `.env` includes `XRAYRADAR_DATABASE_URL` pointing at `db` (not `localhost`), for example:

```bash
XRAYRADAR_DATABASE_URL=postgresql+psycopg2://xrayradar:xrayradar@db:5432/xrayradar
```

```bash
docker run --rm \
  --name xrayradar-server-local \
  --network xrayradar-server_default \
  -p 8001:8000 \
  --env-file .env \
  -e XRAYRADAR_COOKIE_SECURE=false \
  xrayradar-server:local
```

If your Compose project name is different, the network name will be different too. You can list Docker networks and use the one ending in `_default`.

## Database migrations (Alembic)

This project uses Alembic for schema migrations.

To apply migrations locally:

**If using `uv` (recommended):**

```bash
export XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar"
uv run alembic -c alembic.ini upgrade head
```

**If using pip/conda:**

```bash
export XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar"
alembic -c alembic.ini upgrade head
```

**Note:** Always use `uv run alembic` (not the system `alembic` command) to ensure the correct SQLAlchemy version is used.

**Available migrations:**
- `0001_init` - Initial schema (projects, tokens, events, token_project_access, users)
- `0002_user_projects_fingerprints` - User-owned projects, token requests, event fingerprints

### Render.com

On Render, the recommended approach is to run migrations during deploy/startup.

This repo includes a `Dockerfile`. If your Render service uses Docker, the marketing site build happens as part of the Docker image build (multi-stage build) and you do not need a separate Render “Build Command”.

If you are not using Docker on Render, you typically want to:

1) Build the marketing site (Vite) into `xrayradar-web/dist`.
2) Point the backend at that directory with `XRAYRADAR_WEB_DIST`.

Example Render Build Command (non-Docker):

```bash
cd xrayradar-web && npm ci && npm run build
```

Example start command:

```bash
alembic -c alembic.ini upgrade head && uvicorn --proxy-headers --forwarded-allow-ips='*' --app-dir src xrayradar_server.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Required environment variables (typical):

- `XRAYRADAR_DATABASE_URL`
- `XRAYRADAR_ENV=production`

If you want the backend to serve the marketing site (non-Docker builds), set:

- `XRAYRADAR_WEB_DIST=xrayradar-web/dist`

Admin UI / GitHub OAuth (recommended in production):

- `XRAYRADAR_SESSION_SECRET`
- `XRAYRADAR_ADMIN_EMAILS` (comma-separated allowlist)
- `XRAYRADAR_GITHUB_CLIENT_ID`
- `XRAYRADAR_GITHUB_CLIENT_SECRET`
- `XRAYRADAR_GITHUB_REDIRECT_URI` (e.g. `https://<your-domain>/auth/github/callback`)

Cookie security note:

- In production, serve the site over HTTPS and keep secure cookies enabled.
- For local HTTP testing only, set `XRAYRADAR_COOKIE_SECURE=false` to avoid OAuth state-cookie issues.

This avoids needing `psql` locally.

## Dependency locking (uv)

If you want reproducible dependency installs, you can generate a lockfile:

```bash
uv lock
uv sync
```

## Test coverage

Run the test suite with coverage locally (from the `xrayradar-server` root directory):

```bash
uv sync --extra dev
uv run pytest -q --cov=src/xrayradar_server --cov-report=term-missing
```

**Note**: Make sure you're in the `xrayradar-server` root directory (not `xrayradar-web`) when running backend tests.

Generate a coverage XML report (useful for CI/reporting tools):

```bash
uv run pytest -q --cov=src/xrayradar_server --cov-report=xml:coverage.xml
```

In CI, the workflow uploads `coverage.xml` as a build artifact for each Python version.

## SDK endpoint compatibility

The SDK sends events to:

- `POST /api/{project_id}/store/`

Example DSN to point the SDK to this server:

- `http://localhost:8001/1`

### Testing event ingestion

Two scripts are available for testing:

**1. Basic test event** (`scripts/send_test_event.py`):
Sends a simple test event with basic exception info.

```bash
python scripts/send_test_event.py \
  --base-url http://127.0.0.1:8001 \
  --project-id 1 \
  --token "<your_token>" \
  --message "Test error"
```

**2. Real error with stack trace** (`scripts/send_real_error.py`):
Sends a real exception with:
- Full stack trace with source code context
- Breadcrumbs (user activity timeline)
- User context (ID, email, IP)
- Device/runtime information
- Tags and metadata

This is useful for testing features in the dashboard.

```bash
python scripts/send_real_error.py \
  --base-url http://127.0.0.1:8001 \
  --project-id 1 \
  --token "<your_token>"
```

## Authentication

All endpoints require authentication.

Requests use the header:

- `X-Xrayradar-Token: <token>`

### Environment variables

- `XRAYRADAR_DATABASE_URL` (required)
- `XRAYRADAR_ENV` (optional, set to `production` in production)
- `XRAYRADAR_COOKIE_SECURE` (optional, defaults to `true` when `XRAYRADAR_ENV=production`)

If you run using `--env-file .env`, you can put all variables in `.env`.

### Admin UI (GitHub OAuth)

The server serves a minimal admin UI at:

- `GET /admin`

The UI is protected by GitHub OAuth and an email allowlist. It includes:

- **Tokens**: Create tokens, manage token-project access
- **Token requests**: Fulfill user token requests
- **Project logs**: Browse raw events with filtering and detail view

Required environment variables:

- `XRAYRADAR_GITHUB_CLIENT_ID`
- `XRAYRADAR_GITHUB_CLIENT_SECRET`
- `XRAYRADAR_SESSION_SECRET` (used to sign the session cookie)
- `XRAYRADAR_ADMIN_EMAILS` (comma-separated allowlist)

OAuth endpoints:

- `GET /auth/github/login`
- `GET /auth/github/callback`
- `POST /auth/logout`

Session status endpoint:

- `GET /api/admin/me`


## Admin API

Admin endpoints live under `/api/admin/...`.

You can authenticate as admin using a DB token with `is_admin=true`:

- header `X-Xrayradar-Token: <admin token>`

### Create an admin token

`POST /api/admin/tokens`

Body:

```json
{"name":"primary-admin","is_admin":true}
```

Response includes the generated token string. Use it in subsequent calls:

- `X-Xrayradar-Token: <token>`

### Bootstrapping the first admin token

Since all admin endpoints require an existing admin token, you must create the very first admin token by inserting it into the database.

1) Generate a secure token value (any high-entropy random string works).

2) Insert into the `tokens` table:

```sql
INSERT INTO tokens (name, token, email, is_admin, created_at, revoked_at)
VALUES ('primary-admin', '<PASTE_TOKEN_HERE>', NULL, true, now(), NULL);
```

3) Use it in requests:

`X-Xrayradar-Token: <PASTE_TOKEN_HERE>`

### Create a non-admin token

`POST /api/admin/tokens`

Body:

```json
{"name":"ingest-token","email":"owner@example.com","is_admin":false}
```

### Database migration note (existing databases)

If you already have a database created before `tokens.email` was added, you can either run Alembic migrations (recommended) or apply the SQL manually.

Apply migrations:

```bash
alembic -c alembic.ini upgrade head
```

Manual SQL:

```sql
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS email varchar(320);
CREATE INDEX IF NOT EXISTS ix_tokens_email ON tokens(email);
```

### Grant/revoke project access for a token

Grant:

- `POST /api/admin/tokens/{token_id}/projects/{project_id}/grant`

Revoke:

- `POST /api/admin/tokens/{token_id}/projects/{project_id}/revoke`

List project grants (including revoked):

- `GET /api/admin/tokens/{token_id}/projects`

### List / revoke tokens

- `GET /api/admin/tokens`
- `POST /api/admin/tokens/{token_id}/revoke`

### Token requests

Users can request tokens via the client dashboard. Admins can fulfill these requests:

- `GET /api/admin/token-requests` - List all token requests
- `POST /api/admin/token-requests/{request_id}/fulfill` - Create a token for a user and mark the request as fulfilled

The admin UI (`/admin#requests`) provides a UI for managing token requests.

### Project events (admin)

Admin-only endpoints for browsing project events:

- `GET /api/admin/projects/{project_id}/events` - List events with filtering (level, environment, release, message search, pagination)
- `GET /api/admin/projects/{project_id}/events/{event_id}` - Get full event detail including payload

These endpoints support admin session cookies (from GitHub OAuth) or admin tokens.

## Client signup and login

The marketing site (`/`) includes signup and login functionality:

- **Signup**: Click "Choose Free" or "Choose Basic" in the Pricing section to open the signup modal
- **Login**: Click "Sign in" in the top navbar to go to `/login`

Endpoints:

- `POST /auth/signup` - Create a new user account
- `POST /auth/login` - Sign in with email/password
- `POST /auth/logout` - Sign out
- `GET /api/me` - Get current user info (requires session cookie)

## Client dashboard

After logging in, users can access the dashboard at `/dashboard`:

- **Projects**: Create and list user-owned projects
- **Issues**: View issues grouped by fingerprint
- **Issue detail**: Drill down into individual events and view full JSON payloads

### User API endpoints

All user endpoints require authentication via session cookie (set after login):

**Projects:**
- `GET /api/user/projects` - List user's projects
- `POST /api/user/projects` - Create a new project (owned by the logged-in user)

**Issues (grouped by fingerprint):**
- `GET /api/user/projects/{project_id}/issues` - List issues for a project (grouped by fingerprint)
- `GET /api/user/projects/{project_id}/issues/{fingerprint}/events` - List events for a specific issue
- `GET /api/user/projects/{project_id}/events/{event_id}` - Get full event detail including payload

**Tokens:**
- `GET /api/user/tokens` - List tokens owned by the user
- `GET /api/user/tokens/{token_id}/projects` - List projects a token has access to
- `POST /api/user/tokens/{token_id}/projects/{project_id}/grant` - Grant a token access to a project (user must own both)

**Token requests:**
- `GET /api/user/token-requests` - List user's token requests
- `POST /api/user/token-requests` - Request a new token (admin will fulfill it)

### How tokens work with projects

**Important:** Tokens are **not automatically linked to projects**. When you receive a token from an admin, you must grant it access to your projects before you can use it.

**Workflow:**
1. Request a token from an admin via the dashboard (`/dashboard/tokens`)
2. Admin fulfills the request and creates a token for you
3. Go to `/dashboard/tokens` and find your token
4. Click "Manage project access" on the token
5. Click "Grant access" for each project you want to use the token with
6. Use the token in your SDK with the project's DSN

**Why this design?**
- Tokens can be granted access to multiple projects
- You control which projects each token can access
- You can revoke access later if needed (via admin UI)
- Provides fine-grained access control

### Issue grouping (fingerprinting)

Events are automatically grouped by fingerprint on ingestion. The fingerprinting algorithm:

1. Uses the SDK-provided `fingerprint` field if present
2. Otherwise computes a hash from:
   - Exception type
   - Exception value/message
   - First in-app stack frame (filename, function, line number)

This provides issue grouping where similar errors are grouped together for easier debugging.
