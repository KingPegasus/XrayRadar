import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TokensPage } from './TokensPage'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('TokensPage', () => {
  const me = { email: 'test@example.com' }

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
    api.fetchJson
      .mockRejectedValueOnce(new Error('Failed to load')) // projects fails
      .mockResolvedValueOnce([]) // tokens (might succeed)
      .mockResolvedValueOnce([]) // requests (might succeed)

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
})
