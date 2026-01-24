import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePathname } from './usePathname'

describe('usePathname', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'location', {
      value: { pathname: '/' },
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('returns current pathname', () => {
    Object.defineProperty(window, 'location', {
      value: { pathname: '/dashboard' },
      writable: true,
      configurable: true,
    })
    const { result } = renderHook(() => usePathname())
    expect(result.current).toBe('/dashboard')
  })

  it('updates on popstate event', () => {
    Object.defineProperty(window, 'location', {
      value: { pathname: '/' },
      writable: true,
      configurable: true,
    })
    const { result } = renderHook(() => usePathname())
    expect(result.current).toBe('/')

    act(() => {
      Object.defineProperty(window, 'location', {
        value: { pathname: '/dashboard' },
        writable: true,
        configurable: true,
      })
      window.dispatchEvent(new PopStateEvent('popstate'))
    })

    expect(result.current).toBe('/dashboard')
  })

  it('handles missing pathname', () => {
    Object.defineProperty(window, 'location', {
      value: {},
      writable: true,
      configurable: true,
    })
    const { result } = renderHook(() => usePathname())
    expect(result.current).toBe('/')
  })

  it('cleans up event listener on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
    const { unmount } = renderHook(() => usePathname())
    unmount()
    expect(removeEventListenerSpy).toHaveBeenCalledWith('popstate', expect.any(Function))
  })
})
