import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { IssueStatusBadge } from './IssueStatusBadge'

describe('IssueStatusBadge', () => {
  it('renders open status badge', () => {
    render(<IssueStatusBadge status="open" />)
    expect(screen.getByText('Open')).toBeInTheDocument()
  })

  it('renders in_progress status badge', () => {
    render(<IssueStatusBadge status="in_progress" />)
    expect(screen.getByText('In Progress')).toBeInTheDocument()
  })

  it('renders resolved status badge', () => {
    render(<IssueStatusBadge status="resolved" />)
    expect(screen.getByText('Resolved')).toBeInTheDocument()
  })

  it('renders ignored status badge', () => {
    render(<IssueStatusBadge status="ignored" />)
    expect(screen.getByText('Ignored')).toBeInTheDocument()
  })

  it('shows resolved release when provided', () => {
    render(<IssueStatusBadge status="resolved" resolvedRelease="v1.0.0" />)
    expect(screen.getByText('Resolved')).toBeInTheDocument()
    expect(screen.getByText('(v1.0.0)')).toBeInTheDocument()
  })

  it('shows reopened indicator when reopened and status is open', () => {
    render(<IssueStatusBadge status="open" reopened={true} />)
    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.getByText('(reopened)')).toBeInTheDocument()
  })

  it('does not show reopened indicator when status is not open', () => {
    render(<IssueStatusBadge status="resolved" reopened={true} />)
    expect(screen.getByText('Resolved')).toBeInTheDocument()
    expect(screen.queryByText('(reopened)')).not.toBeInTheDocument()
  })

  it('does not show reopened indicator when reopened is false', () => {
    render(<IssueStatusBadge status="open" reopened={false} />)
    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.queryByText('(reopened)')).not.toBeInTheDocument()
  })

  it('renders as button when onClick is provided', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(<IssueStatusBadge status="open" onClick={onClick} />)
    
    const badge = screen.getByText('Open')
    expect(badge.tagName).toBe('BUTTON')
    expect(badge).toHaveAttribute('type', 'button')
    expect(badge).toHaveAttribute('title', 'Click to change status')
    expect(badge).toHaveAttribute('aria-label', 'Change issue status')
    
    await user.click(badge)
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('renders as span when onClick is not provided', () => {
    render(<IssueStatusBadge status="open" />)
    const badge = screen.getByText('Open')
    expect(badge.tagName).toBe('SPAN')
    expect(badge).not.toHaveAttribute('onClick')
  })

  it('shows edit icon when onClick is provided', () => {
    const onClick = vi.fn()
    render(<IssueStatusBadge status="open" onClick={onClick} />)
    const badge = screen.getByText('Open')
    const icon = badge.querySelector('svg')
    expect(icon).toBeInTheDocument()
    expect(icon).toHaveAttribute('aria-hidden', 'true')
  })

  it('does not show edit icon when onClick is not provided', () => {
    render(<IssueStatusBadge status="open" />)
    const badge = screen.getByText('Open')
    const icon = badge.querySelector('svg')
    expect(icon).not.toBeInTheDocument()
  })

  it('defaults to open status when invalid status provided', () => {
    render(<IssueStatusBadge status="invalid" />)
    expect(screen.getByText('Open')).toBeInTheDocument()
  })
})
