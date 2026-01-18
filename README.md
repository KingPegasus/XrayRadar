# xrayradar-server

Minimal FastAPI + Postgres backend for the `xrayradar` Python SDK.

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

3) Run API:

```bash
uvicorn --app-dir src xrayradar_server.main:app --reload --port 8001 --env-file .env
```

If you prefer, you can also run with:

```bash
export XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar"
PYTHONPATH=src uvicorn xrayradar_server.main:app --reload --port 8001
```

## Database migrations (Alembic)

This project uses Alembic for schema migrations.

To apply migrations locally:

```bash
XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar" \
alembic -c alembic.ini upgrade head
```

If you are running with `--env-file .env`, make sure `.env` contains `XRAYRADAR_DATABASE_URL` and run:

```bash
alembic -c alembic.ini upgrade head
```

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

## SDK endpoint compatibility

The SDK sends events to:

- `POST /api/{project_id}/store/`

Example DSN to point the SDK to this server:

- `http://localhost:8001/1`

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

The UI is protected by GitHub OAuth and an email allowlist.

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
