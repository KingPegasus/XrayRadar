import { useState, useMemo } from 'react'

/**
 * Get icon for breadcrumb type
 */
function getTypeIcon(type) {
  switch (type) {
    case 'http':
      return '↔'
    case 'navigation':
      return '→'
    case 'ui':
      return '👆'
    case 'console':
      return '⌨'
    case 'error':
      return '!'
    case 'query':
      return '⚡'
    case 'user':
      return '👤'
    default:
      return '•'
  }
}

/**
 * Get CSS class for breadcrumb level
 */
function getLevelClass(level) {
  switch (level) {
    case 'debug':
      return 'breadcrumbLevel--debug'
    case 'warning':
      return 'breadcrumbLevel--warning'
    case 'error':
      return 'breadcrumbLevel--error'
    case 'info':
    default:
      return 'breadcrumbLevel--info'
  }
}

/**
 * Parse timestamp to ms, treating ISO strings without timezone as UTC.
 * Older records / SDK may send UTC without "Z"; JS otherwise parses as local time (e.g. GMT+5),
 * which can show bogus "300m after" when the offset is 5 hours.
 */
function parseTimestampAsUtc(value) {
  if (value == null) return NaN
  if (typeof value === 'number' && !isNaN(value)) return value
  const s = typeof value === 'string' ? value.trim() : String(value)
  if (!s) return NaN
  // ISO-like without Z or ±offset → treat as UTC
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s) && !/Z|[+-]\d{2}:?\d{2}$/.test(s)) {
    return new Date(s + 'Z').getTime()
  }
  return new Date(value).getTime()
}

/**
 * Calculate relative time string (e.g., "2s before error")
 */
function getRelativeTime(breadcrumbTimestamp, errorTimestamp) {
  if (!breadcrumbTimestamp || !errorTimestamp) {
    return null
  }

  try {
    const bcTime = parseTimestampAsUtc(breadcrumbTimestamp)
    const errTime = parseTimestampAsUtc(errorTimestamp)
    const diffMs = errTime - bcTime

    if (isNaN(diffMs)) {
      return null
    }

    if (diffMs < 0) {
      // Breadcrumb after error (shouldn't happen, but handle it)
      const absDiff = Math.abs(diffMs)
      if (absDiff < 1000) return 'just after'
      if (absDiff < 60000) return `${Math.round(absDiff / 1000)}s after`
      return `${Math.round(absDiff / 60000)}m after`
    }

    if (diffMs < 1000) return 'just before'
    if (diffMs < 60000) return `${Math.round(diffMs / 1000)}s before`
    if (diffMs < 3600000) return `${Math.round(diffMs / 60000)}m before`
    return `${Math.round(diffMs / 3600000)}h before`
  } catch {
    return null
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return '—'
  try {
    const date = new Date(timestamp)
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return '—'
    }
    return date.toLocaleTimeString()
  } catch {
    return '—'
  }
}

export function BreadcrumbTimeline({ breadcrumbs, errorTimestamp }) {
  const [expandedIndex, setExpandedIndex] = useState(null)
  const [showNewestFirst, setShowNewestFirst] = useState(false)

  const sortedBreadcrumbs = useMemo(() => {
    if (!breadcrumbs || breadcrumbs.length === 0) return []
    const sorted = [...breadcrumbs]
    if (showNewestFirst) {
      sorted.reverse()
    }
    return sorted
  }, [breadcrumbs, showNewestFirst])

  if (!breadcrumbs || breadcrumbs.length === 0) {
    return (
      <div className="breadcrumbTimeline breadcrumbTimeline--empty">
        No breadcrumbs recorded for this event.
      </div>
    )
  }

  const toggleExpand = (idx) => {
    setExpandedIndex(expandedIndex === idx ? null : idx)
  }

  return (
    <div className="breadcrumbTimeline">
      <div className="breadcrumbTimelineHeader">
        <span className="breadcrumbTimelineCount">
          {breadcrumbs.length} breadcrumb{breadcrumbs.length !== 1 ? 's' : ''}
        </span>
        <button
          type="button"
          className="breadcrumbTimelineToggle"
          onClick={() => setShowNewestFirst(!showNewestFirst)}
        >
          {showNewestFirst ? '↓ Oldest first' : '↑ Newest first'}
        </button>
      </div>

      <div className="breadcrumbTimelineList">
        {sortedBreadcrumbs.map((crumb, idx) => {
          const type = crumb.type || 'default'
          const level = crumb.level || 'info'
          const message = crumb.message || ''
          const data = crumb.data
          const hasData = data && Object.keys(data).length > 0
          const isExpanded = expandedIndex === idx
          const relativeTime = getRelativeTime(crumb.timestamp, errorTimestamp)

          return (
            <div
              key={idx}
              className={`breadcrumbItem ${getLevelClass(level)} ${isExpanded ? 'breadcrumbItem--expanded' : ''}`}
            >
              <div className="breadcrumbItemMain" onClick={() => hasData && toggleExpand(idx)}>
                <span className="breadcrumbIcon" title={type}>
                  {getTypeIcon(type)}
                </span>

                <span className="breadcrumbType">{type}</span>

                {crumb.category && (
                  <span className="breadcrumbCategory">{crumb.category}</span>
                )}

                <span className="breadcrumbMessage" title={message}>
                  {message || (hasData ? JSON.stringify(data) : '(no message)')}
                </span>

                <span className="breadcrumbTime">
                  {relativeTime && (
                    <span className="breadcrumbRelativeTime">{relativeTime}</span>
                  )}
                  <span className="breadcrumbAbsoluteTime">
                    {formatTimestamp(crumb.timestamp)}
                  </span>
                </span>

                {hasData && (
                  <span className="breadcrumbExpandIcon">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                )}
              </div>

              {isExpanded && hasData && (
                <div className="breadcrumbData">
                  <pre>{JSON.stringify(data, null, 2)}</pre>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
