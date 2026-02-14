import { useState } from 'react'
import { Link } from '../components/Link'
import { SectionHeader } from '../components/SectionHeader'
import { Check } from '../components/Check'
import { Logo } from '../components/Logo'
import { FrameworkLogo } from '../components/FrameworkLogo'
import { FEATURES } from '../utils/constants'
import {
  SDK_FRAMEWORKS,
  QUICK_SETUP_SNIPPETS,
  PYPI_URL,
  NPM_URL,
} from '../utils/sdkFrameworks'

const DEFAULT_LANG = 'python'
const DEFAULT_FRAMEWORK = { python: 'fastapi', js: 'node' }

export function LandingPage({ me, onSignupOpen, onLogout }) {
  const [logoError, setLogoError] = useState(false)
  const [quickLang, setQuickLang] = useState(DEFAULT_LANG)
  const [quickFramework, setQuickFramework] = useState(DEFAULT_FRAMEWORK[DEFAULT_LANG])

  const frameworks = SDK_FRAMEWORKS[quickLang]
  const snippetKey = `${quickLang}_${quickFramework}`
  const snippet = QUICK_SETUP_SNIPPETS[snippetKey]

  const setLang = (lang) => {
    setQuickLang(lang)
    setQuickFramework(DEFAULT_FRAMEWORK[lang])
  }

  return (
    <>
      <header className="nav">
        <div className="container navInner">
          <a className="brand" href="#top">
            {!logoError && (
              <span className="logo" aria-hidden="true">
                <Logo width={230} height={44} onError={() => setLogoError(true)} />
              </span>
            )}
            {logoError && <span className="brand-text">XrayRadar</span>}
          </a>
          <nav className="navLinks" aria-label="Primary">
            <a href="#features">Features</a>
            <a href="#sdks">SDKs</a>
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
                <a className="button" href="/login">
                  Sign in
                </a>
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
                XrayRadar is a minimal error tracking service: lightweight SDKs + a simple server.
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
              <div className="quickSetupTabs" role="tablist" aria-label="Quick setup tech stack">
                <div className="quickSetupLevel quickSetupLevelLang">
                  <div className="quickSetupLangTabs">
                    <button
                      type="button"
                      role="tab"
                      aria-selected={quickLang === 'python'}
                      aria-controls="quick-setup-panel"
                      id="tab-python"
                      className={quickLang === 'python' ? 'quickSetupTab quickSetupTabLang quickSetupTabActive' : 'quickSetupTab quickSetupTabLang'}
                      onClick={() => setLang('python')}
                    >
                      Python
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={quickLang === 'js'}
                      aria-controls="quick-setup-panel"
                      id="tab-js"
                      className={quickLang === 'js' ? 'quickSetupTab quickSetupTabLang quickSetupTabActive' : 'quickSetupTab quickSetupTabLang'}
                      onClick={() => setLang('js')}
                    >
                      JavaScript
                    </button>
                  </div>
                </div>
                <div className="quickSetupLevel quickSetupLevelFramework">
                  <div className="quickSetupFrameworkTabs" role="tablist">
                    {frameworks.map((fw) => (
                      <button
                        key={fw.id}
                        type="button"
                        role="tab"
                        aria-selected={quickFramework === fw.id}
                        aria-controls="quick-setup-panel"
                        id={`tab-${fw.id}`}
                        className={quickFramework === fw.id ? 'quickSetupTab quickSetupTabFramework quickSetupTabActive' : 'quickSetupTab quickSetupTabFramework'}
                        onClick={() => setQuickFramework(fw.id)}
                      >
                        {fw.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="kbd" style={{ marginTop: 12 }} id="quick-setup-panel" role="tabpanel" aria-labelledby={`tab-${quickFramework}`}>
                Quick setup — {snippet?.label ?? ''}
              </div>
              {snippet && (
                <pre className="code" style={{ marginTop: 12 }}>{snippet.code}</pre>
              )}
              <div style={{ marginTop: 12, fontSize: 13, color: 'var(--muted)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                {quickLang === 'python' ? (
                  <>
                    <a href={PYPI_URL} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand)', textDecoration: 'underline' }}>
                      View on PyPI →
                    </a>
                    <span style={{ opacity: 0.7 }}>Also works with Graphene Django</span>
                  </>
                ) : (
                  <>
                    <a href={NPM_URL} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand)', textDecoration: 'underline' }}>
                      View on npm →
                    </a>
                    <span style={{ opacity: 0.7 }}>Also: Remix, Vite</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="section sectionSdk" id="sdks">
          <div className="container">
            <SectionHeader
              title="Integrate with your stack"
              desc="Official SDKs for Python and JavaScript/TypeScript with first-class framework support."
            />
            <div className="sdkGrid">
              <div className="sdkCard panel">
                <h3 className="sdkCardTitle">Python</h3>
                <p className="sdkCardDesc">Official SDK on PyPI — middleware for Django, FastAPI, Flask.</p>
                <div className="sdkFrameworks" role="list">
                  {SDK_FRAMEWORKS.python.map((fw) => (
                    <span key={fw.id} className="sdkFrameworkChip" role="listitem">
                      <FrameworkLogo logoId={fw.logoId} size={24} alt={fw.name} />
                      <span className="sdkFrameworkChipName">{fw.name}</span>
                    </span>
                  ))}
                </div>
                <a href={PYPI_URL} target="_blank" rel="noopener noreferrer" className="sdkLink">
                  View on PyPI →
                </a>
              </div>
              <div className="sdkCard panel">
                <h3 className="sdkCardTitle">JavaScript / TypeScript</h3>
                <p className="sdkCardDesc">Packages on npm — Node, browser, React, Next.js, Remix.</p>
                <div className="sdkFrameworks" role="list">
                  {SDK_FRAMEWORKS.js.map((fw) => (
                    <span key={fw.id} className="sdkFrameworkChip" role="listitem">
                      <FrameworkLogo logoId={fw.logoId} size={24} alt={fw.name} />
                      <span className="sdkFrameworkChipName">{fw.name}</span>
                    </span>
                  ))}
                </div>
                <a href={NPM_URL} target="_blank" rel="noopener noreferrer" className="sdkLink">
                  View on npm →
                </a>
              </div>
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
                  <li><Check /> 1,000 events stored</li>
                  <li><Check /> Early access account</li>
                  <li><Check /> Token-based auth</li>
                  <li><Check /> Minimal ingestion API + storage</li>
                  <li><Check /> No email alerts (upgrade for alerts)</li>
                </ul>
                <div style={{ marginTop: 16 }}>
                  <button type="button" className="button buttonPrimary" onClick={() => onSignupOpen('Free')}>
                    Choose Free
                  </button>
                </div>
              </div>

              <div className="card panel" style={{ borderColor: 'rgba(79, 124, 255, 0.38)' }}>
                <div className="badge">Basic</div>
                <div className="price">$3<span style={{ color: 'var(--muted)', fontSize: 14, fontWeight: 600 }}>/mo</span></div>
                <div className="small" style={{ color: 'var(--muted)' }}>Early access paid plan (no automated billing yet)</div>
                <ul className="list">
                  <li><Check /> Up to 15,000 events storage</li>
                  <li><Check /> Priority ingestion (best effort)</li>
                  <li><Check /> Email alerts (10 min cooldown)</li>
                </ul>
                <div style={{ marginTop: 16 }}>
                  <button type="button" className="button buttonPrimary" onClick={() => onSignupOpen('Basic')}>
                    Choose Basic
                  </button>
                </div>
              </div>

              <div className="card panel" style={{ borderColor: 'rgba(158, 124, 255, 0.38)' }}>
                <div className="badge">Teams</div>
                <div className="price">$5<span style={{ color: 'var(--muted)', fontSize: 14, fontWeight: 600 }}>/mo</span></div>
                <div className="small" style={{ color: 'var(--muted)' }}>Team access, up to 5 members</div>
                <ul className="list">
                  <li><Check /> Up to 25,000 events storage</li>
                  <li><Check /> Email alerts (1 min cooldown)</li>
                  <li><Check /> Environment views + member environment ACL</li>
                  <li><Check /> Environment-scoped alert routing</li>
                  <li><Check /> Team access: invite up to 5 members, assign projects</li>
                  <li><Check /> Revoke access per project or remove from team</li>
                </ul>
                <div style={{ marginTop: 16 }}>
                  <button type="button" className="button buttonPrimary" onClick={() => onSignupOpen('Teams')}>
                    Choose Teams
                  </button>
                </div>
              </div>

              <div className="card panel" style={{ borderColor: 'rgba(158, 124, 255, 0.38)' }}>
                <div className="badge">Teams Pro</div>
                <div className="price">$7<span style={{ color: 'var(--muted)', fontSize: 14, fontWeight: 600 }}>/mo</span></div>
                <div className="small" style={{ color: 'var(--muted)' }}>Larger team, up to 10 members</div>
                <ul className="list">
                  <li><Check /> Up to 50,000 events storage</li>
                  <li><Check /> Email alerts (1 min cooldown)</li>
                  <li><Check /> Environment views + member environment ACL</li>
                  <li><Check /> Environment-scoped alert routing</li>
                  <li><Check /> Team access: invite up to 10 members</li>
                  <li><Check /> Revoke access per project or remove from team</li>
                </ul>
                <div style={{ marginTop: 16 }}>
                  <button type="button" className="button buttonPrimary" onClick={() => onSignupOpen('Teams Pro')}>
                    Choose Teams Pro
                  </button>
                </div>
              </div>
            </div>

            <p className="sectionDesc" style={{ marginTop: 14 }}>
              Enterprise (SAML, audit logs, longer retention) is planned.
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
                  No. The DSN is a simple project endpoint like <code>https://xrayradar.com/&lt;project_id&gt;</code>. Auth is done via token header.
                </p>
              </div>
              <div className="card">
                <h3 className="cardTitle">Where do I find my token after creating it?</h3>
                <p className="cardText">
                  Client tokens can be viewed anytime in your tokens page.
                </p>
              </div>
              <div className="card">
                <h3 className="cardTitle">Do you offer self-hosting?</h3>
                <p className="cardText">
                  XrayRadar is offered as a hosted service. If you need a dedicated deployment or on-prem setup, reach out and we'll discuss options.
                </p>
              </div>
            </div>
          </div>
        </section>

        <footer className="footer">
          <div className="container footerInner">
            <div className="small">© {new Date().getFullYear()} XrayRadar</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
              <div className="small" style={{ display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap' }}>
                <a href="#features">Features</a>
                <a href="#sdks">SDKs</a>
                <a href="#pricing">Pricing</a>
                <a href="https://pypi.org/project/xrayradar/" target="_blank" rel="noopener noreferrer">Python SDK</a>
                <a href="https://www.npmjs.com/package/@xrayradar/node" target="_blank" rel="noopener noreferrer">JavaScript SDK</a>
                <Link to="/privacy">Privacy Policy</Link>
                <Link to="/terms">Terms of Service</Link>
                <a href="mailto:dev@xrayradar.com">Contact</a>
                <a href="#top">Back to top</a>
              </div>
              <a 
                href="https://www.linkedin.com/company/xrayradar" 
                target="_blank" 
                rel="noopener noreferrer"
                aria-label="LinkedIn"
                style={{ display: 'inline-flex', alignItems: 'center', color: 'var(--muted-2)' }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style={{ display: 'block' }}>
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
              </a>
            </div>
          </div>
        </footer>
      </main>
    </>
  )
}
