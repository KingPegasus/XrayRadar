export function UsageDetailsCard({ usage, loading, error }) {
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Usage</div>
      {loading ? (
        <div style={{ color: 'var(--muted)', fontSize: 13 }}>Loading usage...</div>
      ) : error ? (
        <div className="fieldError">{error}</div>
      ) : usage ? (
        <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
            <div>
              <span style={{ fontSize: 24, fontWeight: 700 }}>{usage.current_count.toLocaleString()}</span>
              <span style={{ color: 'var(--muted)', fontSize: 14, marginLeft: 6 }}>
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
            <div style={{ height: 8, background: 'rgba(255, 255, 255, 0.1)', borderRadius: 4, overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, usage.percentage_used || 0)}%`,
                  background: usage.is_exceeded ? '#ef4444' : usage.is_near_limit ? '#f59e0b' : '#4f7cff',
                  borderRadius: 4,
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
    </div>
  )
}
