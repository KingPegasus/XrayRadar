export function AccountInfoCard({ me }) {
  return (
    <section className="pageSection">
      <h2 className="pageSectionTitle">Account</h2>
      <div className="pageCard">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
            <span className="pageCardText" style={{ margin: 0 }}>Email</span>
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
            <span className="pageCardText" style={{ margin: 0 }}>Plan</span>
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
            <span className="pageCardText" style={{ margin: 0 }}>Member since</span>
            <span className="pageCardText" style={{ margin: 0 }}>
              {me?.created_at ? new Date(me.created_at).toLocaleDateString() : '—'}
            </span>
          </div>
        </div>
      </div>
    </section>
  )
}
