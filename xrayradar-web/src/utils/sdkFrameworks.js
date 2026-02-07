/**
 * SDK frameworks and quick-setup snippets for the landing page.
 * Framework logos use inline SVGs (Simple Icons–style paths).
 */

export const SDK_FRAMEWORKS = {
  python: [
    { id: 'fastapi', name: 'FastAPI', logoId: 'fastapi' },
    { id: 'django', name: 'Django', logoId: 'django' },
    { id: 'flask', name: 'Flask', logoId: 'flask' },
  ],
  js: [
    { id: 'node', name: 'Node.js', logoId: 'node' },
    { id: 'react', name: 'React', logoId: 'react' },
    { id: 'nextjs', name: 'Next.js', logoId: 'nextjs' },
  ],
}

/**
 * Quick setup code snippets by language and framework.
 * Key: `${language}_${frameworkId}`
 */
export const QUICK_SETUP_SNIPPETS = {
  python_fastapi: {
    label: 'FastAPI',
    code: `pip install xrayradar

# main.py
from fastapi import FastAPI
from xrayradar import ErrorTracker
from xrayradar.integrations.fastapi import FastAPIIntegration

app = FastAPI()
tracker = ErrorTracker(
    dsn="https://xrayradar.com/<project_id>",
    auth_token="<token>"
)
FastAPIIntegration.init_app(app, tracker)

# That's it! Exceptions are auto-captured
# with request context and breadcrumbs.`,
  },
  python_django: {
    label: 'Django',
    code: `pip install xrayradar

# settings.py

import xrayradar
from xrayradar.integrations.django import init_django_integration

client = xrayradar.init(
    dsn="https://xrayradar.com/<project_id>",
    auth_token="<token>"
)
init_django_integration(client)

MIDDLEWARE = [
  # ... your other middleware ...
  "xrayradar.integrations.django.ErrorTrackerMiddleware",
]

# That's it! Exceptions are auto-captured
# with request context and breadcrumbs.`,
  },
  python_flask: {
    label: 'Flask',
    code: `pip install xrayradar

# app.py
from flask import Flask
from xrayradar import ErrorTracker
from xrayradar.integrations.flask import FlaskIntegration

app = Flask(__name__)
tracker = ErrorTracker(
    dsn="https://xrayradar.com/<project_id>",
    auth_token="<token>"
)
FlaskIntegration.init_app(app, tracker)

# That's it! Exceptions are auto-captured with request context.`,
  },
  js_node: {
    label: 'Node.js',
    code: `npm install @xrayradar/node

import { init, captureException } from "@xrayradar/node";

init({
  dsn: "https://xrayradar.com/<project_id>",
  authToken: "<token>",
});

captureException(new Error("Something broke"));`,
  },
  js_react: {
    label: 'React',
    code: `npm install @xrayradar/react

import { init, ErrorBoundary } from "@xrayradar/react";

init({
  dsn: "https://xrayradar.com/<project_id>",
  authToken: "<token>",
});

function App() {
  return (
    <ErrorBoundary>
      <YourApp />
    </ErrorBoundary>
  );
}`,
  },
  js_nextjs: {
    label: 'Next.js',
    code: `npm install @xrayradar/nextjs

// instrumentation.ts (project root)
import { init } from "@xrayradar/node";
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    init({
      dsn: process.env.XRAYRADAR_DSN,
      authToken: process.env.XRAYRADAR_AUTH_TOKEN,
    });
  }
}

// app/layout.tsx (or _app.tsx) - client
import { init, ErrorBoundary } from "@xrayradar/react";
if (typeof window !== "undefined") {
  init({ dsn: process.env.NEXT_PUBLIC_XRAYRADAR_DSN, authToken: process.env.NEXT_PUBLIC_XRAYRADAR_AUTH_TOKEN });
}
export default function RootLayout({ children }) {
  return <ErrorBoundary>{children}</ErrorBoundary>;
}`,
  },
}

export const PYPI_URL = 'https://pypi.org/project/xrayradar/'
export const NPM_URL = 'https://www.npmjs.com/package/@xrayradar/node'
