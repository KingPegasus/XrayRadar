import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TermsOfServicePage } from './TermsOfServicePage'

vi.mock('../components/Link', () => ({
  Link: ({ to, children }) => <a href={to}>{children}</a>,
}))

describe('TermsOfServicePage', () => {
  it('renders terms of service with key sections', () => {
    render(<TermsOfServicePage />)

    expect(screen.getByRole('heading', { name: /Terms of Service/i })).toBeInTheDocument()
    expect(screen.getByText(/Effective:/i)).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /Back to home/i }).length).toBeGreaterThan(0)

    expect(screen.getByRole('heading', { name: /Acceptance/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Contact/i })).toBeInTheDocument()
  })

  it('includes link to Privacy Policy in Acceptance section', () => {
    render(<TermsOfServicePage />)
    expect(screen.getByRole('link', { name: /Privacy Policy/i })).toBeInTheDocument()
  })

  it('includes Governing Law section', () => {
    render(<TermsOfServicePage />)
    expect(screen.getByRole('heading', { name: /Governing Law/i })).toBeInTheDocument()
  })
})
