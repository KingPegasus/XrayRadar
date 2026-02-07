import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlanDetailsCard } from './PlanDetailsCard'

describe('PlanDetailsCard', () => {
  it('renders Free plan details', () => {
    render(<PlanDetailsCard me={{ plan: 'Free', email: 'a@b.com' }} />)
    expect(screen.getByText(/Free Plan/i)).toBeInTheDocument()
    expect(screen.getByText(/1,000 events storage/i)).toBeInTheDocument()
    expect(screen.getByText(/Want more events and email alerts\?/i)).toBeInTheDocument()
    expect(screen.getByText(/Contact to Upgrade/i)).toBeInTheDocument()
  })

  it('renders Free plan with no email (mailto fallback)', () => {
    render(<PlanDetailsCard me={{ plan: 'Free' }} />)
    const link = screen.getByRole('link', { name: /Contact to Upgrade/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('body=Hi'))
  })

  it('renders Basic plan details', () => {
    render(<PlanDetailsCard me={{ plan: 'Basic' }} />)
    expect(screen.getByText(/Basic Plan — \$3\/mo/i)).toBeInTheDocument()
    expect(screen.getByText(/Up to 15,000 events storage/i)).toBeInTheDocument()
  })

  it('renders Teams plan details', () => {
    render(<PlanDetailsCard me={{ plan: 'Teams' }} />)
    expect(screen.getByText(/Teams Plan — \$5\/mo/i)).toBeInTheDocument()
    expect(screen.getByText(/Up to 25,000 events storage/i)).toBeInTheDocument()
    expect(screen.getByText(/invite up to 5 members/i)).toBeInTheDocument()
  })

  it('renders Teams Pro plan details', () => {
    render(<PlanDetailsCard me={{ plan: 'Teams Pro' }} />)
    expect(screen.getByText(/Teams Pro Plan — \$7\/mo/i)).toBeInTheDocument()
    expect(screen.getByText(/Up to 50,000 events storage/i)).toBeInTheDocument()
    expect(screen.getByText(/invite up to 10 members/i)).toBeInTheDocument()
  })

  it('renders unknown plan fallback', () => {
    render(<PlanDetailsCard me={{ plan: 'Enterprise' }} />)
    expect(screen.getByText(/You're on the Enterprise plan/i)).toBeInTheDocument()
  })

  it('renders Unknown when me has no plan', () => {
    render(<PlanDetailsCard me={{ email: 'a@b.com' }} />)
    expect(screen.getByText(/You're on the Unknown plan/i)).toBeInTheDocument()
  })
})
