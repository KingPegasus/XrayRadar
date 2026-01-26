import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProjectsPage } from './ProjectsPage'
import * as api from '../utils/api'
import * as navigation from '../utils/navigation'

vi.mock('../utils/api')
vi.mock('../utils/navigation')

describe('ProjectsPage', () => {
  const me = { email: 'test@example.com' }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders projects page', () => {
    api.fetchJson.mockResolvedValueOnce([])
    render(<ProjectsPage me={me} />)
    expect(screen.getByText('Projects')).toBeInTheDocument()
    expect(screen.getByText(/Signed in as/i)).toBeInTheDocument()
  })

  it('loads and displays projects', async () => {
    const projects = [
      { id: 1, name: 'Project 1' },
      { id: 2, name: 'Project 2' },
    ]
    api.fetchJson.mockResolvedValueOnce(projects)
    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Project 1')).toBeInTheDocument()
      expect(screen.getByText('Project 2')).toBeInTheDocument()
    })
  })

  it('displays error when loading fails', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error('Failed to load'))
    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    })
  })

  it('displays error when loading fails with no message', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error())
    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load projects/i)).toBeInTheDocument()
    })
  })

  it('creates a new project', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // Initial load
      .mockResolvedValueOnce({ id: 1, name: 'New Project' }) // Create
      .mockResolvedValueOnce([{ id: 1, name: 'New Project' }]) // Reload

    render(<ProjectsPage me={me} />)

    const input = screen.getByPlaceholderText(/New project name/i)
    const button = screen.getByRole('button', { name: /Create project/i })

    await user.type(input, 'New Project')
    await user.click(button)

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'New Project' }),
      })
    })
  })

  it('validates project name is required', async () => {
    const user = userEvent.setup()
    api.fetchJson.mockResolvedValueOnce([])
    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/New project name/i)).toBeInTheDocument()
    })

    const button = screen.getByRole('button', { name: /Create project/i })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText(/Project name is required/i)).toBeInTheDocument()
    })
  })

  it('navigates to project on click', async () => {
    const user = userEvent.setup()
    const projects = [{ id: 1, name: 'Project 1' }]
    api.fetchJson.mockResolvedValueOnce(projects)
    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Project 1')).toBeInTheDocument()
    })

    const projectCard = screen.getByText('Project 1').closest('.card')
    await user.click(projectCard)

    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard/projects/1')
  })

  it('handles error when creating project fails', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // Initial load
      .mockRejectedValueOnce(new Error('Failed to create project')) // Create fails

    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/New project name/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/New project name/i)
    const button = screen.getByRole('button', { name: /Create project/i })

    await user.type(input, 'New Project')
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText(/Failed to create project/i)).toBeInTheDocument()
    })
  })

  it('prevents double submission when busy', async () => {
    const user = userEvent.setup()
    let createCallCount = 0
    api.fetchJson
      .mockResolvedValueOnce([]) // Initial load
      .mockImplementation((url, opts) => {
        if (opts?.method === 'POST') {
          createCallCount++
          return new Promise(() => {}) // Never resolves to keep busy=true
        }
        return Promise.resolve([])
      })

    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/New project name/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/New project name/i)
    const button = screen.getByRole('button', { name: /Create project/i })

    await user.type(input, 'New Project')
    
    // First click sets busy to true
    await user.click(button)
    
    // Immediately click again - should hit early return at line 26 (if (busy) return)
    // This tests the branch where busy is true
    await user.click(button)

    // Should only call create API once due to early return when busy is true (line 26)
    expect(createCallCount).toBe(1)
  })

  it('returns early when busy is true', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // Initial load
      .mockImplementation(() => new Promise(() => {})) // Never resolves

    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/New project name/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/New project name/i)
    const button = screen.getByRole('button', { name: /Create project/i })

    await user.type(input, 'New Project')
    
    // First click sets busy to true
    await user.click(button)
    
    // Immediately click again - should return early at line 26
    await user.click(button)

    // Should only call fetchJson once (initial load + create)
    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledTimes(2)
    })
  })

  it('handles error when creating project fails with no message', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // Initial load
      .mockRejectedValueOnce(new Error()) // Create fails with no message

    render(<ProjectsPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/New project name/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/New project name/i)
    const button = screen.getByRole('button', { name: /Create project/i })

    await user.type(input, 'New Project')
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText(/Failed to create project/i)).toBeInTheDocument()
    })
  })
})
