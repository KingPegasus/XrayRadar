export const FEATURES = [
  {
    title: 'Lightweight SDKs',
    text: 'Drop-in error capture for Python and JavaScript/TypeScript. Keep the payload clean and predictable, and ship without heavy dependencies.',
  },
  {
    title: 'Auto-capture middleware',
    text: 'Python: built-in middleware for Django, FastAPI, and Flask. JS: Node, React, Next.js. Automatically captures unhandled exceptions with request context and breadcrumbs.',
  },
  {
    title: 'Simple DSN + Token auth',
    text: 'Point your app at a project DSN and authenticate using a token header. No embedded credentials in DSNs.',
  },
  {
    title: 'Minimal server + ingestion API',
    text: 'Store events, keep payloads searchable, and debug quickly. Built to stay simple and reliable.',
  },
  {
    title: 'Breadcrumb tracking',
    text: 'Capture the trail of events leading to errors. HTTP requests are auto-captured, plus add custom breadcrumbs for full context.',
  },
  {
    title: 'Email alerts',
    text: 'Get notified when errors occur. Configure per-project email alerts with cooldown settings to avoid alert fatigue.',
  },
  {
    title: 'Environment views + ACL',
    text: 'Filter noise by environment (production, staging, etc.) and control which environments teammates can access in each project.',
  },
  {
    title: 'Token environment scoping',
    text: 'Scope token access per project and per environment, so ingest and automation credentials only reach the environments they need.',
  },
]
