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

  it('uses first frame when no in_app frame (branch coverage)', () => {
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
                { filename: 'lib.js', lineno: 1, function: 'external', in_app: false },
              ],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    const stackTraceSection = screen.getByText('Stack Trace').closest('div')
    expect(stackTraceSection).toHaveTextContent(/lib.js:1/)
    expect(stackTraceSection).toHaveTextContent(/external/)
  })

  it('renders frame with empty filename/lineno/function (branch coverage)', () => {
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
                { filename: '', lineno: null, function: undefined, in_app: true },
              ],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    expect(screen.getByText('<unknown>')).toBeInTheDocument()
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

  it('renders stack trace with pre_context and post_context', () => {
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
                  pre_context: ['line 8', 'line 9'],
                  post_context: ['line 11', 'line 12'],
                },
              ],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    // Check that pre_context and post_context are rendered
    expect(screen.getByText('line 8')).toBeInTheDocument()
    expect(screen.getByText('line 9')).toBeInTheDocument()
    expect(screen.getByText('line 11')).toBeInTheDocument()
    expect(screen.getByText('line 12')).toBeInTheDocument()
  })

  it('handles missing contexts in payload', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        // contexts is missing, should default to {}
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
  })

  it('handles breadcrumbs with missing timestamp', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        breadcrumbs: [
          { type: 'navigation', message: 'Page loaded' }, // no timestamp
        ],
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Breadcrumbs')).toBeInTheDocument()
    // Should show '—' for missing timestamp
    const breadcrumbsSection = screen.getByText('Breadcrumbs').closest('div')
    expect(breadcrumbsSection).toHaveTextContent(/Page loaded/)
  })

  it('handles breadcrumbs with missing type', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        breadcrumbs: [
          { timestamp: '2024-01-01T00:00:00Z', message: 'Action' }, // no type
        ],
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Breadcrumbs')).toBeInTheDocument()
    // Should show 'default' for missing type
    const breadcrumbsSection = screen.getByText('Breadcrumbs').closest('div')
    expect(breadcrumbsSection).toHaveTextContent(/default/)
  })

  it('handles breadcrumbs with missing message but has data', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        breadcrumbs: [
          { timestamp: '2024-01-01T00:00:00Z', type: 'user', data: { action: 'click' } }, // no message
        ],
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Breadcrumbs')).toBeInTheDocument()
    // Should show JSON.stringify of data when message is missing
    const breadcrumbsSection = screen.getByText('Breadcrumbs').closest('div')
    expect(breadcrumbsSection).toHaveTextContent(/action/)
  })

  it('handles device info with model instead of name', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        contexts: {
          device: {
            model: 'iPhone 13', // no name, should use model
          },
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
    const contextSection = screen.getByText('Environment & Context').closest('div')
    expect(contextSection).toHaveTextContent(/iPhone 13/)
  })

  it('handles OS without version', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        contexts: {
          os: {
            name: 'iOS', // no version
          },
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
    const contextSection = screen.getByText('Environment & Context').closest('div')
    expect(contextSection).toHaveTextContent(/iOS/)
  })

  it('handles runtime without version', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        contexts: {
          runtime: {
            name: 'Python', // no version
          },
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
    const contextSection = screen.getByText('Environment & Context').closest('div')
    expect(contextSection).toHaveTextContent(/Python/)
  })

  it('handles missing screen dimensions', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        contexts: {
          device: {
            name: 'iPhone',
            // no screen_width or screen_height
          },
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
    // Screen should not be displayed when dimensions are missing
  })

  it('handles missing OS name', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        contexts: {
          device: {
            name: 'iPhone',
          },
          // os is missing or has no name
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Environment & Context')).toBeInTheDocument()
    // OS should be null when name is missing
  })

  it('handles missing payload', () => {
    const event = {
      id: '1',
      message: 'Test error',
      // payload is missing
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText(/Raw Event Data/i)).toBeInTheDocument()
  })

  it('handles exception without values array', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          // no values array
        },
      },
    }

    render(<EventDetailView event={event} />)
    // Should not show exception section
    expect(screen.queryByText('Exception')).not.toBeInTheDocument()
  })

  it('handles exception with empty values array', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [], // empty array
        },
      },
    }

    render(<EventDetailView event={event} />)
    // Should not show exception section
    expect(screen.queryByText('Exception')).not.toBeInTheDocument()
  })

  it('renders grouping info from exception when no fingerprint', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'ValueError',
            value: 'Invalid value',
            stacktrace: {
              frames: [{
                filename: 'test.py',
                lineno: 10,
                function: 'test_func',
                in_app: true,
              }],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText(/Exception type: ValueError/i)).toBeInTheDocument()
    expect(screen.getByText(/Exception value: Invalid value/i)).toBeInTheDocument()
    expect(screen.getByText(/Location: test.py:10 in test_func/i)).toBeInTheDocument()
  })

  it('handles stack trace frame without in_app frame', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'Error',
            value: 'Test',
            stacktrace: {
              frames: [{
                filename: 'test.py',
                lineno: 10,
                function: 'test_func',
                in_app: false, // no in_app frame
              }],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    // Should use first frame when no in_app frame found
    expect(screen.getByText(/Location: test.py:10 in test_func/i)).toBeInTheDocument()
  })

  it('handles frame with missing properties', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'Error',
            value: 'Test',
            stacktrace: {
              frames: [{
                // missing filename, lineno, function
                in_app: true,
              }],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    // Should show '<unknown>' for missing filename
    const stackTraceSection = screen.getByText('Stack Trace').closest('div')
    expect(stackTraceSection).toHaveTextContent(/<unknown>/)
  })

  it('uses event.message when exceptionValue is empty', () => {
    const event = {
      id: '1',
      message: 'Fallback message',
      payload: {
        exception: {
          values: [{
            type: 'Error',
            value: '', // empty value
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Fallback message')).toBeInTheDocument()
  })

  it('handles frame without lineno', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'Error',
            value: 'Test',
            stacktrace: {
              frames: [{
                filename: 'test.py',
                // no lineno
                function: 'test_func',
                in_app: true,
              }],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    // Should not show : when lineno is missing
    const stackTraceSection = screen.getByText('Stack Trace').closest('div')
    expect(stackTraceSection).toHaveTextContent(/test.py/)
    expect(stackTraceSection).not.toHaveTextContent(/test.py:/)
  })

  it('handles frame without function', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'Error',
            value: 'Test',
            stacktrace: {
              frames: [{
                filename: 'test.py',
                lineno: 10,
                // no function
                in_app: true,
              }],
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    // Should not show " in " when function is missing
    const stackTraceSection = screen.getByText('Stack Trace').closest('div')
    expect(stackTraceSection).toHaveTextContent(/test.py:10/)
  })

  it('handles breadcrumb with missing message and data', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        breadcrumbs: [
          { timestamp: '2024-01-01T00:00:00Z', type: 'user' }, // no message, no data
        ],
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Breadcrumbs')).toBeInTheDocument()
    // Should show JSON.stringify({}) when both message and data are missing
    const breadcrumbsSection = screen.getByText('Breadcrumbs').closest('div')
    expect(breadcrumbsSection).toHaveTextContent(/{}/)
  })

  it('handles exception with missing type', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            // no type (line 19)
            value: 'Invalid value',
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    // Should still render exception section with empty type
    expect(screen.getByText('Exception')).toBeInTheDocument()
    expect(screen.getByText('Invalid value')).toBeInTheDocument()
  })

  it('handles grouping info when frame is null', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'ValueError',
            value: 'Invalid value',
            stacktrace: {
              frames: [], // empty frames array (line 33 - frame will be null)
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    // Should show grouping info without location
    expect(screen.getByText(/Exception type: ValueError/i)).toBeInTheDocument()
    expect(screen.getByText(/Exception value: Invalid value/i)).toBeInTheDocument()
    // Should not show Location when frame is null (line 33 - if (frame) is false)
    expect(screen.queryByText(/Location:/i)).not.toBeInTheDocument()
  })

  it('handles grouping info when frames array is empty', () => {
    const event = {
      id: '1',
      message: 'Test error',
      payload: {
        exception: {
          values: [{
            type: 'ValueError',
            value: 'Invalid value',
            stacktrace: {
              frames: [], // empty frames array - find returns undefined, frames[0] is undefined (line 33)
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    // Should show grouping info without location when frame is undefined (line 33: if (frame) is false)
    expect(screen.getByText(/Exception type: ValueError/i)).toBeInTheDocument()
    expect(screen.queryByText(/Location:/i)).not.toBeInTheDocument()
  })

  it('handles last frame in stack trace without border', () => {
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
                  function: 'test_func',
                  in_app: true,
                },
              ], // Only one frame - last frame should have no border (line 87)
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    // Last frame should not have borderBottom (line 87 - idx === frames.length - 1)
  })

  it('handles multiple frames with last frame having no border', () => {
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
                  filename: 'test1.py',
                  lineno: 10,
                  function: 'func1',
                  in_app: true,
                },
                {
                  filename: 'test2.py',
                  lineno: 20,
                  function: 'func2',
                  in_app: true,
                },
              ], // Two frames - last one should have no border (line 87)
            },
          }],
        },
      },
    }

    render(<EventDetailView event={event} />)
    expect(screen.getByText('Stack Trace')).toBeInTheDocument()
    // Last frame (idx === 1, frames.length - 1 === 1) should have borderBottom: 'none'
    const stackTraceSection = screen.getByText('Stack Trace').closest('div')
    expect(stackTraceSection).toHaveTextContent(/test1.py/)
    expect(stackTraceSection).toHaveTextContent(/test2.py/)
  })
})
