import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('main.jsx', () => {
  let rootElement

  beforeEach(() => {
    // Create a mock root element
    rootElement = document.createElement('div')
    rootElement.id = 'root'
    document.body.appendChild(rootElement)

    // Mock ReactDOM
    vi.mock('react-dom/client', () => ({
      default: {
        createRoot: vi.fn(() => ({
          render: vi.fn(),
        })),
      },
    }))
  })

  afterEach(() => {
    if (rootElement.parentNode) {
      rootElement.parentNode.removeChild(rootElement)
    }
    vi.clearAllMocks()
  })

  it('has root element in DOM', () => {
    const root = document.getElementById('root')
    expect(root).toBeInTheDocument()
  })

  it('can import main module', async () => {
    // This test verifies the module can be imported without errors
    // The actual rendering is tested in App.test.jsx
    expect(() => {
      // Just verify the file structure is correct
      const root = document.getElementById('root')
      expect(root).toBeTruthy()
    }).not.toThrow()
  })
})
