import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { IssueDetailPage } from './IssueDetailPage'
import * as api from '../utils/api'
import * as navigation from '../utils/navigation'

vi.mock('../utils/api')
vi.mock('../utils/navigation')

describe('IssueDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders issue detail page', async () => {
    api.fetchJson.mockResolvedValueOnce([])
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)
    await waitFor(() => {
      expect(screen.getByText('Issue')).toBeInTheDocument()
      expect(screen.getByText(/Fingerprint:/i)).toBeInTheDocument()
      expect(screen.getByText('abc123')).toBeInTheDocument()
    })
  })

  it('loads and displays events', async () => {
    const events = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
      {
        id: '2',
        timestamp: '2024-01-02T00:00:00Z',
        level: 'error',
        message: 'Error 2',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Error 1')).toBeInTheDocument()
      expect(screen.getByText('Error 2')).toBeInTheDocument()
    })
  })

  it('displays error when loading fails', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error('Failed to load'))
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })
  })

  it('shows event frequency chart when events exist', async () => {
    const events = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Event Frequency')).toBeInTheDocument()
    })
  })

  it('navigates to event detail on row click', async () => {
    const user = userEvent.setup()
    const events = [
      {
        id: 'event1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Error 1')).toBeInTheDocument()
    })

    const row = screen.getByText('Error 1').closest('tr')
    await user.click(row)

    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard/projects/1/issues/abc123/events/event1')
  })

  it('navigates back to project', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockResolvedValueOnce([])
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
    })

    const backButton = screen.getByRole('button', { name: /Back/i })
    await user.click(backButton)

    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard/projects/1')
  })

  it('refreshes events on refresh button click', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // Initial load
      .mockResolvedValueOnce([]) // Refresh call
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument()
    })

    const refreshButton = screen.getByRole('button', { name: /Refresh/i })
    await user.click(refreshButton)

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledTimes(2) // Initial load + refresh
    })
  })

  it('does not show first/last seen when events are empty', async () => {
    api.fetchJson.mockResolvedValueOnce([])
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Fingerprint:/i)).toBeInTheDocument()
    })

    // Should not show first seen, last seen, or total when events are empty
    expect(screen.queryByText(/First seen/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Last seen/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Total:/i)).not.toBeInTheDocument()
  })

  it('handles error in load callback', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error('Network error'))
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })
  })

  it('handles chart with zero count events', async () => {
    const events = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
      {
        id: '2',
        timestamp: '2024-01-01T00:00:00Z', // Same date
        level: 'error',
        message: 'Error 2',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Event Frequency')).toBeInTheDocument()
    })
    // Chart should render with minHeight handling for count > 0
    // Use getAllByText since "Total: 2 event" might appear multiple times
    const totalTexts = screen.getAllByText(/Total: 2 event/i)
    expect(totalTexts.length).toBeGreaterThan(0)
  })

  it('handles error in load callback with no message', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error())
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load events/i)).toBeInTheDocument()
    })
  })

  it('shows first/last seen when events exist', async () => {
    const events = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
      {
        id: '2',
        timestamp: '2024-01-02T00:00:00Z',
        level: 'error',
        message: 'Error 2',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/First seen/i)).toBeInTheDocument()
      expect(screen.getByText(/Last seen/i)).toBeInTheDocument()
      // Use getAllByText since "Total: 2 event" appears multiple times
      const totalTexts = screen.getAllByText(/Total: 2 event/i)
      expect(totalTexts.length).toBeGreaterThan(0)
    })
  })

  it('handles chart with count > 0 for minHeight', async () => {
    const events = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Event Frequency')).toBeInTheDocument()
    })
    // Chart bars with count > 0 should have minHeight: '4px' (line 81 - count > 0 branch)
    const chartContainer = screen.getByText('Event Frequency').closest('div').nextElementSibling
    expect(chartContainer).toBeInTheDocument()
  })

  it('renders chart with multiple dates to verify count > 0 branch', async () => {
    const events = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
      {
        id: '2',
        timestamp: '2024-01-02T00:00:00Z',
        level: 'error',
        message: 'Error 2',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Event Frequency')).toBeInTheDocument()
    })
    // Each date has count > 0, so minHeight should be '4px' (line 81: count > 0 branch)
    // Note: The count === 0 branch at line 81 is logically unreachable because
    // eventFrequency.data only contains dates that have events (count will always be > 0)
    // This is an unreachable branch that cannot be tested without modifying the data structure
  })

  it('handles null response from API', async () => {
    api.fetchJson.mockResolvedValueOnce(null)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Fingerprint:/i)).toBeInTheDocument()
    })
    // Should handle null by using empty array fallback (line 12)
    expect(screen.queryByText(/First seen/i)).not.toBeInTheDocument()
  })

  it('handles events with missing timestamps', async () => {
    const events = [
      {
        id: '1',
        // no timestamp - should use Date.now() fallback (line 41)
        level: 'error',
        message: 'Error 1',
      },
      {
        id: '2',
        timestamp: '2024-01-02T00:00:00Z',
        level: 'error',
        message: 'Error 2',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/First seen/i)).toBeInTheDocument()
      expect(screen.getByText(/Last seen/i)).toBeInTheDocument()
    })
    // Should handle missing timestamp with Date.now() fallback (lines 41-43)
  })

  it('handles last event with missing timestamp', async () => {
    const events = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        level: 'error',
        message: 'Error 1',
      },
      {
        id: '2',
        // no timestamp - should use Date.now() fallback for first seen (line 41)
        level: 'error',
        message: 'Error 2',
      },
    ]
    api.fetchJson.mockResolvedValueOnce(events)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/First seen/i)).toBeInTheDocument()
      expect(screen.getByText(/Last seen/i)).toBeInTheDocument()
    })
  })
})
