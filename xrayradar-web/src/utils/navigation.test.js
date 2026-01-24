import { describe, it, expect, vi, beforeEach } from 'vitest'
import { navigate } from './navigation'

describe('navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(window, 'location', {
      value: { pathname: '/' },
      writable: true,
      configurable: true,
    })
    window.history.pushState = vi.fn()
    window.dispatchEvent = vi.fn()
  })

  it('navigates to new path', () => {
    navigate('/dashboard')
    expect(window.history.pushState).toHaveBeenCalledWith({}, '', '/dashboard')
    expect(window.dispatchEvent).toHaveBeenCalled()
  })

  it('does not navigate if path is same', () => {
    Object.defineProperty(window, 'location', {
      value: { pathname: '/dashboard' },
      writable: true,
      configurable: true,
    })
    navigate('/dashboard')
    expect(window.history.pushState).not.toHaveBeenCalled()
  })

  it('dispatches popstate event', () => {
    navigate('/test')
    const call = window.dispatchEvent.mock.calls[0][0]
    expect(call.type).toBe('popstate')
    expect(call).toBeInstanceOf(PopStateEvent)
  })
})
