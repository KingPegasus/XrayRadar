import { Link } from './Link'
import { Logo } from './Logo'

export function DashboardLayout({ me, onLogout, children }) {
  return (
    <>
      <header className="nav">
        <div className="container navInner">
          <Link className="brand" to="/">
            <span className="logo" aria-hidden="true">
              <Logo size={36} />
            </span>
            <span>XrayRadar</span>
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
