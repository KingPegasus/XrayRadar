import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EventDetailView } from './EventDetailView'

describe('EventDetailView', () => {
  it('renders exception details', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'ValueError',
            value: 'Invalid value',
            stacktrace: null,
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('ValueError')).toBeInTheDocument()
    expect(screen.getByText('Invalid value')).toBeInTheDocument()
  })

  it('renders stack trace', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'Error',
            value: 'Test',
            stacktrace: {
              frames: [
                {
                  filename: 'test.py',
                  lineno: 10,
                  function: 'test_function',
                  in_app: true,
                  context_line: 'raise Error()',
                },
              ],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    // Check for unique content in stack trace
    const stackTraceSection = screen.getByText('Stack Trace').closest('div')
    expect(stackTraceSection).toHaveTextContent(/test.py:10/)
    expect(stackTraceSection).toHaveTextContent(/test_function/)
  })

  it('renders breadcrumbs', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        breadcrumbs: [
          { timestamp: '2024-01-01T00:00:00Z', type: 'navigation', message: 'Page loaded' },
          { timestamp: '2024-01-01T00:00:01Z', type: 'user', message: 'Button clicked' },
        ],
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Breadcrumbs')).toBeInTheDocument()
    const breadcrumbsSection = screen.getByText('Breadcrumbs').closest('div')
    expect(breadcrumbsSection).toHaveTextContent(/Page loaded/)
    expect(breadcrumbsSection).toHaveTextContent(/Button clicked/)
  })

  it('renders tags', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        tags: {
          browser: 'Chrome',
          os: 'Linux',
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText(/browser: Chrome/i)).toBeInTheDocument()
    expect(screen.getByText(/os: Linux/i)).toBeInTheDocument()
  })

  it('renders user data', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        user: {
          id: '123',
          email: 'user@example.com',
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
    // User data is in the Environment & Context section
    const contextSection = screen.getByText('Environment & Context').closest('div')
    expect(contextSection).toHaveTextContent(/user@example.com/)
  })

  it('renders device info', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        contexts: {
          device: {
            name: 'iPhone',
            screen_width: 375,
            screen_height: 667,
          },
          os: {
            name: 'iOS',
            version: '15.0',
          },
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
    const contextSection = screen.getByText('Environment & Context').closest('div')
    expect(contextSection).toHaveTextContent(/iPhone/)
    expect(contextSection).toHaveTextContent(/iOS 15.0/)
  })

  it('renders grouping info with fingerprint', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        fingerprint: ['abc123', 'def456'],
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText(/SDK fingerprint: abc123, def456/i)).toBeInTheDocument()
  })

  it('renders raw payload', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        test: 'data',
      },
    }

    render(<EventDetailView event={event} />)
    const details = screen.getByText(/Show raw JSON payload/i)
    expect(details).toBeInTheDocument()
  })

  it('handles empty event', () => {
    const event = {
      id: '1',
      message: '',
      payload: {},
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText(/Raw Event Data/i)).toBeInTheDocument()
  })
})
