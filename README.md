<p align="center">
  <img src="xrayradar-web/public/logo.svg" alt="XrayRadar" width="520" />
</p>

**XrayRadar** is an error-monitoring platform: your applications send exceptions and context to a central server, which groups them into **issues**, surfaces them in a **dashboard**, and can **notify** you by email when something breaks. It is designed to stay simple to self-host while remaining comfortable for small teams and production workloads.

This repository contains the **open-source backend and web app** (FastAPI + PostgreSQL + React) that powers ingestion, auth, projects, API tokens, alerts, and the marketing site. **Client SDKs** (below) send events to the HTTP API exposed here.

> **GitHub:** The project is published under the repository name **XrayRadar**. The Python package metadata in `pyproject.toml` still uses the name `xrayradar-server` for installs from a local checkout (`uv sync` / tooling); that does not change how you run or brand the app.

![Backend Coverage](https://img.shields.io/badge/backend%20coverage-97%25-brightgreen?style=flat-square)
![Frontend Coverage](https://img.shields.io/badge/frontend%20coverage-96%25-brightgreen?style=flat-square)

## What you get

- **Ingestion API** — `POST /api/{project_id}/store/` accepts structured error payloads (stack traces, breadcrumbs, user/device context, tags).
- **Issue grouping** — Events are fingerprinted into issues so you see distinct problems, not an endless raw stream.
- **Dashboard** — Sign up, create projects, browse issues and events, manage API tokens and (with the right plan) team access and environment-scoped visibility.
- **Alerts** — Project- and environment-level email digests with cooldowns; optional [Resend](https://resend.com/) integration for transactional mail (verification, password reset, alerts).
- **Admin tools** — GitHub OAuth–backed admin UI and APIs for tokens, users, token requests, and operational visibility.
- **Marketing site** — The `xrayradar-web` Vite/React app builds into static assets served by the backend in production.

## Client SDKs

Events are sent to `POST /api/{project_id}/store/` using a **DSN** and API token. Official libraries (same assets as the marketing site in [`xrayradar-web/src/assets/sdk-logos/`](xrayradar-web/src/assets/sdk-logos/)):

<table>
<tr valign="top">
<td width="32%">

**Python**

<p align="left">Official SDK on PyPI — middleware for <strong>Django</strong>, <strong>FastAPI</strong>, <strong>Flask</strong>.</p>

<p align="left">
<a href="https://pypi.org/project/xrayradar/"><img src="xrayradar-web/src/assets/sdk-logos/fastapi.svg" width="22" height="22" alt="FastAPI" valign="middle" /> FastAPI</a><br /><br />
<a href="https://pypi.org/project/xrayradar/"><img src="xrayradar-web/src/assets/sdk-logos/django.svg" width="22" height="22" alt="Django" valign="middle" /> Django</a><br /><br />
<a href="https://pypi.org/project/xrayradar/"><img src="xrayradar-web/src/assets/sdk-logos/flask.svg" width="22" height="22" alt="Flask" valign="middle" /> Flask</a>
</p>

<p align="left"><a href="https://pypi.org/project/xrayradar/"><strong>View on PyPI →</strong></a></p>

</td>
<td width="36%">

**JavaScript / TypeScript**

<p align="left">Packages on npm — <strong>Node</strong>, <strong>Express</strong>, <strong>Koa</strong>, <strong>React</strong>, <strong>Next.js</strong>, <strong>Remix</strong>.</p>

<p align="left">
<a href="https://www.npmjs.com/package/@xrayradar/node"><img src="xrayradar-web/src/assets/sdk-logos/node.svg" width="22" height="22" alt="Node.js" valign="middle" /> Node.js</a><br /><br />
<a href="https://www.npmjs.com/package/@xrayradar/node"><img src="xrayradar-web/src/assets/sdk-logos/Express.svg" width="22" height="22" alt="Express" valign="middle" /> Express</a><br /><br />
<a href="https://www.npmjs.com/package/@xrayradar/node"><img src="xrayradar-web/src/assets/sdk-logos/koa.svg" width="22" height="22" alt="Koa" valign="middle" /> Koa</a><br /><br />
<a href="https://www.npmjs.com/package/@xrayradar/react"><img src="xrayradar-web/src/assets/sdk-logos/react.svg" width="22" height="22" alt="React" valign="middle" /> React</a><br /><br />
<a href="https://www.npmjs.com/package/@xrayradar/nextjs"><img src="xrayradar-web/src/assets/sdk-logos/nextjs.svg" width="22" height="22" alt="Next.js" valign="middle" /> Next.js</a><br /><br />
<a href="https://www.npmjs.com/package/@xrayradar/node"><strong>Remix</strong></a> <sub>(via <code>@xrayradar/node</code>)</sub>
</p>

<p align="left"><a href="https://www.npmjs.com/package/@xrayradar/node"><strong>View on npm →</strong></a></p>

</td>
<td width="32%">

**Android / Kotlin**

<p align="left">Kotlin SDK on <strong>Maven Central</strong> — crash capture, breadcrumbs, offline queue, <strong>WorkManager</strong> retry. minSdk <strong>24+</strong>.</p>

<p align="left">
<a href="https://github.com/KingPegasus/XrayRadar-Android-SDK"><img src="xrayradar-web/src/assets/sdk-logos/android.svg" width="22" height="22" alt="Android" valign="middle" /> Android</a><br /><br />
<a href="https://github.com/KingPegasus/XrayRadar-Android-SDK"><img src="xrayradar-web/src/assets/sdk-logos/Kotlin.svg" width="22" height="22" alt="Kotlin" valign="middle" /> Kotlin</a>
</p>

<p align="left">
<a href="https://central.sonatype.com/artifact/com.xrayradar/xrayradar-android"><strong>Maven Central →</strong></a><br />
<a href="https://github.com/KingPegasus/XrayRadar-Android-SDK"><strong>View on GitHub →</strong></a>
</p>

</td>
</tr>
</table>

## Screenshots

### User dashboard

Signed-in experience for creating projects, triaging issues, and (on team plans) managing access.

<p align="center">
  <img src="docs/images/user-dashboard.png" alt="XrayRadar user dashboard home with stats and getting-started guidance" width="960" />
</p>

<p align="center">
  <img src="docs/images/user-projects.png" alt="XrayRadar projects list in the user dashboard" width="960" />
</p>

<p align="center">
  <img src="docs/images/user-project-issues.png" alt="XrayRadar project issues view: grouped errors and issue list" width="960" />
</p>

Team / environment access (Teams and Teams Pro plans):

<p align="center">
  <img src="docs/images/team-config.png" alt="XrayRadar team and environment access configuration" width="960" />
</p>

### Admin panel (`/admin`)

GitHub OAuth–protected operator UI: tokens, token requests, users, deletion requests, and project logs. The home view shows **system statistics** (projects, tokens, users by plan, events, and email delivery breakdown).

<p align="center">
  <img src="docs/images/admin-system-statistics.png" alt="XrayRadar admin panel: System Statistics dashboard with sidebar and metric cards for projects, tokens, users, events, and emails" width="960" />
</p>

Additional assets live under [`docs/images/`](docs/images/).

## Who it is for

- Teams that want **self-hosted** error tracking with a clear codebase.
- Developers already using the **XrayRadar SDKs** who need to point at their own server or contribute to the server implementation.

## Repository layout

| Path | Role |
| --- | --- |
| `src/xrayradar_server/` | FastAPI application (Python import package `xrayradar_server`) |
| `xrayradar-web/` | React (Vite) UI: landing, auth, dashboard |
| `docs/architecture/` | Design and flow documentation |
| `alembic/` | Database migrations |

## Quick start

1. Start Postgres: `docker compose up -d`
2. Install and migrate:

```bash
cp .env.example .env   # then edit if needed
uv sync
export XRAYRADAR_DATABASE_URL="postgresql+psycopg2://xrayradar:xrayradar@localhost:5432/xrayradar"
uv run alembic -c alembic.ini upgrade head
```

3. (Optional) Build the web UI: `cd xrayradar-web && npm ci && npm run build && cd ..`

4. Run the API:

```bash
uv run uvicorn --app-dir src xrayradar_server.main:app --reload --port 8001 --env-file .env
```

Point the SDK at `http://localhost:8001/<project_id>` (see [DEVELOPERS.md](DEVELOPERS.md) for DSN details and test scripts).

## Documentation

| Doc | Purpose |
| --- | --- |
| [DEVELOPERS.md](DEVELOPERS.md) | Local dev, Docker, Render, env vars, tests, security scripts, API reference |
| [docs/architecture/](docs/architecture/) | System design |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [SECURITY.md](SECURITY.md) | Security policy and reporting |

## Security

CI runs backend (`bandit`, `pip-audit`) and frontend (`npm audit`) checks. Report vulnerabilities per [SECURITY.md](SECURITY.md).

## Contributing

Issues and pull requests are welcome. Use [DEVELOPERS.md](DEVELOPERS.md) for setup, tests (`uv run pytest`, `cd xrayradar-web && npm test`), and conventions.

## License

This project is licensed under the [MIT License](LICENSE).
