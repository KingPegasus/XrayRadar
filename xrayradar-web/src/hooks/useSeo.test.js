import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useSeo } from './useSeo'

const meta = (sel) => document.head.querySelector(sel)?.getAttribute('content')

describe('useSeo', () => {
  it('sets title, description and canonical for indexable pages', () => {
    renderHook(() => useSeo('/privacy'))
    expect(document.title).toBe('Privacy Policy — XrayRadar')
    expect(meta('meta[name="robots"]')).toMatch(/^index/)
    expect(document.head.querySelector('link[rel="canonical"]').getAttribute('href')).toBe('https://xrayradar.com/privacy')
    expect(meta('meta[property="og:url"]')).toBe('https://xrayradar.com/privacy')
  })

  it('marks dashboard pages noindex and removes canonical', () => {
    renderHook(() => useSeo('/dashboard/projects/1'))
    expect(document.title).toBe('Dashboard — XrayRadar')
    expect(meta('meta[name="robots"]')).toBe('noindex, follow')
    expect(document.head.querySelector('link[rel="canonical"]')).toBeNull()
    expect(document.head.querySelector('meta[property="og:url"]')).toBeNull()
  })

  it('marks unknown pages as not found', () => {
    renderHook(() => useSeo('/nope'))
    expect(document.title).toBe('Page not found — XrayRadar')
    expect(meta('meta[name="robots"]')).toBe('noindex, follow')
  })
})
