import { useState } from 'react'
import { Link } from './Link'
import { Logo } from './Logo'

export function DashboardLayout({ me, onLogout, children }) {
  const [logoError, setLogoError] = useState(false)
  return (
    <>
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
