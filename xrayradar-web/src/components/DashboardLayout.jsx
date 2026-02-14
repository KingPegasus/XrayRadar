import { useState } from 'react'
import { Link } from './Link'
import { Logo } from './Logo'
import { EmailVerificationBanner } from './EmailVerificationBanner'

export function DashboardLayout({ me, onLogout, children }) {
  const [logoError, setLogoError] = useState(false)
  return (
    <>
      <EmailVerificationBanner me={me} />
      <header className="nav">
        <div className="container navInner">
          <Link className="brand" to="/">
            {!logoError && (
              <span className="logo" aria-hidden="true">
                <Logo width={230} height={44} onError={() => setLogoError(true)} />
              </span>
            )}
            {logoError && <span className="brand-text">XrayRadar</span>}
          </Link>
          <nav className="navLinks" aria-label="Primary">
            <Link to="/dashboard">Overview</Link>
            <Link to="/dashboard/projects">Projects</Link>
            <Link to="/dashboard/tokens">Tokens</Link>
            {(me?.plan === 'Teams' || me?.plan === 'Teams Pro') && <Link to="/dashboard/team">Team</Link>}
            <Link to="/dashboard/settings">Settings</Link>
            {me?.plan && (
              <span
                className="badge"
                style={{
                  background: (me.plan === 'Basic' || me.plan === 'Teams' || me.plan === 'Teams Pro') ? 'rgba(79, 124, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                  fontSize: 11,
                  padding: '4px 8px',
                }}
              >
                {me.plan}
              </span>
            )}
            <button type="button" className="button" onClick={onLogout}>
              Sign out
            </button>
          </nav>
        </div>
      </header>
      {children}
      <footer className="footer" style={{ padding: '16px 0' }}>
        <div className="container footerInner">
          <div className="small" style={{ display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap' }}>
            <Link to="/privacy">Privacy</Link>
            <Link to="/terms">Terms</Link>
            <a href="mailto:dev@xrayradar.com">Contact</a>
          </div>
        </div>
      </footer>
    </>
  )
}
