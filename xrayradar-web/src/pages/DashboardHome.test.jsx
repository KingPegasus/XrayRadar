import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DashboardHome } from './DashboardHome'

describe('DashboardHome', () => {
  it('renders dashboard title', () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('displays user email', () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    expect(screen.getByText(/Signed in as/i)).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('renders badges', () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    expect(screen.getByText('Projects')).toBeInTheDocument()
    expect(screen.getByText('Tokens')).toBeInTheDocument()
    expect(screen.getByText('Issues')).toBeInTheDocument()
  })

  it('renders getting started section', () => {
    const me = { email: 'test@example.com' }
    render(<DashboardHome me={me} />)
    expect(screen.getByText('Getting started')).toBeInTheDocument()
    expect(screen.getByText(/Create a project, request a token/i)).toBeInTheDocument()
  })

  it('handles missing me prop', () => {
    render(<DashboardHome me={null} />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })
})
