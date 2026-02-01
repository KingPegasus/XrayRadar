import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlanDetailsCard } from './PlanDetailsCard'

describe('PlanDetailsCard', () => {
  it('renders Free plan details', () => {
    render(<PlanDetailsCard me={{ plan: 'Free', email: 'a@b.com' }} />)
    expect(screen.getByText(/Free Plan/i)).toBeInTheDocument()
    expect(screen.getByText(/5,000 events storage/i)).toBeInTheDocument()
    expect(screen.getByText(/Contact to Upgrade/i)).toBeInTheDocument()
  })

  it('renders Free plan with no email (mailto fallback)', () => {
    render(<PlanDetailsCard me={{ plan: 'Free' }} />)
    const link = screen.getByRole('link', { name: /Contact to Upgrade/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('body=Hi'))
  })

  it('renders Basic plan details', () => {
    render(<PlanDetailsCard me={{ plan: 'Basic' }} />)
    expect(screen.getByText(/Basic Plan — \$1\/mo/i)).toBeInTheDocument()
    expect(screen.getByText(/50,000 events storage/i)).toBeInTheDocument()
  })

  it('renders unknown plan fallback', () => {
    render(<PlanDetailsCard me={{ plan: 'Pro' }} />)
    expect(screen.getByText(/You're on the Pro plan/i)).toBeInTheDocument()
  })

  it('renders Unknown when me has no plan', () => {
    render(<PlanDetailsCard me={{ email: 'a@b.com' }} />)
    expect(screen.getByText(/You're on the Unknown plan/i)).toBeInTheDocument()
  })
})
