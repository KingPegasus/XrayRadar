import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

// Mock fetch globally
global.fetch = vi.fn()

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset window.location before each test
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/',
        href: '/',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
    })
    // Reset history mocks
    window.history.pushState.mockClear()
  })

  it('renders the landing page', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    render(<App />)
    
    // Wait for fetch to complete
    await waitFor(() => {
      expect(screen.getByText(/Error tracking that stays out of your way/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/XrayRadar is a minimal error tracking stack/i)).toBeInTheDocument()
  })

  it('shows sign in button when not authenticated', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    render(<App />)
    
    // Wait for fetch and use more specific query
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /Sign in/i })).toBeInTheDocument()
    })
  })

  it('opens signup modal when clicking pricing button', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    render(<App />)
    
    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText(/Error tracking that stays out of your way/i)).toBeInTheDocument()
    })
    
    const freeButton = screen.getByRole('button', { name: /Choose Free/i })
    await user.click(freeButton)

    // Modal should appear - check for unique modal content (the form input is unique to modal)
    await waitFor(() => {
      // Check for modal-specific content that's unique
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    }, { timeout: 3000 })
    
    // Verify modal is visible with unique content
    expect(screen.getByText(/Use an email \+ password to create your account/i)).toBeInTheDocument()
  })

  it('shows dashboard link when authenticated', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 1, email: 'test@example.com' }),
    })

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /Dashboard/i })).toBeInTheDocument()
    })
  })
})

describe('SignupModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/',
        href: '/',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
    })
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    render(<App />)
    
    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText(/Error tracking that stays out of your way/i)).toBeInTheDocument()
    })
    
    const freeButton = screen.getByRole('button', { name: /Choose Free/i })
    await user.click(freeButton)

    // Wait for modal to appear - check for unique modal content
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    }, { timeout: 3000 })

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const submitButton = screen.getByRole('button', { name: /Create account/i })

    await user.type(emailInput, 'invalid-email')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('validates password length', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    render(<App />)
    
    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText(/Error tracking that stays out of your way/i)).toBeInTheDocument()
    })
    
    const freeButton = screen.getByRole('button', { name: /Choose Free/i })
    await user.click(freeButton)

    // Wait for modal to appear - check for unique modal content
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    }, { timeout: 3000 })

    const emailInput = screen.getByPlaceholderText(/you@company.com/i)
    const passwordInputs = screen.getAllByPlaceholderText(/••••••••/i)
    const passwordInput = passwordInputs[0] // First one is the password field
    const submitButton = screen.getByRole('button', { name: /Create account/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'short')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Password must be at least 8 characters/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })
})

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Set pathname before component reads it
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

  it('renders login form', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    render(<App />)
    
    // Wait for fetch to complete and form to render
    await waitFor(() => {
      // Check for the form elements which are more reliable
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    })
    
    // Verify all form elements are present
    // "Sign in" appears multiple times (div and button), so check for unique descriptive text
    expect(screen.getByText(/Use your email \+ password to access your dashboard/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument()
    // Verify button exists - this is unique
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument()
  })

  it('validates email on submit', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    render(<App />)
    
    // Wait for form to render
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    })
    
    // Use getByRole to find the submit button specifically
    const submitButton = screen.getByRole('button', { name: /Sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument()
    })
  })
})
