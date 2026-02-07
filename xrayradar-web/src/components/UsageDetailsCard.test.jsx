import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UsageDetailsCard } from './UsageDetailsCard'

describe('UsageDetailsCard', () => {
  it('shows loading state', () => {
    render(<UsageDetailsCard usage={null} loading={true} error="" />)
    expect(screen.getByText(/Loading usage/i)).toBeInTheDocument()
  })

  it('shows error state', () => {
    render(<UsageDetailsCard usage={null} loading={false} error="Failed to load" />)
    expect(screen.getByText('Failed to load')).toBeInTheDocument()
  })

  it('shows usage data', () => {
    render(
      <UsageDetailsCard
        usage={{
          current_count: 100,
          limit: 1000,
          percentage_used: 2,
          is_exceeded: false,
          is_near_limit: false,
        }}
        loading={false}
        error=""
      />
    )
    expect(screen.getByText(/100/)).toBeInTheDocument()
    expect(screen.getByText(/1,000/)).toBeInTheDocument()
  })

  it('shows exceeded message', () => {
    render(
      <UsageDetailsCard
        usage={{
          current_count: 1000,
          limit: 1000,
          percentage_used: 100,
          is_exceeded: true,
          is_near_limit: false,
        }}
        loading={false}
        error=""
      />
    )
    expect(screen.getByText(/You've exceeded your event limit/i)).toBeInTheDocument()
  })

  it('shows near limit message', () => {
    render(
      <UsageDetailsCard
        usage={{
          current_count: 900,
          limit: 1000,
          percentage_used: 90,
          is_exceeded: false,
          is_near_limit: true,
        }}
        loading={false}
        error=""
      />
    )
    expect(screen.getByText(/You're approaching your event limit/i)).toBeInTheDocument()
  })

  it('shows unlimited when limit is null', () => {
    render(
      <UsageDetailsCard
        usage={{
          current_count: 100,
          limit: null,
          percentage_used: null,
          is_exceeded: false,
          is_near_limit: false,
        }}
        loading={false}
        error=""
      />
    )
    expect(screen.getByText(/∞/)).toBeInTheDocument()
  })

  it('shows bar without percentage when percentage_used is null', () => {
    render(
      <UsageDetailsCard
        usage={{
          current_count: 50,
          limit: 100,
          percentage_used: null,
          is_exceeded: false,
          is_near_limit: false,
        }}
        loading={false}
        error=""
      />
    )
    expect(screen.getByText(/50/)).toBeInTheDocument()
    expect(screen.getByText(/100/)).toBeInTheDocument()
    expect(screen.queryByText(/% used/)).not.toBeInTheDocument()
  })
})
