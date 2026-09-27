# Runbook: Migrate XrayRadar from Render Postgres to SQLite

This runbook covers moving an existing XrayRadar deployment on Render.com from a
managed PostgreSQL instance to a local SQLite database on the same web service, in
order to stop paying for the Postgres instance.

It assumes the repo is deployed with the included `Dockerfile`. If you use a
non-Docker Render service, the same steps apply but the start command is set
manually (see `DEVELOPERS.md`).

## 1. Goal and trade-offs

- **Goal:** run XrayRadar against `sqlite:///...` instead of Render Postgres.
- **What you keep:** all projects, users, tokens, events, and settings.
- **What you lose/accept:**
  - SQLite only works for a **single web-service instance**. Do not enable
    auto-scaling or multiple replicas.
  - Render web services have an **ephemeral filesystem**. SQLite is only durable
    if the file lives on a Render **Persistent Disk**.

If you do not attach a persistent disk, the database is wiped on every deploy and
restart.

## 2. What happens on deployment

The Docker image `CMD` is:

```bash
python scripts/run_migrations.py && uvicorn ...
```

`scripts/run_migrations.py` inspects `XRAYRADAR_DATABASE_URL`:

- **Postgres URL** (`postgresql+psycopg2://...`): runs `alembic upgrade head`.
- **SQLite URL** (`sqlite:///...`): prints `SQLite detected: skipping Alembic
  migrations (schema is created by init_db()).` and does not run Alembic.

Then uvicorn starts, FastAPI's lifespan calls `init_db()`, which runs
`Base.metadata.create_all()`. On SQLite this creates any missing tables from the
SQLAlchemy models. On a fresh SQLite file this means an **empty** database, so the
data migration below must be completed before you point traffic at SQLite.

## 3. Pre-migration checklist

- [ ] Render web service is set to **1 instance** (no auto-scaling).
- [ ] You have a Render **Persistent Disk** created and mounted (Step 4).
- [ ] You can access the Postgres internal connection string (Step 5).
- [ ] You have a rollback plan (Step 8) in case the switch fails.

## 4. Step 1 — Attach a persistent disk

1. In Render, open your **Web Service**.
2. Go to **Disks** and create a persistent disk.
3. Set a **Mount Path** such as `/var/data` and choose a size.
4. Save. Render redeploys the service to mount the disk.

The SQLite file will live at `/var/data/xrayradar.db`.

## 5. Step 2 — Get the Postgres connection string

You need the **internal** Postgres URL so the migration can read the source data.
Two common options:

- If the Postgres database is linked to the service, Render may expose it as an
  environment variable (often `DATABASE_URL`), or
- Open the **PostgreSQL** database in Render and copy the **Internal Database URL**
  (the `...onrender.com` / internal hostname, not the external/public one).

Keep the app pointed at Postgres for now (`XRAYRADAR_DATABASE_URL` unchanged).

## 6. Step 3 — Migrate the data

Run the migration from the Render **Shell** (one-off command in the running
service) so it can reach both the internal Postgres and the mounted disk:

```bash
python scripts/migrate_postgres_to_sqlite.py \
  --source "postgresql+psycopg2://USER:PASSWORD@HOST:5432/xrayradar" \
  --target "sqlite:////var/data/xrayradar.db"
```

Notes:

- Use the internal Postgres hostname/credentials from Step 2.
- `sqlite:////var/data/xrayradar.db` has four slashes: `sqlite://` + the absolute
  path `/var/data/xrayradar.db`.
- The script creates the SQLite schema from the models, copies every table while
  preserving primary keys and foreign keys, and prints a per-table row count.

Verify the counts look correct (e.g. `events`, `users`, `projects` are non-zero if
you have data).

## 7. Step 4 — Switch the service to SQLite

1. In the service **Environment**, set:

   ```text
   XRAYRADAR_DATABASE_URL=sqlite:////var/data/xrayradar.db
   ```

2. Confirm the instance count is still **1**.
3. Deploy.

On deploy, the logs should show `SQLite detected: skipping Alembic migrations`.
The app then serves from the migrated SQLite file.

## 8. Step 5 — Verify

- [ ] Open the dashboard and confirm projects/issues/events are present.
- [ ] Log in as an admin and confirm `/admin` system statistics show the expected
      event and email counts.
- [ ] Send a test event and confirm it appears.
- [ ] Confirm `XRAYRADAR_DATABASE_URL` in the service environment starts with
      `sqlite:///`.

## 9. Step 6 — Retire Postgres (after a grace period)

Do not delete Postgres immediately. Keep it for a few days while you confirm
ingestion and reads are stable on SQLite, then delete the Postgres instance from
Render to stop the charge.

## 10. Rollback plan

If SQLite misbehaves after the switch, roll back by:

1. Set `XRAYRADAR_DATABASE_URL` back to the Postgres URL.
2. Redeploy.

Postgres still has the data (as long as it was not deleted), so this restores the
previous state. Any events ingested while on SQLite would need to be re-migrated
forward into Postgres separately; for a short verification window this is usually
acceptable.

## 11. Gotchas

- **Ephemeral disk without a mount:** SQLite data is lost on every deploy/restart.
- **Multiple instances:** two replicas each have their own SQLite file and will
  diverge. Keep the instance count at 1.
- **Four slashes:** `sqlite:////var/data/xrayradar.db` (absolute path), not
  `sqlite:///var/data/...`.
- **SQLite skips Alembic:** future schema changes are applied by `init_db()` on
  fresh tables only; existing SQLite tables are not auto-migrated. If you add
  columns later, you will need a manual SQL/script step for SQLite (the Alembic
  migrations remain Postgres-only).
