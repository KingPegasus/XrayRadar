# Dashboard Error Statistics

## Overview

The dashboard error statistics feature provides users with comprehensive insights into error patterns across all their projects. It displays error totals, unique issue counts, trends, top errors, and a 30-day frequency chart to help users understand their application's health at a glance.

## Features

1. **Total Errors** — Error counts for last 24h, 7d, and 30d
2. **Unique Issues Count** — Distinct error fingerprints for 24h, 7d, and 30d
3. **Error Trend Graph** — Percentage change (up/down/same) vs previous period for 7d and 30d
4. **Top 5 Errors** — Most frequent errors by count in the last 30 days
5. **Daily Frequency Chart** — Visual representation of error frequency over 30 days

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DashboardHome (React)                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  On mount: fetchJson('/api/user/dashboard/stats')              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                   │                                  │
│                                   ▼                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Display:                                                       │ │
│  │  • Summary cards (24h/7d/30d totals, unique issues)           │ │
│  │  • Trend cards (7d/30d percentage change with up/down arrows)  │ │
│  │  • EventFrequencyChart (30-day bar chart)                      │ │
│  │  • Top 5 errors list (clickable links to issue detail)         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP GET
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│            Backend: /api/user/dashboard/stats                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Route: routers/user/dashboard.py                              │ │
│  │  Auth: require_user (session cookie)                           │ │
│  │  Response: DashboardStatsOut                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                   │                                  │
│                                   ▼                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Query Database:                                                │ │
│  │  1. Get user's project IDs                                     │ │
│  │  2. Count events (error level only) for 24h/7d/30d             │ │
│  │  3. Count unique fingerprints for 24h/7d/30d                   │ │
│  │  4. Compare current vs previous period for trends              │ │
│  │  5. Get top 5 errors by frequency (last 30d)                   │ │
│  │  6. Aggregate daily event counts for 30-day chart              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                   │                                  │
│                                   ▼                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Return JSON:                                                   │ │
│  │  {                                                              │ │
│  │    "totals": { "last_24h": N, "last_7d": N, "last_30d": N },  │ │
│  │    "unique_issues": { "last_24h": N, "last_7d": N, ... },     │ │
│  │    "trend_7d": { "current": N, "previous": N,                 │ │
│  │                  "percent_change": X.X, "direction": "up" },  │ │
│  │    "trend_30d": { ... },                                       │ │
│  │    "top_5_errors": [                                           │ │
│  │      { "fingerprint": "...", "message": "...", "count": N,    │ │
│  │        "project_id": N, "project_name": "..." }, ...          │ │
│  │    ],                                                          │ │
│  │    "trend_daily": { "2026-01-01": N, "2026-01-02": N, ... }   │ │
│  │  }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Database Schema

The feature queries the following tables:

- **`projects`** — To filter events by user's projects
- **`events`** — To count errors, fingerprints, and aggregate statistics

### Key Queries

1. **Total error counts** (24h, 7d, 30d):
   ```sql
   SELECT COUNT(*) FROM events
   WHERE project_id IN (user_projects)
     AND level = 'error'
     AND timestamp >= <time_threshold>
   ```

2. **Unique issue counts**:
   ```sql
   SELECT COUNT(DISTINCT fingerprint) FROM events
   WHERE project_id IN (user_projects)
     AND level = 'error'
     AND fingerprint IS NOT NULL
     AND timestamp >= <time_threshold>
   ```

3. **Trend comparison** (7d vs previous 7d):
   ```sql
   -- Current 7d
   SELECT COUNT(*) FROM events WHERE timestamp >= now - 7d
   -- Previous 7d
   SELECT COUNT(*) FROM events WHERE timestamp >= now - 14d AND timestamp < now - 7d
   -- Calculate: ((current - previous) / previous) * 100
   ```

4. **Top 5 errors**:
   ```sql
   SELECT project_id, fingerprint, COUNT(*) as cnt
   FROM events
   WHERE project_id IN (user_projects)
     AND level = 'error'
     AND fingerprint IS NOT NULL
     AND timestamp >= now - 30d
   GROUP BY project_id, fingerprint
   ORDER BY cnt DESC
   LIMIT 5
   ```

5. **Daily frequency**:
   ```sql
   SELECT DATE(timestamp) as dt, COUNT(*) as cnt
   FROM events
   WHERE project_id IN (user_projects)
     AND level = 'error'
     AND timestamp >= now - 30d
   GROUP BY DATE(timestamp)
   ```

## Backend Implementation

### Endpoint

**Route:** `GET /api/user/dashboard/stats`  
**Auth:** Session-based user authentication (`require_user`)  
**Response Schema:** `DashboardStatsOut`

### Response Schema

```python
class DashboardTotalsOut(BaseModel):
    last_24h: int = 0
    last_7d: int = 0
    last_30d: int = 0

class DashboardUniqueIssuesOut(BaseModel):
    last_24h: int = 0
    last_7d: int = 0
    last_30d: int = 0

class DashboardTrendOut(BaseModel):
    current: int = 0
    previous: int = 0
    percent_change: float = 0.0
    direction: str = "same"  # "up" | "down" | "same"

class TopErrorOut(BaseModel):
    fingerprint: str
    message: str
    count: int
    project_id: int
    project_name: str

class DashboardStatsOut(BaseModel):
    totals: DashboardTotalsOut
    unique_issues: DashboardUniqueIssuesOut
    trend_7d: DashboardTrendOut
    trend_30d: DashboardTrendOut
    top_5_errors: list[TopErrorOut]
    trend_daily: dict[str, int]  # ISO date string -> event count
```

