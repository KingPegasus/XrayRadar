import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginPage } from './LoginPage'

// Mock fetch globally
global.fetch = vi.fn()

// Mock Link component
vi.mock('../components/Link', () => ({
  Link: ({ to, children, className }) => <a href={to} className={className}>{children}</a>,
}))

// Mock navigation
vi.mock('../utils/navigation', () => ({
  navigate: vi.fn(),
}))

describe('LoginPage', () => {
  const mockOnLoggedIn = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/login',
        href: '/login',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })
  })

  it('renders login form', () => {
    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    // Use getAllByText since "Sign in" appears in heading and button
    expect(screen.getAllByText(/Sign in/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Use your email \+ password to access your dashboard/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Back/i })).toBeInTheDocument()
  })

  it('validates email format on submit', async () => {
    const user = userEvent.setup()
    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const submitButton = screen.getByRole('button', { name: /Sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument()
    })
  })

  it('validates password is required', async () => {
    const user = userEvent.setup()
    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument()
    })
  })

  it('handles successful login', async () => {
    const user = userEvent.setup()
    const mockMe = { id: 1, email: 'test@example.com' }

    fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMe,
      })

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/auth/login', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      }))
    })

    await waitFor(() => {
      expect(mockOnLoggedIn).toHaveBeenCalledWith(mockMe)
    })

    await waitFor(() => {
      expect(window.location.href).toBe('/dashboard')
    })
  })

  it('handles login error response', async () => {
    const user = userEvent.setup()

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Invalid credentials' }),
    })

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument()
    })

    expect(mockOnLoggedIn).not.toHaveBeenCalled()
  })

  it('handles login error without detail message', async () => {
    const user = userEvent.setup()

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({}),
    })

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Request failed \(500\)/i)).toBeInTheDocument()
    })
  })

  it('handles fetch error', async () => {
    const user = userEvent.setup()

    fetch.mockRejectedValueOnce(new Error('Network error'))

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong. Please try again./i)).toBeInTheDocument()
    })

    expect(mockOnLoggedIn).not.toHaveBeenCalled()
  })

  it('handles case when fetchMe returns null after login', async () => {
    const user = userEvent.setup()

    fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
      })

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load user info after login/i)).toBeInTheDocument()
    })

    expect(mockOnLoggedIn).not.toHaveBeenCalled()
  })

  it('trims and lowercases email', async () => {
    const user = userEvent.setup()
    const mockMe = { id: 1, email: 'test@example.com' }

    fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMe,
      })

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, '  TEST@EXAMPLE.COM  ')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/auth/login', expect.objectContaining({
        body: JSON.stringify({ email: 'test@example.com', password: 'password123' }),
      }))
    })
  })

  it('prevents double submission', async () => {
    const user = userEvent.setup()

    let loginCallCount = 0
    fetch.mockImplementation((url, opts) => {
      if (url === '/auth/login' && opts?.method === 'POST') {
        loginCallCount++
        return new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          status: 200,
        }), 100))
      }
      return Promise.resolve({ ok: false, status: 401 })
    })

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    
    // Click submit button - this sets submitting to true
    await user.click(submitButton)
    
    // Immediately click again - should hit early return at line 13 (if (submitting) return)
    // This tests the branch where submitting is true
    await user.click(submitButton)

    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 150))

    // Should only call login API once due to early return when submitting is true (line 13)
    expect(loginCallCount).toBe(1)
  })


  it('shows submitting state', async () => {
    const user = userEvent.setup()

    fetch.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({
      ok: true,
      status: 200,
    }), 100)))

    render(<LoginPage onLoggedIn={mockOnLoggedIn} />)

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInput = screen.getByPlaceholderText(/••••••••/i)
    const submitButton = screen.getByRole('button', { name: /Sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    // Button should show submitting state
    expect(screen.getByText(/Signing in…/i)).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })
})
