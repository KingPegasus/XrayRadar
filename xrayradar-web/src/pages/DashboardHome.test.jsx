import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DashboardHome } from './DashboardHome'
import { fetchJson } from '../utils/api'

vi.mock('../utils/api')
vi.mock('../utils/navigation', () => ({ navigate: vi.fn() }))
vi.mock('../components/Link', () => ({ Link: ({ children, to }) => <a href={to}>{children}</a> }))
vi.mock('../components/EventFrequencyChart', () => ({ EventFrequencyChart: () => <div>EventFrequencyChart</div> }))

const emptyStats = {
  totals: { last_24h: 0, last_7d: 0, last_30d: 0 },
  unique_issues: { last_24h: 0, last_7d: 0, last_30d: 0 },
  trend_7d: { current: 0, previous: 0, percent_change: 0, direction: 'same' },
  trend_30d: { current: 0, previous: 0, percent_change: 0, direction: 'same' },
  top_5_errors: [],
  trend_daily: {},
}

describe('DashboardHome', () => {
  beforeEach(() => {
    vi.mocked(fetchJson).mockResolvedValue(emptyStats)
  })

  it('renders dashboard title', async () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    expect(screen.getByText('Error overview')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByText(/Loading stats/i)).not.toBeInTheDocument()
    })
  })

  it('displays user email', async () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    expect(screen.getByText(/Signed in as/i)).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledWith('/api/user/dashboard/stats')
    })
  })

  it('shows loading then stats when fetch succeeds', async () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    expect(screen.getByText(/Loading stats/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByText(/Loading stats/i)).not.toBeInTheDocument()
    })
    expect(screen.getByText(/Errors \(24h\)/i)).toBeInTheDocument()
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(1)
  })

  it('renders getting started section when no events (empty stats)', async () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    await waitFor(() => {
      expect(screen.getByText('Getting started')).toBeInTheDocument()
      expect(screen.getByText(/Set up your first project in three steps/i)).toBeInTheDocument()
      expect(screen.getByText(/Create a project in Projects/i)).toBeInTheDocument()
      expect(screen.getByText(/Request a token from an admin in Tokens/i)).toBeInTheDocument()
      expect(screen.getByText(/Assign token access to your project from Tokens/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Create project/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Request and assign token/i })).toBeInTheDocument()
    })
  })

  it('shows error and retry when fetch fails', async () => {
    vi.mocked(fetchJson).mockRejectedValueOnce(new Error('Network error'))
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
    })
    vi.mocked(fetchJson).mockResolvedValueOnce(emptyStats)
    await userEvent.click(screen.getByRole('button', { name: /Retry/i }))
    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledTimes(2)
    })
  })

  it('shows top 5 errors when stats include them', async () => {
    vi.mocked(fetchJson).mockResolvedValueOnce({
      ...emptyStats,
      totals: { last_24h: 5, last_7d: 10, last_30d: 20 },
      top_5_errors: [
        { fingerprint: 'fp1', message: 'Error A', count: 3, project_id: 1, project_name: 'P1' },
      ],
    })
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    await waitFor(() => {
      expect(screen.getByText('Error A')).toBeInTheDocument()
      expect(screen.getByText(/P1/i)).toBeInTheDocument()
      expect(screen.getByText(/3 event/i)).toBeInTheDocument()
    })
  })

  it('handles missing me prop', async () => {
    render(<DashboardHome me={null} />)
    expect(screen.getByText('Error overview')).toBeInTheDocument()
    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledWith('/api/user/dashboard/stats')
    })
  })

  it('shows event frequency chart when trend_daily has data', async () => {
    const today = new Date().toISOString().split('T')[0]
    vi.mocked(fetchJson).mockResolvedValueOnce({
      ...emptyStats,
      totals: { last_24h: 1, last_7d: 1, last_30d: 1 },
      trend_daily: { [today]: 1 },
    })
    render(<DashboardHome me={{ email: 'u@x.com' }} />)
    await waitFor(() => {
      expect(screen.getByText(/Event frequency \(30d\)/i)).toBeInTheDocument()
      expect(screen.getByText(/EventFrequencyChart/i)).toBeInTheDocument()
    })
  })

  it('shows top error with single event and no message', async () => {
    vi.mocked(fetchJson).mockResolvedValueOnce({
      ...emptyStats,
      totals: { last_24h: 1, last_7d: 1, last_30d: 1 },
      top_5_errors: [
        { fingerprint: 'fp1', message: '', count: 1, project_id: 1, project_name: 'P1' },
      ],
    })
    render(<DashboardHome me={{ email: 'u@x.com' }} />)
    await waitFor(() => {
      expect(screen.getByText('(no message)')).toBeInTheDocument()
      expect(screen.getByText(/1 event\b/)).toBeInTheDocument()
    })
  })

  it('shows trend down for 7d and 30d', async () => {
    vi.mocked(fetchJson).mockResolvedValueOnce({
      ...emptyStats,
      trend_7d: { current: 80, previous: 100, percent_change: -20, direction: 'down' },
      trend_30d: { current: 90, previous: 100, percent_change: -10, direction: 'down' },
    })
    render(<DashboardHome me={{ email: 'u@x.com' }} />)
    await waitFor(() => {
      expect(screen.getByText(/↓ -20%/)).toBeInTheDocument()
      expect(screen.getByText(/↓ -10%/)).toBeInTheDocument()
    })
  })

  it('getting started links point to projects and tokens', async () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    await waitFor(() => {
      expect(screen.getByText('Getting started')).toBeInTheDocument()
    })
    const createLink = screen.getByRole('link', { name: /Create project/i })
    const tokenLink = screen.getByRole('link', { name: /Request and assign token/i })
    expect(createLink).toHaveAttribute('href', '/dashboard/projects')
    expect(tokenLink).toHaveAttribute('href', '/dashboard/tokens')
  })

  it('shows trend same when direction is same', async () => {
    vi.mocked(fetchJson).mockResolvedValueOnce({
      ...emptyStats,
      trend_7d: { current: 100, previous: 100, percent_change: 0, direction: 'same' },
      trend_30d: { current: 100, previous: 100, percent_change: 0, direction: 'same' },
    })
    render(<DashboardHome me={{ email: 'u@x.com' }} />)
    await waitFor(() => {
      expect(screen.getByText(/7d trend/i)).toBeInTheDocument()
      expect(screen.getByText(/30d trend/i)).toBeInTheDocument()
    })
    const zeroPct = screen.getAllByText(/0%/)
    expect(zeroPct.length).toBeGreaterThanOrEqual(1)
  })

  it('shows trend up with positive percent change', async () => {
    vi.mocked(fetchJson).mockResolvedValueOnce({
      ...emptyStats,
      trend_7d: { current: 120, previous: 100, percent_change: 20, direction: 'up' },
      trend_30d: { current: 110, previous: 100, percent_change: 10, direction: 'up' },
    })
    render(<DashboardHome me={{ email: 'u@x.com' }} />)
    await waitFor(() => {
      expect(screen.getByText(/7d trend/i)).toBeInTheDocument()
      expect(screen.getByText(/30d trend/i)).toBeInTheDocument()
    })
    const trendSection = screen.getByText(/7d trend/i).closest('.dashboardTrendRow')
    expect(trendSection).toHaveTextContent('20')
    expect(trendSection).toHaveTextContent('10')
    expect(trendSection).toHaveTextContent('↑')
  })
})
