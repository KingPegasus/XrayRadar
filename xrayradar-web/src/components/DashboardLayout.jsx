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
                <Logo width={120} height={36} onError={() => setLogoError(true)} />
              </span>
            )}
            {logoError && <span className="brand-text">XrayRadar</span>}
          </Link>
          <nav className="navLinks" aria-label="Primary">
            <Link to="/dashboard">Projects</Link>
            <Link to="/dashboard/tokens">Tokens</Link>
            <Link to="/dashboard/settings">Settings</Link>
            {me?.plan && (
              <span
                className="badge"
                style={{
                  background: me.plan === 'Basic' ? 'rgba(79, 124, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)',
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
    </>
  )
}
