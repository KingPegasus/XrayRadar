export function DashboardHome({ me }) {
  return (
    <main style={{ padding: '46px 0' }}>
      <div className="container">
        <div className="panel" style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontWeight: 900, letterSpacing: '-0.02em', fontSize: 22 }}>Dashboard</div>
              <div className="small" style={{ color: 'var(--muted)', marginTop: 8 }}>
                Signed in as <code>{me?.email}</code>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <span className="badge">Projects</span>
              <span className="badge">Tokens</span>
              <span className="badge">Issues</span>
            </div>
          </div>

          <div className="card" style={{ marginTop: 14, background: 'rgba(255, 255, 255, 0.04)' }}>
            <div className="cardTitle">Getting started</div>
            <p className="cardText">
              Create a project, request a token from an admin, then send test events and inspect grouped issues.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
