import React from 'react'

const FEATURES = [
  {
    title: 'Lightweight SDKs',
    text: 'Drop-in error capture for your apps. Keep the payload clean and predictable, and ship without heavy dependencies.',
  },
  {
    title: 'Simple DSN + Token auth',
    text: 'Point your app at a project DSN and authenticate using a token header. No embedded credentials in DSNs.',
  },
  {
    title: 'Minimal server + ingestion API',
    text: 'Store events, keep payloads searchable, and debug quickly. Built to stay simple and reliable.',
  },
]

function Check() {
  return <span className="dot" aria-hidden="true" />
}

function SectionHeader({ title, desc }) {
  return (
    <div>
      <h2 className="sectionTitle">{title}</h2>
      {desc ? <p className="sectionDesc">{desc}</p> : null}
    </div>
  )
}

function _isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || '').trim())
}

function SignupModal({ open, plan, onClose }) {
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [confirm, setConfirm] = React.useState('')
  const [error, setError] = React.useState('')
  const [submitting, setSubmitting] = React.useState(false)
  const [done, setDone] = React.useState(false)

  React.useEffect(() => {
    if (open) {
      setEmail('')
      setPassword('')
      setConfirm('')
      setError('')
      setSubmitting(false)
      setDone(false)
    }
  }, [open])

  const _readErrorMessage = async (resp) => {
    try {
      const data = await resp.json()
      if (data && typeof data.detail === 'string' && data.detail.trim()) {
        return data.detail
      }
    } catch {
      // ignore
    }
    return `Request failed (${resp.status})`
  }

  const _getMe = async () => {
    try {
      const resp = await fetch('/api/me', { credentials: 'include' })
      if (!resp.ok) return null
      return await resp.json()
    } catch {
      return null
    }
  }

  if (!open) return null

  const submit = async (e) => {
    e.preventDefault()
    if (submitting) return

    const trimmedEmail = email.trim().toLowerCase()
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }

    setError('')
    setSubmitting(true)
    try {
      const resp = await fetch('/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: trimmedEmail, password, plan }),
      })

      if (!resp.ok) {
        setError(await _readErrorMessage(resp))
        return
      }

      await _getMe()
      setDone(true)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modalOverlay" role="dialog" aria-modal="true" aria-label="Sign up">
      <div className="modalCard panel">
        <div className="modalHeader">
          <div>
            <div className="badge">{plan}</div>
            <div style={{ marginTop: 10, fontWeight: 800, letterSpacing: '-0.02em', fontSize: 18 }}>
              {done ? 'You’re in!' : 'Create your account'}
            </div>
            <div className="small" style={{ color: 'var(--muted)', marginTop: 6 }}>
              {done
                ? 'You can now continue and we’ll use this session for the dashboard later.'
                : 'Use an email + password to create your account.'}
            </div>
          </div>
          <button type="button" className="modalClose" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {done ? (
          <div style={{ marginTop: 14 }}>
            <div className="card" style={{ background: 'rgba(255, 255, 255, 0.04)' }}>
              <div className="cardTitle">Next steps</div>
              <p className="cardText">
                1) Create a token in your server
                <br />
                2) Set <code>XRAYRADAR_DSN</code> and <code>XRAYRADAR_AUTH_TOKEN</code>
                <br />
                3) Capture your first exception
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <button type="button" className="button buttonPrimary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={submit} style={{ marginTop: 14 }}>
            <label className="fieldLabel">Email</label>
            <input
              className="fieldInput"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              autoComplete="email"
            />

            <label className="fieldLabel" style={{ marginTop: 10 }}>
              Password
            </label>
            <input
              className="fieldInput"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              type="password"
              autoComplete="new-password"
            />

            <label className="fieldLabel" style={{ marginTop: 10 }}>
              Confirm password
            </label>
            <input
              className="fieldInput"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="••••••••"
              type="password"
              autoComplete="new-password"
            />

            {error ? (
              <div className="fieldError" role="alert" style={{ marginTop: 10 }}>
                {error}
              </div>
            ) : null}

            <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap' }}>
              <button className="button buttonPrimary" type="submit">
                Create account
              </button>
              <button className="button" type="button" onClick={onClose}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [signupOpen, setSignupOpen] = React.useState(false)
  const [signupPlan, setSignupPlan] = React.useState('Free')

  const openSignup = (plan) => {
    setSignupPlan(plan)
    setSignupOpen(true)
  }

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
            <a className="button buttonPrimary" href="#pricing">Get started</a>
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
                  <button type="button" className="button buttonPrimary" onClick={() => openSignup('Free')}>
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
                  <button type="button" className="button buttonPrimary" onClick={() => openSignup('Basic')}>
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
                  Xrayradar is offered as a hosted service. If you need a dedicated deployment or on-prem setup, reach out and we’ll discuss options.
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

      <SignupModal open={signupOpen} plan={signupPlan} onClose={() => setSignupOpen(false)} />
    </>
  )
}
