import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BreadcrumbTimeline } from './BreadcrumbTimeline'

describe('BreadcrumbTimeline', () => {
  describe('empty states', () => {
    it('shows empty message when breadcrumbs is undefined', () => {
      render(<BreadcrumbTimeline breadcrumbs={undefined} />)
      expect(screen.getByText('No breadcrumbs recorded for this event.')).toBeInTheDocument()
    })

    it('shows empty message when breadcrumbs is null', () => {
      render(<BreadcrumbTimeline breadcrumbs={null} />)
      expect(screen.getByText('No breadcrumbs recorded for this event.')).toBeInTheDocument()
    })

    it('shows empty message when breadcrumbs is empty array', () => {
      render(<BreadcrumbTimeline breadcrumbs={[]} />)
      expect(screen.getByText('No breadcrumbs recorded for this event.')).toBeInTheDocument()
    })
  })

  describe('rendering breadcrumbs', () => {
    it('renders single breadcrumb', () => {
      const breadcrumbs = [
        { type: 'http', message: 'GET /api/users', level: 'info' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('1 breadcrumb')).toBeInTheDocument()
      expect(screen.getByText('http')).toBeInTheDocument()
      expect(screen.getByText('GET /api/users')).toBeInTheDocument()
    })

    it('renders multiple breadcrumbs with plural count', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request 1' },
        { type: 'ui', message: 'Click' },
        { type: 'navigation', message: 'Navigate' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('3 breadcrumbs')).toBeInTheDocument()
      expect(screen.getByText('Request 1')).toBeInTheDocument()
      expect(screen.getByText('Click')).toBeInTheDocument()
      expect(screen.getByText('Navigate')).toBeInTheDocument()
    })

    it('renders breadcrumb types correctly', () => {
      const breadcrumbs = [
        { type: 'http', message: 'HTTP' },
        { type: 'navigation', message: 'Nav' },
        { type: 'ui', message: 'UI' },
        { type: 'console', message: 'Console' },
        { type: 'error', message: 'Error' },
        { type: 'query', message: 'Query' },
        { type: 'user', message: 'User' },
        { type: 'default', message: 'Default' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('8 breadcrumbs')).toBeInTheDocument()
    })

    it('shows default type when type is missing', () => {
      const breadcrumbs = [
        { message: 'No type specified' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('default')).toBeInTheDocument()
    })

    it('renders category when present', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request', category: 'api' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('api')).toBeInTheDocument()
    })
  })

  describe('timestamps', () => {
    it('shows formatted timestamp', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:45Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Should show some time format (exact format depends on locale)
      const timeElements = screen.getAllByText(/\d{1,2}:\d{2}/)
      expect(timeElements.length).toBeGreaterThan(0)
    })

    it('shows dash when timestamp is missing', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('—')).toBeInTheDocument()
    })

    it('shows relative time when errorTimestamp provided', () => {
      const errorTime = new Date('2026-01-27T12:30:50Z')
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:45Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime.toISOString()} />)
      
      expect(screen.getByText('5s before')).toBeInTheDocument()
    })

    it('shows "just before" for very recent breadcrumbs', () => {
      const errorTime = new Date('2026-01-27T12:30:50.500Z')
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:50Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime.toISOString()} />)
      
      expect(screen.getByText('just before')).toBeInTheDocument()
    })

    it('shows minutes for longer intervals', () => {
      const errorTime = new Date('2026-01-27T12:35:00Z')
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:00Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime.toISOString()} />)
      
      expect(screen.getByText('5m before')).toBeInTheDocument()
    })

    it('shows hours for very long intervals', () => {
      const errorTime = new Date('2026-01-27T14:30:00Z')
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:00Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime.toISOString()} />)
      
      expect(screen.getByText('2h before')).toBeInTheDocument()
    })
  })

  describe('sorting toggle', () => {
    it('shows oldest first by default', () => {
      const breadcrumbs = [
        { type: 'http', message: 'First', timestamp: '2026-01-27T12:00:00Z' },
        { type: 'http', message: 'Second', timestamp: '2026-01-27T12:01:00Z' },
        { type: 'http', message: 'Third', timestamp: '2026-01-27T12:02:00Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      const messages = screen.getAllByText(/First|Second|Third/)
      expect(messages[0]).toHaveTextContent('First')
      expect(messages[2]).toHaveTextContent('Third')
    })

    it('toggles to newest first when button clicked', () => {
      const breadcrumbs = [
        { type: 'http', message: 'First', timestamp: '2026-01-27T12:00:00Z' },
        { type: 'http', message: 'Second', timestamp: '2026-01-27T12:01:00Z' },
        { type: 'http', message: 'Third', timestamp: '2026-01-27T12:02:00Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Click toggle button
      fireEvent.click(screen.getByText('↑ Newest first'))
      
      // Now should show newest first
      const messages = screen.getAllByText(/First|Second|Third/)
      expect(messages[0]).toHaveTextContent('Third')
      expect(messages[2]).toHaveTextContent('First')
      
      // Button text should change
      expect(screen.getByText('↓ Oldest first')).toBeInTheDocument()
    })

    it('toggles back to oldest first', () => {
      const breadcrumbs = [
        { type: 'http', message: 'First' },
        { type: 'http', message: 'Second' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Toggle to newest first
      fireEvent.click(screen.getByText('↑ Newest first'))
      // Toggle back to oldest first
      fireEvent.click(screen.getByText('↓ Oldest first'))
      
      expect(screen.getByText('↑ Newest first')).toBeInTheDocument()
    })
  })

  describe('expandable data', () => {
    it('shows expand icon when breadcrumb has data', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request', data: { status_code: 200 } }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('▶')).toBeInTheDocument()
    })

    it('does not show expand icon when breadcrumb has no data', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.queryByText('▶')).not.toBeInTheDocument()
    })

    it('expands to show data when clicked', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request', data: { status_code: 200, duration_ms: 45 } }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Click to expand
      fireEvent.click(screen.getByText('Request'))
      
      // Should show expanded data
      expect(screen.getByText('▼')).toBeInTheDocument()
      expect(screen.getByText(/"status_code": 200/)).toBeInTheDocument()
      expect(screen.getByText(/"duration_ms": 45/)).toBeInTheDocument()
    })

    it('collapses data when clicked again', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request', data: { status_code: 200 } }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Expand
      fireEvent.click(screen.getByText('Request'))
      expect(screen.getByText('▼')).toBeInTheDocument()
      
      // Collapse
      fireEvent.click(screen.getByText('Request'))
      expect(screen.getByText('▶')).toBeInTheDocument()
    })

    it('shows JSON data when no message provided', () => {
      const breadcrumbs = [
        { type: 'http', data: { url: '/api/test' } }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Should show JSON representation of data as message
      expect(screen.getByText('{"url":"/api/test"}')).toBeInTheDocument()
    })

    it('shows "(no message)" when neither message nor data', () => {
      const breadcrumbs = [
        { type: 'http' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(screen.getByText('(no message)')).toBeInTheDocument()
    })
  })

  describe('level styling', () => {
    it('applies debug level class', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Debug', level: 'debug' }
      ]
      const { container } = render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(container.querySelector('.breadcrumbLevel--debug')).toBeInTheDocument()
    })

    it('applies info level class', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Info', level: 'info' }
      ]
      const { container } = render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(container.querySelector('.breadcrumbLevel--info')).toBeInTheDocument()
    })

    it('applies warning level class', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Warning', level: 'warning' }
      ]
      const { container } = render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(container.querySelector('.breadcrumbLevel--warning')).toBeInTheDocument()
    })

    it('applies error level class', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Error', level: 'error' }
      ]
      const { container } = render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(container.querySelector('.breadcrumbLevel--error')).toBeInTheDocument()
    })

    it('defaults to info level when not specified', () => {
      const breadcrumbs = [
        { type: 'http', message: 'No level' }
      ]
      const { container } = render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      expect(container.querySelector('.breadcrumbLevel--info')).toBeInTheDocument()
    })
  })

  describe('type icons', () => {
    it('shows HTTP icon for http type', () => {
      const breadcrumbs = [{ type: 'http', message: 'Test' }]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      expect(screen.getByTitle('http')).toHaveTextContent('↔')
    })

    it('shows navigation icon for navigation type', () => {
      const breadcrumbs = [{ type: 'navigation', message: 'Test' }]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      expect(screen.getByTitle('navigation')).toHaveTextContent('→')
    })

    it('shows error icon for error type', () => {
      const breadcrumbs = [{ type: 'error', message: 'Test' }]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      expect(screen.getByTitle('error')).toHaveTextContent('!')
    })

    it('shows default icon for unknown type', () => {
      const breadcrumbs = [{ type: 'unknown', message: 'Test' }]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      expect(screen.getByTitle('unknown')).toHaveTextContent('•')
    })
  })

  describe('edge cases', () => {
    it('handles invalid timestamp gracefully', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: 'invalid-date' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Should show dash for invalid timestamp
      expect(screen.getByText('—')).toBeInTheDocument()
    })

    it('handles empty data object', () => {
      const breadcrumbs = [
        { type: 'http', message: 'Request', data: {} }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      
      // Should not show expand icon for empty data
      expect(screen.queryByText('▶')).not.toBeInTheDocument()
    })

    it('handles breadcrumb after error time', () => {
      const errorTime = new Date('2026-01-27T12:30:00Z')
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:05Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime.toISOString()} />)
      
      // Should show "after" for breadcrumbs after error
      expect(screen.getByText('5s after')).toBeInTheDocument()
    })

    it('parses ISO timestamps without Z as UTC (avoids GMT+5 "300m after" bug)', () => {
      // Older records / SDK may send UTC without "Z"; JS would parse as local time.
      // We treat timezone-less ISO as UTC so relative time is correct.
      const errorTime = '2026-01-29T03:01:44'
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-29T03:01:45' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime} />)
      // With UTC parsing: breadcrumb 1s after error → "1s after". Without fix (local parse) could show "300m after" at GMT+5.
      expect(screen.getByText('1s after')).toBeInTheDocument()
    })

    it('returns null for NaN diff in relative time (covers line 75)', () => {
      // When timestamps produce NaN, should not crash
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:00Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp="invalid" />)
      // Should render without crashing, relative time should be hidden/null
      expect(screen.getByText('Request')).toBeInTheDocument()
    })

    it('shows "just after" for breadcrumb very shortly after error (covers line 81)', () => {
      const errorTime = new Date('2026-01-27T12:30:00Z')
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:30:00.500Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime.toISOString()} />)
      expect(screen.getByText('just after')).toBeInTheDocument()
    })

    it('shows minutes after for longer after intervals (covers line 83)', () => {
      const errorTime = new Date('2026-01-27T12:30:00Z')
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: '2026-01-27T12:35:00Z' }
      ]
      render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp={errorTime.toISOString()} />)
      expect(screen.getByText('5m after')).toBeInTheDocument()
    })

    it('catches errors in relative time calculation (covers line 91)', () => {
      // Malformed timestamp should not crash
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: {} }
      ]
      // Should render without throwing
      expect(() => {
        render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} errorTimestamp="2026-01-27T12:30:00Z" />)
      }).not.toThrow()
      expect(screen.getByText('Request')).toBeInTheDocument()
    })

    it('catches errors in timestamp formatting (covers line 108)', () => {
      // Invalid timestamp object should not crash
      const breadcrumbs = [
        { type: 'http', message: 'Request', timestamp: { toString: () => { throw new Error('fail') } } }
      ]
      // Should render without throwing and show dash
      expect(() => {
        render(<BreadcrumbTimeline breadcrumbs={breadcrumbs} />)
      }).not.toThrow()
      expect(screen.getByText('—')).toBeInTheDocument()
    })
  })
})
