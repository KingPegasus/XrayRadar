# xrayradar-web

Web application for Xrayradar (React + Vite). Includes a marketing landing page, user authentication, and a full dashboard for managing projects, viewing issues, and managing tokens.

## Local development

```bash
npm install
npm run dev
```

Then open:

- http://localhost:5173

The app will show:
- `/` - Marketing landing page with signup
- `/login` - Login page
- `/dashboard` - User dashboard (requires authentication)
  - `/dashboard` - Projects list
  - `/dashboard/tokens` - Token management
  - `/dashboard/projects/{id}` - Project issues
  - `/dashboard/projects/{id}/issues/{fingerprint}` - Issue details
  - `/dashboard/projects/{id}/issues/{fingerprint}/events/{eventId}` - Event details

**Note:** The frontend uses relative URLs for API calls, so it will connect to the same origin. For local development, you need to run the backend as well:

```bash
# From the xrayradar-server root directory
uvicorn --app-dir src xrayradar_server.main:app --reload --port 8001 --env-file .env
```

Then access the app at http://localhost:8001 (the backend will serve the frontend in production, or you can proxy Vite dev server to the backend).

## Production build

```bash
npm run build
npm run preview
```

## Serving via the backend (production)

In production, the backend serves the compiled static files from `dist/`.

Build:

```bash
npm ci
npm run build
```

Then start the backend with:

- `XRAYRADAR_WEB_DIST=xrayradar-web/dist`

This will serve:

- `/` - Marketing landing page and dashboard (SPA routing)
- `/assets/...` - Static assets (JS, CSS, images)

While keeping API routes intact:

- `/api/...` - API endpoints
- `/auth/...` - Authentication endpoints
- `/admin` - Admin UI (server-rendered)

The backend handles client-side routing by serving `index.html` for all non-API routes.

## Features

- **Marketing Landing Page**: Public-facing homepage with features and pricing
- **User Authentication**: Signup and login functionality
- **Dashboard**: Full-featured dashboard for authenticated users
  - **Projects**: Create and manage projects
  - **Issues**: View error issues grouped by fingerprint (Sentry-like)
  - **Events**: View detailed event information with stack traces, breadcrumbs, and context
  - **Tokens**: Request and manage API tokens for project access
- **Sentry-like Error Display**: Rich error details including:
  - Stack traces with source context
  - Breadcrumbs timeline
  - User and device information
  - Environment and tags
  - Event frequency charts

## Testing

The project uses [Vitest](https://vitest.dev/) for unit and component testing, along with [React Testing Library](https://testing-library.com/react) for component testing.

### Running Tests

```bash
# Run tests in watch mode
npm test

# Run tests once
npm test -- --run

# Run tests with UI
npm run test:ui

# Run tests with coverage report
npm run test:coverage
```

### Test Organization

Tests follow a **co-located** structure (professional React convention), where test files are placed next to the source files they test:

```
src/
├── components/
│   ├── Link.jsx
│   └── Link.test.jsx          # Co-located test
├── pages/
│   ├── ProjectsPage.jsx
│   └── ProjectsPage.test.jsx   # Co-located test
├── utils/
│   ├── api.js
│   └── api.test.js            # Co-located test
└── hooks/
    ├── usePathname.js
    └── usePathname.test.js     # Co-located test
```

### Writing Tests

Example test file structure:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MyComponent from './MyComponent'

describe('MyComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    render(<MyComponent />)
    const button = screen.getByRole('button')
    await user.click(button)
    // Assert expected behavior
  })
})
```

### Test Setup

The test setup file (`src/test/setup.js`) configures:
- `@testing-library/jest-dom` matchers for better assertions
- Browser API mocks (window.location, window.history, PopStateEvent)
- Automatic cleanup after each test
- jsdom environment for browser simulation

### E2E Testing (Optional)

For end-to-end testing, consider adding [Playwright](https://playwright.dev/) or [Cypress](https://www.cypress.io/):

```bash
npm install -D @playwright/test
# or
npm install -D cypress
```

## Notes

- Pricing tiers (displayed on landing page):
  - Free: 5k errors stored
  - Basic: $1/month, 50k errors stored
