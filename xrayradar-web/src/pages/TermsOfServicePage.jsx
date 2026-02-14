import { Link } from '../components/Link'

export function TermsOfServicePage() {
  return (
    <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
      <div className="container" style={{ maxWidth: 800 }}>
        <div className="pageCard">
          <header className="pageHeader">
            <h1 className="pageTitle">Terms of Service</h1>
            <p className="pageSubtitle">
              Effective: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
            <div style={{ marginTop: 12 }}>
              <Link to="/" className="small">Back to home</Link>
            </div>
          </header>

          <section className="pageSection" style={{ marginTop: 24 }}>
            <h2 className="pageSectionTitle">Acceptance</h2>
            <p className="pageCardText">
              By accessing or using XrayRadar, you agree to be bound by these Terms of Service. If you do not agree, do not use the service. Our <Link to="/privacy">Privacy Policy</Link> describes how we collect and use information and is incorporated into these Terms.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Service Description</h2>
            <p className="pageCardText">
              XrayRadar is an error-tracking and monitoring service. We offer Free, Basic, and Pro tiers. Service availability, features, and limits may change over time.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Account</h2>
            <p className="pageCardText">
              You are responsible for maintaining the security of your account credentials and for all activity under your account. You must provide accurate information and keep it up to date. You must use a secure password and not share it.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Acceptable Use</h2>
            <p className="pageCardText">
              You may not use the service for any illegal purpose or in violation of applicable laws. You may not abuse, overload, or reverse-engineer the service. You must not use the service to transmit malware, spam, or content that infringes third-party rights.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">User Content and Service Data</h2>
            <p className="pageCardText">
              You retain ownership of any content or data you submit to XrayRadar. By using the service, you grant us a license to process, store, and display that data as necessary to provide the service. You are responsible for ensuring that the data you send via our SDKs (including personally identifiable information) complies with applicable law and that you have the right to share it with us.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Fees</h2>
            <p className="pageCardText">
              Free, Basic, and Pro plans are available. Payment terms apply where fees are charged. Fees are generally non-refundable. We may change pricing with reasonable notice.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Termination</h2>
            <p className="pageCardText">
              You may stop using the service at any time and request account deletion. We may suspend or terminate your access if you violate these Terms or for other reasons at our discretion. Upon termination, your right to use the service ends. We may retain some data as required by law or for legitimate business purposes.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Disclaimers</h2>
            <p className="pageCardText">
              THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED. WE DO NOT GUARANTEE UNAVAILABILITY OF THE SERVICE OR THAT IT WILL MEET YOUR REQUIREMENTS.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Limitation of Liability</h2>
            <p className="pageCardText">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, OUR AGGREGATE LIABILITY FOR CLAIMS ARISING OUT OF OR RELATED TO THE SERVICE SHALL NOT EXCEED THE FEES YOU PAID US IN THE SIX (6) MONTHS PRECEDING THE CLAIM. WE ARE NOT LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Indemnity</h2>
            <p className="pageCardText">
              You agree to indemnify and hold harmless XrayRadar and its affiliates from claims, damages, and expenses (including legal fees) arising from your use of the service, your violation of these Terms, or your violation of any third-party rights.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Governing Law</h2>
            <p className="pageCardText">
              These Terms are governed by the laws of the jurisdiction in which XrayRadar operates. Any disputes shall be resolved in the courts of that jurisdiction. Please contact us for the applicable governing law if unclear.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Changes</h2>
            <p className="pageCardText">
              We may modify these Terms from time to time. We will post the updated Terms on this page and update the effective date. Continued use of the service after changes constitutes acceptance of the revised Terms.
            </p>
          </section>

          <section className="pageSection">
            <h2 className="pageSectionTitle">Contact</h2>
            <p className="pageCardText">
              For questions about these Terms, contact us at <a href="mailto:dev@xrayradar.com">dev@xrayradar.com</a>.
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
