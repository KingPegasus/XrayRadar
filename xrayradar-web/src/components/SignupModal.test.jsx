import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SignupModal } from './SignupModal'
import * as api from '../utils/api'

vi.mock('../utils/api')

describe('SignupModal', () => {
  const onClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it('does not render when closed', () => {
    render(<SignupModal open={false} plan="Free" onClose={onClose} />)
    expect(screen.queryByText(/Create your account/i)).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    render(<SignupModal open={true} plan="Free" onClose={onClose} />)
    expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    expect(screen.getByText('Free')).toBeInTheDocument()
    expect(screen.getByText(/Use an email \+ password to create your account/i)).toBeInTheDocument()
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    render(<SignupModal open={true} plan="Free" onClose={onClose} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const submitButton = screen.getByRole('button', { name: /Create account/i })

    await user.type(emailInput, 'invalid-email')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument()
    })
  })

  it('validates password length', async () => {
    const user = userEvent.setup()
    render(<SignupModal open={true} plan="Free" onClose={onClose} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/i)
    const passwordInput = passwordInputs[0]
    const submitButton = screen.getByRole('button', { name: /Create account/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'short')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Password must be at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('validates password match', async () => {
    const user = userEvent.setup()
    render(<SignupModal open={true} plan="Free" onClose={onClose} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/i)
    const passwordInput = passwordInputs[0]
    const confirmInput = passwordInputs[1]
    const submitButton = screen.getByRole('button', { name: /Create account/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmInput, 'different')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('handles successful signup', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    })
    api.fetchMe.mockResolvedValueOnce({ id: 1, email: 'test@example.com' })

    render(<SignupModal open={true} plan="Free" onClose={onClose} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/i)
    const passwordInput = passwordInputs[0]
    const confirmInput = passwordInputs[1]
    const submitButton = screen.getByRole('button', { name: /Create account/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/You're in!/i)).toBeInTheDocument()
    })
  })

  it('handles signup error', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Email already exists' }),
    })
    api.readErrorMessage.mockResolvedValueOnce('Email already exists')

    render(<SignupModal open={true} plan="Free" onClose={onClose} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/i)
    const passwordInput = passwordInputs[0]
    const confirmInput = passwordInputs[1]
    const submitButton = screen.getByRole('button', { name: /Create account/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Email already exists/i)).toBeInTheDocument()
    })
  })

  it('resets form when modal opens', () => {
    const { rerender } = render(<SignupModal open={false} plan="Free" onClose={onClose} />)
    rerender(<SignupModal open={true} plan="Free" onClose={onClose} />)
    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    expect(emailInput).toHaveValue('')
  })
})
