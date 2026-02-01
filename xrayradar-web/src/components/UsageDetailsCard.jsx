export function UsageDetailsCard({ usage, loading, error }) {
  return (
    <section className="pageSection">
      <h2 className="pageSectionTitle">Usage</h2>
      {loading ? (
        <p className="pageEmpty" style={{ margin: 0 }}>Loading usage…</p>
      ) : error ? (
        <div className="fieldError">{error}</div>
      ) : usage ? (
        <div className="pageCard">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
            <div>
              <span className="pageCardTitle" style={{ fontSize: 24 }}>{usage.current_count.toLocaleString()}</span>
              <span className="pageCardText" style={{ marginLeft: 8, display: 'inline' }}>
                / {usage.limit != null ? usage.limit.toLocaleString() : '∞'} events
              </span>
            </div>
            {usage.percentage_used != null && (
              <span style={{ fontSize: 13, color: usage.is_near_limit ? '#f59e0b' : 'var(--muted)' }}>
                {usage.percentage_used.toFixed(1)}% used
              </span>
            )}
          </div>
          {usage.limit != null && (
            <div style={{ height: 10, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 8, overflow: 'hidden', marginTop: 8 }}>
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, usage.percentage_used || 0)}%`,
                  background: usage.is_exceeded ? '#ef4444' : usage.is_near_limit ? '#f59e0b' : 'var(--brand)',
                  borderRadius: 8,
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          )}
          {usage.is_exceeded && (
            <div style={{ marginTop: 12, fontSize: 13, color: '#ef4444' }}>
              You've exceeded your event limit. New events will be rejected.
            </div>
          )}
          {usage.is_near_limit && !usage.is_exceeded && (
            <div style={{ marginTop: 12, fontSize: 13, color: '#f59e0b' }}>
              You're approaching your event limit.
            </div>
          )}
        </div>
      ) : null}
    </section>
  )
}
