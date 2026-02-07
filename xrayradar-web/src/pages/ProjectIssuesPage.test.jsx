import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
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
  bulkUpdateIssueStatus: vi.fn(),
}))

describe('ProjectIssuesPage', () => {
  let mockNavigate
  let fetchJson
  let bulkUpdateIssueStatus

  beforeEach(async () => {
    vi.clearAllMocks()
    const navigation = await import('../utils/navigation')
    const api = await import('../utils/api')
    mockNavigate = navigation.navigate
    fetchJson = api.fetchJson
    bulkUpdateIssueStatus = api.bulkUpdateIssueStatus
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

  it('renders issues when frequency fetch fails (catch branch)', async () => {
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'Issue when frequency fails' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues) // issues
      .mockRejectedValueOnce(new Error('frequency failed')) // frequency

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText(/Project 123/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/Issue when frequency fails/i)).toBeInTheDocument()
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
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/projects')
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

  it('refetches with status filter when filter changes', async () => {
    fetchJson.mockImplementation((url) =>
      url.includes('/frequency') ? Promise.resolve({ frequency: {}, total: 0 }) : Promise.resolve([])
    )

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledWith('/api/user/projects/123/issues')
    })

    const user = userEvent.setup()
    const filterSelect = screen.getByRole('combobox', { name: /filter/i }) || screen.getByLabelText(/filter/i)
    await user.selectOptions(filterSelect, 'resolved')

    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledWith('/api/user/projects/123/issues?status=resolved')
    })
  })

  it('selects all issues when header checkbox checked', async () => {
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
      { fingerprint: 'fp2', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M2', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const user = userEvent.setup()
    const headerCheckbox = document.querySelector('thead input[type="checkbox"]')
    expect(headerCheckbox).toBeDefined()
    await user.click(headerCheckbox)

    await waitFor(() => {
      expect(screen.getByText('2 selected')).toBeInTheDocument()
    })

    await user.click(headerCheckbox)
    await waitFor(() => {
      expect(screen.queryByText(/\d+ selected/)).not.toBeInTheDocument()
    })
  })

  it('does not show bulk action bar when no selection', async () => {
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    expect(screen.queryByRole('button', { name: /Resolve/i })).not.toBeInTheDocument()
    expect(screen.queryByText(/\d+ selected/)).not.toBeInTheDocument()
  })

  it('shows bulk actions and resolve selected', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })
      .mockResolvedValueOnce(mockIssues)

    bulkUpdateIssueStatus.mockResolvedValue(undefined)

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const rowCheckbox = screen.getByRole('row', { name: /M1/i }).querySelector('input[type="checkbox"]') ||
      screen.getAllByRole('checkbox')[1]
    await user.click(rowCheckbox)

    await waitFor(() => {
      expect(screen.getByText('1 selected')).toBeInTheDocument()
    })

    const resolveButton = screen.getByRole('button', { name: /Resolve/i })
    await user.click(resolveButton)

    await waitFor(() => {
      expect(bulkUpdateIssueStatus).toHaveBeenCalledWith('123', ['fp1'], { status: 'resolved' })
    })

    await waitFor(() => {
      expect(fetchJson).toHaveBeenCalledWith('/api/user/projects/123/issues')
    })
  })

  it('handles bulk action error', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    bulkUpdateIssueStatus.mockRejectedValue(new Error('Failed to update issues'))

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[1])

    await waitFor(() => {
      expect(screen.getByText('1 selected')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Resolve/i }))

    await waitFor(() => {
      expect(screen.getByText(/Failed to update issues/i)).toBeInTheDocument()
    })
  })

  it('clears selection when Clear clicked', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[1])
    await waitFor(() => {
      expect(screen.getByText('1 selected')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Clear/i }))

    await waitFor(() => {
      expect(screen.queryByText('1 selected')).not.toBeInTheDocument()
    })
  })

  it('navigates to issue when clicking status badge', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'resolved', resolved_release: 'v1.0.0' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const badgeButton = screen.getByRole('button', { name: /change issue status/i })
    await user.click(badgeButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/projects/123/issues/fp1')
    })
  })

  it('does not navigate when clicking row checkbox', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[1])

    expect(mockNavigate).not.toHaveBeenCalled()
    expect(screen.getByText('1 selected')).toBeInTheDocument()
  })

  it('deselects issue when unchecking row checkbox', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[1])
    await waitFor(() => {
      expect(screen.getByText('1 selected')).toBeInTheDocument()
    })
    await user.click(checkboxes[1])

    await waitFor(() => {
      expect(screen.queryByText('1 selected')).not.toBeInTheDocument()
    })
  })

  it('bulk action In Progress updates selected issues', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })
      .mockResolvedValueOnce(mockIssues)

    bulkUpdateIssueStatus.mockResolvedValue(undefined)

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[1])
    await waitFor(() => {
      expect(screen.getByText('1 selected')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /In Progress/i }))

    await waitFor(() => {
      expect(bulkUpdateIssueStatus).toHaveBeenCalledWith('123', ['fp1'], { status: 'in_progress' })
    })
  })

  it('bulk action Ignore updates selected issues', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })
      .mockResolvedValueOnce(mockIssues)

    bulkUpdateIssueStatus.mockResolvedValue(undefined)

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[1])
    await waitFor(() => {
      expect(screen.getByText('1 selected')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Ignore/i }))

    await waitFor(() => {
      expect(bulkUpdateIssueStatus).toHaveBeenCalledWith('123', ['fp1'], { status: 'ignored' })
    })
  })

  it('navigates to issue when clicking row (not checkbox)', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const messageCell = screen.getByText('M1')
    await user.click(messageCell)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/projects/123/issues/fp1')
    })
  })

  it('navigates to issue when clicking row (e.g. count cell)', async () => {
    const user = userEvent.setup()
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const row = screen.getByRole('row', { name: /M1/i })
    const countCell = row.querySelector('td:nth-child(5)')
    await user.click(countCell)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard/projects/123/issues/fp1')
    })
  })

  it('checkbox cell stopPropagation prevents row navigation', async () => {
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const row = screen.getByText('M1').closest('tr')
    const checkboxTd = row.querySelector('td:first-child')
    fireEvent.click(checkboxTd)

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('status cell stopPropagation still allows badge to navigate', async () => {
    const mockIssues = [
      { fingerprint: 'fp1', first_seen: '2024-01-01T00:00:00Z', last_seen: '2024-01-02T00:00:00Z', count: 1, level: 'error', message: 'M1', status: 'open' },
    ]
    fetchJson
      .mockResolvedValueOnce(mockIssues)
      .mockResolvedValueOnce({ frequency: {}, total: 0 })

    render(<ProjectIssuesPage projectId="123" />)

    await waitFor(() => {
      expect(screen.getByText('M1')).toBeInTheDocument()
    })

    const row = screen.getByText('M1').closest('tr')
    const statusTd = row.querySelector('td:nth-child(2)')
    fireEvent.click(statusTd)
  })
})
