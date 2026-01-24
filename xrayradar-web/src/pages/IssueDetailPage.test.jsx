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
})
