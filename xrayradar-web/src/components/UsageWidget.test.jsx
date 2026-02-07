import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UsageWidget } from './UsageWidget'
import * as navigation from '../utils/navigation'

vi.mock('../utils/navigation')

describe('UsageWidget', () => {
  it('returns null when usage is undefined', () => {
    const { container } = render(<UsageWidget usage={undefined} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when usage is null', () => {
    const { container } = render(<UsageWidget usage={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders usage with limit', () => {
    render(
      <UsageWidget
        usage={{
          current_count: 100,
          limit: 1000,
          plan: 'Free',
          percentage_used: 2,
          is_exceeded: false,
          is_near_limit: false,
        }}
      />
    )
    expect(screen.getByText(/100/)).toBeInTheDocument()
    expect(screen.getByText(/1,000/)).toBeInTheDocument()
    expect(screen.getByText(/Free Plan/i)).toBeInTheDocument()
  })

  it('renders usage with unlimited (null limit)', () => {
    render(
      <UsageWidget
        usage={{
          current_count: 100,
          limit: null,
          plan: 'Basic',
          is_exceeded: false,
          is_near_limit: false,
        }}
      />
    )
    expect(screen.getByText(/∞/)).toBeInTheDocument()
  })

  it('shows Basic plan badge styling', () => {
    render(
      <UsageWidget
        usage={{
          current_count: 0,
          limit: 50000,
          plan: 'Basic',
          is_exceeded: false,
          is_near_limit: false,
        }}
      />
    )
    expect(screen.getByText(/Basic Plan/i)).toBeInTheDocument()
  })

  it('shows exceeded state with Upgrade button for Free plan', async () => {
    const user = userEvent.setup()
    render(
      <UsageWidget
        usage={{
          current_count: 5000,
          limit: 5000,
          plan: 'Free',
          percentage_used: 100,
          is_exceeded: true,
          is_near_limit: false,
        }}
      />
    )
    expect(screen.getByText(/You've exceeded your event limit/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Upgrade/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Upgrade/i }))
    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard/settings')
  })

  it('shows near limit state with Upgrade button for Free plan', async () => {
    const user = userEvent.setup()
    render(
      <UsageWidget
        usage={{
          current_count: 4500,
          limit: 5000,
          plan: 'Free',
          percentage_used: 90,
          is_near_limit: true,
          is_exceeded: false,
        }}
      />
    )
    expect(screen.getByText(/You're approaching your event limit/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Upgrade/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Upgrade/i }))
    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard/settings')
  })

  it('does not show Upgrade when exceeded but not Free plan', () => {
    render(
      <UsageWidget
        usage={{
          current_count: 50000,
          limit: 50000,
          plan: 'Basic',
          percentage_used: 100,
          is_exceeded: true,
          is_near_limit: false,
        }}
      />
    )
    expect(screen.getByText(/You've exceeded your event limit/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Upgrade/i })).not.toBeInTheDocument()
  })

  it('shows percentage used when provided', () => {
    render(
      <UsageWidget
        usage={{
          current_count: 100,
          limit: 1000,
          plan: 'Free',
          percentage_used: 10,
          is_exceeded: false,
          is_near_limit: false,
        }}
      />
    )
    expect(screen.getByText(/10\.0% used/i)).toBeInTheDocument()
  })
})
