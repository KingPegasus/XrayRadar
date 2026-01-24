import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Mock window.location (can be overridden in individual tests)
Object.defineProperty(window, 'location', {
  value: {
    pathname: '/',
    href: '/',
    assign: vi.fn(),
    replace: vi.fn(),
  },
  writable: true,
  configurable: true,
})

// Mock window.history
Object.defineProperty(window, 'history', {
  value: {
    pushState: vi.fn(),
    replaceState: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  },
  writable: true,
})

// Mock PopStateEvent
global.PopStateEvent = class PopStateEvent extends Event {
  constructor(type, eventInitDict) {
    super(type, eventInitDict)
    this.state = eventInitDict?.state
  }
}

// Cleanup after each test
afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  // Reset location to default
  Object.defineProperty(window, 'location', {
    value: {
      pathname: '/',
      href: '/',
      assign: vi.fn(),
      replace: vi.fn(),
    },
    writable: true,
    configurable: true,
  })
})
