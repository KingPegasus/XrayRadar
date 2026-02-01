import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TokensPage } from './TokensPage'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('TokensPage', () => {
  const me = { email: 'test@example.com', email_verified: true }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders tokens page', () => {
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce([]) // tokens
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)
    expect(screen.getByText('Tokens')).toBeInTheDocument()
    expect(screen.getByText(/Manage your API tokens/i)).toBeInTheDocument()
  })

  it('loads and displays tokens', async () => {
    const tokens = [
      {
        id: 1,
        name: 'Token 1',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: null,
        token: 'secret-token-123',
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce(tokens) // tokens
      .mockResolvedValueOnce([]) // project access
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Token 1')).toBeInTheDocument()
    })
  })

  it('loads and displays token requests', async () => {
    const requests = [
      {
        id: 1,
        name: 'Request 1',
        note: 'Test note',
        created_at: '2024-01-01T00:00:00Z',
        fulfilled_at: null,
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce([]) // tokens
      .mockResolvedValueOnce(requests) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Request 1')).toBeInTheDocument()
      expect(screen.getByText('Test note')).toBeInTheDocument()
    })
  })

  it('creates token request with note', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ id: 1, name: 'New Token' })
      .mockResolvedValueOnce([])

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e.g., Production API/i)).toBeInTheDocument()
    })

    await user.type(screen.getByPlaceholderText(/e.g., Production API/i), 'New Token')
    await user.type(screen.getByPlaceholderText(/Additional context for the admin/i), 'For production')
    await user.click(screen.getByRole('button', { name: /Request token/i }))

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/token-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'New Token', note: 'For production' }),
      })
    })
  })

  it('creates a token request', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce([]) // tokens
      .mockResolvedValueOnce([]) // requests
      .mockResolvedValueOnce({ id: 1, name: 'New Token' }) // create request
      .mockResolvedValueOnce([{ id: 1, name: 'New Token' }]) // reload requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e.g., Production API/i)).toBeInTheDocument()
    })

    const nameInput = screen.getByPlaceholderText(/e.g., Production API/i)
    const submitButton = screen.getByRole('button', { name: /Request token/i })

    await user.type(nameInput, 'New Token')
    await user.click(submitButton)

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/token-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'New Token', note: null }),
      })
    })
  })

  it('validates token name is required', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce([]) // tokens
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Request token/i })).toBeInTheDocument()
    })

    const submitButton = screen.getByRole('button', { name: /Request token/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Token name is required/i)).toBeInTheDocument()
    })
  })

  it('grants project access to token', async () => {
    const user = userEvent.setup()
    const tokens = [
      {
        id: 1,
        name: 'Token 1',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: null,
      },
    ]
    const projects = [{ id: 1, name: 'Project 1' }]
    api.fetchJson
      .mockResolvedValueOnce(projects) // projects
      .mockResolvedValueOnce(tokens) // tokens
      .mockResolvedValueOnce([]) // token 1 projects (no access initially)
      .mockResolvedValueOnce([]) // requests
      .mockResolvedValueOnce({}) // grant access POST
      .mockResolvedValueOnce(tokens) // reload tokens after grant
      .mockResolvedValueOnce([{ project_id: 1 }]) // reload token 1 projects after grant

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Token 1')).toBeInTheDocument()
    }, { timeout: 3000 })

    const manageButton = screen.getByRole('button', { name: /Manage project access/i })
    await user.click(manageButton)

    await waitFor(() => {
      expect(screen.getByText(/Grant access to projects/i)).toBeInTheDocument()
    }, { timeout: 3000 })

    const grantButton = screen.getByRole('button', { name: /Grant access/i })
    await user.click(grantButton)

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/tokens/1/projects/1/grant', {
        method: 'POST',
      })
    }, { timeout: 3000 })
  })

  it('displays error when loading fails', async () => {
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects') {
        return Promise.reject(new Error('Failed to load'))
      }
      return Promise.resolve([]) // tokens and requests succeed
    })

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('shows revoked tokens', async () => {
    const tokens = [
      {
        id: 1,
        name: 'Revoked Token',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: '2024-01-02T00:00:00Z',
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce(tokens) // tokens
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Revoked Token')).toBeInTheDocument()
    })
    // Check for revoked badge (more specific)
    const tokenCard = screen.getByText('Revoked Token').closest('.card')
    expect(tokenCard).toHaveTextContent(/Revoked/)
  })

  it('handles error when loading project access for token fails', async () => {
    const tokens = [
      {
        id: 1,
        name: 'Token 1',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: null,
      },
    ]
    let projectAccessCallCount = 0
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce(tokens) // tokens
      .mockImplementation((url) => {
        if (url === `/api/user/tokens/1/projects`) {
          projectAccessCallCount++
          // This rejection triggers the catch block at line 35: tp[t.id] = []
          return Promise.reject(new Error('Failed to load access'))
        }
        return Promise.resolve([]) // requests
      })

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Token 1')).toBeInTheDocument()
    })
    
    // Verify the catch block was executed (line 35: tp[t.id] = [])
    // by checking token renders without project access
    const tokenCard = screen.getByText('Token 1').closest('.card')
    expect(tokenCard).toHaveTextContent(/Project access: None/)
    
    // Verify the API was called (proving we entered the try block)
    expect(projectAccessCallCount).toBe(1)
  })

  it('handles error when loading tokens fails', async () => {
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockRejectedValueOnce(new Error('Failed to load tokens')) // tokens fails
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load tokens/i)).toBeInTheDocument()
    })
  })

  it('handles error when loading token requests fails', async () => {
    // Make projects and tokens succeed, but requests fail
    // Since all three load in parallel, we need to ensure requests is the last to complete
    api.fetchJson
      .mockImplementation((url) => {
        if (url === '/api/user/token-requests') {
          return Promise.reject(new Error('Failed to load token requests'))
        }
        return Promise.resolve([])
      })

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load token requests/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('handles error when granting access fails', async () => {
    const user = userEvent.setup()
    const tokens = [
      {
        id: 1,
        name: 'Token 1',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: null,
      },
    ]
    const projects = [{ id: 1, name: 'Project 1' }]
    let grantCallCount = 0
    api.fetchJson
      .mockImplementation((url, opts) => {
        if (url === '/api/user/projects') {
          return Promise.resolve(projects)
        }
        if (url === '/api/user/tokens') {
          return Promise.resolve(tokens)
        }
        if (url === '/api/user/tokens/1/projects') {
          return Promise.resolve([])
        }
        if (url === '/api/user/token-requests') {
          return Promise.resolve([])
        }
        if (url === '/api/user/tokens/1/projects/1/grant' && opts?.method === 'POST') {
          grantCallCount++
          if (grantCallCount === 1) {
            // First call fails
            return Promise.reject(new Error('Failed to grant access'))
          }
          // Subsequent calls (from loadTokens) succeed
          return Promise.resolve({})
        }
        return Promise.resolve([])
      })

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Token 1')).toBeInTheDocument()
    }, { timeout: 3000 })

    const manageButton = screen.getByRole('button', { name: /Manage project access/i })
    await user.click(manageButton)

    await waitFor(() => {
      expect(screen.getByText(/Grant access to projects/i)).toBeInTheDocument()
    }, { timeout: 3000 })

    const grantButton = screen.getByRole('button', { name: /Grant access/i })
    await user.click(grantButton)

    // Verify the grant API was called (this covers the error path)
    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/tokens/1/projects/1/grant', {
        method: 'POST',
      })
    })

    // Check that error is displayed (the catch block sets the error)
    await waitFor(() => {
      const errorAlert = screen.queryByRole('alert')
      expect(errorAlert).toBeInTheDocument()
      expect(errorAlert?.textContent).toContain('Failed')
    }, { timeout: 3000 })
  })

  it('handles error when creating token request fails', async () => {
    const user = userEvent.setup()
    let callCount = 0
    api.fetchJson
      .mockImplementation((url, opts) => {
        callCount++
        if (url === '/api/user/projects' || url === '/api/user/tokens' || url === '/api/user/token-requests') {
          if (callCount <= 3) {
            return Promise.resolve([])
          }
        }
        // This is the create request call
        if (opts && opts.method === 'POST' && url === '/api/user/token-requests') {
          return Promise.reject(new Error('Failed to create token request'))
        }
        // After error, loadRequests is called again
        if (callCount > 4 && url === '/api/user/token-requests' && !opts) {
          return Promise.resolve([])
        }
        return Promise.resolve([])
      })

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e.g., Production API/i)).toBeInTheDocument()
    })

    const nameInput = screen.getByPlaceholderText(/e.g., Production API/i)
    const submitButton = screen.getByRole('button', { name: /Request token/i })

    await user.type(nameInput, 'New Token')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Failed to create token request/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('handles create token request error with no message', async () => {
    const user = userEvent.setup()
    let callCount = 0
    api.fetchJson.mockImplementation((url, opts) => {
      callCount++
      if (callCount <= 3 && (url === '/api/user/projects' || url === '/api/user/tokens' || url === '/api/user/token-requests')) {
        return Promise.resolve([])
      }
      if (opts?.method === 'POST' && url === '/api/user/token-requests') {
        return Promise.reject(new Error()) // No message
      }
      if (callCount > 4 && url === '/api/user/token-requests' && !opts) {
        return Promise.resolve([])
      }
      return Promise.resolve([])
    })

    render(<TokensPage me={me} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/e.g., Production API/i)).toBeInTheDocument())

    await user.type(screen.getByPlaceholderText(/e.g., Production API/i), 'New Token')
    await user.click(screen.getByRole('button', { name: /Request token/i }))

    await waitFor(() => {
      expect(screen.getByText(/Failed to create token request/i)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('shows token with project access badges', async () => {
    const user = userEvent.setup()
    const tokens = [{ id: 1, name: 'Token 1', created_at: '2024-01-01T00:00:00Z', revoked_at: null }]
    const projects = [{ id: 1, name: 'Project 1' }]
    api.fetchJson.mockImplementation((url) => {
      if (url === '/api/user/projects') return Promise.resolve(projects)
      if (url === '/api/user/tokens') return Promise.resolve(tokens)
      if (url === '/api/user/tokens/1/projects') return Promise.resolve([{ project_id: 1 }])
      if (url === '/api/user/token-requests') return Promise.resolve([])
      return Promise.resolve([])
    })

    render(<TokensPage me={me} />)

    await waitFor(() => expect(screen.getByText('Token 1')).toBeInTheDocument())
    await waitFor(() => expect(screen.getByText(/Project access: 1 project\(s\)/i)).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Manage project access/i }))
    await waitFor(() => {
      expect(screen.getByText('Project 1')).toBeInTheDocument()
      expect(screen.getByText(/Has access/i)).toBeInTheDocument()
    })
  })

  it('shows request without note', async () => {
    const requests = [{ id: 1, name: 'Request 1', created_at: '2024-01-01T00:00:00Z', fulfilled_at: null }]
    api.fetchJson
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(requests)

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Request 1')).toBeInTheDocument()
    })
    expect(screen.queryByText(/Test note/i)).not.toBeInTheDocument()
  })

  it('handles note textarea onChange', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce([]) // tokens
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Additional context for the admin/i)).toBeInTheDocument()
    })

    const noteTextarea = screen.getByPlaceholderText(/Additional context for the admin/i)
    await user.type(noteTextarea, 'Test note')

    expect(noteTextarea).toHaveValue('Test note')
  })

  it('handles fulfilled token request', async () => {
    const requests = [
      {
        id: 1,
        name: 'Request 1',
        note: 'Test note',
        created_at: '2024-01-01T00:00:00Z',
        fulfilled_at: '2024-01-02T00:00:00Z', // Fulfilled (line 265, 268)
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce([]) // tokens
      .mockResolvedValueOnce(requests) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Request 1')).toBeInTheDocument()
    })
    // Should show "Fulfilled" badge (line 268-270) and fulfilled date (line 265)
    expect(screen.getByText('Fulfilled')).toBeInTheDocument()
    expect(screen.getByText(/Fulfilled:/i)).toBeInTheDocument()
  })

  it('handles project access when project is not found in projects list', async () => {
    const tokens = [
      {
        id: 1,
        name: 'Token 1',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: null,
      },
    ]
    const projects = [
      { id: 2, name: 'Other Project' }, // project 1 is NOT in this list
    ]
    let callCount = 0
    api.fetchJson.mockImplementation((url) => {
      callCount++
      if (url === '/api/user/projects') {
        return Promise.resolve(projects)
      }
      if (url === '/api/user/tokens') {
        return Promise.resolve(tokens)
      }
      if (url === `/api/user/tokens/1/projects`) {
        return Promise.resolve([{ project_id: 1 }]) // token 1 has access to project_id 1
      }
      if (url === '/api/user/token-requests') {
        return Promise.resolve([])
      }
      return Promise.resolve([])
    })

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Token 1')).toBeInTheDocument()
    })

    // Wait for project access to be loaded and rendered
    await waitFor(() => {
      const tokenCard = screen.getByText('Token 1').closest('.card')
      // Token has access to project 1, so should show "1 project(s)"
      expect(tokenCard).toHaveTextContent(/Project access: 1 project\(s\)/)
    }, { timeout: 3000 })

    // Token has access to project_id 1, but project with id=1 is not in projects list
    // So when mapping hasAccess, projects.find((p) => p.id === 1) returns undefined
    // Testing line 176: return proj ? (...) : null - the falsy branch (proj is undefined)
    const tokenCard = screen.getByText('Token 1').closest('.card')
    // The project name badge should NOT appear because proj is undefined (line 176 returns null)
    // Verify no project badge is rendered for project 1
    const allBadges = tokenCard?.querySelectorAll('.badge') || []
    const projectNameBadges = Array.from(allBadges).filter(badge => 
      badge.textContent === 'Other Project' || badge.textContent === 'Project 1'
    )
    // Should not have a badge for project 1 since it's not in the projects list
    // This verifies that line 176's null branch is executed when proj is undefined
    expect(projectNameBadges.length).toBe(0)
  })

  it('handles non-array tokens response', async () => {
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce({ invalid: true }) // tokens returns object, not array
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/No tokens yet/i)).toBeInTheDocument()
    })
  })

  it('shows verify email banner when not verified', async () => {
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce([]) // tokens
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={{ email: 'test@example.com', email_verified: false }} />)

    await waitFor(() => {
      expect(screen.getByText(/Verify your email to request tokens or grant project access/i)).toBeInTheDocument()
    })
  })

  it('displays token value when fulfilled', async () => {
    const tokens = [
      {
        id: 1,
        name: 'My Token',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: null,
        token: 'secret-abc-123',
      },
    ]
    api.fetchJson
      .mockResolvedValueOnce([]) // projects
      .mockResolvedValueOnce(tokens) // tokens
      .mockResolvedValueOnce([]) // token projects
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('secret-abc-123')).toBeInTheDocument()
    })
  })

  it('shows no tokens when tokens is empty array', async () => {
    api.fetchJson
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/No tokens yet/i)).toBeInTheDocument()
    })
  })

  it('prevents double token request submission', async () => {
    const user = userEvent.setup()
    let requestCount = 0
    api.fetchJson.mockImplementation((url, opts) => {
      if (url === '/api/user/projects' || url === '/api/user/tokens' || url === '/api/user/token-requests') {
        if (!opts?.method) return Promise.resolve([])
      }
      if (opts?.method === 'POST' && url === '/api/user/token-requests') {
        requestCount++
        return new Promise(resolve => setTimeout(() => resolve({ id: 1 }), 100))
      }
      return Promise.resolve([])
    })

    render(<TokensPage me={me} />)

    await waitFor(() => expect(screen.getByPlaceholderText(/e.g., Production API/i)).toBeInTheDocument())

    await user.type(screen.getByPlaceholderText(/e.g., Production API/i), 'New Token')
    const btn = screen.getByRole('button', { name: /Request token/i })
    await user.click(btn)
    await user.click(btn)

    await new Promise(r => setTimeout(r, 150))
    expect(requestCount).toBe(1)
  })

  it('collapses expanded token when clicking Hide button', async () => {
    const user = userEvent.setup()
    const tokens = [
      {
        id: 1,
        name: 'Token 1',
        created_at: '2024-01-01T00:00:00Z',
        revoked_at: null,
      },
    ]
    const projects = [{ id: 1, name: 'Project 1' }]
    api.fetchJson
      .mockResolvedValueOnce(projects) // projects
      .mockResolvedValueOnce(tokens) // tokens
      .mockResolvedValueOnce([{ project_id: 1 }]) // token 1 has access to project 1
      .mockResolvedValueOnce([]) // requests

    render(<TokensPage me={me} />)

    await waitFor(() => {
      expect(screen.getByText('Token 1')).toBeInTheDocument()
    })

    // Click to expand (line 189: isExpanded is false, sets to t.id)
    const manageButton = screen.getByRole('button', { name: /Manage project access/i })
    await user.click(manageButton)

    await waitFor(() => {
      expect(screen.getByText(/Grant access to projects/i)).toBeInTheDocument()
    })

    // Click to collapse (line 189: isExpanded is true, sets to null)
    const hideButton = screen.getByRole('button', { name: /Hide project access/i })
    await user.click(hideButton)

    // Should collapse the expanded section
    await waitFor(() => {
      expect(screen.queryByText(/Grant access to projects/i)).not.toBeInTheDocument()
    })
  })
})