### Implementation Details

**File:** `src/xrayradar_server/routers/user/dashboard.py`

- Filters events by user's projects and error level only
- Uses timezone-aware datetime calculations for accurate time windows
- Computes trend percentages with special handling for zero previous counts
- Fetches latest error message for each top error fingerprint
- Returns daily counts as a dict for efficient frontend chart rendering

## Frontend Implementation

### Component

**File:** `xrayradar-web/src/pages/DashboardHome.jsx`

### Features

1. **Loading State** — Animated dots and loading message
2. **Error Handling** — Displays error message with retry button
3. **Summary Cards** — Four cards showing key metrics
4. **Trend Cards** — Visual indicators (↑/↓) with color coding:
   - Red for upward trend (more errors)
   - Green for downward trend (fewer errors)
   - Gray for no change
5. **Event Frequency Chart** — Reuses `EventFrequencyChart` component
6. **Top 5 Errors List** — Clickable items linking to issue detail pages
7. **Empty State** — Helpful message when no events exist (24h/7d/30d)

### Chart Data Processing

The frontend transforms the `trend_daily` dict into an array suitable for the chart:

1. Generate last 30 calendar days (including today)
2. Map each date to event count from `trend_daily` (default 0 if missing)
3. Calculate `maxCount` for chart scaling
4. Pass to `EventFrequencyChart` component

### Styling

**File:** `xrayradar-web/src/styles.css`

- `.dashboardStatsGrid` — 4-column responsive grid for summary cards
- `.dashboardTrendRow` — Flex container for trend cards
- `.dashboardTrendValue--up` — Red color for increasing errors
- `.dashboardTrendValue--down` — Green color for decreasing errors
- `.dashboardTopErrorsList` — Styled list with hover effects
- `.dashboardChartCard` — Container for 30-day frequency chart

## User Flow

```
1. User logs in and lands on dashboard home page
   │
   ▼
2. Frontend calls GET /api/user/dashboard/stats
   │
   ▼
3. Backend queries events table across all user projects
   │
   ▼
4. Backend returns aggregated statistics (totals, trends, top errors, daily data)
   │
   ▼
5. Frontend renders:
   • Summary cards (24h/7d/30d totals, unique issues)
   • Trend cards with visual indicators
   • 30-day frequency bar chart
   • Top 5 errors list with clickable links
   │
   ▼
6. User clicks on a top error → Navigate to issue detail page
   OR
   User sees empty state → Navigate to projects page to get started
```

## Performance Considerations

- **Index Requirements:**
  - `events(project_id, level, timestamp)` — For time-based filtering
  - `events(project_id, fingerprint, timestamp)` — For unique counts and top errors
  - `events(timestamp)` — For date aggregation

- **Query Optimization:**
  - All queries filter by `level = 'error'` to reduce dataset
  - Separate queries for different time windows (avoid complex subqueries)
  - Top 5 limit prevents unbounded result sets
  - Daily aggregation uses efficient `DATE()` function

- **Frontend Optimization:**
  - `useMemo` for chart data transformation (avoids recalculation on every render)
  - `useCallback` for load function (stable reference for useEffect)
  - Conditional rendering prevents unnecessary DOM updates

## Testing

### Backend Tests

**File:** `tests/user/test_dashboard.py`

Tests cover:
- Empty state (no events)
- Single project with events
- Multiple projects aggregation
- Trend calculations (up/down/same)
- Top errors ordering and message extraction
- Daily frequency aggregation
- Time window boundaries (24h/7d/30d)
- Authentication requirements

### Frontend Tests

**File:** `xrayradar-web/src/pages/DashboardHome.test.jsx`

Tests cover:
- Loading state display
- Error state with retry button
- Summary cards rendering
- Trend indicators (up/down/same) with correct styling
- Event frequency chart rendering
- Top 5 errors list with correct links
- Empty state message and "Go to Projects" button
- Chart data transformation logic

## Future Enhancements

1. **Customizable Time Ranges** — Allow users to select custom date ranges
2. **Error Level Filtering** — Toggle between error/warning/info levels
3. **Project Filtering** — View stats for specific projects only
4. **Export Functionality** — Download stats as CSV or PDF
5. **Real-time Updates** — WebSocket or polling for live dashboard
6. **Comparison View** — Side-by-side comparison of different time periods
7. **Alert Thresholds** — Visual indicators when error rates exceed thresholds

## Related Documentation

- [Event Ingestion](./event-ingest.md) — How events are captured and stored
- [Event Frequency](./event-frequency.md) — Project-level frequency charts
- [Usage Limiting](./usage-limiting.md) — Event storage limits by plan tier
- [Email Alerts](./email-alerts.md) — Error notifications via email
