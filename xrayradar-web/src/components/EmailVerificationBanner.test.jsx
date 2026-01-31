import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EmailVerificationBanner } from './EmailVerificationBanner'

describe('EmailVerificationBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns null when me is undefined', () => {
    const { container } = render(<EmailVerificationBanner me={undefined} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when me.email_verified is true', () => {
    const { container } = render(
      <EmailVerificationBanner me={{ email: 'a@b.com', email_verified: true }} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows banner when email not verified', () => {
    render(<EmailVerificationBanner me={{ email: 'a@b.com', email_verified: false }} />)
    expect(screen.getByText(/Please verify your email address/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Resend email/i })).toBeInTheDocument()
  })

  it('calls resend and shows success', async () => {
    const user = userEvent.setup()
    global.fetch = vi.fn().mockResolvedValue({ ok: true })

    render(<EmailVerificationBanner me={{ email: 'a@b.com', email_verified: false }} />)

    await user.click(screen.getByRole('button', { name: /Resend email/i }))

    await waitFor(() => {
      expect(screen.getByText(/Verification email sent/i)).toBeInTheDocument()
    })
  })

  it('shows error when resend fails', async () => {
    const user = userEvent.setup()
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Too many requests' }),
    })

    render(<EmailVerificationBanner me={{ email: 'a@b.com', email_verified: false }} />)

    await user.click(screen.getByRole('button', { name: /Resend email/i }))

    await waitFor(() => {
      expect(screen.getByText(/Too many requests/i)).toBeInTheDocument()
    })
  })

  it('shows network error on fetch failure', async () => {
    const user = userEvent.setup()
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    render(<EmailVerificationBanner me={{ email: 'a@b.com', email_verified: false }} />)

    await user.click(screen.getByRole('button', { name: /Resend email/i }))

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })
  })
})
