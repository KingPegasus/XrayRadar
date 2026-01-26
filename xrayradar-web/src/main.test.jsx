import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock ReactDOM before importing
const mockRender = vi.fn()
const mockCreateRoot = vi.fn(() => ({
  render: mockRender,
}))

vi.mock('react-dom/client', () => ({
  default: {
    createRoot: mockCreateRoot,
  },
}))

// Mock App component
vi.mock('./App', () => ({
  default: () => <div>Mock App</div>,
}))

describe('main.jsx', () => {
  let rootElement

  beforeEach(() => {
    vi.clearAllMocks()
    // Create a mock root element
    rootElement = document.createElement('div')
    rootElement.id = 'root'
    document.body.appendChild(rootElement)
  })

  afterEach(() => {
    if (rootElement.parentNode) {
      rootElement.parentNode.removeChild(rootElement)
    }
  })

  it('has root element in DOM', () => {
    const root = document.getElementById('root')
    expect(root).toBeInTheDocument()
  })

  it('renders App to root element', async () => {
    // Dynamically import main.jsx to trigger the render
    await import('./main.jsx')

    // Wait for the render to be called
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(mockCreateRoot).toHaveBeenCalledWith(rootElement)
    expect(mockRender).toHaveBeenCalled()
    
    // Verify render was called with some content (App wrapped in StrictMode)
    expect(mockRender.mock.calls.length).toBeGreaterThan(0)
  })
})
