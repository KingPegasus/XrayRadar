export function IssueStatusBadge({ status, resolvedRelease, reopened, onClick }) {
  const statusConfig = {
    open: { label: 'Open', className: 'status-badge status-badge-open' },
    in_progress: { label: 'In Progress', className: 'status-badge status-badge-in-progress' },
    resolved: { label: 'Resolved', className: 'status-badge status-badge-resolved' },
    ignored: { label: 'Ignored', className: 'status-badge status-badge-ignored' },
  }

  const config = statusConfig[status] || statusConfig.open
  const Component = onClick ? 'button' : 'span'
  const componentProps = onClick
    ? {
        onClick,
        type: 'button',
        title: 'Click to change status',
        'aria-label': 'Change issue status',
        style: {
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 4,
        },
      }
    : {}

  return (
    <Component className={config.className} {...componentProps}>
      {config.label}
      {reopened && status === 'open' && (
        <span className="status-badge-reopened" title="This issue was previously resolved and has been reopened">
          {' '}(reopened)
        </span>
      )}
      {status === 'resolved' && resolvedRelease && (
        <span className="status-badge-release"> ({resolvedRelease})</span>
      )}
      {onClick && (
        <svg
          width="10"
          height="10"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ opacity: 0.7, flexShrink: 0 }}
          aria-hidden="true"
        >
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
      )}
    </Component>
  )
}
