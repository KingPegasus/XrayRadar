import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AcceptInvitePage } from './AcceptInvitePage'

vi.mock('../utils/api', () => ({
  fetchJson: vi.fn(),
}))

vi.mock('../utils/navigation', () => ({
  navigate: vi.fn(),
}))

describe('AcceptInvitePage', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    const { fetchJson } = await import('../utils/api')
    fetchJson.mockResolvedValue(undefined)
  })

  it('shows error when token is missing', async () => {
    render(<AcceptInvitePage token="" onSuccess={undefined} />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Invalid invite link: missing token/i)
    })
    expect(screen.getByText(/Go to dashboard/i)).toBeInTheDocument()
  })

  it('shows loading then success and redirects when no onSuccess', async () => {
    const { fetchJson } = await import('../utils/api')
    const { navigate } = await import('../utils/navigation')
    fetchJson.mockResolvedValue(undefined)

    render(<AcceptInvitePage token="valid-token" onSuccess={undefined} />)
    expect(screen.getByText(/Accepting invite/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/Invite accepted. Redirecting/i)).toBeInTheDocument()
    })
    expect(fetchJson).toHaveBeenCalledWith(
      '/api/user/team/invites/accept',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ token: 'valid-token' }),
      })
    )
    expect(navigate).toHaveBeenCalledWith('/dashboard')
  })

  it('shows loading then success and calls onSuccess when provided', async () => {
    const { fetchJson } = await import('../utils/api')
    const { navigate } = await import('../utils/navigation')
    fetchJson.mockResolvedValue(undefined)
    const onSuccess = vi.fn()

    render(<AcceptInvitePage token="valid-token" onSuccess={onSuccess} />)
    await waitFor(() => {
      expect(screen.getByText(/Invite accepted. Redirecting/i)).toBeInTheDocument()
    })
    expect(onSuccess).toHaveBeenCalled()
    expect(navigate).not.toHaveBeenCalled()
  })

  it('shows error when API fails', async () => {
    const { fetchJson } = await import('../utils/api')
    fetchJson.mockRejectedValue(new Error('Invite expired'))

    render(<AcceptInvitePage token="bad-token" onSuccess={undefined} />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Invite expired/i)
    })
    expect(screen.getByText(/Go to dashboard/i)).toBeInTheDocument()
  })

  it('shows generic error when API fails with no message', async () => {
    const { fetchJson } = await import('../utils/api')
    fetchJson.mockRejectedValue(new Error())

    render(<AcceptInvitePage token="x" onSuccess={undefined} />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Failed to accept invite/i)
    })
  })
})
