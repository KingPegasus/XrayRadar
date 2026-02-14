import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PrivacyPolicyPage } from './PrivacyPolicyPage'

vi.mock('../components/Link', () => ({
  Link: ({ to, children }) => <a href={to}>{children}</a>,
}))

describe('PrivacyPolicyPage', () => {
  it('renders privacy policy with key sections', () => {
    render(<PrivacyPolicyPage />)

    expect(screen.getByRole('heading', { name: /Privacy Policy/i })).toBeInTheDocument()
    expect(screen.getByText(/Effective:/i)).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /Back to home/i }).length).toBeGreaterThan(0)

    expect(screen.getByRole('heading', { name: /Scope/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Information We Collect/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Cookies/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Contact/i })).toBeInTheDocument()
  })

  it('includes Scope section content about Service Data', () => {
    render(<PrivacyPolicyPage />)
    expect(screen.getAllByText(/Service Data/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/error and event data/i)).toBeInTheDocument()
  })

  it('includes Cookies section content', () => {
    render(<PrivacyPolicyPage />)
    expect(screen.getByText(/xrayradar_user_session/i)).toBeInTheDocument()
  })
})
