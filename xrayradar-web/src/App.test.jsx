import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Suspense } from 'react'
import App from './App'

// Wrap App in Suspense so lazy-loaded routes (DashboardLayout, LoginPage, etc.) don't throw
// "A component suspended while responding to synchronous input"
function renderApp(ui = <App />, options = {}) {
  return render(ui, {
    wrapper: ({ children }) => <Suspense fallback={null}>{children}</Suspense>,
    ...options,
  })
}

// Mock fetch globally
global.fetch = vi.fn()

// Mock navigation (must include NAVIGATE_EVENT for usePathname)
vi.mock('./utils/navigation', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, navigate: vi.fn() }
})

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

    renderApp()
    
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

    renderApp()
    
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

    renderApp()
    
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

  it('opens signup modal with Basic plan when clicking Basic button', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    renderApp()
    
    await waitFor(() => {
      expect(screen.getByText(/Error tracking that stays out of your way/i)).toBeInTheDocument()
    })
    
    const basicButton = screen.getByRole('button', { name: /Choose Basic/i })
    await user.click(basicButton)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    }, { timeout: 3000 })
    
    expect(screen.getByText(/Use an email \+ password to create your account/i)).toBeInTheDocument()
  })

  it('shows dashboard link when authenticated', async () => {
    // Mock /api/me specifically so no other fetch steals the response
    fetch.mockImplementation((url) => {
      if (String(url).includes('/api/me')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ id: 1, email: 'test@example.com' }),
        })
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`))
    })
    try {
      renderApp()
      // findByRole retries until link appears (lazy LandingPage + me fetch)
      const dashboardLink = await screen.findByRole('link', { name: /Dashboard/i }, { timeout: 5000 })
      expect(dashboardLink).toBeInTheDocument()
    } finally {
      fetch.mockReset()
    }
  })

  it('handles logout', async () => {
    const user = userEvent.setup()
    const mockMe = { id: 1, email: 'test@example.com' }

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMe,
      })
      .mockResolvedValueOnce({
        ok: true,
      })

    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/dashboard',
        href: '/dashboard',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Sign out/i })).toBeInTheDocument()
    })

    const signOutButton = screen.getByRole('button', { name: /Sign out/i })
    await user.click(signOutButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
    })
  })

  it('handles logout error gracefully', async () => {
    const user = userEvent.setup()
    const mockMe = { id: 1, email: 'test@example.com' }

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMe,
      })
      .mockRejectedValueOnce(new Error('Network error'))

    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/dashboard',
        href: '/dashboard',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Sign out/i })).toBeInTheDocument()
    })

    const signOutButton = screen.getByRole('button', { name: /Sign out/i })
    await user.click(signOutButton)

    // Should still navigate even if logout fails
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
    })
  })

  it('redirects to login when accessing dashboard without auth', async () => {
    const { navigate } = await import('./utils/navigation')
    
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/dashboard',
        href: '/dashboard',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    renderApp()

    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith('/login')
    }, { timeout: 2000 })
  })

  it('shows loading state when me is not loaded', async () => {
    fetch.mockImplementation(() => new Promise(() => {})) // Never resolves

    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/dashboard',
        href: '/dashboard',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    const { container } = renderApp()

    // Should render nothing while loading
    await waitFor(() => {
      expect(container.firstChild).toBeNull()
    })
  })

  it('renders dashboard when authenticated', async () => {
    const mockMe = { id: 1, email: 'test@example.com' }

    fetch.mockImplementation((url) => {
      if (String(url).includes('/api/me')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockMe,
        })
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`))
    })
    try {
      Object.defineProperty(window, 'location', {
        value: {
          pathname: '/dashboard',
          href: '/dashboard',
          assign: vi.fn(),
          replace: vi.fn(),
        },
        writable: true,
        configurable: true,
      })

      renderApp()
      // findByRole retries until DashboardLayout + DashboardRouter lazy load and show Projects link
      const projectsLink = await screen.findByRole('link', { name: /Projects/i }, { timeout: 5000 })
      expect(projectsLink).toBeInTheDocument()
    } finally {
      fetch.mockReset()
    }
  })

  it('renders ForgotPasswordPage when path is /forgot-password', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/forgot-password',
        href: '/forgot-password',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByText(/Forgot password/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    })
  })

  it('renders ResetPasswordPage when path is /reset-password', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/reset-password',
        href: '/reset-password',
        search: '?token=abc123',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByText(/Set new password/i)).toBeInTheDocument()
    })
  })

  it('renders PrivacyPolicyPage when path is /privacy', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/privacy',
        href: '/privacy',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Privacy Policy/i })).toBeInTheDocument()
    })
  })

  it('renders TermsOfServicePage when path is /terms', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/terms',
        href: '/terms',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Terms of Service/i })).toBeInTheDocument()
    })
  })

  it('renders VerifyEmailPage when path is /verify-email', async () => {
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/verify-email',
        href: '/verify-email',
        search: '?token=test-token-123',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    const meUser = { id: 1, email: 'verified@example.com' }
    fetch.mockImplementation((url) => {
      if (url.startsWith('/auth/verify-email')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ message: 'Email verified successfully!' }),
        })
      }
      if (url === '/api/me') {
        return Promise.resolve({ ok: true, json: async () => meUser })
      }
      return Promise.reject(new Error('Unexpected fetch'))
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByText(/Verifying your email/i)).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('Email Verified!')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('redirects to login when accessing accept-invite without auth', async () => {
    const { navigate } = await import('./utils/navigation')
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/accept-invite',
        href: '/accept-invite',
        search: '',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    renderApp()

    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith('/login?next=' + encodeURIComponent('/accept-invite'))
    }, { timeout: 2000 })
  })

  it('redirects to login with full accept-invite URL including search when unauthenticated', async () => {
    const { navigate } = await import('./utils/navigation')
    fetch.mockResolvedValueOnce({ ok: false, status: 401 })

    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/accept-invite',
        href: '/accept-invite?token=abc',
        search: '?token=abc',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    renderApp()

    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith('/login?next=' + encodeURIComponent('/accept-invite?token=abc'))
    }, { timeout: 2000 })
  })

  it('renders accept-invite page when authenticated', async () => {
    const mockMe = { id: 1, email: 'user@example.com' }
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockMe,
    })

    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/accept-invite',
        href: '/accept-invite',
        search: '?token=invite-token-123',
        assign: vi.fn(),
        replace: vi.fn(),
      },
      writable: true,
      configurable: true,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByText(/Accepting invite/i)).toBeInTheDocument()
    }, { timeout: 2000 })
  })

  it('closes signup modal', async () => {
    const user = userEvent.setup()
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    renderApp()

    await waitFor(() => {
      expect(screen.getByText(/Error tracking that stays out of your way/i)).toBeInTheDocument()
    })

    const freeButton = screen.getByRole('button', { name: /Choose Free/i })
    await user.click(freeButton)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/you@company.com/i)).toBeInTheDocument()
    })

    // Close modal
    const closeButton = screen.getByRole('button', { name: /Close/i })
    await user.click(closeButton)

    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/you@company.com/i)).not.toBeInTheDocument()
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

    renderApp()
    
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

    renderApp()
    
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

    renderApp()
    
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

    renderApp()
    
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
