import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AccountInfoCard } from './AccountInfoCard'

describe('AccountInfoCard', () => {
  it('renders account info with verified badge', () => {
    render(
      <AccountInfoCard
        me={{
          email: 'test@example.com',
          email_verified: true,
          plan: 'Basic',
          created_at: '2024-01-01T00:00:00Z',
        }}
      />
    )
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    expect(screen.getByText('Verified')).toBeInTheDocument()
    expect(screen.getByText('Basic')).toBeInTheDocument()
  })

  it('renders unverified badge when not verified', () => {
    render(<AccountInfoCard me={{ email: 'a@b.com', email_verified: false }} />)
    expect(screen.getByText('Unverified')).toBeInTheDocument()
  })

  it('renders default values when me is minimal', () => {
    render(<AccountInfoCard me={{ email: 'x@y.com' }} />)
    expect(screen.getByText('x@y.com')).toBeInTheDocument()
    expect(screen.getByText('Free')).toBeInTheDocument()
  })

  it('renders dash when me is null', () => {
    render(<AccountInfoCard me={null} />)
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThanOrEqual(1)
  })
})
