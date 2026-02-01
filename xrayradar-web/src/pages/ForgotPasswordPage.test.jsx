import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ForgotPasswordPage } from './ForgotPasswordPage'

global.fetch = vi.fn()

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders forgot password form', () => {
    render(<ForgotPasswordPage />)

    expect(screen.getByText(/Forgot password/i)).toBeInTheDocument()
    expect(screen.getByText(/Enter your email.*send you a link/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Send reset link/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Back to sign in/i })).toBeInTheDocument()
  })

  it('validates email format on submit', async () => {
    const user = userEvent.setup()
    render(<ForgotPasswordPage />)

    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument()
    })
    expect(fetch).not.toHaveBeenCalled()
  })

  it('validates email has @', async () => {
    const user = userEvent.setup()
    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'invalid')
    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument()
    })
    expect(fetch).not.toHaveBeenCalled()
  })

  it('shows success state after successful submit', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({ ok: true, status: 200 })

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText(/Check your email/i)).toBeInTheDocument()
      expect(screen.getByText(/If an account exists for that email/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Back to sign in/i })).toHaveAttribute('href', '/login')
    })
  })

  it('calls forgot-password API with correct body', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({ ok: true })

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: 'user@example.com' }),
      })
    })
  })

  it('trims and lowercases email', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({ ok: true })

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), '  USER@EXAMPLE.COM  ')
    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/auth/forgot-password', expect.objectContaining({
        body: JSON.stringify({ email: 'user@example.com' }),
      }))
    })
  })

  it('handles error response', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Rate limit exceeded' }),
    })

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText(/Rate limit exceeded/i)).toBeInTheDocument()
    })
  })

  it('handles fetch error', async () => {
    const user = userEvent.setup()
    fetch.mockRejectedValueOnce(new Error('Network error'))

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong. Please try again/i)).toBeInTheDocument()
    })
  })

  it('returns early when submitting on second click', async () => {
    const user = userEvent.setup()
    let callCount = 0
    fetch.mockImplementation((url) => {
      if (url === '/auth/forgot-password') {
        callCount++
        return new Promise(r => setTimeout(() => r({ ok: true }), 200))
      }
      return Promise.reject(new Error('Unexpected'))
    })

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    const btn = screen.getByRole('button', { name: /Send reset link/i })
    await user.click(btn)
    await user.click(btn)

    await new Promise(r => setTimeout(r, 250))
    expect(callCount).toBe(1)
  })

  it('shows submitting state', async () => {
    const user = userEvent.setup()
    fetch.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100)))

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    await user.click(screen.getByRole('button', { name: /Send reset link/i }))

    expect(screen.getByText(/Sending…/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sending…/i })).toBeDisabled()
  })

  it('prevents double submission', async () => {
    const user = userEvent.setup()
    let callCount = 0
    fetch.mockImplementation(() => {
      callCount++
      return new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100))
    })

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    const submitButton = screen.getByRole('button', { name: /Send reset link/i })
    await user.click(submitButton)
    await user.click(submitButton)

    await new Promise(resolve => setTimeout(resolve, 150))

    expect(callCount).toBe(1)
  })

  it('prevents form submission when already submitting (covers line 12)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    fetch.mockImplementation(() => {
      callCount++
      return new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100))
    })

    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText(/you@company.com/i), 'user@example.com')
    const form = screen.getByRole('button', { name: /Send reset link/i }).closest('form')
    
    // Submit via form event (triggers e.preventDefault, then checks submitting state)
    fireEvent.submit(form)
    // Try to submit again immediately while first is pending
    fireEvent.submit(form)

    await new Promise(resolve => setTimeout(resolve, 150))

    // Should only call fetch once due to "if (submitting) return" check
    expect(callCount).toBe(1)
  })
})
