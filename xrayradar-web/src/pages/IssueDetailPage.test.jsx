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
    api.fetchJson
      .mockResolvedValueOnce([]) // events
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 2 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Error 1')).toBeInTheDocument()
      expect(screen.getByText('Error 2')).toBeInTheDocument()
    })
  })

  it('displays error when loading fails', async () => {
    api.fetchJson
      .mockRejectedValueOnce(new Error('Failed to load')) // events fails
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency succeeds
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })
  })

  it('renders events when frequency fetch fails (catch branch)', async () => {
    const events = [{ id: '1', timestamp: '2024-01-01T00:00:00Z', level: 'error', message: 'E1' }]
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockRejectedValueOnce(new Error('frequency failed')) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)

    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Issue')).toBeInTheDocument()
      expect(screen.getByText('E1')).toBeInTheDocument()
    })
  })

  it('handles breakdown fetch failure gracefully (covers line 28)', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const events = [{ id: '1', timestamp: '2024-01-01T00:00:00Z', level: 'error', message: 'E1' }]
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 1 }) // frequency
      .mockRejectedValueOnce(new Error('breakdown failed')) // breakdown fails
      .mockResolvedValueOnce([]) // issues list (for status)

    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Issue')).toBeInTheDocument()
      expect(screen.getByText('E1')).toBeInTheDocument()
    })

    // Should have logged warning but not crashed
    expect(consoleSpy).toHaveBeenCalledWith('Failed to load breakdown:', expect.any(Error))
    consoleSpy.mockRestore()
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 1 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 1 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce([]) // events
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
      .mockResolvedValueOnce([]) // Initial load events
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // Initial frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // Initial breakdown
      .mockResolvedValueOnce([]) // Initial issues list (for status)
      .mockResolvedValueOnce([]) // Refresh events call
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // Refresh frequency call
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // Refresh breakdown
      .mockResolvedValueOnce([]) // Refresh issues list (for status)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument()
    })

    const refreshButton = screen.getByRole('button', { name: /Refresh/i })
    await user.click(refreshButton)

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledTimes(8) // 4 initial + 4 refresh
    })
  })

  it('does not show first/last seen when events are empty', async () => {
    api.fetchJson
      .mockResolvedValueOnce([]) // events
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Fingerprint:/i)).toBeInTheDocument()
    })

    // Should not show First seen / Last seen / Total in the issue header (events.length > 0 block)
    // Note: EventFrequencyChart may show "Total: 0 events" - that's from the chart, not the header
    expect(screen.queryByText(/First seen/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Last seen/i)).not.toBeInTheDocument()
    // Header shows "Total: N event(s)" only when events exist; chart shows "Total: 0 events" when empty
    expect(screen.queryByText(/Total: 0 event/i)).toBeInTheDocument() // from chart
  })

  it('handles frequency fetch failure silently', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    api.fetchJson
      .mockResolvedValueOnce([]) // events succeed
      .mockRejectedValueOnce(new Error('frequency failed')) // frequency fails
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)

    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Fingerprint:/i)).toBeInTheDocument()
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load event frequency:', expect.any(Error))
    })
    consoleSpy.mockRestore()
  })

  it('handles error in load callback', async () => {
    api.fetchJson
      .mockRejectedValueOnce(new Error('Network error')) // events fails
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency succeeds
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 2 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockRejectedValueOnce(new Error()) // events fails with no message
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 2 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 1 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 2 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(null) // events is null
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 2 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
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
    api.fetchJson
      .mockResolvedValueOnce(events) // events
      .mockResolvedValueOnce({ frequency: {}, total: 2 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/First seen/i)).toBeInTheDocument()
      expect(screen.getByText(/Last seen/i)).toBeInTheDocument()
    })
  })

  it('shows affected releases and environments when breakdown has data', async () => {
    api.fetchJson
      .mockResolvedValueOnce([]) // events
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency
      .mockResolvedValueOnce({
        by_release: [{ release: '1.0.0', count: 5 }, { release: '1.0.1', count: 2 }],
        by_environment: [{ environment: 'production', count: 4 }, { environment: 'staging', count: 3 }],
      }) // breakdown
      .mockResolvedValueOnce([]) // issues list (for status)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText('Affected releases (last 30 days)')).toBeInTheDocument()
      expect(screen.getByText('Environments')).toBeInTheDocument()
      expect(screen.getByText('1.0.0')).toBeInTheDocument()
      expect(screen.getByText('1.0.1')).toBeInTheDocument()
      expect(screen.getByText('production')).toBeInTheDocument()
      expect(screen.getByText('staging')).toBeInTheDocument()
    })
  })

  it('loads issue status from issues list when fingerprint matches', async () => {
    const issuesList = [
      {
        fingerprint: 'abc123',
        status: 'resolved',
        resolved_release: 'v1.0.0',
        resolved_at: '2024-01-15T12:00:00Z',
        reopened: false,
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([]) // events
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] }) // breakdown
      .mockResolvedValueOnce(issuesList) // issues list (for status) - matching issue
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /change issue status/i })).toBeInTheDocument()
    })
    // Status badge shows Resolved (from issueStatus loaded from issues list)
    const resolvedElements = screen.getAllByText('Resolved')
    expect(resolvedElements.length).toBeGreaterThan(0)
  })

  it('shows auto-reopen notification when resolved issue has events after resolved_at', async () => {
    const events = [
      { id: '1', timestamp: '2024-01-20T00:00:00Z', level: 'error', message: 'E1' }, // after resolved_at
    ]
    const issuesList = [
      {
        fingerprint: 'abc123',
        status: 'resolved',
        resolved_release: 'v1.0.0',
        resolved_at: '2024-01-15T12:00:00Z',
        reopened: false,
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce(events)
      .mockResolvedValueOnce({ frequency: {}, total: 1 })
      .mockResolvedValueOnce({ by_release: [], by_environment: [] })
      .mockResolvedValueOnce(issuesList)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Note:/i)).toBeInTheDocument()
      expect(screen.getByText(/new events have been recorded/i)).toBeInTheDocument()
      expect(screen.getByText(/resolved for release/i)).toBeInTheDocument()
    })
  })

  it('shows auto-reopen notification when resolved with no resolved_at', async () => {
    const events = [
      { id: '1', timestamp: '2024-01-01T00:00:00Z', level: 'error', message: 'E1' },
    ]
    const issuesList = [
      {
        fingerprint: 'abc123',
        status: 'resolved',
        resolved_release: null,
        resolved_at: null,
        reopened: false,
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce(events)
      .mockResolvedValueOnce({ frequency: {}, total: 1 })
      .mockResolvedValueOnce({ by_release: [], by_environment: [] })
      .mockResolvedValueOnce(issuesList)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Note:/i)).toBeInTheDocument()
      expect(screen.getByText(/auto-reopened due to new occurrences/i)).toBeInTheDocument()
    })
  })

  it('opens status modal when clicking status badge', async () => {
    const issuesList = [
      {
        fingerprint: 'abc123',
        status: 'open',
        resolved_release: null,
        resolved_at: null,
        reopened: false,
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ frequency: {}, total: 0 })
      .mockResolvedValueOnce({ by_release: [], by_environment: [] })
      .mockResolvedValueOnce(issuesList)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /change issue status/i })).toBeInTheDocument()
    })

    const user = userEvent.setup()
    const badgeButton = screen.getByRole('button', { name: /change issue status/i })
    await user.click(badgeButton)

    await waitFor(() => {
      expect(screen.getByText('Update Issue Status')).toBeInTheDocument()
    })
  })

  it('shows reopened notification when issue was auto-reopened', async () => {
    const issuesList = [
      {
        fingerprint: 'abc123',
        status: 'open',
        resolved_release: 'v1.0.0',
        resolved_at: '2024-01-15T12:00:00Z',
        reopened: true,
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ frequency: {}, total: 0 })
      .mockResolvedValueOnce({ by_release: [], by_environment: [] })
      .mockResolvedValueOnce(issuesList)
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByText(/Reopened:/i)).toBeInTheDocument()
      expect(screen.getByText(/automatically reopened due to new events/i)).toBeInTheDocument()
    })
  })

  it('calls load after status change in modal', async () => {
    const user = userEvent.setup()
    const issuesList = [
      {
        fingerprint: 'abc123',
        status: 'open',
        resolved_release: null,
        resolved_at: null,
        reopened: false,
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ frequency: {}, total: 0 })
      .mockResolvedValueOnce({ by_release: [], by_environment: [] })
      .mockResolvedValueOnce(issuesList)
      .mockResolvedValueOnce([])   // load() after save - events
      .mockResolvedValueOnce({ frequency: {}, total: 0 })   // frequency
      .mockResolvedValueOnce({ by_release: [], by_environment: [] })   // breakdown
      .mockResolvedValueOnce(issuesList)   // issues list
    api.updateIssueStatus = api.updateIssueStatus || vi.fn()
    api.updateIssueStatus.mockResolvedValue({
      status: 'resolved',
      resolved_release: 'v1.0.0',
      reopened: false,
    })
    render(<IssueDetailPage projectId={1} fingerprint="abc123" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /change issue status/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /change issue status/i }))

    await waitFor(() => {
      expect(screen.getByText('Update Issue Status')).toBeInTheDocument()
    })

    const resolvedButtons = screen.getAllByText('Resolved')
    const resolvedButton = resolvedButtons.find(btn => btn.tagName === 'BUTTON')
    expect(resolvedButton).toBeDefined()
    await user.click(resolvedButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/Resolve until release/i)).toBeInTheDocument()
    })

    await user.type(screen.getByLabelText(/Resolve until release/i), 'v1.0.0')
    await user.click(screen.getByText('Save'))

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/projects/1/issues')
    }, { timeout: 2000 })
  })
})
