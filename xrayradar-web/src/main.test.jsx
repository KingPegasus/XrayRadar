/* global document, setTimeout */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('main.jsx', () => {
  let rootElement
  let mockRender
  let mockCreateRoot

  beforeEach(() => {
    mockRender = vi.fn()
    mockCreateRoot = vi.fn(() => ({ render: mockRender }))

    rootElement = document.createElement('div')
    rootElement.id = 'root'
    document.body.appendChild(rootElement)
  })

  afterEach(() => {
    vi.doUnmock('react-dom/client')
    if (rootElement.parentNode) {
      rootElement.parentNode.removeChild(rootElement)
    }
  })

  it('has root element in DOM', () => {
    const root = document.getElementById('root')
    expect(root).toBeInTheDocument()
  })

  it('renders App to root element', async () => {
    vi.resetModules()
    vi.doMock('react-dom/client', () => ({
      default: {
        createRoot: mockCreateRoot,
      },
    }))

    await import('./main.jsx')

    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(mockCreateRoot).toHaveBeenCalledWith(rootElement)
    expect(mockRender).toHaveBeenCalled()
    expect(mockRender.mock.calls.length).toBeGreaterThan(0)
  })
})
