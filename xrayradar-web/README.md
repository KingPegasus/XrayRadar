# xrayradar-web

Marketing site for Xrayradar (React + Vite).

## Local development

```bash
npm install
npm run dev
```

Then open:

- http://localhost:5173

If you want the marketing site to talk to a local backend for signup/login, run the API as well:

```bash
uvicorn --app-dir src xrayradar_server.main:app --reload --port 8001 --env-file .env
```

## Production build

```bash
npm run build
npm run preview
```

## Serving via the backend (production)

In production, the backend can serve the compiled static files from `dist/`.

Build:

```bash
npm ci
npm run build
```

Then start the backend with:

- `XRAYRADAR_WEB_DIST=xrayradar-web/dist`

This will serve:

- `/` (marketing site)
- `/assets/...` (static assets)

While keeping API routes intact:

- `/api/...`
- `/auth/...`

## Notes

- Pricing tiers:
  - Free: 5k errors stored
  - Basic: $1/month, 50k errors stored
