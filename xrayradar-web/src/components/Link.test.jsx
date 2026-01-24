import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link } from './Link'
import * as navigation from '../utils/navigation'

vi.mock('../utils/navigation', () => ({
  navigate: vi.fn(),
}))

describe('Link', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders link with correct href', () => {
    render(<Link to="/dashboard">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    expect(link).toHaveAttribute('href', '/dashboard')
  })

  it('calls navigate on click', async () => {
    const user = userEvent.setup()
    render(<Link to="/dashboard">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    await user.click(link)
    expect(navigation.navigate).toHaveBeenCalledWith('/dashboard')
  })

  it('prevents default navigation', async () => {
    const user = userEvent.setup()
    render(<Link to="/dashboard">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true })
    const preventDefaultSpy = vi.spyOn(clickEvent, 'preventDefault')
    link.dispatchEvent(clickEvent)
    expect(preventDefaultSpy).toHaveBeenCalled()
  })

  it('allows opening in new tab with meta key', () => {
    render(<Link to="/dashboard">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    const clickEvent = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      metaKey: true,
      button: 0,
    })
    link.dispatchEvent(clickEvent)
    expect(navigation.navigate).not.toHaveBeenCalled()
  })

  it('applies className', () => {
    render(<Link to="/dashboard" className="custom-class">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    expect(link).toHaveClass('custom-class')
  })
})
