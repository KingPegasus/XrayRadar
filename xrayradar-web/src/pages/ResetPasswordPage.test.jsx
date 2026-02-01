import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ResetPasswordPage } from './ResetPasswordPage'
import * as navigation from '../utils/navigation'

vi.mock('../utils/navigation')

global.fetch = vi.fn()

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows invalid link when no token in URL', () => {
    Object.defineProperty(window, 'location', {
      value: { search: '', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    render(<ResetPasswordPage />)

    expect(screen.getByText(/Invalid link/i)).toBeInTheDocument()
    expect(screen.getByText(/This reset link is missing a token/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Request new link/i })).toHaveAttribute('href', '/forgot-password')
  })

  it('renders set new password form when token in URL', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
      expect(screen.getByText(/Enter your new password below/i)).toBeInTheDocument()
      expect(screen.getAllByPlaceholderText(/••••••••/)).toHaveLength(2)
      expect(screen.getByRole('button', { name: /Reset password/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Back to sign in/i })).toBeInTheDocument()
    })
  })

  it('validates password length', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'short')
    await user.type(passwordInputs[1], 'short')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    await waitFor(() => {
      expect(screen.getByText(/Password must be at least 8 characters/i)).toBeInTheDocument()
    })
    expect(fetch).not.toHaveBeenCalled()
  })

  it('validates password confirmation match', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'password123')
    await user.type(passwordInputs[1], 'password456')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument()
    })
    expect(fetch).not.toHaveBeenCalled()
  })

  it('shows success state after successful reset', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({ ok: true })

    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'newpassword123')
    await user.type(passwordInputs[1], 'newpassword123')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    await waitFor(() => {
      expect(screen.getByText(/Password reset/i)).toBeInTheDocument()
      expect(screen.getByText(/Your password has been updated/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument()
    })
  })

  it('calls reset-password API with correct body', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({ ok: true })

    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'newpassword123')
    await user.type(passwordInputs[1], 'newpassword123')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ token: 'abc123token', new_password: 'newpassword123' }),
      })
    })
  })

  it('calls navigate on Sign in after success', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({ ok: true })

    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'newpassword123')
    await user.type(passwordInputs[1], 'newpassword123')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Sign in/i }))
    expect(navigation.navigate).toHaveBeenCalledWith('/login')
  })

  it('handles error response', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=expired-token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid or expired reset token' }),
    })

    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'newpassword123')
    await user.type(passwordInputs[1], 'newpassword123')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    await waitFor(() => {
      expect(screen.getByText(/Invalid or expired reset token/i)).toBeInTheDocument()
    })
  })

  it('handles fetch error', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=valid-token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    fetch.mockRejectedValueOnce(new Error('Network error'))

    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'newpassword123')
    await user.type(passwordInputs[1], 'newpassword123')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong. Please try again/i)).toBeInTheDocument()
    })
  })

  it('returns early when submitting on second click', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    let callCount = 0
    fetch.mockImplementation((url) => {
      if (url === '/auth/reset-password') {
        callCount++
        return new Promise(r => setTimeout(() => r({ ok: true }), 200))
      }
      return Promise.reject(new Error('Unexpected'))
    })

    render(<ResetPasswordPage />)

    await waitFor(() => expect(screen.getByText(/Set new password/i)).toBeInTheDocument())

    const inputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(inputs[0], 'newpassword123')
    await user.type(inputs[1], 'newpassword123')
    const btn = screen.getByRole('button', { name: /Reset password/i })
    await user.click(btn)
    await user.click(btn)

    await new Promise(r => setTimeout(r, 250))
    expect(callCount).toBe(1)
  })

  it('shows submitting state', async () => {
    Object.defineProperty(window, 'location', {
      value: { search: '?token=abc123token', pathname: '/reset-password' },
      writable: true,
      configurable: true,
    })

    const user = userEvent.setup()
    fetch.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100)))

    render(<ResetPasswordPage />)

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/)
    await user.type(passwordInputs[0], 'newpassword123')
    await user.type(passwordInputs[1], 'newpassword123')
    await user.click(screen.getByRole('button', { name: /Reset password/i }))

    expect(screen.getByText(/Resetting…/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Resetting…/i })).toBeDisabled()
  })
})
