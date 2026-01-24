import { Link } from '../components/Link'
import { SectionHeader } from '../components/SectionHeader'
import { Check } from '../components/Check'
import { FEATURES } from '../utils/constants'

export function LandingPage({ me, onSignupOpen, onLogout }) {
  return (
    <>
      <header className="nav">
        <div className="container navInner">
          <a className="brand" href="#top">
            <span className="logo" aria-hidden="true" />
            <span>Xrayradar</span>
          </a>
          <nav className="navLinks" aria-label="Primary">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#faq">FAQ</a>
            {me ? (
              <>
                <Link className="button" to="/dashboard">
                  Dashboard
                </Link>
                <button type="button" className="button buttonPrimary" onClick={onLogout}>
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link className="button" to="/login">
                  Sign in
                </Link>
                <a className="button buttonPrimary" href="#pricing">
                  Get started
                </a>
              </>
            )}
          </nav>
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="container heroGrid">
            <div>
              <h1 className="h1">
                Error tracking that stays out of your way.
              </h1>
              <p className="lead">
                Xrayradar is a minimal error tracking stack: lightweight SDKs + a simple server.
                Capture exceptions, keep context, and debug faster — without the bloat.
              </p>

              <div style={{ display: 'flex', gap: 12, marginTop: 18, flexWrap: 'wrap' }}>
                <a className="button buttonPrimary" href="#pricing">View pricing</a>
                <a className="button" href="#features">See features</a>
              </div>

              <div style={{ marginTop: 18, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <span className="badge">SDK + Server</span>
                <span className="badge">Hosted service</span>
                <span className="badge">Fast to integrate</span>
              </div>
            </div>

            <div className="panel heroCard">
              <div className="kbd">Quick setup</div>
              <pre className="code" style={{ marginTop: 12 }}>{`# Install
pip install xrayradar

# Env
XRAYRADAR_DSN=http://localhost:8001/1
XRAYRADAR_AUTH_TOKEN=<token>

# Capture
from xrayradar import init, capture_exception

client = init(dsn=XRAYRADAR_DSN, auth_token=XRAYRADAR_AUTH_TOKEN)
try:
    1 / 0
except Exception as e:
    capture_exception(e)`}</pre>
            </div>
          </div>
        </section>

        <section className="section" id="features">
          <div className="container">
            <SectionHeader
              title="Built for shipping"
              desc="A small, predictable system: capture errors with clean metadata, store them, and make debugging boring again."
            />

            <div className="grid3">
              {FEATURES.map((f) => (
                <div className="card" key={f.title}>
                  <h3 className="cardTitle">{f.title}</h3>
                  <p className="cardText">{f.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="section" id="pricing">
          <div className="container">
            <SectionHeader
              title="Simple pricing"
              desc="Start free. Upgrade when you want a paid plan (early access)."
            />

            <div className="pricingGrid">
              <div className="card panel">
                <div className="badge">Free</div>
                <div className="price">$0<span style={{ color: 'var(--muted)', fontSize: 14, fontWeight: 600 }}>/mo</span></div>
                <div className="small" style={{ color: 'var(--muted)' }}>Best for testing and small apps</div>
                <ul className="list">
                  <li><Check /> Early access account</li>
                  <li><Check /> Token-based auth</li>
                  <li><Check /> Minimal ingestion API + storage</li>
                </ul>
                <div style={{ marginTop: 16 }}>
                  <button type="button" className="button buttonPrimary" onClick={() => onSignupOpen('Free')}>
                    Choose Free
                  </button>
                </div>
              </div>

              <div className="card panel" style={{ borderColor: 'rgba(79, 124, 255, 0.38)' }}>
                <div className="badge">Basic</div>
                <div className="price">$1<span style={{ color: 'var(--muted)', fontSize: 14, fontWeight: 600 }}>/mo</span></div>
                <div className="small" style={{ color: 'var(--muted)' }}>Early access paid plan (no automated billing yet)</div>
                <ul className="list">
                  <li><Check /> 50,000 errors stored</li>
                  <li><Check /> Everything in Free</li>
                  <li><Check /> Priority ingestion (best effort)</li>
                </ul>
                <div style={{ marginTop: 16 }}>
                  <button type="button" className="button buttonPrimary" onClick={() => onSignupOpen('Basic')}>
                    Choose Basic
                  </button>
                </div>
              </div>
            </div>

            <p className="sectionDesc" style={{ marginTop: 14 }}>
              Need more? Team/Enterprise tiers are planned (SAML, audit logs, longer retention).
            </p>
          </div>
        </section>

        <section className="section" id="faq">
          <div className="container">
            <SectionHeader title="FAQ" desc="Short answers to common questions." />

            <div className="grid3">
              <div className="card">
                <h3 className="cardTitle">Is the DSN supposed to contain credentials?</h3>
                <p className="cardText">
                  No. The DSN is a simple project endpoint like <code>http://host:port/&lt;project_id&gt;</code>. Auth is done via token header.
                </p>
              </div>
              <div className="card">
                <h3 className="cardTitle">Where do I find my token after creating it?</h3>
                <p className="cardText">
                  For security, the token value is shown only once at creation. Copy it and store it in your secrets manager.
                </p>
              </div>
              <div className="card">
                <h3 className="cardTitle">Do you offer self-hosting?</h3>
                <p className="cardText">
                  Xrayradar is offered as a hosted service. If you need a dedicated deployment or on-prem setup, reach out and we'll discuss options.
                </p>
              </div>
            </div>
          </div>
        </section>

        <footer className="footer">
          <div className="container footerInner">
            <div className="small">© {new Date().getFullYear()} Xrayradar</div>
            <div className="small" style={{ display: 'flex', gap: 14 }}>
              <a href="#features">Features</a>
              <a href="#pricing">Pricing</a>
              <a href="#top">Back to top</a>
            </div>
          </div>
        </footer>
      </main>
    </>
  )
}
