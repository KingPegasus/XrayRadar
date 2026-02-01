import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { VerifyEmailPage } from './VerifyEmailPage'
import * as navigation from '../utils/navigation'

vi.mock('../utils/navigation')

describe('VerifyEmailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows error when no token in URL', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    render(<VerifyEmailPage />)

    await waitFor(() => {
      expect(screen.getByText(/Verification Failed/i)).toBeInTheDocument()
      expect(screen.getByText(/No verification token provided/i)).toBeInTheDocument()
    })
  })

  it('shows verifying then success when token is valid', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=valid-token', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    global.fetch = vi.fn()
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Email verified successfully!' }),
    })

    const onVerified = vi.fn()
    render(<VerifyEmailPage onVerified={onVerified} />)

    expect(screen.getByText(/Verifying your email/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Email Verified!')).toBeInTheDocument()
      expect(onVerified).toHaveBeenCalled()
    })
  })

  it('shows error when verification fails', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=bad-token', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    global.fetch = vi.fn()
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid or expired token' }),
    })

    render(<VerifyEmailPage />)

    await waitFor(() => {
      expect(screen.getByText(/Verification Failed/i)).toBeInTheDocument()
      expect(screen.getByText(/Invalid or expired token/i)).toBeInTheDocument()
    })
  })

  it('shows Verification failed when res not ok and no detail', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=x', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({}),
    })
    global.fetch = fetchMock

    render(<VerifyEmailPage />)

    await waitFor(
      () => {
        expect(screen.getByText('Verification failed.')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )
  })

  it('shows default success message when res ok but no message', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=valid', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    global.fetch = vi.fn()
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    })

    render(<VerifyEmailPage onVerified={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/Email Verified!/i)).toBeInTheDocument()
      expect(screen.getByText(/Email verified successfully!/i)).toBeInTheDocument()
    })
  })

  it('navigates to dashboard on Go to Dashboard click after success', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=valid', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    global.fetch = vi.fn()
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Done' }),
    })

    const user = userEvent.setup()
    render(<VerifyEmailPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Go to Dashboard/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Go to Dashboard/i }))
    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard')
  })

  it('handles network error', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=valid', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    render(<VerifyEmailPage />)

    await waitFor(() => {
      expect(screen.getByText(/Verification Failed/i)).toBeInTheDocument()
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })
  })

  it('navigates to dashboard on Go to Dashboard click after error', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=bad-token', pathname: '/verify-email' },
      writable: true,
      configurable: true,
    })

    global.fetch = vi.fn()
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid token' }),
    })

    const user = userEvent.setup()
    render(<VerifyEmailPage />)

    await waitFor(() => {
      expect(screen.getByText(/Verification Failed/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Go to Dashboard/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Go to Dashboard/i }))
    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard')
  })
})
