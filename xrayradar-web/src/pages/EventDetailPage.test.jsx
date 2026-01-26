import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EventDetailPage } from './EventDetailPage'
import * as api from '../utils/api'
import * as navigation from '../utils/navigation'

vi.mock('../utils/api')
vi.mock('../utils/navigation')
vi.mock('../components/EventDetailView', () => ({
  EventDetailView: ({ event }) => <div>EventDetailView: {event?.id}</div>,
}))

describe('EventDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state', () => {
    api.fetchJson.mockImplementation(() => new Promise(() => {})) // Never resolves
    render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)
    expect(screen.getByText(/Loading event/i)).toBeInTheDocument()
  })

  it('loads and displays event', async () => {
    const event = {
      id: 'event1',
      timestamp: '2024-01-01T00:00:00Z',
      message: 'Test error',
      payload: {},
    }
    api.fetchJson.mockResolvedValueOnce(event)
    render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)

    await waitFor(() => {
      expect(screen.getByText('Event Details')).toBeInTheDocument()
    }, { timeout: 3000 })

    await waitFor(() => {
      expect(screen.getByText(/EventDetailView: event1/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays error when loading fails', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error('Failed to load'))
    render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Back to Issue/i })).toBeInTheDocument()
    })
  })

  it('displays error message when error has no message', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error())
    render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load event/i)).toBeInTheDocument()
    })
  })

  it('navigates back to issue on error', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockRejectedValueOnce(new Error('Failed to load'))
    render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Back to Issue/i })).toBeInTheDocument()
    })

    const backButton = screen.getByRole('button', { name: /Back to Issue/i })
    await user.click(backButton)

    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard/projects/1/issues/abc123')
  })

  it('navigates back to issue from header', async () => {
    const user = userEvent.setup()
    const event = {
      id: 'event1',
      timestamp: '2024-01-01T00:00:00Z',
      message: 'Test error',
      payload: {},
    }
    api.fetchJson.mockResolvedValueOnce(event)
    render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Back to Issue/i })).toBeInTheDocument()
    })

    const backButton = screen.getByRole('button', { name: /Back to Issue/i })
    await user.click(backButton)

    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard/projects/1/issues/abc123')
  })

  it('reloads when eventId changes', async () => {
    const event1 = { id: 'event1', timestamp: '2024-01-01T00:00:00Z', message: 'Error 1', payload: {} }
    const event2 = { id: 'event2', timestamp: '2024-01-02T00:00:00Z', message: 'Error 2', payload: {} }

    api.fetchJson
      .mockResolvedValueOnce(event1)
      .mockResolvedValueOnce(event2)

    const { rerender } = render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)

    await waitFor(() => {
      expect(screen.getByText(/EventDetailView: event1/i)).toBeInTheDocument()
    })

    rerender(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event2" />)

    await waitFor(() => {
      expect(screen.getByText(/EventDetailView: event2/i)).toBeInTheDocument()
    })
  })

  it('returns null when event is null after loading', async () => {
    api.fetchJson.mockResolvedValueOnce(null)
    const { container } = render(<EventDetailPage projectId={1} fingerprint="abc123" eventId="event1" />)

    await waitFor(() => {
      // Should not show loading or error, just return null
      expect(screen.queryByText(/Loading event/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/Event Details/i)).not.toBeInTheDocument()
    })
  })
})
