# xrayradar-server

Minimal FastAPI + Postgres backend for the `xrayradar` Python SDK.

## Run locally

1) Start Postgres:

```bash
docker compose up -d
```

2) Run API:

```bash
export XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar"
uvicorn --app-dir src xrayradar_server.main:app --reload --port 8001
```

If you prefer, you can also run with:

```bash
export XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar"
PYTHONPATH=src uvicorn xrayradar_server.main:app --reload --port 8001
```

## SDK endpoint compatibility

The SDK sends events to:

- `POST /api/{project_id}/store/`

Example DSN to point the SDK to this server:

- `http://localhost:8001/1`

Note: the current SDK only uses `project_id` from the DSN path and does not reliably send auth yet. The MVP server accepts ingest without auth.
