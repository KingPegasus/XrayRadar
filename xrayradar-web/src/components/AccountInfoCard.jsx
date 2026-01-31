export function AccountInfoCard({ me }) {
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Account</div>
      <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
            <span style={{ color: 'var(--muted)', fontSize: 13 }}>Email</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13 }}>{me?.email || '—'}</span>
              {me?.email_verified ? (
                <span className="badge" style={{ background: 'rgba(134, 239, 172, 0.2)', color: '#86efac', fontSize: 10 }}>
                  Verified
                </span>
              ) : (
                <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', fontSize: 10 }}>
                  Unverified
                </span>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
            <span style={{ color: 'var(--muted)', fontSize: 13 }}>Plan</span>
            <span
              className="badge"
              style={{
                background: me?.plan === 'Basic' ? 'rgba(79, 124, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)',
              }}
            >
              {me?.plan || 'Free'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
            <span style={{ color: 'var(--muted)', fontSize: 13 }}>Member since</span>
            <span style={{ fontSize: 13 }}>
              {me?.created_at ? new Date(me.created_at).toLocaleDateString() : '—'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
