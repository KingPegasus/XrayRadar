export function PlanDetailsCard({ me }) {
  return (
    <section className="pageSection">
      <h2 className="pageSectionTitle">Plan Details</h2>
      <div className="pageCard">
        {me?.plan === 'Free' ? (
          <>
            <div style={{ marginBottom: 12 }}>
              <div className="pageCardTitle" style={{ marginBottom: 8 }}>Free Plan</div>
              <ul className="pageCardText" style={{ margin: 0, paddingLeft: 20, lineHeight: 1.6 }}>
                <li>1,000 events storage</li>
                <li>No email alerts (upgrade for alerts)</li>
                <li>Basic API access</li>
              </ul>
            </div>
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 12 }}>
              <div className="pageCardText" style={{ marginBottom: 10 }}>
                Want more events and email alerts?
              </div>
              <a
                href={`mailto:dev@xrayradar.com?subject=Upgrade%20to%20Basic%20Plan&body=Hi,%0A%0AI'd%20like%20to%20upgrade%20my%20XrayRadar%20account%20to%20the%20Basic%20plan.%0A%0AEmail:%20${encodeURIComponent(me?.email || '')}%0A%0AThanks!`}
                className="button buttonPrimary"
                style={{ display: 'inline-block' }}
              >
                Contact to Upgrade ($3/mo)
              </a>
            </div>
          </>
        ) : me?.plan === 'Basic' ? (
          <>
            <div className="pageCardTitle" style={{ marginBottom: 8 }}>Basic Plan — $3/mo</div>
            <ul className="pageCardText" style={{ margin: 0, paddingLeft: 20, lineHeight: 1.6 }}>
              <li>Up to 15,000 events storage</li>
              <li>Email alerts (10 min cooldown)</li>
              <li>Priority ingestion (best effort)</li>
            </ul>
            <div className="pageCardText" style={{ marginTop: 12, fontSize: 12 }}>
              Billing is currently manual. Contact us for any plan changes.
            </div>
          </>
        ) : me?.plan === 'Teams' ? (
          <>
            <div className="pageCardTitle" style={{ marginBottom: 8 }}>Teams Plan — $5/mo</div>
            <ul className="pageCardText" style={{ margin: 0, paddingLeft: 20, lineHeight: 1.6 }}>
              <li>Up to 25,000 events storage</li>
              <li>Email alerts (1 min cooldown)</li>
              <li>Team access: invite up to 5 members</li>
            </ul>
            <div className="pageCardText" style={{ marginTop: 12, fontSize: 12 }}>
              Billing is currently manual. Contact us for any plan changes.
            </div>
          </>
        ) : me?.plan === 'Teams Pro' ? (
          <>
            <div className="pageCardTitle" style={{ marginBottom: 8 }}>Teams Pro Plan — $7/mo</div>
            <ul className="pageCardText" style={{ margin: 0, paddingLeft: 20, lineHeight: 1.6 }}>
              <li>Up to 50,000 events storage</li>
              <li>Email alerts (1 min cooldown)</li>
              <li>Team access: invite up to 10 members</li>
            </ul>
            <div className="pageCardText" style={{ marginTop: 12, fontSize: 12 }}>
              Billing is currently manual. Contact us for any plan changes.
            </div>
          </>
        ) : (
          <p className="pageCardText" style={{ margin: 0 }}>
            You're on the {me?.plan || 'Unknown'} plan.
          </p>
        )}
      </div>
    </section>
  )
}
