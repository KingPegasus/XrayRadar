export function PlanDetailsCard({ me }) {
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#cbd5e1' }}>Plan Details</div>
      <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: 16, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
        {me?.plan === 'Free' ? (
          <>
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Free Plan</div>
              <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--muted)', fontSize: 13, lineHeight: 1.6 }}>
                <li>5,000 events storage</li>
                <li>Email alerts (10 min cooldown)</li>
                <li>Basic API access</li>
              </ul>
            </div>
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 12, marginTop: 12 }}>
              <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 10 }}>
                Want more events and faster alerts?
              </div>
              <a
                href={`mailto:dev@xrayradar.com?subject=Upgrade%20to%20Basic%20Plan&body=Hi,%0A%0AI'd%20like%20to%20upgrade%20my%20XrayRadar%20account%20to%20the%20Basic%20plan.%0A%0AEmail:%20${encodeURIComponent(me?.email || '')}%0A%0AThanks!`}
                className="button buttonPrimary"
                style={{ display: 'inline-block' }}
              >
                Contact to Upgrade ($1/mo)
              </a>
            </div>
          </>
        ) : me?.plan === 'Basic' ? (
          <>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Basic Plan — $1/mo</div>
            <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--muted)', fontSize: 13, lineHeight: 1.6 }}>
              <li>50,000 events storage</li>
              <li>Email alerts (1 min cooldown)</li>
              <li>Priority ingestion (best effort)</li>
            </ul>
            <div style={{ marginTop: 12, fontSize: 12, color: 'var(--muted)' }}>
              Billing is currently manual. Contact us for any plan changes.
            </div>
          </>
        ) : (
          <div style={{ color: 'var(--muted)', fontSize: 13 }}>
            You're on the {me?.plan || 'Unknown'} plan.
          </div>
        )}
      </div>
    </div>
  )
}
