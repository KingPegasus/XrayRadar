import { navigate } from '../utils/navigation'

export function UsageWidget({ usage }) {
  if (!usage) return null

  return (
    <div style={{ marginTop: 14, padding: 14, background: 'rgba(255, 255, 255, 0.04)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="badge" style={{ background: usage.plan === 'Basic' ? 'rgba(79, 124, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)' }}>
            {usage.plan} Plan
          </span>
          <span style={{ fontSize: 13, color: 'var(--muted)' }}>
            {usage.current_count.toLocaleString()} / {usage.limit != null ? usage.limit.toLocaleString() : '∞'} events
          </span>
        </div>
        {usage.percentage_used != null && (
          <span style={{ fontSize: 13, color: usage.is_near_limit ? '#f59e0b' : 'var(--muted)' }}>
            {usage.percentage_used.toFixed(1)}% used
          </span>
        )}
      </div>
      {usage.limit != null && (
        <div style={{ marginTop: 10, height: 6, background: 'rgba(255, 255, 255, 0.1)', borderRadius: 3, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${Math.min(100, usage.percentage_used || 0)}%`,
              background: usage.is_exceeded ? '#ef4444' : usage.is_near_limit ? '#f59e0b' : '#4f7cff',
              borderRadius: 3,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      )}
      {usage.is_exceeded && (
        <div style={{ marginTop: 8, fontSize: 12, color: '#ef4444', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span>You've exceeded your event limit. New events will be rejected.</span>
          {usage.plan === 'Free' && (
            <button
              type="button"
              className="button buttonPrimary"
              style={{ fontSize: 11, padding: '4px 10px' }}
              onClick={() => navigate('/dashboard/settings')}
            >
              Upgrade
            </button>
          )}
        </div>
      )}
      {usage.is_near_limit && !usage.is_exceeded && (
        <div style={{ marginTop: 8, fontSize: 12, color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span>You're approaching your event limit.</span>
          {usage.plan === 'Free' && (
            <button
              type="button"
              className="button"
              style={{ fontSize: 11, padding: '4px 10px' }}
              onClick={() => navigate('/dashboard/settings')}
            >
              Upgrade
            </button>
          )}
        </div>
      )}
    </div>
  )
}
