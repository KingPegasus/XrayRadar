import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link } from './Link'

describe('Link', () => {
  let hrefAssign

  beforeEach(() => {
    hrefAssign = vi.fn()
    const loc = { pathname: '/', assign: vi.fn(), replace: vi.fn() }
    Object.defineProperty(loc, 'href', {
      set: (v) => hrefAssign(v),
      get: () => '',
      configurable: true,
    })
    Object.defineProperty(window, 'location', { value: loc, configurable: true, writable: true })
  })

  it('renders link with correct href', () => {
    render(<Link to="/dashboard">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    expect(link).toHaveAttribute('href', '/dashboard')
  })

  it('navigates on click', async () => {
    const user = userEvent.setup()
    render(<Link to="/dashboard">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    await user.click(link)
    expect(hrefAssign).toHaveBeenCalledWith('/dashboard')
  })

  it('prevents default navigation', async () => {
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
    expect(hrefAssign).not.toHaveBeenCalled()
  })

  it('applies className', () => {
    render(<Link to="/dashboard" className="custom-class">Dashboard</Link>)
    const link = screen.getByRole('link', { name: /Dashboard/i })
    expect(link).toHaveClass('custom-class')
  })

  it('does not intercept external http URLs', async () => {
    const user = userEvent.setup()
    render(<Link to="http://example.com">External</Link>)
    await user.click(screen.getByRole('link', { name: /External/i }))
    expect(hrefAssign).not.toHaveBeenCalled()
  })

  it('does not intercept external https URLs', async () => {
    const user = userEvent.setup()
    render(<Link to="https://example.com">External</Link>)
    await user.click(screen.getByRole('link', { name: /External/i }))
    expect(hrefAssign).not.toHaveBeenCalled()
  })

  it('does not intercept mailto links', async () => {
    const user = userEvent.setup()
    render(<Link to="mailto:dev@example.com">Email</Link>)
    await user.click(screen.getByRole('link', { name: /Email/i }))
    expect(hrefAssign).not.toHaveBeenCalled()
  })

  it('does not intercept hash-only links', async () => {
    const user = userEvent.setup()
    render(<Link to="#section">Section</Link>)
    await user.click(screen.getByRole('link', { name: /Section/i }))
    expect(hrefAssign).not.toHaveBeenCalled()
  })

  it('does not intercept empty or falsy href', async () => {
    const user = userEvent.setup()
    const { container } = render(<Link to="">Empty</Link>)
    const link = container.querySelector('a[href=""]')
    await user.click(link)
    expect(hrefAssign).not.toHaveBeenCalled()
  })
})
