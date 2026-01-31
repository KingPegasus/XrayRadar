import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DeleteAccountCard } from './DeleteAccountCard'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('DeleteAccountCard', () => {
  const me = { email: 'test@example.com', email_verified: true }

  beforeEach(() => {
    vi.clearAllMocks()
    api.fetchJson.mockResolvedValue(null)
  })

  it('shows Delete Account button when no pending request', async () => {
    render(<DeleteAccountCard me={me} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Delete My Account/i })).toBeInTheDocument()
    })
  })

  it('shows verify email message when not verified', async () => {
    render(<DeleteAccountCard me={{ ...me, email_verified: false }} />)

    await waitFor(() => {
      expect(screen.getByText(/Verify your email to request account deletion/i)).toBeInTheDocument()
      // No Delete button when unverified - only the message
      expect(screen.queryByRole('button', { name: /Delete My Account/i })).not.toBeInTheDocument()
    })
  })

  it('shows confirm form when Delete clicked', async () => {
    const user = userEvent.setup()
    render(<DeleteAccountCard me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Delete My Account/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Delete My Account/i }))

    expect(screen.getByText(/Confirm Account Deletion/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Request Account Deletion/i })).toBeInTheDocument()
  })

  it('submits deletion request', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce({ created_at: '2024-01-01T00:00:00Z' })

    render(<DeleteAccountCard me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Delete My Account/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Delete My Account/i }))

    await waitFor(() => expect(screen.getByRole('button', { name: /Request Account Deletion/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Request Account Deletion/i }))

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/deletion-request', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }))
    })
  })

  it('shows pending request when one exists', async () => {
    api.fetchJson.mockResolvedValue({
      created_at: '2024-01-01T00:00:00Z',
      reason: 'No longer need',
    })

    render(<DeleteAccountCard me={me} />)

    await waitFor(() => {
      expect(screen.getByText(/Account Deletion Requested/i)).toBeInTheDocument()
      expect(screen.getByText(/Reason: No longer need/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Cancel Request/i })).toBeInTheDocument()
    })
  })

  it('cancels deletion request', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce({ created_at: '2024-01-01T00:00:00Z' })
      .mockResolvedValueOnce({})

    render(<DeleteAccountCard me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Cancel Request/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Cancel Request/i }))

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/deletion-request', { method: 'DELETE' })
    })
  })

  it('handles fetch error on initial load', async () => {
    api.fetchJson.mockRejectedValueOnce(new Error('Network error'))

    render(<DeleteAccountCard me={me} />)

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith('/api/user/deletion-request')
    })
    await waitFor(() => {
      expect(screen.getByText(/Danger Zone/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Delete My Account/i })).toBeInTheDocument()
    })
  })

  it('shows error when request deletion fails', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce(null)
      .mockRejectedValueOnce(new Error('Request failed'))

    render(<DeleteAccountCard me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Delete My Account/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Delete My Account/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Request Account Deletion/i })).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Request Account Deletion/i }))

    await waitFor(() => {
      expect(screen.getByText(/Request failed/i)).toBeInTheDocument()
    })
  })

  it('shows error when cancel request fails', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce({ created_at: '2024-01-01T00:00:00Z' })
      .mockRejectedValueOnce(new Error('Cancel failed'))

    render(<DeleteAccountCard me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Cancel Request/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Cancel Request/i }))

    await waitFor(() => {
      expect(screen.getByText(/Cancel failed/i)).toBeInTheDocument()
    })
  })

  it('submits deletion request with reason', async () => {
    const user = userEvent.setup()
    api.fetchJson
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce({ created_at: '2024-01-02T00:00:00Z' })

    render(<DeleteAccountCard me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Delete My Account/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Delete My Account/i }))

    await waitFor(() => expect(screen.getByPlaceholderText(/Help us improve/i)).toBeInTheDocument())
    await user.type(screen.getByPlaceholderText(/Help us improve/i), 'Switching to another tool')
    await user.click(screen.getByRole('button', { name: /Request Account Deletion/i }))

    await waitFor(() => {
      expect(api.fetchJson).toHaveBeenCalledWith(
        '/api/user/deletion-request',
        expect.objectContaining({
          body: JSON.stringify({ reason: 'Switching to another tool' }),
        })
      )
    })
  })

  it('cancel button in confirm form closes form', async () => {
    const user = userEvent.setup()
    render(<DeleteAccountCard me={me} />)

    await waitFor(() => expect(screen.getByRole('button', { name: /Delete My Account/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /Delete My Account/i }))

    await waitFor(() => expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /^Cancel$/i }))

    expect(screen.queryByText(/Confirm Account Deletion/i)).not.toBeInTheDocument()
  })
})
