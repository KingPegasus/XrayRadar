import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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
})
