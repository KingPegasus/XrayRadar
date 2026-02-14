import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LandingPage } from './LandingPage'

// Mock Logo component
vi.mock('../components/Logo', () => ({
  Logo: ({ onError }) => {
    // Trigger error callback to test error handling (line 17)
    if (onError) {
      setTimeout(() => onError(), 0)
    }
    return null
  },
}))

// Mock Link component
vi.mock('../components/Link', () => ({
  Link: ({ to, children, className }) => <a href={to} className={className}>{children}</a>,
}))

describe('LandingPage', () => {
  const mockOnSignupOpen = vi.fn()
  const mockOnLogout = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('handles logo error and shows fallback text', async () => {
    render(<LandingPage me={null} onSignupOpen={mockOnSignupOpen} onLogout={mockOnLogout} />)

    await waitFor(() => {
      expect(screen.getByText('XrayRadar')).toBeInTheDocument()
    }, { timeout: 2000 })
  })

  it('renders Teams and Teams Pro pricing cards and Choose buttons', () => {
    render(<LandingPage me={null} onSignupOpen={mockOnSignupOpen} onLogout={mockOnLogout} />)
    expect(screen.getByText('Teams')).toBeInTheDocument()
    expect(screen.getByText('Teams Pro')).toBeInTheDocument()
    expect(screen.getByText(/Up to 25,000 events storage/)).toBeInTheDocument()
    expect(screen.getByText(/Up to 50,000 events storage/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Choose Teams$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Choose Teams Pro/i })).toBeInTheDocument()
  })

  it('calls onSignupOpen with Teams when Choose Teams is clicked', async () => {
    render(<LandingPage me={null} onSignupOpen={mockOnSignupOpen} onLogout={mockOnLogout} />)
    await userEvent.click(screen.getByRole('button', { name: /Choose Teams$/i }))
    expect(mockOnSignupOpen).toHaveBeenCalledWith('Teams')
  })

  it('calls onSignupOpen with Teams Pro when Choose Teams Pro is clicked', async () => {
    render(<LandingPage me={null} onSignupOpen={mockOnSignupOpen} onLogout={mockOnLogout} />)
    await userEvent.click(screen.getByRole('button', { name: /Choose Teams Pro/i }))
    expect(mockOnSignupOpen).toHaveBeenCalledWith('Teams Pro')
  })

  it('switches language when clicking Python or JavaScript tabs', async () => {
    const user = userEvent.setup()
    render(<LandingPage me={null} onSignupOpen={mockOnSignupOpen} onLogout={mockOnLogout} />)

    const pythonTab = screen.getByRole('tab', { name: /^Python$/i })
    const jsTab = screen.getByRole('tab', { name: /^JavaScript$/i })

    expect(pythonTab).toHaveAttribute('aria-selected', 'true')
    await user.click(jsTab)
    expect(jsTab).toHaveAttribute('aria-selected', 'true')
    expect(pythonTab).toHaveAttribute('aria-selected', 'false')

    await user.click(pythonTab)
    expect(pythonTab).toHaveAttribute('aria-selected', 'true')
  })

  it('switches framework when clicking framework tabs', async () => {
    const user = userEvent.setup()
    render(<LandingPage me={null} onSignupOpen={mockOnSignupOpen} onLogout={mockOnLogout} />)

    const fastapiTab = screen.getByRole('tab', { name: /FastAPI/i })
    const djangoTab = screen.getByRole('tab', { name: /Django/i })
    const flaskTab = screen.getByRole('tab', { name: /Flask/i })

    expect(fastapiTab).toHaveAttribute('aria-selected', 'true')
    await user.click(djangoTab)
    expect(djangoTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText(/Quick setup — Django/i)).toBeInTheDocument()

    await user.click(flaskTab)
    expect(flaskTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText(/Quick setup — Flask/i)).toBeInTheDocument()
  })

  it('shows snippet code when framework is selected', async () => {
    render(<LandingPage me={null} onSignupOpen={mockOnSignupOpen} onLogout={mockOnLogout} />)

    expect(screen.getByText(/Quick setup — FastAPI/i)).toBeInTheDocument()
    expect(screen.getByText(/pip install xrayradar/i)).toBeInTheDocument()
  })
})
