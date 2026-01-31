import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProjectIssuesPage } from './ProjectIssuesPage'

// Mock fetch globally
global.fetch = vi.fn()

// Mock navigation
vi.mock('../utils/navigation', () => ({
  navigate: vi.fn(),
}))

// Mock api
vi.mock('../utils/api', () => ({
  fetchJson: vi.fn(),
}))

describe('ProjectIssuesPage', () => {
  let mockNavigate
  let fetchJson

  beforeEach(async () => {
    vi.clearAllMocks()
    const navigation = await import('../utils/navigation')
    const api = await import('../utils/api')
    mockNavigate = navigation.navigate
    fetchJson = api.fetchJson
  })

  it('renders project issues page', async () => {
    const mockIssues = [
      {
        fingerprint: 'fp1',
        first_seen: '2024-01-01T00:00:00Z',
        last_seen: '2024-01-02T00:00:00Z',
        count: 5,
        level: 'error',
        message: 'Test error message',
      },
    ]

    fetchJson
      .mockResolvedValueOnce(mockIssues) // issues
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // events/frequency

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Project 123/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/Issues are grouped by fingerprint/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
  })

  it('displays issues in table', async () => {
    const mockIssues = [
      {
        fingerprint: 'fp1',
        first_seen: '2024-01-01T10:00:00Z',
        last_seen: '2024-01-02T15:30:00Z',
        count: 5,
        level: 'error',
        message: 'Test error message',
      },
      {
        fingerprint: 'fp2',
        first_seen: '2024-01-03T08:00:00Z',
        last_seen: '2024-01-03T09:00:00Z',
        count: 2,
        level: 'warning',
        message: 'Another error',
      },
    ]

    fetchJson
      .mockResolvedValueOnce(mockIssues) // issues
      .mockResolvedValueOnce({ frequency: {}, total: 5 }) // events/frequency

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Test error message/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/Another error/i)).toBeInTheDocument()
    // Check that table contains both issues with their counts
    const table = screen.getByRole('table')
    expect(table.textContent).toContain('5')
    expect(table.textContent).toContain('2')
    expect(table.textContent).toContain('error')
    expect(table.textContent).toContain('warning')
  })

  it('handles empty issues list', async () => {
    fetchJson
      .mockResolvedValueOnce([]) // issues
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // events/frequency

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Project 123/i)).toBeInTheDocument()
    })

    // Table headers should still be present
    expect(screen.getByText(/First seen/i)).toBeInTheDocument()
    expect(screen.getByText(/Last seen/i)).toBeInTheDocument()
    expect(screen.getByText(/Count/i)).toBeInTheDocument()
    expect(screen.getByText(/Level/i)).toBeInTheDocument()
    expect(screen.getByText(/Message/i)).toBeInTheDocument()
  })

  it('handles null response from API', async () => {
    fetchJson
      .mockResolvedValueOnce(null) // issues
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // events/frequency

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Project 123/i)).toBeInTheDocument()
    })

    // Should handle null by using empty array fallback
    // Table should still render with headers
    expect(screen.getByText(/First seen/i)).toBeInTheDocument()
  })

  it('handles fetch error', async () => {
    fetchJson.mockImplementation((url) => {
      if (url.includes('/issues') && !url.includes('/frequency')) {
        return Promise.reject(new Error('Failed to load issues'))
      }
      return Promise.resolve({ frequency: {}, total: 0 })
    })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load issues/i)).toBeInTheDocument()
    })
  })

  it('handles fetch error without message', async () => {
    fetchJson.mockImplementation((url) => {
      if (url.includes('/issues') && !url.includes('/frequency')) {
        return Promise.reject(new Error())
      }
      return Promise.resolve({ frequency: {}, total: 0 })
    })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load issues/i)).toBeInTheDocument()
    })
  })

  it('navigates to issue detail on row click', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      {
        fingerprint: 'fp1',
        first_seen: '2024-01-01T00:00:00Z',
        last_seen: '2024-01-02T00:00:00Z',
        count: 5,
        level: 'error',
        message: 'Test error message',
      },
    ]

    fetchJson
      .mockResolvedValueOnce(mockIssues) // issues
      .mockResolvedValueOnce({ frequency: {}, total: 5 }) // events/frequency

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Test error message/i)).toBeInTheDocument()
    })

    const row = screen.getByText(/Test error message/i).closest('tr')
    await user.click(row)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/projects/123/issues/fp1')
    })
  })

  it('navigates back to dashboard', async () => {
    const user = userEvent.setup()
    fetchJson
      .mockResolvedValueOnce([]) // issues
      .mockResolvedValueOnce({ frequency: {}, total: 0 }) // events/frequency

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
    })

    const backButton = screen.getByRole('button', { name: /Back/i })
    await user.click(backButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('handles frequency fetch failure silently', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    fetchJson
      .mockResolvedValueOnce([]) // issues succeed
      .mockRejectedValueOnce(new Error('frequency failed')) // frequency fails

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Project 123/i)).toBeInTheDocument()
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load event frequency:', expect.any(Error))
    })
    consoleSpy.mockRestore()
  })

  it('refetches when projectId changes', async () => {
    fetchJson.mockImplementation((url) =>
      url.includes('/frequency') ? Promise.resolve({ frequency: {}, total: 0 }) : Promise.resolve([])
    )
    const { rerender } = render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledWith('/api/user/projects/123/issues')
    })

    vi.clearAllMocks()
    fetchJson.mockImplementation((url) =>
      url.includes('/frequency') ? Promise.resolve({ frequency: {}, total: 0 }) : Promise.resolve([])
    )
    rerender(<ProjectIssuesPage projectId="456" />)

    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledWith('/api/user/projects/456/issues')
    })
  })

  it('clears error when projectId changes', async () => {
    fetchJson.mockImplementation((url) => {
      if (url.includes('/projects/123/issues') && !url.includes('/frequency')) {
        return Promise.reject(new Error('Failed to load'))
      }
      return Promise.resolve(url.includes('/frequency') ? { frequency: {}, total: 0 } : [])
    })

    const { rerender } = render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })

    vi.clearAllMocks()
    fetchJson.mockImplementation((url) =>
      url.includes('/frequency') ? Promise.resolve({ frequency: {}, total: 0 }) : Promise.resolve([])
    )
    rerender(<ProjectIssuesPage projectId="456" />)

    await waitFor(() => {
      expect(screen.queryByText(/Failed to load/i)).not.toBeInTheDocument()
    })
  })
})
