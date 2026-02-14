import { Link } from '../components/Link'

export function PrivacyPolicyPage() {
  return (
    <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
      <div className="container" style={{ maxWidth: 800 }}>
        <div className="pageCard">
          <header className="pageHeader">
            <h1 className="pageTitle">Privacy Policy</h1>
            <p className="pageSubtitle">
              Effective: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
            <div style={{ marginTop: 12 }}>
              <Link to="/" className="small">Back to home</Link>
            </div>
          </header>

          <section className="pageSection" style={{ marginTop: 24 }}>
            <h2 className="pageSectionTitle">Scope</h2>
            <p className="pageCardText">
              This Privacy Policy applies to personal information we collect through the XrayRadar website, dashboard, and authentication. It does not cover &quot;Service Data&quot;—error and event data that you send to XrayRadar via our SDKs from your applications. We process Service Data on your behalf; you are responsible for ensuring your collection and use of that data complies with applicable laws.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Information We Collect</h2>
            <p className="pageCardText">
              <strong>Account data:</strong> When you sign up, we collect your email address and password (stored in hashed form). We use this to create and manage your account and authenticate you.
            </p>
            <p className="pageCardText">
              <strong>Session cookies:</strong> We use cookies to maintain your session (e.g., <code>xrayradar_user_session</code>) and, when using GitHub OAuth, for OAuth state (<code>xrayradar_oauth_state</code>). These are essential for the service to function.
            </p>
            <p className="pageCardText">
              <strong>Service Data:</strong> When you use our SDKs, your applications send error events (stack traces, breadcrumbs, user context, etc.) to our servers. We store and display this data to provide the error-tracking service. You control what data your applications send; we recommend scrubbing sensitive information before sending.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">How We Use Your Information</h2>
            <p className="pageCardText">
              We use your information to provide, maintain, and improve the XrayRadar service; to authenticate you; to send verification and password-reset emails and optional alert notifications (via Resend); and to communicate with you about the service.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Cookies</h2>
            <p className="pageCardText">
              We use essential session cookies to keep you logged in and to support OAuth flows. These cookies are necessary for the service to work. We do not use third-party advertising cookies. You can disable cookies in your browser, but doing so may prevent you from using the dashboard.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Subprocessors</h2>
            <p className="pageCardText">
              We use third-party services to operate XrayRadar, including Resend (email delivery), our hosting provider, and our database (PostgreSQL). These providers process data on our behalf under agreements designed to protect your information.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Data Retention</h2>
            <p className="pageCardText">
              We retain your account data for as long as your account is active. When you request account deletion and an admin fulfills the request, we delete your account and associated data. Deletion is completed within 30 days, except where we must retain data to comply with legal obligations.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Your Rights</h2>
            <p className="pageCardText">
              Depending on your location, you may have the right to access, correct, or delete your personal information; to restrict or object to processing; and to data portability. You can request account deletion from your dashboard settings. For other requests, contact us at <a href="mailto:dev@xrayradar.com">dev@xrayradar.com</a>.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">International Transfers</h2>
            <p className="pageCardText">
              Your data may be stored and processed in the United States or other regions where our service providers operate. We take steps to ensure appropriate safeguards when data is transferred across borders.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Children&apos;s Privacy</h2>
            <p className="pageCardText">
              XrayRadar is not intended for individuals under 13 years of age. We do not knowingly collect personal information from children under 13. If you believe we have collected such information, please contact us.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">GDPR and CCPA</h2>
            <p className="pageCardText">
              We aim to comply with the EU General Data Protection Regulation (GDPR) and the California Consumer Privacy Act (CCPA). We do not sell your personal information. If you have questions about our compliance, please contact us.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Changes</h2>
            <p className="pageCardText">
              We may update this Privacy Policy from time to time. We will post the current version on this page and update the effective date. If we make material changes that reduce your rights, we will notify you by email or through the service.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Contact</h2>
            <p className="pageCardText">
              For privacy-related questions or requests, contact us at <a href="mailto:dev@xrayradar.com">dev@xrayradar.com</a>.
            </p>
          </section>

          <div style={{ marginTop: 32 }}>
            <Link to="/" className="small">Back to home</Link>
          </div>
        </div>
      </div>
    </main>
  )
}
